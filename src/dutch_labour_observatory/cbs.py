"""Small client for the CBS StatLine OData API."""

from __future__ import annotations

import json
import re
import tempfile
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://opendata.cbs.nl/ODataApi/OData"
TABLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
RESOURCE_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


class CbsApiError(RuntimeError):
    """Raised when a CBS response is not shaped like an OData response."""


class CbsODataClient:
    """Read paginated resources from one CBS StatLine table."""

    def __init__(
        self,
        *,
        base_url: str = BASE_URL,
        timeout_seconds: float = 30,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def fetch(
        self,
        table_id: str,
        resource: str = "TypedDataSet",
        *,
        select: Iterable[str] | None = None,
        filter_expression: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return all pages for an OData resource."""

        url = self._build_url(
            table_id,
            resource,
            select=select,
            filter_expression=filter_expression,
        )
        rows: list[dict[str, Any]] = []

        while url:
            payload = self._get_json(url)
            page = payload.get("value")
            if not isinstance(page, list):
                raise CbsApiError("CBS response does not contain a list-valued 'value'")
            if not all(isinstance(row, dict) for row in page):
                raise CbsApiError("CBS response contains a non-object observation")
            rows.extend(page)
            next_url = payload.get("@odata.nextLink") or payload.get("odata.nextLink")
            if next_url is not None and not isinstance(next_url, str):
                raise CbsApiError("CBS response contains an invalid pagination link")
            url = next_url

        return rows

    def _build_url(
        self,
        table_id: str,
        resource: str,
        *,
        select: Iterable[str] | None,
        filter_expression: str | None,
    ) -> str:
        if not TABLE_ID_PATTERN.fullmatch(table_id):
            raise ValueError("table_id may contain only letters and digits")
        if not RESOURCE_PATTERN.fullmatch(resource):
            raise ValueError(
                "resource may contain only letters, digits, and underscores"
            )

        query: dict[str, str] = {}
        if select:
            query["$select"] = ",".join(select)
        if filter_expression:
            query["$filter"] = filter_expression

        url = f"{self.base_url}/{table_id}/{resource}"
        return f"{url}?{urlencode(query)}" if query else url

    def _get_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "dutch-labour-observatory/0.1",
            },
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            payload = json.load(response)
        if not isinstance(payload, dict):
            raise CbsApiError("CBS response is not a JSON object")
        return payload


def write_snapshot(
    output_path: Path,
    *,
    table_id: str,
    resource: str,
    rows: list[dict[str, Any]],
) -> None:
    """Atomically write observations together with retrieval metadata."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "source": "Statistics Netherlands (CBS) StatLine",
        "table_id": table_id,
        "resource": resource,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "row_count": len(rows),
        "rows": rows,
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output_path.parent,
        delete=False,
        suffix=".tmp",
    ) as handle:
        json.dump(snapshot, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary_path = Path(handle.name)

    temporary_path.replace(output_path)

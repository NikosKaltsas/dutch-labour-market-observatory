from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.cbs import CbsODataClient, write_snapshot


class FakeResponse(io.BytesIO):
    pass


class CbsODataClientTests(unittest.TestCase):
    def test_fetch_follows_odata_pagination(self) -> None:
        payloads = iter(
            [
                {"value": [{"ID": 1}], "@odata.nextLink": "https://next"},
                {"value": [{"ID": 2}]},
            ]
        )
        requested_urls: list[str] = []

        def opener(request, *, timeout):
            self.assertEqual(timeout, 30)
            requested_urls.append(request.full_url)
            return FakeResponse(json.dumps(next(payloads)).encode("utf-8"))

        rows = CbsODataClient(opener=opener).fetch(
            "12345ENG",
            select=["ID", "Periods"],
            filter_expression="Periods eq '2025MM01'",
        )

        self.assertEqual(rows, [{"ID": 1}, {"ID": 2}])
        self.assertIn("%24select=ID%2CPeriods", requested_urls[0])
        self.assertEqual(requested_urls[1], "https://next")

    def test_rejects_unsafe_table_identifier(self) -> None:
        with self.assertRaises(ValueError):
            CbsODataClient().fetch("../secrets")

    def test_snapshot_contains_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            write_snapshot(
                output,
                table_id="12345ENG",
                resource="TypedDataSet",
                rows=[{"value": 7}],
            )
            snapshot = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(snapshot["row_count"], 1)
        self.assertEqual(snapshot["table_id"], "12345ENG")
        self.assertIn("retrieved_at_utc", snapshot)


if __name__ == "__main__":
    unittest.main()

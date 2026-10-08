# Local validation and publication checklist

## Validation on 2026-10-08 (Europe/Berlin)

Run from the project root using the existing local virtual environment:

| Check | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q` | 43 passed |
| `.venv/Scripts/python.exe -m ruff check .` | All checks passed |
| `.venv/Scripts/dbt.exe test --profiles-dir .` | 63 passed; 0 warnings, errors, or skips |
| PBIX archive structure | Two pages, both 1920 × 1080; saved definitions-page edits present |

These checks used the existing local warehouse and environment. They do not
constitute a fresh CBS extraction, a clean-environment rebuild, a Power BI refresh,
or a visual rendering test. The DAX companion files document the build; they are
not automatically synchronized with the binary model.

## Remaining report checks

- [x] Save explicit NoFilter overrides from the donut to **both** the gauge and
  quarterly column chart. Verified in the saved archive on 2026-10-08 after the
  author updated and saved the report. The overview is now the active page.
- [ ] Final visual regression check in Desktop: with 2022–2023 selected, gauge
  122.8 and all eight quarter bars remain unchanged after selecting Negative.
- [x] Capture the overview with All years selected and no visible chart selection.
  The saved PBIX has no Year selection filter and opens on the overview.
- [x] Review the author-supplied screenshots: both pages are readable, including
  the limitations text, without editing panes or tooltips. This is screenshot
  review, not an automated rendering test of every viewport.
- [x] Save the supplied images unchanged as `docs/images/overview.png` and
  `docs/images/definitions.png`, and embed them in the README. The quarterly chart
  scrollbar is explained in the caption.
- [ ] Optional wording polish: rename the donut center label to **Months in
  current selection**. The supplied screenshot still says **Months with available
  data**, which describes its All-years state but is less clear after a slice click.
- [ ] Review embedded model data and local source paths in Power BI before public
  release. The report intentionally includes CBS-derived imported data; this
  preparation does not certify the compressed model as free of private metadata.

## Repository and publication

- The repository boundary is this project directory, not the parent portfolio.
- Project `.gitignore` excludes the virtual environment, generated data, dbt
  artifacts, local dbt user ID, credentials, caches, and recovery files.
- The finished PBIX, public source catalogue, relative DuckDB profile, code,
  documentation, tests, and DAX are intended versioned assets.
- [x] Review staged file names and changes before the first commit: 79
  project-only files; no CVs, temporary files, virtual environment, raw exports,
  warehouse, dbt outputs, or local dbt user identity. Relative Markdown links
  resolve; Git whitespace check passes. A heuristic text credential scan found
  no matches, but is not a guarantee about the compressed PBIX model.
- [x] Owner and public visibility confirmed by the author. Published at
  https://github.com/NikosKaltsas/dutch-labour-market-observatory on 2026-10-08.
- [ ] Run a full clean-environment rebuild before claiming reproducibility has
  been validated end to end.

The optional written briefing and walkthrough remain backlog items, not completed
deliverables. No software license has been selected; choose one before describing
this repository as licensed open source. CBS source terms remain separate.

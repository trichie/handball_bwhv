# Handball BWHV

Prepare announcer player lists from public BWHV fixtures and match reports. The script caches completed league games, combines historical rosters for both teams, and exports printable Excel sheets with goals, roster appearances, and room for handwritten additions.

## Setup and run

Requires Python 3.13 or newer, uv, and internet access to Handball4all for fixtures and reports.

```sh
uv sync --locked
uv run handball_bwhv.py
```

Run from the project directory. Edit `parameters.json` before running:

| Setting | Meaning |
| --- | --- |
| `teams` | Worksheet/cache labels mapped to exact BWHV team names and league URLs. URLs must include `ogId` and `lId` in their fragment query. |
| `season` | Cache folder below `matches/`. |
| `next_date` | Selected match day as `YYYY-MM-DD`. |
| `excel_path` | Workbook destination; `{next_date}` is replaced with the selected date. |
| `n_matches` | Number of latest completed matches to consider per team; `null` means all available history. |
| `refresh` | Set to `true` to download and reparse successful cached reports too. |

Labels must be valid Excel worksheet names and suitable filename components. The supplied configuration is an example setup for three teams of TSV 1848 Bad Saulgau—the men's, women's, and second teams—in the 2026/2027 season.

League caches are saved to `matches/<season>/bwhv_<label>.json`. The default workbook destination is `output/matches_<next_date>.xlsx`; parent folders are created automatically. Existing destination workbooks are overwritten when an export is produced. If no preparations match the selected day, no workbook is written and any existing workbook remains.

Read console output for unavailable reports and partial preparations. Historical rosters do not guarantee the actual match-day lineup; confirm names and jersey numbers before announcing. A roster appearance means the player was listed, not necessarily that they played.

## Maintenance

The makefile expects Ruff and Ty on `PATH`; they are not runtime dependencies. `make ruff-ty` runs lint fixes, formatting, and type checking. Its lint step includes unsafe fixes, so review changes afterward. There is currently no automated test suite.

See [USER_WORKFLOW.md](USER_WORKFLOW.md) for the user journey, [PROJECT.md](PROJECT.md) for implementation details, [SPECS.md](SPECS.md) for the behavior baseline, and [CHANGELOG.md](CHANGELOG.md) for recorded changes.

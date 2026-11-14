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

Each cache also contains `league_table` with the full official standings rows, retrieval timestamp, and any availability error. Every successful league fetch replaces this snapshot, even with `refresh` set to `false`. Standings represent the latest data fetched, not a prediction for the fixture date. Missing or unreadable standings clear the old snapshot and are reported explicitly.

## Edit and print

Each exported match has a player sheet and a separate `<label>_TABELLE` sheet with the latest official league standings. Every sheet is configured as one A4 portrait page with a print area and scaling to one page wide by one page tall.

Player columns are `Nr.`, `Spieler`, `Spiele`, `Tore (7m)`, `Gelb`, `2 min`, `Rot`. `Tore (7m)` displays total goals with scored seven-metre goals in parentheses, such as `42 (8)`. Goals and disciplinary counts are totals from the selected readable match reports.

Below the standings, both teams' previous results appear newest first, with date, home team, away team, and final score in home:away order. These use the same `n_matches` selection as player preparation: `null` includes all eligible games, including results whose PDFs are unavailable. No games are omitted to fit the page; long histories make the one-page print smaller.

Sheets follow the configured team order, with each player sheet immediately followed by its standings sheet: `MAENNER`, `MAENNER_TABELLE`, `FRAUEN`, `FRAUEN_TABELLE`, and so on. Export the entire workbook in this order and print the PDF double-sided, flipping on the long edge, to put each player list and its table on the front and back of the same piece of paper.

Make manual corrections in Excel, then export or print the **entire workbook** to PDF using the saved print areas and scaling. Use the blank player rows for additions. If you add content outside a print area, extend that sheet's print area first; keep A4 paper and fit-to-one-page scaling. Check PDF print preview after edits, especially after adding rows or enlarging fonts, since fitting more content can reduce readability. The script produces Excel, and PDF export is a manual step.

If standings are unavailable, their sheet shows a warning and player sheets remain available. Long worksheet labels are shortened for standings sheet names, and conflicting derived names receive a suffix.

Read console output for unavailable reports and partial preparations. Historical rosters do not guarantee the actual match-day lineup; confirm names and jersey numbers before announcing. A roster appearance means the player was listed, not necessarily that they played.

## Maintenance

The makefile expects Ruff and Ty on `PATH`; they are not runtime dependencies. `make ruff-ty` runs lint fixes, formatting, and type checking. Its lint step includes unsafe fixes, so review changes afterward. There is currently no automated test suite.

See [USER_WORKFLOW.md](USER_WORKFLOW.md) for the user journey, [PROJECT.md](PROJECT.md) for implementation details, [SPECS.md](SPECS.md) for the behavior baseline, and [CHANGELOG.md](CHANGELOG.md) for recorded changes.

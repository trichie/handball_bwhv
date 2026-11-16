# Handball BWHV

Current version: **0.3.0**.

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
| `n_matches` | Number of latest completed or cancelled fixtures to consider per team; `null` means all available history. |
| `scorer_top_n` | Positive number of league leaders in the scorer ranking; default `10`. |
| `scorer_per_team` | Positive minimum number of scorers from each participating team; default `3`. Players already among the league leaders count toward this minimum. |
| `refresh` | Set to `true` to download and reparse successful cached reports too. |

Labels must be valid Excel worksheet names and suitable filename components. The supplied configuration is an example setup for three teams of TSV 1848 Bad Saulgau—the men's, women's, and second teams—in the 2026/2027 season.

League caches are saved to `matches/<season>/bwhv_<label>.json`. The default workbook destination is `output/matches_<next_date>.xlsx`; parent folders are created automatically. Existing destination workbooks are overwritten when an export is produced. If no preparations match the selected day, no workbook is written and any existing workbook remains.

Each cache also contains `league_table` with the full official standings rows, retrieval timestamp, and any availability error. Every successful league fetch replaces this snapshot, even with `refresh` set to `false`. Standings represent the latest data fetched, not a prediction for the fixture date. Missing or unreadable standings clear the old snapshot and are reported explicitly.

## Edit and print

The standings page shows the league table at the top, both teams' histories side by side with a blank separator column, and the configured team's upcoming fixtures below the longer history.

Each exported match has a player sheet and a separate `<label>_TABELLE` sheet with the latest official league standings. Every sheet is configured as one A4 portrait page with a print area and scaling to one page wide by one page tall.

Player columns are `Nr.`, `Spieler`, `Spiele`, `Tore (7m)`, `Gelb`, `2 min`, `Rot`. `Tore (7m)` displays total goals with scored seven-metre goals in parentheses, such as `42 (8)`. Goals and disciplinary counts are totals from the selected readable match reports.

The player page starts with `Matchblatt`, the league name, match date and kickoff, both teams in home/away order, and a `-- powered by https://github.com/trichie/handball_bwhv` project link.

The player page uses compact header and scorer-row heights with minimal spacing to leave more room for readable A4 printing. All data and five blank addition rows per team are retained; long labels receive additional row height.

Player and fill-in rows retain their height for handwritten notes. The separate standings/history/upcoming page uses compact rows, increasing height only for wrapped text.

Each player's jersey number is the number they started with in their latest readable appearance within the selected history. Older appearances do not replace it, and published jersey changes use the initial number.

Below both player lists and their blank addition rows, a season scorer ranking shows the league leaders selected by `scorer_top_n` plus each participating team's best `scorer_per_team` players if not already listed (defaults: 10 and 3). It uses all readable reports for completed, non-cancelled league games before the selected fixture, independently of `n_matches`. Columns are `Rg.`, `Spieler (Verein)`, `Spiele`, `Tore (7m)`, `Gelb`, `2 min`, `Rot`. Tied goal totals share ranks (1, 1, 3); club and name determine a stable display order and configured league-player cutoff. The ranking is calculated from public reports and carries a warning if eligible reports are unavailable. It stays on the same A4 player page, so the added content can reduce print size.

Scorer-ranking rows for either participating team are bold. League-table headers align with their content: numbers right, team names left. Upcoming-fixture `Heim` and `Auswärts` labels are both centered, with home games bold.

Below the standings, both teams' previous results appear newest first, with date, home team, away team, and final score in home:away order. These use the same `n_matches` selection as player preparation: `null` includes all eligible games, including results whose PDFs are unavailable. No games are omitted to fit the page; long histories make the one-page print smaller.

Past cancellations count toward `n_matches` and show `Abgesagt` with the published comment instead of a score. They contribute no player statistics and are not replaced by older played games. Cancelled fixtures are saved in JSON even without a score; unavailable goal values are `null`. History requires a known kickoff before both the lookup time and the selected fixture.

The table page also includes the configured team's upcoming fixtures after the selected match, earliest first, through and including its next home game. If no home game remains, all remaining scheduled fixtures are listed. This section shows date, kickoff, both teams, and `Heim`/`Auswärts`, and is independent of `n_matches`. The opponent's future fixtures are omitted. Cancelled, live, completed, or unknown-kickoff fixtures are excluded; an empty remaining schedule is stated explicitly.

Sheets follow the configured team order, with each player sheet immediately followed by its standings sheet: `MAENNER`, `MAENNER_TABELLE`, `FRAUEN`, `FRAUEN_TABELLE`, and so on. Export the entire workbook in this order and print the PDF double-sided, flipping on the long edge, to put each player list and its table on the front and back of the same piece of paper.

Make manual corrections in Excel, then export or print the **entire workbook** to PDF using the saved print areas and scaling. Use the blank player rows for additions. If you add content outside a print area, extend that sheet's print area first; keep A4 paper and fit-to-one-page scaling. Check PDF print preview after edits, especially after adding rows or enlarging fonts, since fitting more content can reduce readability. The script produces Excel, and PDF export is a manual step.

If standings are unavailable, their sheet shows a warning and player sheets remain available. Long worksheet labels are shortened for standings sheet names, and conflicting derived names receive a suffix.

Read console output for unavailable reports and partial preparations. Historical rosters do not guarantee the actual match-day lineup; confirm names and jersey numbers before announcing. A roster appearance means the player was listed, not necessarily that they played.

## Maintenance

The makefile expects Ruff and Ty on `PATH`; they are not runtime dependencies. `make ruff-ty` runs lint fixes, formatting, and type checking. Its lint step includes unsafe fixes, so review changes afterward. There is currently no automated test suite.

See [USER_WORKFLOW.md](USER_WORKFLOW.md) for the user journey, [PROJECT.md](PROJECT.md) for implementation details, [SPECS.md](SPECS.md) for the behavior baseline, and [CHANGELOG.md](CHANGELOG.md) for recorded changes.

# Project implementation

## Structure and execution

The application is a single Python module, `handball_bwhv.py`, with JSON configuration in `parameters.json`. Running the module calls `run_match_day(**load_parameters())`. There is no web interface, database, or command-line argument parser.

Runtime dependencies are HTTPX for HTTP, pypdf for PDF text extraction, tqdm for sync progress, and XlsxWriter for workbook generation. Python requires 3.13 or newer. Dependency resolution is recorded in `uv.lock`.

## Workflow

- `load_parameters` reads JSON from the working directory and substitutes `{next_date}` in `excel_path` before converting it to `Path`.
- `sync_league` requests Handball4all league data, replaces the current official table snapshot from `content.score`, merges actual and future game lists by game ID, and records completed games. Completion means not live and both goal values numeric. Cancellation is detected from German comment keywords.
- `parse_report` uses PDF layout text to extract home/away players, officials, statistics, and ordered events. Both player rosters and an event table are required. New downloads are checked against official team goal totals during synchronization.
- `enrich_report` retains raw actions and adds structured action, participant, team, and jersey-change fields. Unknown actions and ambiguous team resolution carry `action_error` values.
- `prepare_match` resolves an exact team-list name to its fixture alias, selects a fixture, and combines each team's earlier completed, non-cancelled matches. History must precede both the lookup time and selected kickoff. With `n_matches`, the latest N matches are selected before report availability is checked.
- Players are combined by name after removing jersey-change annotations. Goals, scored seven-metre goals, yellow cards, two-minute suspensions, red cards, and roster appearances accumulate across readable selected reports. Accumulated statistics use `total_` keys; `games` counts roster appearances. Other player statistics and the starting jersey number come from the latest readable report. Officials are deduplicated by name and role.
- `format_preparation` prints players, officials, sources, and errors. `run_match_day` attaches the synced table to each preparation and reports table errors. `export_matches` writes a player sheet and a standings sheet per preparation on the selected day. Player sheets retain two player tables and eight blank rows per team. All sheets use A4 portrait printing fitted to one page through `_print_page`.

`prepare_match` can also select the next future, non-live, incomplete fixture when no date is supplied. An explicit date may select a completed or live fixture; the earliest kickoff on that date wins. Times use `Europe/Zurich`; an explicitly supplied `now` must be timezone-aware.

## Persistence and errors

Each `matches/<season>/bwhv_<label>.json` cache has schema version 1, league and organization IDs, league metadata, `games` keyed by game ID, and `reports` keyed by PDF ID. Existing cache identity and schema must match the requested league. Reports contain parsed rosters/events or a status and error message. Game records retain official scores, points where readable, comments, report links, and available parsed data.

The additive `league_table` field contains `retrieved_at` (an aware ISO timestamp), `rows` (complete API standings rows in official order), and `error` (`null` on success). Existing schema-1 caches acquire it on their next sync. Each successful league fetch replaces and saves the snapshot before report processing, even if there are no completed games. Empty, missing, or unreadable tables replace old rows with an availability error. HTTP failure before a league response preserves the old cache but prevents that team's preparation, following the existing workflow.

Standings sheets display `tabScore`, `tabTeamname`, played/won/drawn/lost counts, goals for/against, goal difference, and points for/against. Source-only fields remain in JSON. The standings are current at retrieval, independent of the selected fixture date; the script does not calculate official rankings. Derived worksheet names are shortened and suffixed on collision. Saved print areas cover each sheet's content; manual additions outside those areas require updating the print area before exporting to PDF.

Worksheets are created in configured team order as consecutive player/standings pairs for duplex printing. Player sheet names are reserved before creation to prevent derived table names from conflicting with later player sheets. A missing table still gets a warning sheet, preserving page pairing.

Player sheets place seven-column tables side by side: `Nr.`, `Spieler`, `Spiele`, `Tore (7m)`, `Gelb`, `2 min`, `Rot`. The goals cell combines total goals and scored seven-metre goals as `42 (8)`. The print area spans A:O to include both teams' statistics and eight blank addition rows per team.

Below the standings, `_export_league_table` writes both teams' prior results from each preparation entry's `reports` list. This reuses `prepare_match`'s date cutoffs, descending order, and `n_matches` limit (`None` includes all). Each row shows date, home/away teams, and the official final score, independently of PDF availability. Empty histories are marked explicitly. The print area includes both result sections on the same A4 page, even with unavailable standings; long histories reduce print scale rather than being truncated.

Successful reports are reused unless `refresh` is true; failed reports are retried. Each completed game is saved using a temporary sibling file followed by replacement. Existing records absent from later API responses are retained. Raw PDF bytes are not saved. `enrich_actions` can update structured events in an existing cache without network access.

HTTP requests use a 30-second timeout and follow redirects. Report HTTP/parsing failures are recorded and preparation continues where handled. `run_match_day` catches HTTP, value, key, and PDF errors per configured team and proceeds with the others; it does not catch every filesystem or export failure. Fixture lookup still requires network access when reports are cached.

## Known limitations and maintenance

- PDF extraction depends on the published layout and German action wording; there is no OCR fallback.
- Names are the player identity key, so namesakes can merge and spelling changes can split records. Jersey numbers are historical.
- Missing reports reduce totals and can produce empty lists. Excel output omits officials and source/error details; inspect console output.
- Configuration has no schema validation. Labels are used directly in cache paths and worksheet names.
- Existing workbooks are overwritten only when an export is produced; no-match runs leave old files untouched.
- There is no automated test suite. Ruff and Ty commands are provided by the makefile and require separately available tools. `make ruff-ty` modifies source through lint fixes and formatting.

Keep behavior changes aligned with `SPECS.md`, and update user documentation when configuration or output changes.

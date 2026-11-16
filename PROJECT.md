# Project implementation

Current implemented version: **0.3.0**, declared in `pyproject.toml` and mirrored by the root package in `uv.lock`.

## Structure and execution

The application is a single Python module, `handball_bwhv.py`, with JSON configuration in `parameters.json`. Running the module calls `run_match_day(**load_parameters())`. There is no web interface, database, or command-line argument parser.

Runtime dependencies are HTTPX for HTTP, pypdf for PDF text extraction, tqdm for sync progress, and XlsxWriter for workbook generation. Python requires 3.13 or newer. Dependency resolution is recorded in `uv.lock`.

## Workflow

- `load_parameters` reads JSON from the working directory and substitutes `{next_date}` in `excel_path` before converting it to `Path`.
- `sync_league` requests Handball4all league data, replaces the current official table snapshot from `content.score`, merges actual and future game lists by game ID, and records completed or cancelled games. Completion means not live and both goal values numeric. Cancellation is detected from German comment keywords. Cancelled games are retained without numeric scores; missing goals are `null`, and their PDFs are not downloaded.
- `parse_report` uses PDF layout text to extract home/away players, officials, statistics, and ordered events. Both player rosters and an event table are required. New downloads are checked against official team goal totals during synchronization.
- `enrich_report` retains raw actions and adds structured action, participant, team, and jersey-change fields. Unknown actions and ambiguous team resolution carry `action_error` values.
- `prepare_match` resolves an exact team-list name to its fixture alias, selects a fixture, and selects each team's earlier completed or cancelled fixtures. History must have a known kickoff preceding both the lookup time and selected kickoff. With `n_matches`, the latest N fixtures are selected before report availability is checked. Cancellations occupy a slot, are marked in the report entry's error text, and contribute no player statistics.
- Players are combined by name after removing jersey-change annotations. Goals, scored seven-metre goals, yellow cards, two-minute suspensions, red cards, and roster appearances accumulate across readable selected reports. Accumulated statistics use `total_` keys; `games` counts roster appearances. Other player statistics and the starting jersey number come from the latest readable report. Officials are deduplicated by name and role.
- `format_preparation` prints players, officials, sources, and errors. `run_match_day` attaches the synced table to each preparation and reports table errors. `export_matches` writes a player sheet and a standings sheet per preparation on the selected day. Player sheets retain two player tables and five blank rows per team. All sheets use A4 portrait printing fitted to one page through `_print_page`.

`prepare_match` can also select the next future, non-live, incomplete fixture when no date is supplied. An explicit date may select a completed or live fixture; the earliest kickoff on that date wins. Times use `Europe/Zurich`; an explicitly supplied `now` must be timezone-aware.

## Persistence and errors

When a synced dataset is supplied, `prepare_match` adds `scorer_ranking` using the league API's full game list and cached reports. `_scorer_ranking` filters completed, non-cancelled games with known starts before the selected kickoff, without applying `n_matches`. It groups by fixture team alias and normalized player name, displays the report's club name, and accumulates appearances and all five displayed statistics. This keeps namesakes at different clubs distinct and handles differences between fixture aliases and published report names.

Ranking rows are sorted by total goals descending, club, and player name. Equal goals receive competition ranks; selection keeps `scorer_top_n` league leaders plus the first `scorer_per_team` players for each participating fixture alias, without duplicate rows. The defaults are 10 league leaders and 3 per participating team. The settings are passed from `run_match_day` to `prepare_match` and validated as positive integers before preparation makes HTTP requests; omitted settings retain defaults. The snapshot contains selected `rows`, `readable_reports`, and `missing_reports`. It is derived per preparation and does not change the league-cache schema. Direct preparation without a synced dataset does not build league-wide statistics.

`_export_scorer_ranking` appends the ranking below both player tables and their five blank addition rows, using A for rank, B:J for player/club, and K:O for statistics. It shows report coverage and missing-report warnings or explicit empty/unavailable messages. The player page print area expands to include every ranking row while retaining A4 portrait and one-page scaling. The ranking is calculated from readable PDFs rather than an official scorer-table endpoint; unavailable reports can understate totals and change ranks.

The rank header is `Rg.`. Every displayed cell in a participating team's scorer row is bold, matched through fixture aliases so published club-name differences do not prevent highlighting. Other clubs remain regular. League-table numeric headers are right-aligned and the team-name header is left-aligned. Both upcoming home/away labels are centered; home labels remain bold.

Standings sheets use an A:S column grid with a narrow separator column J. Logical league-table columns span the appropriate cells above two equal-width history blocks (A:I and K:S), separated by a blank column J. Both histories start at the same row; shared row heights use the larger wrapped-text estimate. Upcoming fixtures span the page below the longer history. The full print area remains one A4 portrait page.

Each `matches/<season>/bwhv_<label>.json` cache has schema version 1, league and organization IDs, league metadata, `games` keyed by game ID, and `reports` keyed by PDF ID. Existing cache identity and schema must match the requested league. Reports contain parsed rosters/events or a status and error message. Game records retain official scores, points where readable, comments, report links, and available parsed data.

The additive `league_table` field contains `retrieved_at` (an aware ISO timestamp), `rows` (complete API standings rows in official order), and `error` (`null` on success). Existing schema-1 caches acquire it on their next sync. Each successful league fetch replaces and saves the snapshot before report processing, even if there are no completed games. Empty, missing, or unreadable tables replace old rows with an availability error. HTTP failure before a league response preserves the old cache but prevents that team's preparation, following the existing workflow.

Standings sheets display `tabScore`, `tabTeamname`, played/won/drawn/lost counts, goals for/against, goal difference, and points for/against. Source-only fields remain in JSON. The standings are current at retrieval, independent of the selected fixture date; the script does not calculate official rankings. Derived worksheet names are shortened and suffixed on collision. Saved print areas cover each sheet's content; manual additions outside those areas require updating the print area before exporting to PDF.

Worksheets are created in configured team order as consecutive player/standings pairs for duplex printing. Player sheet names are reserved before creation to prevent derived table names from conflicting with later player sheets. A missing table still gets a warning sheet, preserving page pairing.

Player sheets place seven-column tables side by side: `Nr.`, `Spieler`, `Spiele`, `Tore (7m)`, `Gelb`, `2 min`, `Rot`. The goals cell combines total goals and scored seven-metre goals as `42 (8)`. The print area spans A:O to include both teams' statistics and five blank addition rows per team.

Player sheets begin with a `Matchblatt`/league title, `_label` fixture details (date, kickoff, home/away teams), and a clickable powered-by credit using `PROJECT_URL`, taken from the repository's Git origin URL. Player-table team headings begin on row 4, column headers on row 5, and players on row 6. Five blank addition rows per team and the scorer ranking follow without extra spacer rows, all within the expanded A4 print area. Header and scorer rows use compact heights while preserving the existing data font sizes; text-wrap estimates increase heights for long labels and coverage notes. This reduces vertical scaling pressure when printing to one A4 page.

Player entries are initialized only on their first occurrence while reading reports newest first. `_starting_number` takes the first number in a jersey-change annotation, otherwise the roster number. Thus each player's latest readable appearance supplies their starting number, even when absent from the team's latest report; older appearances only accumulate statistics.

Below the standings, `_export_league_table` writes both teams' prior results from each preparation entry's `reports` list. This reuses `prepare_match`'s date cutoffs, descending order, and `n_matches` limit (`None` includes all). Each row shows date, home/away teams, and the official final score, independently of PDF availability. Empty histories are marked explicitly. The print area includes both result sections on the same A4 page, even with unavailable standings; long histories reduce print scale rather than being truncated.

Cancelled history rows display `Abgesagt` instead of a score and include the published comment, with a taller row for the additional text. They remain part of the same history list and print area. Future cancellations and cancellations without a readable kickoff are not eligible for past history.

Preparations also contain `team_alias` (the configured team's API fixture name) and `upcoming_matches` (raw API fixtures). `prepare_match` selects known kickoffs later than both the selected match and lookup time, excludes completed/live/cancelled games, sorts ascending, and stops after appending the first home game. Without another home game it retains all remaining eligible fixtures. This is independent of the history limit and never selects the opponent's separate schedule. Console output lists these fixtures; the standings sheet adds them after both histories, marks home/away using `team_alias`, and includes them in the same A4 print area. Home fixtures receive a bold label.

Successful reports are reused unless `refresh` is true; failed reports are retried. Each processed completed or cancelled game is saved using a temporary sibling file followed by replacement. Existing records absent from later API responses are retained. Raw PDF bytes are not saved. `enrich_actions` can update structured events in an existing cache without network access.

HTTP requests use a 30-second timeout and follow redirects. Report HTTP/parsing failures are recorded and preparation continues where handled. `run_match_day` catches HTTP, value, key, and PDF errors per configured team and proceeds with the others; it does not catch every filesystem or export failure. Fixture lookup still requires network access when reports are cached.

## Known limitations and maintenance

Standings/history/upcoming sheets use an 18-point default row height, compact spacers, and increased heights for wrapped team names, history text, comments, and upcoming fixtures. Shared history rows use the larger requirement from either side. Player sheets retain 21.5-point player and five fill-in row heights for handwriting.

- PDF extraction depends on the published layout and German action wording; there is no OCR fallback.
- Names are the player identity key, so namesakes can merge and spelling changes can split records. Jersey numbers are historical.
- Missing reports reduce totals and can produce empty lists or incomplete scorer rankings. Excel includes ranking coverage, unavailable-standings warnings, and cancellation comments; officials and individual report links/errors are available in console output.
- Configuration has no general schema validation. History and scorer limits and an explicit lookup timezone are validated by `prepare_match`; malformed settings may otherwise fail during loading or processing. Labels are used directly in cache paths and worksheet names.
- Existing workbooks are overwritten only when an export is produced; no-match runs leave old files untouched.
- There is no automated test suite. Ruff and Ty commands are provided by the makefile and require separately available tools. `make ruff-ty` modifies source through lint fixes and formatting.
- The makefile defines formatting, linting, type-checking, and cleanup targets; it does not currently define `reset-tag`.

Keep behavior changes aligned with `SPECS.md`, and update user documentation when configuration or output changes.

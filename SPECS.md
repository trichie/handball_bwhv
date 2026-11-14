# Behavior baseline

The original baseline records observed behavior. The standings and print requirements below were confirmed by the user. Future behavior changes require explicit requirements and human confirmation under `AGENTS.md`.

## Purpose and scope

Support match announcers by preparing historical player lists for both sides of selected BWHV fixtures and exporting printable Excel sheets. Historical lists are preparation aids; the actual lineup requires confirmation at the venue.

## Existing behavior and acceptance checks

1. Settings are loaded from `parameters.json`: configured teams and league URLs, season, ISO match date, output path, optional history limit, and refresh flag. The output path supports `{next_date}` substitution.
2. Completed league results are persisted in a JSON cache per configured label. Successful reports are reused by PDF ID; missing or failed reports are attempted again, and refresh also reparses successful reports. Cache schema and league identity mismatches raise an error.
3. PDF parsing retains zero-goal players, officials, roster statistics, ordered event text, and structured event fields. Unrecognized action text is retained with an error marker. Missing readable rosters or events reject the report.
4. For a configured team, the selected date yields the earliest non-cancelled fixture with a known kickoff. No fixture on that date yields no preparation for that team.
5. Each side's player list combines earlier completed, non-cancelled matches, optionally limited to the latest positive integer number of matches. Missing reports are reported and do not cause older matches to fill that limit. Goals and roster appearances accumulate by normalized player name.
6. Console preparation text includes report availability, source matches and links, player totals, officials, and handled errors. A handled failure for one configured team allows processing of other teams.
7. Excel export includes one worksheet per available preparation on the selected date, both teams' player numbers/names/goals/appearances, and eight blank addition rows per team. Sheets use A4 portrait printing fitted to one page. No selected preparations means no workbook write.

## Confirmed standings and printing requirements

- Player tables use `Nr.`, `Spieler`, `Spiele`, `Tore (7m)`, `Gelb`, `2 min`, `Rot` in that order. Goals display total goals with scored seven-metre goals in parentheses, for example `42 (8)`. Seven-metre goals, yellow cards, two-minute suspensions, and red cards are summed across the same selected readable reports as goals and roster appearances. Both teams and their blank addition rows remain within the player sheet's one-page A4 print area.
- Use the latest official league table available when synchronizing, regardless of the future fixture date. Preserve all teams, official order, and source fields without reconstructing standings from match results.
- Store a `league_table` snapshot in each league JSON with `retrieved_at`, `rows`, and `error`. Replace it on every successful league API fetch, independently of report refresh. Missing or unreadable standings replace the previous snapshot with empty rows and an explicit error; a failed HTTP fetch leaves the existing cache untouched.
- Export a separate standings worksheet per exported match, showing league name, retrieval time, position, team, matches, wins, draws, losses, goals, goal difference, and points. Report unavailable standings in the console and on the standings sheet while preserving player-sheet export.
- Configure every worksheet with its own print area, A4 portrait paper, and scaling to one page wide by one page tall. Users can edit the workbook before exporting the entire workbook to PDF. Edits outside a print area require extending that area; automated PDF generation is outside this change.
- Keep preparations in configured team order, with each player sheet immediately followed by its standings sheet, including an unavailable-standings sheet when needed. These consecutive page pairs support printing players on the front and standings on the back of each sheet of paper.
- Below the standings, include a result section for each of the two teams using the same selected match history as player preparation. `n_matches` limits each team's results; `null` includes all eligible games. Show date, home team, away team, and final score, newest first, even when a game's PDF is missing or unreadable. Show an explicit message for teams with no prior games. Include both sections in the same one-page A4 print area, without truncating history; large histories may reduce printed readability.

## Boundaries

The current scope does not include guaranteed upcoming lineups, playing-time measurement, OCR, a graphical interface, or fully offline fixture preparation. Public report availability and layout constrain completeness. See `PROJECT.md` for implemented data contracts and limitations.

## Open requirements

Automated acceptance coverage has not yet been established as a persistent test suite.

# Behavior baseline

This initial document records behavior observed in the current implementation. It is not a newly approved feature specification. Future behavior changes require explicit requirements and human confirmation under `AGENTS.md`.

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

## Boundaries

The current scope does not include guaranteed upcoming lineups, playing-time measurement, OCR, a graphical interface, or fully offline fixture preparation. Public report availability and layout constrain completeness. See `PROJECT.md` for implemented data contracts and limitations.

## Open requirements

No new feature requirements are proposed in this baseline. Automated acceptance coverage has not yet been established.

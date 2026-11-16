# Changelog

## 0.3.0

- Add a season-wide scorer ranking below both player lists, using all eligible season games before the selected fixture independently of `n_matches`, with disciplinary totals and report-coverage warnings.
- Add `scorer_top_n` and `scorer_per_team`, defaulting to 10 league leaders and 3 players per participating team, without duplicates. Make participating-team scorer rows bold and use the compact `Rg.` header.
- Add a Matchblatt heading with league, date, kickoff, teams, and a clickable project credit to each player page.
- Compact player-page headers and scorer rows, reduce blank fill-in rows from eight to five per team, and preserve player/fill-in row heights for handwriting.
- Place both teams' histories side by side with a blank separator column. Add the configured team's upcoming fixtures below them through the next home game included, or the rest of the schedule if none remains.
- Use compact standings/history/upcoming row heights with additional room for wrapped text, retaining one A4 portrait page per worksheet and consecutive player/standings pairs for duplex printing.
- Align league-table headers with their values and center both upcoming home/away labels, keeping home games bold.
- Verify that each player's starting number comes from their latest readable appearance and is not overwritten by older reports.
- Count past cancellations toward the last N fixtures without replacement or player statistics. Show cancellation comments in Excel and retain scoreless cancellations in JSON.

## 0.2.0

- Expand player tables to show games, goals with scored seven-metre goals in parentheses, yellow cards, two-minute suspensions, and red cards, summed across selected readable reports.
- Include both teams' selected previous results below the standings on the same A4 page; `n_matches: null` includes all eligible games, including results without readable PDFs.
- Keep each player sheet immediately before its standings sheet, in configured team order, for printing each pair front and back.
- Save the latest full official league standings in JSON on each successful league fetch, replacing the previous snapshot and recording unavailable tables explicitly.
- Add a standings sheet per exported match and configure every worksheet as one A4 portrait print page for manual PDF export after editing.
- Added project setup, workflow, implementation, and behavior-baseline documentation.
- Replaced the placeholder package description with the application's purpose.
- Reduced runtime dependencies to those used by the application, including a direct pypdf dependency.

## Current baseline — 0.1.0

Existing capabilities recorded when this changelog was introduced; no release date is asserted.

- Fetch BWHV fixtures and cache completed league results and parsed public reports.
- Extract rosters, player statistics, officials, and structured match events.
- Configure match-day preparation through `parameters.json` and display synchronization progress.
- Combine historical rosters and export printable Excel player lists.

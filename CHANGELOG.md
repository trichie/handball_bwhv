# Changelog

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

# User workflow

1. Choose the teams, season, match date, and output location in `parameters.json`. Optionally limit how many recent matches contribute to each list.
2. Run the script. It updates league results and the latest official standings in the saved league data, reads new or previously failed public match reports, and prepares lists for the configured teams playing on that day.
3. Review console messages for missing reports or incomplete lists. The text includes source matches, report links, and team officials.
4. Open the Excel workbook and make any manual corrections. Each prepared match has a player sheet and a separate sheet with the latest league standings and retrieval time. Blank player rows allow additions. Review warnings if standings are unavailable.
5. Confirm the actual lineup and jersey numbers at the venue. The lists summarize past reports and can differ from the day's lineup.

Player tables show roster appearances, total goals with scored seven-metre goals in parentheses, yellow cards, two-minute suspensions, and red cards. All totals use the same selected readable reports.

For printing, export the entire workbook to PDF. Each sheet is set to one A4 portrait page. Keep the saved print areas and fit-to-one-page scaling; extend the print area if adding content outside it. Check print preview after edits before printing the PDF.

Each player sheet is immediately followed by its league table, in configured team order. Print the PDF double-sided with long-edge binding so each player list and its table share one piece of paper, front and back.

The table page also lists both teams' previous results, newest first, showing date, home team, away team, and final score. The configured history limit applies here too; `null` means all eligible games. Large histories can make the one-page print small, so check readability in preview.

Teams without a match on the selected day are skipped. Unavailable reports can leave partial or empty player lists. If no match preparations are available, no new workbook is generated; an older file at the output location is left in place.

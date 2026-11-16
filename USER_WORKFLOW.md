# User workflow

Each standings page shows the league table, then the two teams' histories side by side, then upcoming fixtures below the longer history.

1. Choose the teams, season, match date, and output location in `parameters.json`. Optionally limit how many recent matches contribute to each list.
2. Run the script. It updates league results and the latest official standings in the saved league data, reads new or previously failed public match reports, and prepares lists for the configured teams playing on that day.
3. Review console messages for missing reports or incomplete lists. The text includes source matches, report links, and team officials.
4. Open the Excel workbook and make any manual corrections. Each prepared match has a Matchblatt player page with league, date, kickoff, teams, and a project link, followed by a page with the latest league standings and retrieval time. Five blank player rows per team allow additions. Player and fill-in rows retain space for handwriting; the standings page uses compact rows. Review warnings if standings are unavailable.
5. Confirm the actual lineup and jersey numbers at the venue. The lists summarize past reports and can differ from the day's lineup.

Player tables show roster appearances, total goals with scored seven-metre goals in parentheses, yellow cards, two-minute suspensions, and red cards. All totals use the same selected readable reports.

Each player uses their starting jersey number from their latest readable appearance in that history.

Below both player lists is a league scorer ranking: the configured number of league leaders plus each side's best players if not already included (defaults: ten league leaders and three per team). This uses season games before the selected fixture, regardless of the history limit. It includes appearances, goals with seven-metre goals, and disciplinary totals. Check its report-availability note for incomplete totals. The ranking shares the player page, so review print size before printing.

Players from the two participating teams are bold in the scorer ranking. The two past-game lists are separated by a blank column. Upcoming fixtures have centered home/away labels, with home games bold.

For printing, export the entire workbook to PDF. Each sheet is set to one A4 portrait page. Keep the saved print areas and fit-to-one-page scaling; extend the print area if adding content outside it. Check print preview after edits before printing the PDF.

Each player sheet is immediately followed by its league table, in configured team order. Print the PDF double-sided with long-edge binding so each player list and its table share one piece of paper, front and back.

The table page also lists both teams' previous results, newest first, showing date, home team, away team, and final score. The configured history limit applies here too; `null` means all eligible games. Large histories can make the one-page print small, so check readability in preview.

Past cancelled fixtures count toward that history limit. They show `Abgesagt` and the published comment, contribute no player statistics, and are not replaced by older played games.

For the closing announcement, the same table page lists the configured team's next fixtures after the day's match, ending with the next home game included. If no home game remains, it lists the rest of the available schedule. Dates, kickoff times, and home/away labels help announce these games. The opponent's upcoming games are not listed.

Teams without a match on the selected day are skipped. Unavailable reports can leave partial or empty player lists. If no match preparations are available, no new workbook is generated; an older file at the output location is left in place.

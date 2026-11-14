# User workflow

1. Choose the teams, season, match date, and output location in `parameters.json`. Optionally limit how many recent matches contribute to each list.
2. Run the script. It updates league results, reads new or previously failed public match reports, and prepares lists for the configured teams playing on that day.
3. Review console messages for missing reports or incomplete lists. The text includes source matches, report links, and team officials.
4. Open and print the Excel workbook. Each prepared match has a sheet with both teams' player numbers, names, total goals, and roster appearances. Blank rows allow handwritten additions.
5. Confirm the actual lineup and jersey numbers at the venue. The lists summarize past reports and can differ from the day's lineup.

Teams without a match on the selected day are skipped. Unavailable reports can leave partial or empty player lists. If no match preparations are available, no new workbook is generated; an older file at the output location is left in place.

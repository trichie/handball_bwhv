"""Prepare announcer rosters from public BWHV match reports."""

import json
import re
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

import httpx
import xlsxwriter
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from tqdm.auto import tqdm

ACTION_TYPES = {
	'Tor': 'goal',
	'7m-Tor': 'seven_m_goal',
	'7m, KEIN Tor': 'seven_m_missed',
	'2-min Strafe': 'two_min_suspension',
	'Verwarnung': 'yellow_card',
	'Disqualifikation': 'red_card',
	'Disqualifikation mit Bericht': 'red_card_with_report',
}
PERSON_ACTION = re.compile(r'^(.+?) (?:durch|für) (.+) \((\d+|[A-E]), (.+)\)$')
JERSEY_CHANGE = re.compile(r'^Trikotwechsel (.+) \((\d+), (.+)\) von (\d+) nach (\d+)$')
NUMBER_CHANGES = re.compile(r'\s+\((\d+)\s*->\s*\d+(?:,\s*\d+\s*->\s*\d+)*\)$')


def _name(name: str) -> str:
	# Roster names may carry a published jersey-change annotation.
	return NUMBER_CHANGES.sub('', name).strip()


def _starting_number(player: dict) -> int:
	changes = NUMBER_CHANGES.search(player['name'])
	return int(changes[1]) if changes else player['number']


def _split(action: str) -> dict:
	result: dict = {
		'type': 'unknown',
		'player': None,
		'official': None,
		'number': None,
		'official_role': None,
		'team': None,
		'team_source': None,
		'side': None,
		'previous_number': None,
		'new_number': None,
		'action_error': None,
	}
	if action.startswith('Auszeit '):
		result.update(type='timeout', team_source=action.removeprefix('Auszeit ').strip())
		return result
	change = JERSEY_CHANGE.fullmatch(action)
	if change:
		result.update(
			type='jersey_change',
			player=change[1],
			number=int(change[2]),
			team_source=change[3],
			previous_number=int(change[4]),
			new_number=int(change[5]),
		)
		return result
	unnamed = re.fullmatch(r'(.+?) (?:durch|für) (Spieler|Offizieller) (\d+|[A-E]), (.+)', action)
	if unnamed and unnamed[1] in ACTION_TYPES:
		result.update(type=ACTION_TYPES[unnamed[1]], team_source=unnamed[4])
		if unnamed[2] == 'Spieler' and unnamed[3].isdigit():
			result['number'] = int(unnamed[3])
		elif unnamed[2] == 'Offizieller' and unnamed[3] in 'ABCDE':
			result['official_role'] = unnamed[3]
		return result
	person = PERSON_ACTION.fullmatch(action)
	if person and person[1] in ACTION_TYPES:
		result.update(type=ACTION_TYPES[person[1]], team_source=person[4])
		if person[3].isdigit():
			result.update(player=person[2], number=int(person[3]))
		else:
			result.update(official=person[2], official_role=person[3])
		return result
	result['action_error'] = 'Unrecognized action text.'
	return result


def enrich_report(report: dict) -> dict:
	"""Add structured fields to events while retaining the original action text.

	:param report: Parsed PDF with home/away rosters and raw events; updated in place.
	"""
	parsed = [_split(event['action']) for event in report['events']]
	aliases: dict[str, set[str]] = {}
	for side in ('home', 'away'):
		aliases.setdefault(report[side]['team'], set()).add(side)
	for event in parsed:
		name = event['player'] or event['official']
		if not name:
			continue
		collection = 'players' if event['player'] else 'officials'
		sides = [
			side
			for side in ('home', 'away')
			if any(_name(person['name']) == name for person in report[side][collection])
		]
		if len(sides) == 1:
			aliases.setdefault(event['team_source'], set()).add(sides[0])
	for original, event in zip(report['events'], parsed, strict=True):
		if event['team_source']:
			sides = aliases.get(event['team_source'], set())
			if len(sides) == 1:
				side = next(iter(sides))
				event.update(side=side, team=report[side]['team'])
				if event['player'] is None and event['number'] is not None:
					matches = [p for p in report[side]['players'] if p['number'] == event['number']]
					if len(matches) == 1:
						event['player'] = _name(matches[0]['name'])
				if event['official'] is None and event['official_role'] is not None:
					matches = [p for p in report[side]['officials'] if p['role'] == event['official_role']]
					if len(matches) == 1:
						event['official'] = matches[0]['name']
			else:
				event['action_error'] = 'Cannot uniquely resolve the action team.'
		original.update(event)
	return report


def enrich_dataset(dataset: dict) -> dict:
	"""Enrich cached reports and their game records without reading any PDFs.

	:param dataset: League JSON content; updated in place.
	"""
	for report in dataset['reports'].values():
		if report.get('status') == 'ok':
			enrich_report(report)
	for game in dataset['games'].values():
		report = dataset['reports'].get(game['pdf_id'])
		if report and report.get('status') == 'ok':
			game['events'] = report['events']
	return dataset


def _columns(header: str) -> list[int]:
	labels = [
		'Name',
		'Jahrgang',
		'M',
		'R',
		'Tore',
		'7m/',
		'Verw.',
		'Hinausstellungen',
		'Disq.',
		'Ber.',
		'zus.',
	]
	positions = []
	cursor = 0
	for label in labels:
		start = header.index(label, cursor)
		positions.append((start, start + len(label)))
		cursor = start + len(label)
	boundaries = [(left[1] + right[0]) // 2 for left, right in zip(positions, positions[1:], strict=False)]
	boundaries[0] = header.index('Jahrgang')
	return boundaries


def _statistics(line: str, boundaries: list[int]) -> dict:
	values = [line[a:b].strip() for a, b in zip(boundaries, boundaries[1:] + [len(line)], strict=True)]
	birth_year, marker_m, marker_r, goals, seven_m, warning, suspensions, disq, report, extra = values
	if goals and not goals.isdigit():
		raise ValueError(f'Unreadable goals column: {goals!r}')
	if seven_m and not re.fullmatch(r'\d+/\d+', seven_m):
		raise ValueError(f'Unreadable 7m column: {seven_m!r}')
	attempts, scored = map(int, seven_m.split('/')) if seven_m else (0, 0)
	if scored > attempts or scored > int(goals or 0):
		raise ValueError(f'Inconsistent 7m/goals columns: {seven_m!r}, {goals!r}')
	return {
		'goals': int(goals or 0),
		'field_goals': int(goals or 0) - scored,
		'seven_m_attempts': attempts,
		'seven_m_scored': scored,
		'seven_m_missed': attempts - scored,
		'yellow_cards': int(bool(warning)),
		'two_min_penalties': len(suspensions.split()),
		'red_cards': int(bool(disq)),
		'warning_times': warning.split(),
		'two_min_times': suspensions.split(),
		'disqualification_times': disq.split(),
		'disciplinary_report': report or None,
		'additional_penalty': extra or None,
		'birth_year': birth_year or None,
		'marker_m': marker_m or None,
		'marker_r': marker_r or None,
	}


def parse_report(pdf: bytes) -> dict:
	"""Extract home/away rosters and all raw event rows in report order.

	:param pdf: Public match report PDF bytes.
	"""
	if not pdf.startswith(b'%PDF-'):
		raise ValueError('The report URL did not return a PDF.')
	result: dict = {'home': None, 'away': None, 'events': []}
	current = None
	boundaries = None
	in_events = False
	for page in PdfReader(BytesIO(pdf)).pages:
		for line in (page.extract_text(extraction_mode='layout') or '').splitlines():
			if line.strip() == 'Spielverlauf':
				in_events = True
				current = None
				continue
			if in_events:
				row = re.match(r'^\s*(\d{2}:\d{2}:\d{2})\s+(\d{2,3}:\d{2})\s+(?:(\d+:\d+)\s+)?(\S.*)$', line)
				if row:
					result['events'].append(
						{'time': row[1], 'game_time': row[2], 'score': row[3], 'action': row[4].rstrip()}
					)
				elif line.strip() and not re.match(
					r'^\s*(?:Presseinformation|\S+, Spiel Nr\.|Handball4all|Zeit\s+Spielzeit)', line
				):
					if re.match(r'^\s*\d{2}:', line):
						raise ValueError(f'Unreadable event row: {line.strip()}')
					if result['events']:
						result['events'][-1]['action'] += ' ' + line.strip()
				continue
			heading = re.match(r'^\s*(Heim|Gast):\s*(.+?)\s*$', line)
			if heading:
				current = 'home' if heading[1] == 'Heim' else 'away'
				if result[current] is None:
					result[current] = {'team': heading[2], 'players': [], 'officials': []}
				boundaries = None
				continue
			if current is None:
				continue
			if 'Nr.' in line and 'Name' in line and 'Jahrgang' in line:
				boundaries = _columns(line)
				continue
			if line.strip().startswith('Handball4all'):
				current = None
				continue
			if boundaries is None:
				continue
			row = re.fullmatch(r'\s*(\d{1,3}|[A-E])\s+(.+?)\s*', line[: boundaries[0]])
			if row:
				person = {'name': row[2], **_statistics(line, boundaries)}
				if row[1].isdigit():
					result[current]['players'].append({'number': int(row[1]), **person})
				else:
					result[current]['officials'].append({'role': row[1], **person})
	for side in ('home', 'away'):
		if not result[side] or not result[side]['players']:
			raise ValueError(f'No readable {side} roster in the match PDF.')
		result[side]['players'].sort(key=lambda player: (player['number'], player['name']))
	if not result['events']:
		raise ValueError('No readable event table in the match PDF.')
	return enrich_report(result)


API_URL = 'https://spo.handball4all.de/service/if_g_json.php'
TIMEZONE = ZoneInfo('Europe/Zurich')


def _games(data: dict) -> list[dict]:
	games = {}
	for key in ('actualGames', 'futureGames'):
		group = data['content'][key]
		if isinstance(group, dict):
			for game in group.get('games', []):
				games[game['gID']] = game
	return list(games.values())


def _start(game: dict) -> datetime | None:
	value = f'{game["gDate"]} {game["gTime"]}'.strip()
	for pattern in ('%d.%m.%y %H:%M', '%d.%m.%Y %H:%M'):
		try:
			return datetime.strptime(value, pattern).replace(tzinfo=TIMEZONE)
		except ValueError:
			continue
	return None


def _completed(game: dict) -> bool:
	return not game['live'] and all(str(game[key]).strip().isdigit() for key in ('gHomeGoals', 'gGuestGoals'))


def _cancelled(comment: str) -> bool:
	return bool(re.search(r'abgesagt|ausgefallen|zurückgezogen', comment, re.I))


def _teams(game: dict) -> set[str]:
	return {game['gHomeTeam'], game['gGuestTeam']}


def _label(game: dict) -> str:
	return f'{game["gDate"]} {game["gTime"]}: {game["gHomeTeam"]} – {game["gGuestTeam"]}'


def extract_rosters(pdf: bytes) -> dict[str, dict]:
	"""Extract both roster sections, retaining zero-goal players and officials.

	:param pdf: Public match report PDF bytes.
	"""
	parsed = parse_report(pdf)
	return {side: parsed[side] for side in ('home', 'away')}


def _save_dataset(path: Path, dataset: dict) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	temporary = path.with_suffix(path.suffix + '.tmp')
	temporary.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
	temporary.replace(path)


def enrich_actions(path: Path) -> dict:
	"""Split saved action text and persist it without network or PDF access.

	:param path: Existing BWHV league JSON file.
	"""
	dataset = json.loads(path.read_text(encoding='utf-8'))
	enrich_dataset(dataset)
	_save_dataset(path, dataset)
	return dataset


def sync_league(url: str, path: Path, refresh: bool = False) -> dict:
	"""Incrementally save every completed league game and parse uncached PDF IDs.

	:param url: BWHV league URL including its fragment parameters.
	:param path: Destination JSON, also used as the persistent parsed-report cache.
	:param refresh: Reparse successful reports too, for corrected source reports.
	"""
	query = parse_qs(urlsplit(url).fragment.partition('?')[2])
	league_id = query['lId'][0]
	organization_id = query['ogId'][0]
	dataset: dict = (
		json.loads(path.read_text(encoding='utf-8'))
		if path.exists()
		else {
			'schema_version': 1,
			'league_id': league_id,
			'organization_id': organization_id,
			'games': {},
			'reports': {},
		}
	)
	if (dataset.get('schema_version'), dataset.get('league_id'), dataset.get('organization_id')) != (
		1,
		league_id,
		organization_id,
	):
		raise ValueError(f'Cache schema or league does not match: {path}')
	with httpx.Client(timeout=30, follow_redirects=True) as client:
		response = client.get(API_URL, params={'cmd': 'ps', 'og': organization_id, 'cl': league_id, 'ca': 1})
		response.raise_for_status()
		data = response.json()[0]
		dataset['league'] = data['head']['headline2']
		dataset['updated_at'] = datetime.now(TIMEZONE).isoformat()
		completed = [game for game in _games(data) if _completed(game)]
		for game in tqdm(completed, desc=dataset['league'], unit='match'):
			pdf_id = str(game.get('sGID', '')).strip()
			if pdf_id in ('', '0'):
				pdf_id = None
			cancelled = _cancelled(game.get('gComment', ''))
			start = _start(game)
			record: dict = {
				'game_id': str(game['gID']),
				'game_number': game['gNo'],
				'pdf_id': pdf_id,
				'pdf_url': data['head']['repURL'] + pdf_id if pdf_id else None,
				'start': start.isoformat() if start else None,
				'home': {
					'team': game['gHomeTeam'],
					'goals': int(game['gHomeGoals']),
					'points': int(game['gHomePoints'])
					if str(game.get('gHomePoints', '')).strip().isdigit()
					else None,
				},
				'away': {
					'team': game['gGuestTeam'],
					'goals': int(game['gGuestGoals']),
					'points': int(game['gGuestPoints'])
					if str(game.get('gGuestPoints', '')).strip().isdigit()
					else None,
				},
				'comment': game.get('gComment', '').strip(),
				'status': 'cancelled' if cancelled else 'played',
				'error': None if pdf_id or cancelled else 'No public PDF report.',
			}
			if cancelled:
				record['events'] = []
				for side in ('home', 'away'):
					record[side].update(players=[], officials=[])
			if pdf_id and not cancelled:
				cached = dataset['reports'].get(pdf_id)
				if refresh or not cached or cached.get('status') != 'ok':
					try:
						response = client.get(record['pdf_url'])
						response.raise_for_status()
						parsed = parse_report(response.content)
						for side in ('home', 'away'):
							if sum(p['goals'] for p in parsed[side]['players']) != record[side]['goals']:
								raise ValueError(f'{side} player goals do not match the final score.')
						dataset['reports'][pdf_id] = {
							'pdf_id': pdf_id,
							'pdf_url': record['pdf_url'],
							'status': 'ok',
							'parsed_at': datetime.now(TIMEZONE).isoformat(),
							**parsed,
						}
					except (httpx.HTTPError, ValueError, PyPdfError) as exc:
						dataset['reports'][pdf_id] = {
							'pdf_id': pdf_id,
							'pdf_url': record['pdf_url'],
							'status': 'error',
							'error': str(exc),
						}
				cached = dataset['reports'][pdf_id]
				if cached['status'] == 'ok':
					enrich_report(cached)
					for side in ('home', 'away'):
						record[side].update(cached[side])
					record['events'] = cached['events']
				else:
					record['error'] = cached['error']
			dataset['games'][record['game_id']] = record
			_save_dataset(path, dataset)
	_save_dataset(path, dataset)
	return dataset


def prepare_match(
	url: str,
	team: str,
	now: datetime | None = None,
	n_matches: int | None = None,
	dataset: dict | None = None,
	match_date: date | None = None,
) -> dict | None:
	"""Find the next fixture and combine recent rosters with goals and appearances.

	:param url: BWHV league URL including its fragment parameters.
	:param team: Exact full team name from the BWHV team list.
	:param now: Aware lookup time; defaults to current Europe/Zurich time.
	:param n_matches: Positive number of latest played matches, or None for all.
	:param dataset: Optional synced league dataset; reuse its parsed reports.
	:param match_date: Select this calendar day instead of the next future match; return None if absent.
	"""
	if n_matches is not None and (
		isinstance(n_matches, bool) or not isinstance(n_matches, int) or n_matches < 1
	):
		raise ValueError('n_matches must be a positive integer or None.')
	now = now or datetime.now(TIMEZONE)
	if now.utcoffset() is None:
		raise ValueError('now must include a timezone.')
	query = parse_qs(urlsplit(url).fragment.partition('?')[2])
	if dataset is not None and (dataset['league_id'], dataset['organization_id']) != (
		query['lId'][0],
		query['ogId'][0],
	):
		raise ValueError('Dataset belongs to a different league.')
	params = {'cmd': 'ps', 'og': query['ogId'][0], 'cl': query['lId'][0], 'ca': 1}
	with httpx.Client(timeout=30, follow_redirects=True) as client:
		response = client.get(API_URL, params=params)
		response.raise_for_status()
		data = response.json()[0]
		matches = [t for t in data['content']['teamsList'] if t['teamName'] == team]
		if len(matches) != 1:
			raise ValueError(f'Team must match exactly one league entry: {team!r}.')
		response = client.get(API_URL, params=params | {'ca': 0, 'ct': matches[0]['teamID']})
		response.raise_for_status()
		team_games = _games(response.json()[0])
		if not team_games:
			raise ValueError(f'No matches found for {team}.')
		aliases = set.intersection(*(_teams(game) for game in team_games))
		if len(aliases) != 1:
			raise ValueError(f'Cannot uniquely resolve the fixture name for {team}.')
		alias = aliases.pop()
		games = _games(data)
		future = [
			(start, game)
			for game in games
			if alias in _teams(game)
			and (start := _start(game)) is not None
			and (
				start.date() == match_date
				if match_date is not None
				else start > now and not _completed(game) and not game['live']
			)
			and not _cancelled(game.get('gComment', ''))
		]
		if not future:
			if match_date is not None:
				return None
			raise ValueError(f'No next scheduled match with a known kickoff found for {team}.')
		next_start, next_game = min(future, key=lambda candidate: candidate[0])
		opponent = next(name for name in _teams(next_game) if name != alias)
		result = {'league': data['head']['headline2'], 'next_match': next_game, 'teams': []}
		for name in (alias, opponent):
			entry: dict = {'team': name, 'players': [], 'officials': [], 'reports': [], 'error': None}
			result['teams'].append(entry)
			past = [
				game
				for game in games
				if name in _teams(game)
				and _completed(game)
				and not _cancelled(game.get('gComment', ''))
				and (start := _start(game)) is not None
				and start < now
				and start < next_start
			]
			if not past:
				entry['error'] = 'No previous completed league match found.'
				continue
			players = {}
			officials = {}
			for game in sorted(past, key=lambda game: _start(game), reverse=True)[:n_matches]:
				report = {'match': game, 'pdf_url': None, 'error': None}
				entry['reports'].append(report)
				if str(game.get('sGID', 0)).strip() in ('', '0'):
					report['error'] = 'No public PDF report.'
					continue
				report['pdf_url'] = data['head']['repURL'] + str(game['sGID'])
				try:
					if dataset is not None:
						rosters = dataset['reports'].get(str(game['sGID']))
						if not rosters or rosters.get('status') != 'ok':
							raise ValueError(
								rosters.get('error')
								if rosters
								else 'Report missing from cache; run sync_league.'
							)
					else:
						response = client.get(report['pdf_url'])
						response.raise_for_status()
						rosters = extract_rosters(response.content)
					side = 'home' if game['gHomeTeam'] == name else 'away'
					roster = rosters[side]
					entry['team'] = roster['team']
					for player in roster['players']:
						combined = players.setdefault(
							_name(player['name']),
							{
								**player,
								'name': _name(player['name']),
								'number': _starting_number(player),
								'total_goals': 0,
								'games': 0,
							},
						)
						combined['total_goals'] += player['goals']
						combined['games'] += 1
					for official in roster['officials']:
						officials.setdefault((official['name'].strip(), official['role']), official)
				except (httpx.HTTPError, ValueError, PyPdfError) as exc:
					report['error'] = f'Could not read report: {exc}'
			entry['players'] = sorted(players.values(), key=lambda player: (player['number'], player['name']))
			entry['officials'] = sorted(
				officials.values(), key=lambda official: (official['role'], official['name'])
			)

	return result


def format_preparation(result: dict) -> str:
	"""Format a preparation result as readable notebook text.

	:param result: Result returned by prepare_match.
	"""
	lines = [
		result['league'],
		_label(result['next_match']),
		'Preparation lists from recent reports; upcoming lineups may differ.',
	]
	for entry in result['teams']:
		lines.extend(['', entry['team'], 'Nr.  Player'])
		lines.extend(
			f'{p["number"]:>3}  {p["name"]}  {p["total_goals"]} Tore/{p["games"]} Spiele'
			for p in entry['players']
		)
		available = sum(report['error'] is None for report in entry['reports'])
		lines.append(f'Sources: {available}/{len(entry["reports"])} reports readable')
		for report in entry['reports']:
			lines.append(f'Source match: {_label(report["match"])}')
			if report['pdf_url']:
				lines.append(f'PDF: {report["pdf_url"]}')
			if report['error']:
				lines.append(report['error'])
		if entry['error']:
			lines.append(entry['error'])
		lines.append('Team officials:')
		lines.extend(f'  {p["role"]}  {p["name"]}' for p in entry['officials'])
	return '\n'.join(lines)


def export_matches(preparations: dict[str, dict], next_date: date, excel_path: Path) -> Path | None:
	"""Export the selected day's player lists with space for handwritten additions.

	:param preparations: Match preparations keyed by worksheet name.
	:param next_date: Match day used for worksheet filtering.
	:param excel_path: Full destination path for the workbook.
	"""
	selected = {
		label: result
		for label, result in preparations.items()
		if (start := _start(result['next_match'])) is not None
		and start.date() == next_date
		and not _cancelled(result['next_match'].get('gComment', ''))
	}
	if not selected:
		return None
	path = excel_path
	path.parent.mkdir(parents=True, exist_ok=True)
	with xlsxwriter.Workbook(path) as workbook:
		body = workbook.add_format(
			{
				'font_name': 'Arial',
				'font_size': 11,
				'font_color': '#17202A',
				'valign': 'vcenter',
				'bottom': 1,
				'bottom_color': '#D9DEE3',
			}
		)
		number = workbook.add_format(
			{
				'font_name': 'Arial',
				'font_size': 11,
				'font_color': '#17202A',
				'valign': 'vcenter',
				'align': 'right',
				'num_format': '0',
				'bottom': 1,
				'bottom_color': '#D9DEE3',
			}
		)
		heading = workbook.add_format(
			{
				'font_name': 'Arial',
				'font_size': 13,
				'bold': True,
				'font_color': '#17202A',
				'valign': 'vcenter',
				'bottom': 2,
			}
		)
		header = workbook.add_format(
			{
				'font_name': 'Arial',
				'font_size': 11,
				'bold': True,
				'bg_color': '#EDF0F3',
				'align': 'center',
				'valign': 'vcenter',
			}
		)
		for label, result in selected.items():
			sheet = workbook.add_worksheet(label)
			sheet.hide_gridlines(2)
			sheet.set_default_row(21.5)
			sheet.set_row(0, 10)
			sheet.set_row(1, 30)
			for column, width in enumerate((6, 30, 7, 7, 3, 6, 30, 7, 7)):
				sheet.set_column(column, column, width)
			last_row = max(len(team['players']) for team in result['teams']) + 10
			for index, team in enumerate(result['teams']):
				column = index * 5
				sheet.merge_range(1, column, 1, column + 3, team['team'], heading)
				sheet.write_row(2, column, ['Nr.', 'Spieler', 'Tore', 'Spiele'], header)
				for row, player in enumerate(team['players'], 3):
					sheet.write_number(row, column, player['number'], number)
					sheet.write_string(row, column + 1, player['name'], body)
					sheet.write_number(row, column + 2, player['total_goals'], number)
					sheet.write_number(row, column + 3, player['games'], number)
				for row in range(len(team['players']) + 3, len(team['players']) + 11):
					for offset in range(4):
						sheet.write_blank(row, column + offset, None, body if offset == 1 else number)
				sheet.print_area(0, 0, last_row, 8)
				sheet.set_paper(9)
				sheet.set_portrait()
				sheet.fit_to_pages(1, 1)
				sheet.set_margins(0.25, 0.25, 0.3, 0.3)
				sheet.center_horizontally()
	return path


def load_parameters(path: Path = Path('parameters.json')) -> dict:
	"""Load shared workflow settings and convert the Excel path for Python use.

	:param path: JSON parameter file, relative to the current working directory.
	"""
	parameters = json.loads(path.read_text(encoding='utf-8'))
	parameters['excel_path'] = Path(parameters['excel_path'].replace('{next_date}', parameters['next_date']))
	return parameters


def run_match_day(
	teams: dict[str, dict[str, str]],
	season: str,
	next_date: str,
	excel_path: Path,
	n_matches: int | None = None,
	refresh: bool = False,
) -> tuple[dict[str, dict], Path | None]:
	"""Sync configured leagues, prepare the selected day, and export its workbook.

	:param teams: Sheet/cache labels mapped to explicit team names and league URLs.
	:param season: Existing season folder name below matches.
	:param next_date: Match day in ISO YYYY-MM-DD format.
	:param excel_path: Full destination path for the generated workbook.
	:param n_matches: Positive number of recent played matches, or None for all.
	:param refresh: Reparse successful cached reports as well.
	"""
	match_day = date.fromisoformat(next_date)
	preparations = {}
	for label, config in teams.items():
		print(f'\n{label}\n{chr(61) * 72}')
		try:
			url = config['url']
			squad = config['team']
			dataset = sync_league(url, Path('matches') / season / f'bwhv_{label}.json', refresh=refresh)
			issues = [game for game in dataset['games'].values() if game['error']]
			print(f'Saved {len(dataset["games"])} official results; {len(issues)} unavailable reports.')
			for game in issues:
				print(f'  Game {game["game_id"]}: {game["error"]}')
			preparation = prepare_match(
				url, squad, n_matches=n_matches, dataset=dataset, match_date=match_day
			)
		except (httpx.HTTPError, ValueError, KeyError, PyPdfError) as exc:
			print(f'Preparation unavailable: {exc}')
			continue
		if preparation is None:
			print(f'No match on {next_date}.')
			continue
		preparations[label] = preparation
		print(format_preparation(preparation))
	output_path = export_matches(preparations, match_day, excel_path)
	print(f'Excel saved: {output_path}' if output_path else f'No Excel generated: no matches on {next_date}.')
	return preparations, output_path


if __name__ == '__main__':
	preparations, excel_path = run_match_day(**load_parameters())

import fs from 'node:fs/promises';
import path from 'node:path';

const DATA_DIR = path.resolve('public/data');

async function readJson(file) {
  return JSON.parse(await fs.readFile(path.join(DATA_DIR, file), 'utf8'));
}

function byId(items = []) {
  return new Map(items.map((item) => [String(item.id), item]));
}

function statusGroup(game) {
  if (game.completed || game.state === 'post' || game.status === 'STATUS_FINAL') return 'final';
  if (game.state === 'in') return 'live';
  return 'pregame';
}

export function formatKickoff(date, timeZone = 'America/New_York') {
  const value = new Date(date);
  if (Number.isNaN(value.valueOf())) return 'TIME TBD';
  const day = new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric', timeZone }).format(value);
  const time = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit', timeZoneName: 'short', timeZone }).format(value);
  return `${day.toUpperCase()} · ${time.toUpperCase()}`;
}

export async function loadSocialWeek({ season: requestedSeason, week, includeStarted = false }) {
  const manifest = await readJson('manifest.json');
  const season = Number(requestedSeason ?? manifest.latestSeason);
  const seasonData = await readJson(`${season}.json`);
  const latestSeason = Number(manifest.latestSeason);
  const current = season === latestSeason;
  const live = current ? await readJson(`live-${season}.json`) : null;
  const fixtures = current ? await readJson('fixtures.json') : null;

  const requestedSnapshot = seasonData.snapshots?.[String(week)];
  const snapshot = requestedSnapshot ?? seasonData.snapshots?.['99'];
  if (!snapshot) throw new Error(`No ranking snapshot is available for ${season}.`);
  const teams = byId(snapshot.teams);
  const predictions = byId(seasonData.predictions);
  const liveGames = byId(live?.games);

  const sourceGames = current
    ? (fixtures?.games ?? live?.games ?? [])
    : (seasonData.games ?? []);
  const unique = byId(sourceGames.filter((game) => Number(game.week) === Number(week)));
  for (const game of live?.games ?? []) {
    if (Number(game.week) === Number(week)) unique.set(String(game.id), { ...unique.get(String(game.id)), ...game });
  }

  const allGames = [];
  for (const base of unique.values()) {
    if (!base.fbs) continue;
    const id = String(base.id);
    const currentGame = liveGames.get(id);
    const game = currentGame ? { ...base, ...currentGame } : base;
    const home = teams.get(String(game.home));
    const away = teams.get(String(game.away));
    if (!home || !away) continue;

    const archived = predictions.get(id);
    const homeProbability = currentGame?.pregame?.homeWinProbability ?? archived?.prob;
    if (!Number.isFinite(homeProbability)) continue;
    const state = statusGroup(game);
    allGames.push({
      id,
      season,
      week: Number(week),
      date: game.date,
      neutral: Boolean(game.neutral),
      state,
      statusDetail: game.statusDetail ?? (state === 'final' ? 'Final' : null),
      home: { ...home, probability: Number(homeProbability) },
      away: { ...away, probability: 1 - Number(homeProbability) },
      kickoff: formatKickoff(game.date),
      venue: game.detail?.venue?.name ?? null,
      broadcast: game.broadcast ?? game.detail?.broadcast ?? null,
      predictionSource: currentGame?.pregame ? 'live pregame archive' : 'weekly prediction archive',
      modelVersion: currentGame?.pregame?.modelVersion ?? archived?.modelVersion ?? seasonData.model?.version ?? '6.0.0',
    });
  }

  allGames.sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));
  let games = includeStarted ? allGames : allGames.filter((game) => game.state === 'pregame');
  if (!games.length && allGames.length) games = allGames;
  if (!games.length) throw new Error(`No FBS games with published predictions found for ${season} week ${week}.`);

  return {
    season,
    week: Number(week),
    snapshotKey: requestedSnapshot ? Number(week) : 99,
    snapshotThrough: snapshot.through ?? live?.weeklySnapshotThrough ?? null,
    liveUpdatedAt: live?.updatedAt ?? null,
    games,
    allGames,
  };
}


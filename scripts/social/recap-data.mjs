import fs from 'node:fs/promises';
import path from 'node:path';
import { loadSocialWeek } from './data.mjs';
import { scoreGame, selectGames } from './select.mjs';

const DATA_DIR = path.resolve('public/data');
const readJson = async (name) => JSON.parse(await fs.readFile(path.join(DATA_DIR, name), 'utf8'));
const mapBy = (items, key = 'id') => new Map((items ?? []).map((item) => [String(item[key]), item]));
const modelRank = (team) => Number(team?.modelRank ?? team?.rank ?? 999);

function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function snapshotAfterWeek(seasonData, week) {
  return seasonData.snapshots?.[String(Number(week) + 1)] ?? seasonData.snapshots?.['99'];
}

function snapshotBeforeWeek(seasonData, week) {
  if (seasonData.snapshots?.[String(week)]) return seasonData.snapshots[String(week)];
  const candidates = Object.keys(seasonData.snapshots ?? {}).map(Number).filter((key) => key !== 99 && key <= Number(week)).sort((a, b) => b - a);
  return seasonData.snapshots?.[String(candidates[0])] ?? seasonData.snapshots?.['1'];
}

function evaluatedPrediction(prediction, teams) {
  const home = teams.get(String(prediction.home));
  const away = teams.get(String(prediction.away));
  if (!home || !away || !Number.isFinite(prediction.prob) || !Number.isFinite(prediction.hs) || !Number.isFinite(prediction.as) || prediction.hs === prediction.as) return null;
  const homeWon = prediction.hs > prediction.as;
  const pickedHome = prediction.prob >= 0.5;
  return scoreGame({
    id: String(prediction.id),
    season: Number(prediction.season),
    week: Number(prediction.week),
    date: prediction.date,
    neutral: Boolean(prediction.neutral),
    home: { ...home, probability: Number(prediction.prob), score: Number(prediction.hs) },
    away: { ...away, probability: 1 - Number(prediction.prob), score: Number(prediction.as) },
    homeWon,
    pickedHome,
    correct: homeWon === pickedHome,
    winner: homeWon ? 'home' : 'away',
    winnerProbability: homeWon ? Number(prediction.prob) : 1 - Number(prediction.prob),
    modelVersion: prediction.modelVersion ?? '6.0.0',
  });
}

function scorecard(predictions, throughWeek) {
  const games = predictions.filter(Boolean);
  const correct = games.filter((game) => game.correct).length;
  const brier = mean(games.map((game) => (game.home.probability - Number(game.homeWon)) ** 2));
  const logLoss = mean(games.map((game) => {
    const p = Math.max(1e-9, Math.min(1 - 1e-9, game.home.probability));
    return -(Number(game.homeWon) * Math.log(p) + Number(!game.homeWon) * Math.log(1 - p));
  }));
  const confident = games.filter((game) => Math.max(game.home.probability, game.away.probability) >= 0.8);
  return {
    games: games.length,
    correct,
    accuracy: games.length ? correct / games.length : 0,
    brier,
    logLoss,
    confidentGames: confident.length,
    confidentCorrect: confident.filter((game) => game.correct).length,
    label: `Through Week ${throughWeek}`,
  };
}

function movement(preTeams, postTeams) {
  const changes = [];
  for (const team of postTeams.values()) {
    const previous = preTeams.get(String(team.id));
    if (!previous) continue;
    const before = modelRank(previous);
    const after = modelRank(team);
    changes.push({ ...team, previousRank: before, currentRank: after, delta: before - after });
  }
  const riser = [...changes].sort((a, b) => b.delta - a.delta || a.currentRank - b.currentRank)[0];
  const faller = [...changes].sort((a, b) => a.delta - b.delta || a.currentRank - b.currentRank)[0];
  const newTop25 = changes.filter((team) => team.previousRank > 25 && team.currentRank <= 25).sort((a, b) => a.currentRank - b.currentRank)[0] ?? null;
  const outTop25 = changes.filter((team) => team.previousRank <= 25 && team.currentRank > 25).sort((a, b) => b.currentRank - a.currentRank)[0] ?? null;
  return { riser, faller, newTop25, outTop25, all: changes };
}

function byTheNumbers(games, boxRows, postTeams) {
  const margin = (game) => Math.abs(game.home.score - game.away.score);
  const total = (game) => game.home.score + game.away.score;
  const biggestMargin = [...games].sort((a, b) => margin(b) - margin(a))[0];
  const closest = [...games].sort((a, b) => margin(a) - margin(b) || total(b) - total(a))[0];
  const highestTotal = [...games].sort((a, b) => total(b) - total(a))[0];
  const weekRows = boxRows.filter((row) => Number(row.week) === Number(games[0]?.week) && row.fbs);
  const rushing = [...weekRows].filter((row) => Number.isFinite(row.own?.rushYards)).sort((a, b) => b.own.rushYards - a.own.rushYards)[0];
  const offense = [...weekRows].filter((row) => Number.isFinite(row.own?.totalYards)).sort((a, b) => b.own.totalYards - a.own.totalYards)[0];
  const turnovers = [...weekRows].filter((row) => Number.isFinite(row.opponent?.turnovers)).sort((a, b) => b.opponent.turnovers - a.opponent.turnovers)[0];
  const rowStat = (row, value, label) => row ? ({ type: 'team', team: postTeams.get(String(row.teamId)), value, label, gameId: String(row.gameId) }) : null;
  return [
    { type: 'game', game: highestTotal, value: total(highestTotal), label: 'TOTAL POINTS' },
    { type: 'game', game: biggestMargin, value: margin(biggestMargin), label: 'BIGGEST MARGIN' },
    { type: 'game', game: closest, value: margin(closest), label: 'CLOSEST FINISH' },
    rowStat(rushing, Math.round(rushing?.own?.rushYards ?? 0), 'RUSHING YARDS'),
    rowStat(offense, Math.round(offense?.own?.totalYards ?? 0), 'TOTAL YARDS'),
    rowStat(turnovers, Math.round(turnovers?.opponent?.turnovers ?? 0), 'TAKEAWAYS'),
  ].filter(Boolean);
}

export async function loadRecap({ season: requestedSeason, week, featured, upset }) {
  const manifest = await readJson('manifest.json');
  const season = Number(requestedSeason ?? manifest.latestSeason);
  const seasonData = await readJson(`${season}.json`);
  const before = snapshotBeforeWeek(seasonData, week);
  const after = snapshotAfterWeek(seasonData, week);
  if (!before || !after) throw new Error(`A before/after ranking snapshot is not available for ${season} Week ${week}.`);
  const beforeTeams = mapBy(before.teams);
  const afterTeams = mapBy(after.teams);
  const weekEvaluated = seasonData.predictions
    .filter((prediction) => Number(prediction.week) === Number(week) && prediction.fbs)
    .map((prediction) => evaluatedPrediction(prediction, beforeTeams)).filter(Boolean);
  if (!weekEvaluated.length) throw new Error(`No completed FBS predictions are available for ${season} Week ${week}.`);

  const seasonEvaluated = seasonData.predictions
    .filter((prediction) => Number(prediction.week) <= Number(week) && prediction.fbs)
    .map((prediction) => evaluatedPrediction(prediction, beforeTeams)).filter(Boolean);
  const importantSelection = selectGames(weekEvaluated, { featured, featuredCount: 4, otherCount: 0 });
  const important = importantSelection.featured;
  let upsetGame = upset ? weekEvaluated.find((game) => game.id === String(upset)) : null;
  if (upset && !upsetGame) throw new Error(`Upset override game ${upset} is not a completed Week ${week} FBS game.`);
  if (!upsetGame) {
    upsetGame = [...weekEvaluated].sort((a, b) => {
      const aScore = (1 - a.winnerProbability) * (0.62 + 0.38 * a.metrics.quality / 100);
      const bScore = (1 - b.winnerProbability) * (0.62 + 0.38 * b.metrics.quality / 100);
      return bScore - aScore;
    })[0];
  }

  const box = await readJson(`box-${season}.json`);
  let nextWeek = null;
  try {
    const nextContext = await loadSocialWeek({ season, week: Number(week) + 1 });
    nextWeek = { context: nextContext, games: selectGames(nextContext.games, { featuredCount: 4, otherCount: 0 }).featured };
  } catch {
    nextWeek = null;
  }

  const postTop25 = [...afterTeams.values()].sort((a, b) => modelRank(a) - modelRank(b)).slice(0, 25)
    .map((team) => ({ ...team, previousRank: modelRank(beforeTeams.get(String(team.id))), currentRank: modelRank(team), delta: modelRank(beforeTeams.get(String(team.id))) - modelRank(team) }));
  return {
    season,
    week: Number(week),
    modelVersion: weekEvaluated[0].modelVersion,
    beforeThrough: before.through ?? null,
    afterThrough: after.through ?? null,
    top25: postTop25,
    important,
    weekScorecard: scorecard(weekEvaluated, week),
    seasonScorecard: scorecard(seasonEvaluated, week),
    upset: upsetGame,
    movement: movement(beforeTeams, afterTeams),
    numbers: byTheNumbers(weekEvaluated, box.rows ?? [], afterTeams),
    nextWeek,
    completedGames: weekEvaluated,
  };
}


import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import test from 'node:test';
import sharp from 'sharp';
import { loadSocialWeek } from './data.mjs';
import { scoreGame, selectGames } from './select.mjs';

async function currentTestContext() {
  const manifest = JSON.parse(await fs.readFile('public/data/manifest.json', 'utf8'));
  const live = JSON.parse(await fs.readFile(`public/data/live-${manifest.latestSeason}.json`, 'utf8'));
  const source = live.games.find((game) => game.fbs && game.pregame?.homeWinProbability != null);
  const context = await loadSocialWeek({ season: manifest.latestSeason, week: source.week, includeStarted: true });
  return { context, live, source };
}

test('social data uses the published live pregame probability exactly', async () => {
  const { context, source } = await currentTestContext();
  const game = context.games.find((item) => item.id === source.id);
  assert.equal(game.home.probability, source.pregame.homeWinProbability);
  assert.equal(game.away.probability, 1 - source.pregame.homeWinProbability);
});

test('interest scoring prioritizes elite ranked matchups over equal low-ranked teams', () => {
  const game = (homeRank, awayRank, homeProbability) => ({
    id: `${homeRank}-${awayRank}`, date: '2026-10-03T16:00Z',
    home: { id: 'h', modelRank: homeRank, probability: homeProbability },
    away: { id: 'a', modelRank: awayRank, probability: 1 - homeProbability },
  });
  assert.ok(scoreGame(game(3, 1, 0.52)).metrics.interest > scoreGame(game(100, 101, 0.5)).metrics.interest);
});

test('featured override is honored and selection is deterministic', async () => {
  const { context } = await currentTestContext();
  const target = context.games.at(-1).id;
  const first = selectGames(context.games, { featured: target, featuredCount: 4 });
  const second = selectGames(context.games, { featured: target, featuredCount: 4 });
  assert.equal(first.featured[0].id, target);
  assert.deepEqual(first.featured.map((game) => game.id), second.featured.map((game) => game.id));
});

test('generated slide dimensions remain Instagram portrait size', async () => {
  const sample = process.env.SOCIAL_SAMPLE;
  if (!sample) return;
  const metadata = await sharp(sample).metadata();
  assert.equal(metadata.width, 1080);
  assert.equal(metadata.height, 1350);
});


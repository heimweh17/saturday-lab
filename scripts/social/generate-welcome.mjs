#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadSocialWeek } from './data.mjs';
import { hydrateTeams, loadFontCss, makeContactSheet, writePng } from './render.mjs';
import { selectGames } from './select.mjs';
import { followSlide, welcomeSlide } from './welcome-templates.mjs';

async function readJson(name) {
  return JSON.parse(await fs.readFile(path.resolve('public/data', name), 'utf8'));
}

export async function generateWelcome(outputOption) {
  const manifest = await readJson('manifest.json');
  const season = Number(manifest.latestSeason);
  const seasonData = await readJson(`${season}.json`);
  const live = await readJson(`live-${season}.json`);
  const week = Math.min(...live.games.filter((game) => game.fbs && game.state === 'pre' && game.pregame).map((game) => Number(game.week)));
  const weekContext = await loadSocialWeek({ season, week });
  const game = selectGames(weekContext.games, { featuredCount: 1, otherCount: 0 }).featured[0];
  const topTeams = [...seasonData.snapshots['99'].teams].sort((a, b) => a.modelRank - b.modelRank).slice(0, 3);
  await hydrateTeams([...topTeams, game.away, game.home]);
  const context = { season, week, topTeams, game };
  const fontCss = await loadFontCss();
  const slides = [
    { name: 'welcome-to-saturday-lab', svg: welcomeSlide({ context, fontCss, index: 1, total: 2 }) },
    { name: 'follow-the-season', svg: followSlide({ context, fontCss, index: 2, total: 2 }) },
  ];
  const output = path.resolve(outputOption ?? 'outputs/social/welcome-launch');
  await fs.rm(output, { recursive: true, force: true });
  await fs.mkdir(output, { recursive: true });
  const files = [];
  for (let index = 0; index < slides.length; index += 1) {
    const file = path.join(output, `${String(index + 1).padStart(2, '0')}-${slides[index].name}.png`);
    await writePng(slides[index].svg, file);
    files.push(file);
  }
  const contactSheet = path.join(output, 'contact-sheet.png');
  await makeContactSheet(files, contactSheet);
  await fs.writeFile(path.join(output, 'manifest.json'), `${JSON.stringify({
    generatedAt: new Date().toISOString(), edition: 'welcome-launch', season, week,
    currentTopThree: topTeams.map((team) => ({ id: team.id, rank: team.modelRank, team: team.short })),
    featuredExample: { id: game.id, matchup: `${game.away.short} at ${game.home.short}`, awayProbability: game.away.probability, homeProbability: game.home.probability },
    files: files.map((file) => path.basename(file)),
  }, null, 2)}\n`);
  return { output, files, contactSheet };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outputFlag = process.argv.indexOf('--output');
  generateWelcome(outputFlag >= 0 ? process.argv[outputFlag + 1] : undefined).then((result) => {
    console.log(`Generated ${result.files.length} welcome slides in ${result.output}`);
    console.log(`Contact sheet: ${result.contactSheet}`);
  }).catch((error) => { console.error(error.stack ?? error.message); process.exitCode = 1; });
}


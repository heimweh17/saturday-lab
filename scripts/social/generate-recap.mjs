#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadRecap } from './recap-data.mjs';
import { hydrateTeams, loadFontCss, makeContactSheet, writePng } from './render.mjs';
import { movementSlide, nextWeekSlide, numbersSlide, recapUpsetSlide, resultsSlide, scorecardSlide, top25Slide } from './recap-templates.mjs';

function argsFrom(argv) {
  const values = {};
  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith('--')) { positional.push(value); continue; }
    const key = value.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    const next = argv[index + 1];
    if (!next || next.startsWith('--')) values[key] = true;
    else { values[key] = next; index += 1; }
  }
  if (!values.season && positional[0]) values.season = positional[0];
  if (!values.week && positional[1]) values.week = positional[1];
  return values;
}

const usage = () => `Generate a Saturday Lab Monday Recap\n\nUsage:\n  npm run social:recap -- 2026 4\n\nOptions:\n  --featured id,id   Override the four result cards\n  --upset id         Override Upset of the Week\n  --output path      Output directory\n  --keep-svg         Keep editable SVG files\n`;

function gameRecord(game) {
  return game && ({
    id: game.id,
    matchup: `${game.away.short} at ${game.home.short}`,
    final: { away: game.away.score, home: game.home.score },
    pregame: { away: game.away.probability, home: game.home.probability },
    correct: game.correct,
    interest: game.metrics?.interest,
  });
}

export async function generateRecap(options) {
  if (!options.week) throw new Error('A completed week is required. Pass --week 4.');
  const recap = await loadRecap({ season: options.season, week: Number(options.week), featured: options.featured, upset: options.upset });
  if (!recap.nextWeek?.games?.length) throw new Error(`No Week ${recap.week + 1} forecast is available for the final preview slide.`);

  const teams = [
    ...recap.top25,
    ...recap.important.flatMap((game) => [game.away, game.home]),
    recap.upset.away, recap.upset.home,
    recap.movement.riser, recap.movement.faller, recap.movement.newTop25, recap.movement.outTop25,
    ...recap.numbers.map((stat) => stat.team).filter(Boolean),
    ...recap.nextWeek.games.flatMap((game) => [game.away, game.home]),
  ].filter(Boolean);
  await hydrateTeams(teams);
  const fontCss = await loadFontCss();
  const total = 7;
  const slides = [
    { name: 'new-top-25', svg: top25Slide({ recap, fontCss, index: 1, total }) },
    { name: 'weekend-in-four', svg: resultsSlide({ recap, fontCss, index: 2, total }) },
    { name: 'model-scorecard', svg: scorecardSlide({ recap, fontCss, index: 3, total }) },
    { name: `upset-of-week-${recap.upset.id}`, svg: recapUpsetSlide({ recap, fontCss, index: 4, total }) },
    { name: 'rankings-on-the-move', svg: movementSlide({ recap, fontCss, index: 5, total }) },
    { name: 'weekend-by-the-numbers', svg: numbersSlide({ recap, fontCss, index: 6, total }) },
    { name: `week-${recap.week + 1}-preview`, svg: nextWeekSlide({ recap, fontCss, index: 7, total }) },
  ];

  const output = path.resolve(options.output ?? path.join('outputs', 'social', `${recap.season}-week-${recap.week}-recap`));
  await fs.rm(output, { recursive: true, force: true });
  await fs.mkdir(output, { recursive: true });
  const files = [];
  for (let index = 0; index < slides.length; index += 1) {
    const prefix = String(index + 1).padStart(2, '0');
    const target = path.join(output, `${prefix}-${slides[index].name}.png`);
    await writePng(slides[index].svg, target);
    if (options.keepSvg) await fs.writeFile(path.join(output, `${prefix}-${slides[index].name}.svg`), slides[index].svg);
    files.push(target);
  }
  const contactSheet = path.join(output, 'contact-sheet.png');
  await makeContactSheet(files, contactSheet);
  const manifest = {
    generatedAt: new Date().toISOString(),
    edition: 'monday-recap',
    season: recap.season,
    completedWeek: recap.week,
    nextWeek: recap.week + 1,
    modelVersion: recap.modelVersion,
    rankingWindow: { beforeThrough: recap.beforeThrough, afterThrough: recap.afterThrough },
    selectionPolicy: {
      importantResults: 'Same published interest score used by the weekly preview, evaluated against final results.',
      upset: 'Lowest expected winner, moderated by matchup quality; override accepts a completed FBS game ID.',
      movements: 'Direct model-rank difference between the pregame and next published ranking snapshots.',
      numbers: 'Deterministic extrema from final scores and the published team box-score archive.',
    },
    scorecard: { week: recap.weekScorecard, season: recap.seasonScorecard },
    importantResults: recap.important.map(gameRecord),
    upset: gameRecord(recap.upset),
    nextWeekGames: recap.nextWeek.games.map((game) => ({ id: game.id, matchup: `${game.away.short} at ${game.home.short}`, probabilities: { away: game.away.probability, home: game.home.probability } })),
    files: files.map((file) => path.basename(file)),
  };
  await fs.writeFile(path.join(output, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return { output, files, contactSheet, manifest };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const options = argsFrom(process.argv.slice(2));
  if (options.help) console.log(usage());
  else generateRecap(options).then((result) => {
    console.log(`Generated ${result.files.length} recap slides in ${result.output}`);
    console.log(`Contact sheet: ${result.contactSheet}`);
    console.log(`Week accuracy: ${(result.manifest.scorecard.week.accuracy * 100).toFixed(1)}%`);
    console.log(`Upset: ${result.manifest.upset.matchup}`);
  }).catch((error) => {
    console.error(error.stack ?? error.message);
    process.exitCode = 1;
  });
}


#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadSocialWeek } from './data.mjs';
import { selectGames } from './select.mjs';
import { hydrateLogos, loadFontCss, makeContactSheet, writePng } from './render.mjs';
import { closingSlide, featureSlide, otherGamesSlide, overviewSlide, upsetSlide } from './templates.mjs';

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

function usage() {
  return `Generate Saturday Lab social graphics\n\nUsage:\n  npm run social:generate -- --season 2026 --week 6\n\nOptions:\n  --featured id,id    Pin games to the front of Featured Games\n  --upset id          Override Upset Watch\n  --featured-count 4  Number of individual featured slides\n  --other-count 6     Number of games on More Predictions\n  --include-started   Include live/final games when upcoming games exist\n  --output path       Output directory\n  --keep-svg          Keep editable SVG source files\n`;
}

export async function generateSocialGraphics(options) {
  if (!options.week) throw new Error('A week is required. Pass --week 6.');
  const context = await loadSocialWeek({
    season: options.season,
    week: Number(options.week),
    includeStarted: Boolean(options.includeStarted),
  });
  const selection = selectGames(context.games, options);
  const allSelected = [...selection.featured, ...(selection.upset ? [selection.upset] : []), ...selection.others];
  await hydrateLogos(allSelected);
  const fonts = await loadFontCss();
  const slides = [];
  const provisionalTotal = 1 + selection.featured.length + (selection.upset ? 1 : 0) + (selection.others.length ? 1 : 0) + 1;
  let slideIndex = 1;
  slides.push({ name: 'weekly-picks', svg: overviewSlide({ context, selection, fontCss: fonts, index: slideIndex++, total: provisionalTotal }) });
  selection.featured.forEach((game, featureIndex) => {
    slides.push({ name: `featured-${featureIndex + 1}-${game.id}`, gameId: game.id, svg: featureSlide({ context, game, featureIndex: featureIndex + 1, fontCss: fonts, index: slideIndex++, total: provisionalTotal }) });
  });
  if (selection.upset) slides.push({ name: `upset-watch-${selection.upset.id}`, gameId: selection.upset.id, svg: upsetSlide({ context, game: selection.upset, fontCss: fonts, index: slideIndex++, total: provisionalTotal }) });
  if (selection.others.length) slides.push({ name: 'more-predictions', svg: otherGamesSlide({ context, games: selection.others, fontCss: fonts, index: slideIndex++, total: provisionalTotal }) });
  slides.push({ name: 'full-board-online', svg: closingSlide({ context, fontCss: fonts, index: slideIndex, total: provisionalTotal, gameCount: context.games.length }) });

  const output = path.resolve(options.output ?? path.join('outputs', 'social', `${context.season}-week-${context.week}`));
  await fs.rm(output, { recursive: true, force: true });
  await fs.mkdir(output, { recursive: true });
  const files = [];
  for (let index = 0; index < slides.length; index += 1) {
    const prefix = String(index + 1).padStart(2, '0');
    const filename = `${prefix}-${slides[index].name}.png`;
    const target = path.join(output, filename);
    await writePng(slides[index].svg, target);
    if (options.keepSvg) await fs.writeFile(path.join(output, `${prefix}-${slides[index].name}.svg`), slides[index].svg);
    files.push(target);
  }
  const contactSheet = path.join(output, 'contact-sheet.png');
  await makeContactSheet(files, contactSheet);

  const serializeGame = (game) => game && ({
    id: game.id,
    matchup: `${game.away.short} at ${game.home.short}`,
    kickoff: game.kickoff,
    probabilities: { away: game.away.probability, home: game.home.probability },
    ranks: { away: game.away.modelRank, home: game.home.modelRank },
    metrics: game.metrics,
    predictionSource: game.predictionSource,
    modelVersion: game.modelVersion,
  });
  const manifest = {
    generatedAt: new Date().toISOString(),
    season: context.season,
    week: context.week,
    rankingSnapshot: context.snapshotKey,
    snapshotThrough: context.snapshotThrough,
    liveDataUpdatedAt: context.liveUpdatedAt,
    selectionPolicy: '53% ranking quality + 34% projected closeness + ranked/top-10/top-5 matchup bonuses; Upset Watch uses underdog win probability, closeness and ranking gap.',
    filters: { includeStarted: Boolean(options.includeStarted), eligibleGames: context.games.length },
    overrides: { featured: options.featured ?? null, upset: options.upset ?? null },
    featured: selection.featured.map(serializeGame),
    upset: serializeGame(selection.upset),
    others: selection.others.map(serializeGame),
    files: files.map((file) => path.basename(file)),
  };
  await fs.writeFile(path.join(output, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return { output, files, contactSheet, manifest };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const options = argsFrom(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
  } else {
    generateSocialGraphics(options).then((result) => {
      console.log(`Generated ${result.files.length} slides in ${result.output}`);
      console.log(`Contact sheet: ${result.contactSheet}`);
      for (const game of result.manifest.featured) console.log(`Featured: ${game.matchup} (${game.metrics.interest})`);
      if (result.manifest.upset) console.log(`Upset Watch: ${result.manifest.upset.matchup} (${result.manifest.upset.metrics.upset})`);
    }).catch((error) => {
      console.error(error.stack ?? error.message);
      process.exitCode = 1;
    });
  }
}


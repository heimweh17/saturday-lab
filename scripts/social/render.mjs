import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const CACHE_DIR = path.resolve('.cache/social-logos');

function mimeFor(buffer) {
  if (buffer[0] === 0x89 && buffer[1] === 0x50) return 'image/png';
  if (buffer[0] === 0xff && buffer[1] === 0xd8) return 'image/jpeg';
  return 'image/png';
}

async function logoData(team) {
  if (!team.logo) return null;
  await fs.mkdir(CACHE_DIR, { recursive: true });
  const file = path.join(CACHE_DIR, `${team.id}.img`);
  let buffer;
  try {
    buffer = await fs.readFile(file);
  } catch {
    const response = await fetch(team.logo);
    if (!response.ok) return null;
    buffer = Buffer.from(await response.arrayBuffer());
    await fs.writeFile(file, buffer);
  }
  return `data:${mimeFor(buffer)};base64,${buffer.toString('base64')}`;
}

export async function hydrateLogos(games) {
  const teams = new Map();
  for (const game of games) {
    teams.set(String(game.home.id), game.home);
    teams.set(String(game.away.id), game.away);
  }
  await Promise.all([...teams.values()].map(async (team) => {
    team.logoData = await logoData(team);
  }));
}

export async function hydrateTeams(teams) {
  const unique = new Map(teams.filter(Boolean).map((team) => [String(team.id), team]));
  await Promise.all([...unique.values()].map(async (team) => {
    team.logoData = await logoData(team);
  }));
}

async function fontFace(name, file, weight) {
  const bytes = await fs.readFile(path.resolve('scripts/social/assets', file));
  return `@font-face{font-family:'${name}';src:url(data:font/ttf;base64,${bytes.toString('base64')}) format('truetype');font-weight:${weight};font-style:normal;}`;
}

export async function loadFontCss() {
  return [
    await fontFace('SL Display', 'BarlowCondensed-Black.ttf', 900),
    await fontFace('SL Condensed', 'BarlowCondensed-Bold.ttf', 700),
    await fontFace('SL Body', 'Barlow-Medium.ttf', 500),
  ].join('');
}

export async function writePng(svg, file) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await sharp(Buffer.from(svg)).png({ compressionLevel: 9, palette: false }).toFile(file);
}

export async function makeContactSheet(files, target) {
  const thumbs = await Promise.all(files.map((file) => sharp(file).resize(324, 405, { fit: 'cover' }).png().toBuffer()));
  const columns = 3;
  const rows = Math.ceil(thumbs.length / columns);
  const gap = 18;
  const width = columns * 324 + (columns + 1) * gap;
  const height = rows * 405 + (rows + 1) * gap;
  const composites = thumbs.map((input, index) => ({
    input,
    left: gap + (index % columns) * (324 + gap),
    top: gap + Math.floor(index / columns) * (405 + gap),
  }));
  await sharp({ create: { width, height, channels: 4, background: '#050b12' } }).composite(composites).png().toFile(target);
}


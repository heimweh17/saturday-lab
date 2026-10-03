const W = 1080;
const H = 1350;

export const esc = (value = '') => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[char]));
export const pct = (value) => `${(value * 100).toFixed(1)}%`;
export const rank = (team) => `#${team.modelRank ?? team.rank ?? '—'}`;
export const color = (team, fallback) => /^#[0-9a-f]{6}$/i.test(team.color ?? '') ? team.color : fallback;
export const winner = (game) => game.home.probability >= game.away.probability ? game.home : game.away;

function defs(fontCss = '') {
  return `<defs>
    <style>${fontCss}
      .display{font-family:'SL Display',sans-serif;font-weight:900;letter-spacing:.3px}
      .condensed{font-family:'SL Condensed',sans-serif;font-weight:700;letter-spacing:.8px}
      .body{font-family:'SL Body',sans-serif;font-weight:500}
    </style>
    <linearGradient id="ink" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0c1825"/><stop offset="1" stop-color="#04090f"/></linearGradient>
    <radialGradient id="lamp"><stop stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <pattern id="yard" width="90" height="90" patternUnits="userSpaceOnUse"><path d="M0 90H90M90 0V90" stroke="#c8d6df" stroke-opacity=".055" stroke-width="2"/><path d="M45 78v12" stroke="#c8d6df" stroke-opacity=".12" stroke-width="3"/></pattern>
    <pattern id="dots" width="12" height="12" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="#fff" opacity=".08"/></pattern>
    <filter id="shadow"><feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#000" flood-opacity=".48"/></filter>
    <filter id="logoGlow"><feDropShadow dx="0" dy="0" stdDeviation="18" flood-color="#fff" flood-opacity=".25"/></filter>
  </defs>`;
}

export function base(fontCss, accent = '#f4b942') {
  return `${defs(fontCss)}
    <rect width="${W}" height="${H}" fill="url(#ink)"/>
    <rect width="${W}" height="${H}" fill="url(#yard)"/>
    <ellipse cx="180" cy="70" rx="340" ry="280" fill="url(#lamp)"/>
    <ellipse cx="950" cy="80" rx="300" ry="240" fill="url(#lamp)"/>
    <rect x="0" y="0" width="14" height="1350" fill="${accent}"/>
    <path d="M14 1190L1080 860V1350H14Z" fill="#fff" opacity=".025"/>
    <rect x="14" y="0" width="1066" height="1350" fill="url(#dots)" opacity=".24"/>`;
}

export function header(season, week, section) {
  return `<g transform="translate(66 56)">
    <text class="display" x="0" y="38" fill="#f7f4ea" font-size="42">SATURDAY LAB</text>
    <rect x="0" y="57" width="166" height="5" rx="2.5" fill="#f4b942"/>
    <text class="condensed" x="948" y="20" text-anchor="end" fill="#91a5b6" font-size="24">${esc(season)} · WEEK ${esc(week)}</text>
    <text class="condensed" x="948" y="54" text-anchor="end" fill="#f7f4ea" font-size="26">${esc(section)}</text>
  </g>`;
}

export function footer(index, total) {
  return `<g transform="translate(66 1293)">
    <text class="body" fill="#8da1b1" font-size="20">saturday-lab · MODEL v6 · INDEPENDENT PROJECT</text>
    <text class="condensed" x="948" text-anchor="end" fill="#f7f4ea" font-size="24">${String(index).padStart(2, '0')} / ${String(total).padStart(2, '0')}</text>
  </g>`;
}

export function logo(team, x, y, size) {
  if (team.logoData) return `<image href="${team.logoData}" x="${x}" y="${y}" width="${size}" height="${size}" preserveAspectRatio="xMidYMid meet" filter="url(#logoGlow)"/>`;
  return `<circle cx="${x + size / 2}" cy="${y + size / 2}" r="${size * .42}" fill="#fff" opacity=".12"/><text class="display" x="${x + size / 2}" y="${y + size * .65}" text-anchor="middle" fill="#fff" font-size="${size * .36}">${esc(team.abbr)}</text>`;
}

function probabilityBar(game, x, y, width) {
  const awayWidth = Math.round(width * game.away.probability);
  return `<g transform="translate(${x} ${y})">
    <rect width="${width}" height="18" rx="9" fill="${color(game.home, '#64748b')}" opacity=".42"/>
    <rect width="${awayWidth}" height="18" rx="9" fill="${color(game.away, '#64748b')}"/>
    <circle cx="${awayWidth}" cy="9" r="14" fill="#f7f4ea" stroke="#07111c" stroke-width="5"/>
  </g>`;
}

function cardRow(game, y, index) {
  const edge = winner(game);
  return `<g transform="translate(62 ${y})">
    <rect width="956" height="198" rx="24" fill="#111f2d" stroke="#89a0b2" stroke-opacity=".16"/>
    <rect width="9" height="198" rx="4.5" fill="${color(edge, '#f4b942')}"/>
    <text class="condensed" x="38" y="46" fill="#7f95a7" font-size="21">${String(index).padStart(2, '0')} · ${esc(game.kickoff)}</text>
    ${logo(game.away, 36, 66, 92)}${logo(game.home, 456, 66, 92)}
    <text class="condensed" x="142" y="99" fill="#91a5b6" font-size="20">${rank(game.away)}</text>
    <text class="display" x="142" y="137" fill="#f7f4ea" font-size="36">${esc(game.away.short)}</text>
    <text class="condensed" x="562" y="99" fill="#91a5b6" font-size="20">${rank(game.home)}</text>
    <text class="display" x="562" y="137" fill="#f7f4ea" font-size="36">${esc(game.home.short)}</text>
    <text class="display" x="910" y="112" text-anchor="end" fill="#f7f4ea" font-size="48">${pct(edge.probability)}</text>
    <text class="condensed" x="910" y="144" text-anchor="end" fill="#f4b942" font-size="19">${esc(edge.short)} EDGE</text>
  </g>`;
}

export function overviewSlide({ context, selection, fontCss, index, total }) {
  const games = selection.featured.slice(0, 4);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss)}${header(context.season, context.week, 'WEEKLY PICKS')}
    <text class="display" x="66" y="190" fill="#f7f4ea" font-size="78">THE GAMES THAT</text>
    <text class="display" x="66" y="260" fill="#f4b942" font-size="78">DEFINE THE WEEK.</text>
    <text class="body" x="68" y="307" fill="#9eb0be" font-size="23">Four model-selected matchups · probabilities frozen before kickoff</text>
    ${games.map((game, i) => cardRow(game, 342 + i * 215, i + 1)).join('')}
    ${footer(index, total)}
  </svg>`;
}

export function featureSlide({ context, game, featureIndex, fontCss, index, total }) {
  const awayColor = color(game.away, '#34506a');
  const homeColor = color(game.home, '#7b2f35');
  const edge = winner(game);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, color(edge, '#f4b942'))}${header(context.season, context.week, `FEATURED ${String(featureIndex).padStart(2, '0')}`)}
    <defs><linearGradient id="clash" x1="0" y1="0" x2="1" y2="0"><stop stop-color="${awayColor}" stop-opacity=".92"/><stop offset=".47" stop-color="${awayColor}" stop-opacity=".48"/><stop offset=".53" stop-color="${homeColor}" stop-opacity=".48"/><stop offset="1" stop-color="${homeColor}" stop-opacity=".92"/></linearGradient></defs>
    <path d="M14 175H1080V820L540 1030 14 820Z" fill="url(#clash)" opacity=".76"/>
    <path d="M540 175L505 805 540 1018 575 805Z" fill="#f7f4ea" opacity=".08"/>
    <text class="condensed" x="66" y="210" fill="#f7f4ea" font-size="23">${esc(game.kickoff)}</text>
    <text class="condensed" x="1014" y="210" text-anchor="end" fill="#f7f4ea" font-size="23">${game.neutral ? 'NEUTRAL SITE' : `${esc(game.home.short)} HOME`}</text>
    ${logo(game.away, 90, 290, 300)}${logo(game.home, 690, 290, 300)}
    <text class="condensed" x="240" y="650" text-anchor="middle" fill="#d4e0e7" font-size="28">${rank(game.away)}</text>
    <text class="display" x="240" y="708" text-anchor="middle" fill="#fff" font-size="58">${esc(game.away.short)}</text>
    <text class="condensed" x="840" y="650" text-anchor="middle" fill="#d4e0e7" font-size="28">${rank(game.home)}</text>
    <text class="display" x="840" y="708" text-anchor="middle" fill="#fff" font-size="58">${esc(game.home.short)}</text>
    <text class="display" x="240" y="815" text-anchor="middle" fill="#fff" font-size="94">${pct(game.away.probability)}</text>
    <text class="display" x="840" y="815" text-anchor="middle" fill="#fff" font-size="94">${pct(game.home.probability)}</text>
    <rect x="444" y="485" width="192" height="98" rx="49" fill="#07111c" stroke="#fff" stroke-opacity=".2" stroke-width="2"/>
    <text class="display" x="540" y="552" text-anchor="middle" fill="#f4b942" font-size="56">VS</text>
    <g transform="translate(66 936)">
      <text class="condensed" x="0" y="0" fill="#8ea3b3" font-size="22">SATURDAY LAB MODEL EDGE</text>
      <text class="display" x="0" y="76" fill="#f7f4ea" font-size="70">${esc(edge.short)} · ${pct(edge.probability)}</text>
      ${probabilityBar(game, 0, 108, 948)}
      <text class="body" x="0" y="174" fill="#91a5b6" font-size="22">Interest ${game.metrics.interest.toFixed(1)} · Quality ${game.metrics.quality.toFixed(1)} · Closeness ${game.metrics.closeness.toFixed(1)}</text>
      <text class="body" x="0" y="215" fill="#f7f4ea" font-size="22">${esc([game.broadcast, game.venue].filter(Boolean).join(' · ') || 'Game details available at Saturday Lab')}</text>
    </g>
    ${footer(index, total)}
  </svg>`;
}

export function upsetSlide({ context, game, fontCss, index, total }) {
  const underdog = String(game.metrics.underdogTeamId) === String(game.home.id) ? game.home : game.away;
  const favorite = underdog === game.home ? game.away : game.home;
  const underdogSize = underdog.short.length > 13 ? 56 : underdog.short.length > 10 ? 64 : 74;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#ef6a54')}${header(context.season, context.week, 'UPSET WATCH')}
    <path d="M14 195H1080V900L14 1160Z" fill="${color(underdog, '#9b3e4d')}" opacity=".62"/>
    <path d="M14 280L1080 1020" stroke="#ef6a54" stroke-width="18" opacity=".8"/>
    <text class="display" x="66" y="244" fill="#f7f4ea" font-size="92">THE MODEL</text>
    <text class="display" x="66" y="326" fill="#efb36d" font-size="92">SEES A PATH.</text>
    ${logo(underdog, 100, 405, 360)}
    <text class="condensed" x="590" y="455" fill="#d4e0e7" font-size="28">${rank(underdog)} UNDERDOG</text>
    <text class="display" x="590" y="530" fill="#fff" font-size="${underdogSize}">${esc(underdog.short)}</text>
    <text class="display" x="590" y="660" fill="#fff" font-size="126">${pct(underdog.probability)}</text>
    <text class="condensed" x="594" y="704" fill="#f4b942" font-size="24">WIN PROBABILITY</text>
    <rect x="66" y="850" width="948" height="250" rx="28" fill="#08121d" stroke="#fff" stroke-opacity=".14"/>
    <text class="condensed" x="110" y="910" fill="#91a5b6" font-size="22">WHY IT MADE THE BOARD</text>
    <text class="display" x="110" y="977" fill="#f7f4ea" font-size="48">${esc(underdog.short)} vs ${esc(favorite.short)}</text>
    <text class="body" x="110" y="1028" fill="#b1c0ca" font-size="23">${game.metrics.rankGap}-spot ranking gap · ${game.metrics.closeness.toFixed(0)}/100 matchup closeness · ${game.neutral ? 'neutral field' : underdog === game.home ? 'home underdog' : 'road underdog'}</text>
    <text class="body" x="110" y="1070" fill="#b1c0ca" font-size="23">${esc(game.kickoff)}</text>
    ${footer(index, total)}
  </svg>`;
}

function compactRow(game, y) {
  const edge = winner(game);
  return `<g transform="translate(66 ${y})">
    <rect width="948" height="130" rx="18" fill="#101e2b" stroke="#91a5b6" stroke-opacity=".14"/>
    ${logo(game.away, 22, 20, 88)}${logo(game.home, 350, 20, 88)}
    <text class="condensed" x="122" y="50" fill="#91a5b6" font-size="19">${rank(game.away)}</text><text class="display" x="122" y="88" fill="#f7f4ea" font-size="32">${esc(game.away.short)}</text>
    <text class="condensed" x="450" y="50" fill="#91a5b6" font-size="19">${rank(game.home)}</text><text class="display" x="450" y="88" fill="#f7f4ea" font-size="32">${esc(game.home.short)}</text>
    <text class="display" x="908" y="62" text-anchor="end" fill="#f7f4ea" font-size="42">${pct(edge.probability)}</text>
    <text class="condensed" x="908" y="94" text-anchor="end" fill="${color(edge, '#f4b942')}" font-size="19">${esc(edge.short)}</text>
  </g>`;
}

export function otherGamesSlide({ context, games, fontCss, index, total }) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss)}${header(context.season, context.week, 'MORE PREDICTIONS')}
    <text class="display" x="66" y="210" fill="#f7f4ea" font-size="78">THE REST OF</text>
    <text class="display" x="66" y="280" fill="#f4b942" font-size="78">THE BOARD.</text>
    <text class="body" x="68" y="324" fill="#9eb0be" font-size="22">Highest-interest games outside the featured slate</text>
    ${games.slice(0, 6).map((game, i) => compactRow(game, 362 + i * 142)).join('')}
    ${footer(index, total)}
  </svg>`;
}

export function closingSlide({ context, fontCss, index, total, gameCount }) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#55d69e')}${header(context.season, context.week, 'FULL BOARD ONLINE')}
    <circle cx="540" cy="560" r="310" fill="#55d69e" opacity=".08"/><circle cx="540" cy="560" r="240" fill="none" stroke="#55d69e" stroke-opacity=".22" stroke-width="2"/><circle cx="540" cy="560" r="170" fill="none" stroke="#f4b942" stroke-opacity=".2" stroke-width="2"/>
    <text class="display" x="540" y="420" text-anchor="middle" fill="#f7f4ea" font-size="92">EVERY GAME.</text>
    <text class="display" x="540" y="510" text-anchor="middle" fill="#55d69e" font-size="92">ONE MODEL.</text>
    <text class="display" x="540" y="665" text-anchor="middle" fill="#f7f4ea" font-size="160">${gameCount}</text>
    <text class="condensed" x="540" y="715" text-anchor="middle" fill="#9fb1be" font-size="28">FBS PREDICTIONS THIS WEEK</text>
    <rect x="140" y="825" width="800" height="130" rx="65" fill="#f7f4ea"/>
    <text class="display" x="540" y="908" text-anchor="middle" fill="#07111c" font-size="52">SATURDAY-LAB FOOTBALL</text>
    <text class="body" x="540" y="1030" text-anchor="middle" fill="#a9bac5" font-size="25">Rankings · team pages · every matchup · full methodology</text>
    <text class="body" x="540" y="1072" text-anchor="middle" fill="#a9bac5" font-size="22">Independent project · probabilities are model estimates, not betting advice</text>
    ${footer(index, total)}
  </svg>`;
}


import { base, color, esc, footer, header, logo, pct } from './templates.mjs';

const W = 1080;
const H = 1350;
const rankOf = (team) => Number(team.currentRank ?? team.modelRank ?? team.rank ?? 999);

function deltaText(team) {
  if (!Number.isFinite(team.delta) || team.delta === 0) return '—';
  return `${team.delta > 0 ? '▲' : '▼'} ${Math.abs(team.delta)}`;
}

function deltaColor(team) {
  return team.delta > 0 ? '#55d69e' : team.delta < 0 ? '#ef6a54' : '#8da1b1';
}

function rankingRow(team, x, y, width, highlighted = false) {
  return `<g transform="translate(${x} ${y})">
    <rect width="${width}" height="66" rx="14" fill="${highlighted ? color(team, '#263d50') : '#101e2b'}" opacity="${highlighted ? '.78' : '.96'}" stroke="#fff" stroke-opacity=".1"/>
    <text class="display" x="22" y="45" fill="#f7f4ea" font-size="38">${rankOf(team)}</text>
    ${logo(team, 66, 11, 44)}
    <text class="display" x="122" y="43" fill="#f7f4ea" font-size="29">${esc(team.short)}</text>
    <text class="condensed" x="${width - 22}" y="42" text-anchor="end" fill="${deltaColor(team)}" font-size="21">${deltaText(team)}</text>
  </g>`;
}

export function top25Slide({ recap, fontCss, index, total }) {
  const left = recap.top25.slice(0, 13);
  const right = recap.top25.slice(13);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#55d69e')}${header(recap.season, recap.week, 'MONDAY RECAP')}
    <text class="display" x="66" y="202" fill="#f7f4ea" font-size="88">THE NEW TOP 25</text>
    <text class="body" x="69" y="245" fill="#9eb0be" font-size="22">Post–Week ${recap.week} rankings · movement from the pregame board</text>
    ${left.map((team, i) => rankingRow(team, 58, 278 + i * 72, 462, rankOf(team) <= 3)).join('')}
    ${right.map((team, i) => rankingRow(team, 560, 278 + i * 72, 462, false)).join('')}
    ${footer(index, total)}
  </svg>`;
}

function resultCard(game, y, number) {
  const winner = game.homeWon ? game.home : game.away;
  const picked = game.pickedHome ? game.home : game.away;
  return `<g transform="translate(62 ${y})">
    <rect width="956" height="204" rx="24" fill="#101e2b" stroke="#fff" stroke-opacity=".13"/>
    <rect width="10" height="204" rx="5" fill="${game.correct ? '#55d69e' : '#ef6a54'}"/>
    <text class="condensed" x="38" y="43" fill="#8298a9" font-size="20">${String(number).padStart(2, '0')} · FINAL</text>
    ${logo(game.away, 38, 62, 92)}${logo(game.home, 466, 62, 92)}
    <text class="display" x="146" y="98" fill="#f7f4ea" font-size="34">${esc(game.away.short)}</text>
    <text class="display" x="146" y="146" fill="${game.winner === 'away' ? '#fff' : '#8ea1af'}" font-size="48">${game.away.score}</text>
    <text class="display" x="574" y="98" fill="#f7f4ea" font-size="34">${esc(game.home.short)}</text>
    <text class="display" x="574" y="146" fill="${game.winner === 'home' ? '#fff' : '#8ea1af'}" font-size="48">${game.home.score}</text>
    <text class="display" x="914" y="98" text-anchor="end" fill="${game.correct ? '#55d69e' : '#ef6a54'}" font-size="38">${game.correct ? 'HIT' : 'MISS'}</text>
    <text class="condensed" x="914" y="133" text-anchor="end" fill="#f4b942" font-size="19">PICK: ${esc(picked.short)} ${pct(picked.probability)}</text>
    <text class="body" x="914" y="169" text-anchor="end" fill="#90a4b3" font-size="18">Winner: ${esc(winner.short)}</text>
  </g>`;
}

export function resultsSlide({ recap, fontCss, index, total }) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss)}${header(recap.season, recap.week, 'THE WEEKEND IN FOUR')}
    <text class="display" x="66" y="205" fill="#f7f4ea" font-size="84">FOUR GAMES.</text>
    <text class="display" x="66" y="280" fill="#f4b942" font-size="84">FOUR VERDICTS.</text>
    <text class="body" x="69" y="322" fill="#9eb0be" font-size="22">Final scores against Saturday Lab’s frozen pregame picks</text>
    ${recap.important.slice(0, 4).map((game, i) => resultCard(game, 355 + i * 220, i + 1)).join('')}
    ${footer(index, total)}
  </svg>`;
}

export function scorecardSlide({ recap, fontCss, index, total }) {
  const week = recap.weekScorecard;
  const season = recap.seasonScorecard;
  const circumference = 2 * Math.PI * 184;
  const dash = circumference * week.accuracy;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#55d69e')}${header(recap.season, recap.week, 'MODEL SCORECARD')}
    <text class="display" x="66" y="212" fill="#f7f4ea" font-size="88">NO CHERRY-PICKING.</text>
    <text class="body" x="69" y="258" fill="#9eb0be" font-size="23">Every completed FBS prediction from Week ${recap.week}</text>
    <circle cx="540" cy="570" r="184" fill="none" stroke="#203241" stroke-width="34"/>
    <circle cx="540" cy="570" r="184" fill="none" stroke="#55d69e" stroke-width="34" stroke-linecap="round" stroke-dasharray="${dash} ${circumference - dash}" transform="rotate(-90 540 570)"/>
    <text class="display" x="540" y="565" text-anchor="middle" fill="#f7f4ea" font-size="132">${(week.accuracy * 100).toFixed(1)}%</text>
    <text class="condensed" x="540" y="618" text-anchor="middle" fill="#9eb0be" font-size="27">${week.correct} OF ${week.games} CORRECT</text>
    <g transform="translate(66 855)">
      <rect width="296" height="230" rx="24" fill="#101e2b" stroke="#fff" stroke-opacity=".12"/>
      <text class="condensed" x="28" y="50" fill="#8da1b1" font-size="20">SEASON ACCURACY</text>
      <text class="display" x="28" y="129" fill="#f7f4ea" font-size="72">${(season.accuracy * 100).toFixed(1)}%</text>
      <text class="body" x="28" y="174" fill="#9eb0be" font-size="21">${season.correct} / ${season.games} picks</text>
      <rect x="326" width="296" height="230" rx="24" fill="#101e2b" stroke="#fff" stroke-opacity=".12"/>
      <text class="condensed" x="354" y="50" fill="#8da1b1" font-size="20">80%+ FAVORITES</text>
      <text class="display" x="354" y="129" fill="#f4b942" font-size="72">${week.confidentCorrect}/${week.confidentGames}</text>
      <text class="body" x="354" y="174" fill="#9eb0be" font-size="21">correct this week</text>
      <rect x="652" width="296" height="230" rx="24" fill="#101e2b" stroke="#fff" stroke-opacity=".12"/>
      <text class="condensed" x="680" y="50" fill="#8da1b1" font-size="20">LOG LOSS</text>
      <text class="display" x="680" y="129" fill="#f7f4ea" font-size="72">${week.logLoss.toFixed(3)}</text>
      <text class="body" x="680" y="174" fill="#9eb0be" font-size="21">lower is better</text>
    </g>
    <text class="body" x="540" y="1152" text-anchor="middle" fill="#8da1b1" font-size="20">Frozen probabilities evaluated against final results · ties and non-FBS games excluded</text>
    ${footer(index, total)}
  </svg>`;
}

export function recapUpsetSlide({ recap, fontCss, index, total }) {
  const game = recap.upset;
  const winner = game.homeWon ? game.home : game.away;
  const loser = game.homeWon ? game.away : game.home;
  const nameSize = winner.short.length > 12 ? 62 : 76;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#ef6a54')}${header(recap.season, recap.week, 'UPSET OF THE WEEK')}
    <path d="M14 188H1080V980L14 1150Z" fill="${color(winner, '#85384a')}" opacity=".68"/>
    <text class="display" x="66" y="242" fill="#f7f4ea" font-size="84">THE RESULT THE MODEL</text>
    <text class="display" x="66" y="320" fill="#f4b942" font-size="84">DIDN’T SEE COMING.</text>
    ${logo(winner, 88, 400, 350)}
    <text class="condensed" x="575" y="432" fill="#d3dfe6" font-size="25">PREGAME WIN CHANCE</text>
    <text class="display" x="575" y="555" fill="#fff" font-size="120">${pct(winner.probability)}</text>
    <text class="display" x="575" y="648" fill="#fff" font-size="${nameSize}">${esc(winner.short)}</text>
    <text class="condensed" x="575" y="700" fill="#f4b942" font-size="29">BEAT ${esc(loser.short).toUpperCase()}</text>
    <g transform="translate(66 820)">
      <rect width="948" height="230" rx="28" fill="#08121d" stroke="#fff" stroke-opacity=".14"/>
      <text class="condensed" x="45" y="57" fill="#8da1b1" font-size="21">FINAL SCORE</text>
      <text class="display" x="45" y="124" fill="#f7f4ea" font-size="48">${esc(winner.short)}</text>
      <text class="display" x="900" y="124" text-anchor="end" fill="#f7f4ea" font-size="48">${winner.score}</text>
      <text class="display" x="45" y="175" fill="#8da1b1" font-size="42">${esc(loser.short)}</text>
      <text class="display" x="900" y="175" text-anchor="end" fill="#8da1b1" font-size="42">${loser.score}</text>
      <text class="body" x="45" y="210" fill="#a9bac5" font-size="20">${Math.round((1 - winner.probability) * 100)}% model surprise · ${game.metrics.quality.toFixed(0)}/100 matchup quality</text>
    </g>
    ${footer(index, total)}
  </svg>`;
}

function movementCard(item, x, y, label, accent) {
  if (!item) return '';
  const nameSize = item.short.length > 11 ? 32 : item.short.length > 8 ? 37 : 43;
  return `<g transform="translate(${x} ${y})">
    <rect width="456" height="330" rx="28" fill="#101e2b" stroke="#fff" stroke-opacity=".13"/>
    <rect width="456" height="9" rx="4.5" fill="${accent}"/>
    <text class="condensed" x="30" y="55" fill="#8da1b1" font-size="21">${esc(label)}</text>
    ${logo(item, 30, 87, 112)}
    <text class="display" x="166" y="126" fill="#f7f4ea" font-size="${nameSize}">${esc(item.short)}</text>
    <text class="display" x="166" y="196" fill="#f7f4ea" font-size="50">#${item.previousRank} → #${item.currentRank}</text>
    <text class="condensed" x="30" y="278" fill="${accent}" font-size="28">${deltaText(item)}</text>
  </g>`;
}

export function movementSlide({ recap, fontCss, index, total }) {
  const move = recap.movement;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss)}${header(recap.season, recap.week, 'RANKINGS ON THE MOVE')}
    <text class="display" x="66" y="210" fill="#f7f4ea" font-size="86">WHO MOVED —</text>
    <text class="display" x="66" y="286" fill="#f4b942" font-size="86">AND HOW FAR.</text>
    ${movementCard(move.riser, 62, 345, 'BIGGEST RISER', '#55d69e')}
    ${movementCard(move.faller, 562, 345, 'BIGGEST SLIDE', '#ef6a54')}
    ${movementCard(move.newTop25 ?? move.all.filter((team) => team.currentRank <= 25).sort((a,b) => b.delta-a.delta)[0], 62, 707, move.newTop25 ? 'NEW TO THE TOP 25' : 'TOP 25 RISER', '#f4b942')}
    ${movementCard(move.outTop25 ?? move.all.filter((team) => team.previousRank <= 25).sort((a,b) => a.delta-b.delta)[0], 562, 707, move.outTop25 ? 'OUT OF THE TOP 25' : 'TOP 25 SLIDE', '#9e78d8')}
    ${footer(index, total)}
  </svg>`;
}

function numberTile(stat, x, y, i) {
  const title = stat.type === 'game' ? `${stat.game.away.short} ${stat.game.away.score} · ${stat.game.home.short} ${stat.game.home.score}` : stat.team?.short ?? 'Team';
  return `<g transform="translate(${x} ${y})">
    <rect width="456" height="245" rx="26" fill="#101e2b" stroke="#fff" stroke-opacity=".13"/>
    <text class="condensed" x="30" y="50" fill="#8da1b1" font-size="20">${String(i + 1).padStart(2, '0')} · ${esc(stat.label)}</text>
    <text class="display" x="30" y="142" fill="${i % 2 ? '#55d69e' : '#f4b942'}" font-size="82">${stat.value}</text>
    <text class="display" x="30" y="200" fill="#f7f4ea" font-size="31">${esc(title)}</text>
  </g>`;
}

export function numbersSlide({ recap, fontCss, index, total }) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#55d69e')}${header(recap.season, recap.week, 'WEEKEND BY THE NUMBERS')}
    <text class="display" x="66" y="210" fill="#f7f4ea" font-size="88">THE WEEK IN</text>
    <text class="display" x="66" y="288" fill="#55d69e" font-size="88">SIX NUMBERS.</text>
    ${recap.numbers.slice(0, 6).map((stat, i) => numberTile(stat, i % 2 ? 562 : 62, 348 + Math.floor(i / 2) * 270, i)).join('')}
    <text class="body" x="66" y="1188" fill="#8da1b1" font-size="20">Published team box scores · missing values stay blank.</text>
    ${footer(index, total)}
  </svg>`;
}

function nextGameCard(game, y, number) {
  const edge = game.home.probability >= .5 ? game.home : game.away;
  const awaySize = game.away.short.length > 11 ? 28 : 33;
  const homeSize = game.home.short.length > 11 ? 28 : 33;
  return `<g transform="translate(62 ${y})">
    <rect width="956" height="178" rx="24" fill="#101e2b" stroke="#fff" stroke-opacity=".13"/>
    <text class="condensed" x="32" y="42" fill="#8298a9" font-size="19">${String(number).padStart(2, '0')} · ${esc(game.kickoff)}</text>
    ${logo(game.away, 34, 62, 78)}${logo(game.home, 416, 62, 78)}
    <text class="display" x="126" y="104" fill="#f7f4ea" font-size="${awaySize}">#${game.away.modelRank} ${esc(game.away.short)}</text>
    <text class="display" x="508" y="104" fill="#f7f4ea" font-size="${homeSize}">#${game.home.modelRank} ${esc(game.home.short)}</text>
    <text class="display" x="914" y="92" text-anchor="end" fill="#f4b942" font-size="45">${pct(edge.probability)}</text>
    <text class="condensed" x="914" y="126" text-anchor="end" fill="#9eb0be" font-size="18">${esc(edge.short)} EDGE</text>
  </g>`;
}

export function nextWeekSlide({ recap, fontCss, index, total }) {
  const games = recap.nextWeek?.games ?? [];
  const next = recap.week + 1;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#f4b942')}${header(recap.season, next, 'NEXT WEEK PREVIEW')}
    <text class="display" x="66" y="208" fill="#f7f4ea" font-size="78">NEXT SATURDAY</text>
    <text class="display" x="66" y="282" fill="#f4b942" font-size="78">STARTS HERE.</text>
    <text class="body" x="69" y="326" fill="#9eb0be" font-size="22">First look from the new Week ${next} rankings</text>
    ${games.slice(0, 4).map((game, i) => nextGameCard(game, 366 + i * 194, i + 1)).join('')}
    <rect x="160" y="1167" width="760" height="82" rx="41" fill="#f7f4ea"/>
    <text class="display" x="540" y="1221" text-anchor="middle" fill="#07111c" font-size="30">FULL BOARD · SATURDAY-LAB FOOTBALL</text>
    ${footer(index, total)}
  </svg>`;
}


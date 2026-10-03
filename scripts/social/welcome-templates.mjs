import { base, color, esc, footer, logo, pct } from './templates.mjs';

const W = 1080;
const H = 1350;

export function welcomeSlide({ context, fontCss, index, total }) {
  const [first, second, third] = context.topTeams;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss, '#55d69e')}
    <path d="M14 0H1080V555L14 900Z" fill="#15334a" opacity=".5"/>
    <circle cx="875" cy="330" r="250" fill="none" stroke="#55d69e" stroke-opacity=".12" stroke-width="3"/>
    <circle cx="875" cy="330" r="180" fill="none" stroke="#f4b942" stroke-opacity=".13" stroke-width="3"/>
    <text class="condensed" x="66" y="88" fill="#9eb0be" font-size="25">COLLEGE FOOTBALL · THROUGH THE NUMBERS</text>
    <rect x="66" y="112" width="180" height="6" rx="3" fill="#f4b942"/>
    <text class="display" x="66" y="310" fill="#f7f4ea" font-size="150">WELCOME</text>
    <text class="display" x="66" y="445" fill="#f7f4ea" font-size="150">TO THE</text>
    <text class="display" x="66" y="580" fill="#55d69e" font-size="170">LAB.</text>
    <text class="body" x="70" y="655" fill="#b1c0ca" font-size="29">Independent rankings and predictions</text>
    <text class="body" x="70" y="698" fill="#b1c0ca" font-size="29">for every FBS team.</text>
    <g transform="translate(66 808)">
      <rect width="948" height="292" rx="34" fill="#0b1722" stroke="#fff" stroke-opacity=".14"/>
      <text class="condensed" x="38" y="56" fill="#8095a6" font-size="21">THE CURRENT TOP OF THE BOARD</text>
      ${logo(first, 72, 92, 126)}${logo(second, 411, 92, 126)}${logo(third, 750, 92, 126)}
      <text class="display" x="135" y="256" text-anchor="middle" fill="#f7f4ea" font-size="30">#1 ${esc(first.short)}</text>
      <text class="display" x="474" y="256" text-anchor="middle" fill="#f7f4ea" font-size="30">#2 ${esc(second.short)}</text>
      <text class="display" x="813" y="256" text-anchor="middle" fill="#f7f4ea" font-size="30">#3 ${esc(third.short)}</text>
    </g>
    <text class="display" x="66" y="1207" fill="#f7f4ea" font-size="47">SATURDAY LAB</text>
    <text class="condensed" x="1014" y="1204" text-anchor="end" fill="#f4b942" font-size="24">RANKINGS · PREDICTIONS · TEAM DATA</text>
    ${footer(index, total)}
  </svg>`;
}

function rankingLine(team, y) {
  return `<g transform="translate(0 ${y})">
    <text class="display" x="0" y="34" fill="#f7f4ea" font-size="34">${team.modelRank}</text>
    ${logo(team, 48, 0, 42)}
    <text class="display" x="104" y="33" fill="#f7f4ea" font-size="29">${esc(team.short)}</text>
    <text class="condensed" x="300" y="31" text-anchor="end" fill="${team.modelChange > 0 ? '#55d69e' : team.modelChange < 0 ? '#ef6a54' : '#8298a9'}" font-size="20">${team.modelChange > 0 ? '▲' : team.modelChange < 0 ? '▼' : '—'} ${Math.abs(team.modelChange ?? 0) || ''}</text>
  </g>`;
}

export function followSlide({ context, fontCss, index, total }) {
  const game = context.game;
  const edge = game.home.probability >= .5 ? game.home : game.away;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
    ${base(fontCss)}
    <text class="display" x="66" y="95" fill="#f7f4ea" font-size="42">SATURDAY LAB</text>
    <rect x="66" y="114" width="166" height="6" rx="3" fill="#f4b942"/>
    <text class="condensed" x="1014" y="92" text-anchor="end" fill="#93a8b8" font-size="23">WELCOME · ${context.season}</text>
    <text class="display" x="66" y="235" fill="#f7f4ea" font-size="74">FOLLOW THE SEASON</text>
    <text class="display" x="66" y="305" fill="#f4b942" font-size="74">THROUGH THE NUMBERS.</text>
    <g transform="translate(62 372)">
      <rect width="594" height="360" rx="30" fill="#101e2b" stroke="#fff" stroke-opacity=".14"/>
      <rect width="10" height="360" rx="5" fill="${color(edge, '#f4b942')}"/>
      <text class="condensed" x="40" y="56" fill="#8da1b1" font-size="22">WEEKLY GAME PREDICTIONS</text>
      <text class="body" x="40" y="91" fill="#b0c0cb" font-size="19">One-decimal win chances, frozen before kickoff</text>
      ${logo(game.away, 54, 122, 122)}${logo(game.home, 328, 122, 122)}
      <text class="display" x="115" y="284" text-anchor="middle" fill="#f7f4ea" font-size="34">${esc(game.away.short)}</text>
      <text class="display" x="389" y="284" text-anchor="middle" fill="#f7f4ea" font-size="34">${esc(game.home.short)}</text>
      <text class="display" x="115" y="333" text-anchor="middle" fill="#f7f4ea" font-size="43">${pct(game.away.probability)}</text>
      <text class="display" x="389" y="333" text-anchor="middle" fill="#f7f4ea" font-size="43">${pct(game.home.probability)}</text>
      <text class="display" x="252" y="229" text-anchor="middle" fill="#f4b942" font-size="34">VS</text>
    </g>
    <g transform="translate(684 372)">
      <rect width="334" height="360" rx="30" fill="#101e2b" stroke="#fff" stroke-opacity=".14"/>
      <text class="condensed" x="30" y="56" fill="#8da1b1" font-size="22">MONDAY TOP 25</text>
      <text class="body" x="30" y="91" fill="#b0c0cb" font-size="19">A new board every week</text>
      ${context.topTeams.slice(0, 3).map((team, i) => rankingLine(team, 122 + i * 72)).join('')}
    </g>
    <g transform="translate(62 770)">
      <rect width="956" height="312" rx="30" fill="#101e2b" stroke="#fff" stroke-opacity=".14"/>
      <text class="condensed" x="38" y="56" fill="#8da1b1" font-size="22">MATCHUPS · TEAMS · TRENDS</text>
      <text class="body" x="38" y="96" fill="#b0c0cb" font-size="21">Schedules, results, ranking movement and offense × defense data.</text>
      <path d="M52 242 C150 210 205 270 300 194 S480 162 570 204 S740 130 900 155" fill="none" stroke="#55d69e" stroke-width="8" stroke-linecap="round"/>
      <path d="M52 265H904M52 205H904M52 145H904" stroke="#8da1b1" stroke-opacity=".12" stroke-width="2"/>
      <circle cx="300" cy="194" r="12" fill="#f4b942"/><circle cx="570" cy="204" r="12" fill="#f4b942"/><circle cx="900" cy="155" r="12" fill="#f4b942"/>
    </g>
    <text class="display" x="66" y="1177" fill="#f7f4ea" font-size="55">WEEK ${context.week} PICKS THIS WEEKEND.</text>
    <text class="body" x="68" y="1222" fill="#9eb0be" font-size="23">heimweh17.github.io/saturday-lab</text>
    ${footer(index, total)}
  </svg>`;
}


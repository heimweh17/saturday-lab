function clamp(value, min = 0, max = 1) {
  return Math.max(min, Math.min(max, value));
}

function rankQuality(rank) {
  return Math.exp(-(Math.max(1, rank) - 1) / 32);
}

export function scoreGame(game) {
  const homeRank = Number(game.home.modelRank ?? game.home.rank ?? 140);
  const awayRank = Number(game.away.modelRank ?? game.away.rank ?? 140);
  const bestRank = Math.min(homeRank, awayRank);
  const worstRank = Math.max(homeRank, awayRank);
  const quality = 0.58 * Math.max(rankQuality(homeRank), rankQuality(awayRank))
    + 0.42 * Math.min(rankQuality(homeRank), rankQuality(awayRank));
  const closeness = 1 - Math.abs(game.home.probability - 0.5) * 2;
  const rankedVsRanked = homeRank <= 25 && awayRank <= 25 ? 1 : 0;
  const topTenClash = homeRank <= 10 && awayRank <= 10 ? 1 : 0;
  const topFiveClash = homeRank <= 5 && awayRank <= 5 ? 1 : 0;
  const nationalBonus = 0.11 * rankedVsRanked + 0.08 * topTenClash + 0.08 * topFiveClash;
  const interest = clamp(0.53 * quality + 0.34 * closeness + nationalBonus);

  const worseIsHome = homeRank > awayRank;
  const underdogProbability = worseIsHome ? game.home.probability : game.away.probability;
  const favoriteRank = bestRank;
  const underdogRank = worstRank;
  const rankGap = underdogRank - favoriteRank;
  const upsetScore = rankGap >= 6 && underdogProbability >= 0.32
    ? clamp(0.35 * underdogProbability + 0.40 * quality + 0.15 * closeness + 0.10 * clamp(rankGap / 45))
    : 0;

  return {
    ...game,
    metrics: {
      interest: Number((interest * 100).toFixed(1)),
      quality: Number((quality * 100).toFixed(1)),
      closeness: Number((closeness * 100).toFixed(1)),
      upset: Number((upsetScore * 100).toFixed(1)),
      rankedVsRanked: Boolean(rankedVsRanked),
      topTenClash: Boolean(topTenClash),
      underdogTeamId: worseIsHome ? game.home.id : game.away.id,
      underdogProbability,
      rankGap,
    },
  };
}

function parseIds(value) {
  if (!value) return [];
  return String(value).split(',').map((id) => id.trim()).filter(Boolean);
}

export function selectGames(games, options = {}) {
  const scored = games.map(scoreGame);
  const byId = new Map(scored.map((game) => [game.id, game]));
  const featuredCount = Number(options.featuredCount ?? 4);
  const overrides = parseIds(options.featured);
  const featured = [];
  for (const id of overrides) {
    const game = byId.get(id);
    if (!game) throw new Error(`Featured override game ${id} is not in the selected week.`);
    if (!featured.some((item) => item.id === id)) featured.push(game);
  }
  const ranked = [...scored].sort((a, b) => b.metrics.interest - a.metrics.interest || a.date.localeCompare(b.date) || a.id.localeCompare(b.id));
  for (const game of ranked) {
    if (featured.length >= featuredCount) break;
    if (!featured.some((item) => item.id === game.id)) featured.push(game);
  }

  const featuredIds = new Set(featured.map((game) => game.id));
  let upset = null;
  if (options.upset) {
    upset = byId.get(String(options.upset));
    if (!upset) throw new Error(`Upset override game ${options.upset} is not in the selected week.`);
  } else {
    upset = scored
      .filter((game) => !featuredIds.has(game.id) && game.metrics.upset >= 40)
      .sort((a, b) => b.metrics.upset - a.metrics.upset || b.metrics.interest - a.metrics.interest)[0] ?? null;
  }

  const excluded = new Set([...featuredIds, upset?.id].filter(Boolean));
  const others = ranked.filter((game) => !excluded.has(game.id)).slice(0, Number(options.otherCount ?? 6));
  return { featured, upset, others, ranked };
}


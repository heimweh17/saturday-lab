import type {MetadataRoute} from 'next';
import {allGames,allTeamAliases,allTeamSeasons,latestSeason,rankingSnapshotParams,seasons} from '@/lib/server-catalog';
import {gamePath,teamPath,teamSeasonPath} from '@/lib/routes';

const origin='https://heimweh17.github.io/saturday-lab';
export const dynamic='force-static';

export default function sitemap():MetadataRoute.Sitemap{
  const fixed=['/','/rankings/','/teams/','/games/','/matchup/','/rank-trends/','/model/','/introduction/','/methodology/','/legal/'];
  return [
    ...fixed.map(path=>({url:`${origin}${path}`,changeFrequency:'weekly' as const,priority:path==='/'?1:0.7})),
    ...allTeamAliases().map(team=>({url:`${origin}${teamPath(team)}`,changeFrequency:'weekly' as const,priority:0.8})),
    ...allTeamSeasons().map(team=>({url:`${origin}${teamSeasonPath(team,team.season)}`,changeFrequency:team.season===latestSeason?'weekly' as const:'never' as const,priority:0.7})),
    ...seasons.map(season=>({url:`${origin}/rankings/${season}/`,changeFrequency:season===latestSeason?'weekly' as const:'never' as const,priority:0.75})),
    ...rankingSnapshotParams().map(({season,snapshot})=>({url:`${origin}/rankings/${season}/${snapshot}/`,changeFrequency:'never' as const,priority:0.65})),
    ...allGames().map(game=>({url:`${origin}${gamePath(game)}`,changeFrequency:game.completed?'never' as const:'daily' as const,priority:game.completed?0.45:0.75})),
  ];
}

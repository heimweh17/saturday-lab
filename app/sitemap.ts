import type {MetadataRoute} from 'next';
import {allGames,allTeamAliases} from '@/lib/server-catalog';
import {gamePath,teamPath} from '@/lib/routes';

const origin='https://heimweh17.github.io/saturday-lab';
export const dynamic='force-static';

export default function sitemap():MetadataRoute.Sitemap{
  const fixed=['/','/teams/','/matchup/','/rank-trends/','/model/','/methodology/','/legal/'];
  return [
    ...fixed.map(path=>({url:`${origin}${path}`,changeFrequency:'weekly' as const,priority:path==='/'?1:0.7})),
    ...allTeamAliases().map(team=>({url:`${origin}${teamPath(team)}`,changeFrequency:'weekly' as const,priority:0.8})),
    ...allGames().map(game=>({url:`${origin}${gamePath(game)}`,changeFrequency:game.completed?'never' as const:'daily' as const,priority:game.completed?0.45:0.75})),
  ];
}

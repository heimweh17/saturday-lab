import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {RankingsClient} from '@/app/rankings-client';
import {hasSnapshot,latestSeason,rankingSeasonParams,seasons} from '@/lib/server-catalog';

export const dynamicParams=false;
export const generateStaticParams=rankingSeasonParams;
export async function generateMetadata({params}:{params:Promise<{season:string}>}):Promise<Metadata>{const season=Number((await params).season);return seasons.includes(season)?{title:`${season} college football rankings | Saturday Lab`,description:`The final or latest published Saturday Lab FBS ranking snapshot for the ${season} season.`}:{title:'Rankings not found | Saturday Lab'}}
export default async function RankingSeasonPage({params}:{params:Promise<{season:string}>}){
  const season=Number((await params).season);if(!hasSnapshot(season,99))notFound();
  return <RankingsClient initialSeason={season} initialWeek={99} latestSeason={latestSeason} routePath={`/rankings/${season}/`}/>;
}

import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {RankingsClient} from '@/app/rankings-client';
import {hasSnapshot,latestSeason,rankingSnapshotParams,weekFromSnapshotSlug} from '@/lib/server-catalog';

export const dynamicParams=false;
export const generateStaticParams=rankingSnapshotParams;
export async function generateMetadata({params}:{params:Promise<{season:string;snapshot:string}>}):Promise<Metadata>{const p=await params,season=Number(p.season),week=weekFromSnapshotSlug(p.snapshot);return week!==null&&hasSnapshot(season,week)?{title:`${season} ${p.snapshot.replace('-',' ')} rankings | Saturday Lab`,description:`Saturday Lab FBS rankings at the ${p.snapshot.replace('-',' ')} snapshot of the ${season} season.`}:{title:'Ranking snapshot not found | Saturday Lab'}}
export default async function RankingSnapshotPage({params}:{params:Promise<{season:string;snapshot:string}>}){
  const p=await params,season=Number(p.season),week=weekFromSnapshotSlug(p.snapshot);if(week===null||!hasSnapshot(season,week))notFound();
  return <RankingsClient initialSeason={season} initialWeek={week} latestSeason={latestSeason} routePath={`/rankings/${season}/${p.snapshot}/`}/>;
}

import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {TeamPageClient} from '../team-page-client';
import {latestSeason,routesForTeam,seasons,teamBySlugSeason,teamSeasonParams} from '@/lib/server-catalog';

export const dynamicParams=false;
export const generateStaticParams=teamSeasonParams;
export async function generateMetadata({params}:{params:Promise<{team:string;season:string}>}):Promise<Metadata>{const p=await params,season=Number(p.season),team=seasons.includes(season)?teamBySlugSeason(p.team,season):null;return team?{title:`${team.name} ${season} | Saturday Lab`,description:`Permanent ${season} rankings, results and team data for ${team.name}.`}:{title:'Team season not found | Saturday Lab'}}
export default async function TeamSeasonPage({params}:{params:Promise<{team:string;season:string}>}){
  const p=await params,season=Number(p.season),team=seasons.includes(season)?teamBySlugSeason(p.team,season):null;if(!team)notFound();
  return <TeamPageClient teamId={team.id} initialSeason={season} latestSeason={latestSeason} seasonRoutes={routesForTeam(team.id)} routePath={`/teams/${p.team}/${season}/`}/>;
}

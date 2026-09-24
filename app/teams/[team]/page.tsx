import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {teamBySlug,teamParams} from '@/lib/server-catalog';
import {TeamPageClient} from './team-page-client';

export const dynamicParams=false;
export const generateStaticParams=teamParams;
export async function generateMetadata({params}:{params:Promise<{team:string}>}):Promise<Metadata>{const {team:slug}=await params;const team=teamBySlug(slug);return team?{title:`${team.name} | Saturday Lab`,description:`Rankings, schedule forecasts, results and detailed data for ${team.name}.`}:{title:'Team not found | Saturday Lab'}}
export default async function TeamPage({params}:{params:Promise<{team:string}>}){const {team:slug}=await params;const team=teamBySlug(slug);if(!team)notFound();return <TeamPageClient teamId={team.id} initialSeason={team.season}/>}

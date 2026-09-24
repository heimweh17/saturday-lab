import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {gameBySlug,gameParams} from '@/lib/server-catalog';
import {GamePageClient} from './game-page-client';

export const dynamicParams=false;
export const generateStaticParams=()=>gameParams();
export async function generateMetadata({params}:{params:Promise<{season:string;game:string}>}):Promise<Metadata>{const p=await params,game=gameBySlug(Number(p.season),p.game);return game?{title:`${game.awayName} vs. ${game.homeName} | Saturday Lab`,description:`${game.season} game page with score, schedule details, model forecast and team comparison.`}:{title:'Game not found | Saturday Lab'}}
export default async function GamePage({params}:{params:Promise<{season:string;game:string}>}){const p=await params,game=gameBySlug(Number(p.season),p.game);if(!game)notFound();return <GamePageClient game={game}/>}

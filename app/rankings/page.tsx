import type {Metadata} from 'next';
import {RankingsClient} from '@/app/rankings-client';
import {latestSeason} from '@/lib/server-catalog';

export const metadata:Metadata={title:'Current college football rankings | Saturday Lab',description:'The latest Saturday Lab opponent-adjusted FBS power rankings.'};
export default function RankingsAliasPage(){
  return <RankingsClient initialSeason={latestSeason} initialWeek={99} latestSeason={latestSeason} routePath="/rankings/"/>;
}

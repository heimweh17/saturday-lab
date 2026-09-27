import {RankingsClient} from './rankings-client';
import {latestSeason} from '@/lib/server-catalog';

export default function HomePage(){
  return <RankingsClient initialSeason={latestSeason} initialWeek={99} latestSeason={latestSeason} routePath="/"/>;
}

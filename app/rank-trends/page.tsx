import type {Metadata} from 'next';
import {RankTrendsPageClient} from './rank-trends-page-client';
export const metadata:Metadata={title:'Rank Trends | Saturday Lab',description:'Compare weekly national model ranking paths for up to 12 college football teams.'};
export default function RankTrendsPage(){return <RankTrendsPageClient/>}

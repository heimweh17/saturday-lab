import type {Metadata} from 'next';
import {Suspense} from 'react';
import {MatchupPageClient} from './matchup-page-client';
export const metadata:Metadata={title:'Matchup Lab | Saturday Lab',description:'Build a hypothetical college football matchup with venue-adjusted v6 win probabilities.'};
export default function MatchupPage(){return <Suspense fallback={<main><div className="loading">Loading matchup lab…</div></main>}><MatchupPageClient/></Suspense>}

import type {Metadata} from 'next';
import {GamesPageClient} from './games-page-client';

export const metadata:Metadata={title:'Scores & schedule | Saturday Lab',description:'Browse recent college football scores, upcoming games and Saturday Lab win probabilities.'};
export default function GamesPage(){return <GamesPageClient/>}

import type {Metadata} from 'next';
import {TeamDirectory} from './team-directory';

export const metadata:Metadata={title:'Find a Team | Saturday Lab',description:'Search every FBS team and open its rankings, schedule, results and data report.'};
export default function TeamsPage(){return <TeamDirectory/>}

import type {Metadata} from 'next';
import {MethodologyPageClient} from './methodology-page-client';
export const metadata:Metadata={title:'Methodology | Saturday Lab',description:'Equations, metric definitions, data boundaries and reproducibility notes.'};
export default function MethodologyPage(){return <MethodologyPageClient/>}

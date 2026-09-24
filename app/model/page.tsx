import type {Metadata} from 'next';
import {ModelPageClient} from './model-page-client';
export const metadata:Metadata={title:'Model Validation | Saturday Lab',description:'Version 6 validation, calibration, comparisons and research audit.'};
export default function ModelPage(){return <ModelPageClient/>}

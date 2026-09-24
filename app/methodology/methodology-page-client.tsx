"use client";
import {useEffect,useState} from 'react';
import type {Manifest,Report} from '@/app/types';
import {Methodology} from '@/app/methodology';
import {asset} from '@/lib/paths';
export function MethodologyPageClient(){const [manifest,setManifest]=useState<Manifest|null>(null),[report,setReport]=useState<Report|null>(null);useEffect(()=>{Promise.all([fetch(asset('/data/manifest.json')).then(r=>r.json()),fetch(asset('/data/report.json')).then(r=>r.json())]).then(([m,r])=>{setManifest(m as Manifest);setReport(r as Report)})},[]);return <main>{manifest&&report?<Methodology manifest={manifest} report={report}/>:<div className="loading">Loading methodology…</div>}</main>}

"use client";
import {useEffect,useState} from 'react';
import type {Season} from '@/app/types';
import {ModelAudit} from '@/app/model-audit';
import {asset} from '@/lib/paths';
export function ModelPageClient(){const [data,setData]=useState<Season|null>(null);useEffect(()=>{fetch(asset('/data/2026.json')).then(r=>r.json()).then(d=>setData(d as Season))},[]);return <main>{data?<><div className="route-intro"><span className="scoreline">MODEL v6</span><h1>Validation &amp; research</h1><p>The evidence behind the production ranking and forecast model.</p></div><ModelAudit data={data}/></>:<div className="loading">Loading model evidence…</div>}</main>}

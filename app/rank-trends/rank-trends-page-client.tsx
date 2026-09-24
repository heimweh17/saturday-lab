"use client";
import {useEffect,useState} from 'react';
import {useRouter} from 'next/navigation';
import type {Season} from '@/app/types';
import {RankTrends} from '@/app/rank-trends';
import {asset} from '@/lib/paths';
import {teamPath} from '@/lib/routes';
export function RankTrendsPageClient(){const router=useRouter(),[data,setData]=useState<Season|null>(null);useEffect(()=>{fetch(asset('/data/2026.json')).then(r=>r.json()).then(d=>setData(d as Season))},[]);return <main>{data?<RankTrends data={data} onOpenTeam={id=>{const team=data.snapshots['99'].teams.find(t=>t.id===id);if(team)router.push(teamPath(team))}}/>:<div className="loading">Loading ranking history…</div>}</main>}

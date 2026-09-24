"use client";
import type {Team} from './types';
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from '@/components/ui/select';
export const signed=(n:number|null,d=1)=>n==null?'—':`${n>0?'+':''}${n.toFixed(d)}`;
export const fixed=(n:number|null|undefined,d=1)=>n==null?'—':n.toFixed(d);
export const pct=(n:number|null|undefined)=>n==null?'—':`${(n*100).toFixed(1)}%`;
export const weekName=(w:number)=>w===99?'Latest available':w>=30?`Before postseason ${w-30}`:`Before week ${w}`;
export const dateLabel=(v:string|null)=>v?new Date(v).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Preseason';
export function Picker({label,value,onChange,options}:{label:string;value:string;onChange:(v:string)=>void;options:{value:string;label:string}[]}){return <label className="picker"><span>{label}</span><Select value={value} onValueChange={onChange}><SelectTrigger aria-label={label}><SelectValue/></SelectTrigger><SelectContent>{options.map(o=><SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent></Select></label>}
export function Logo({team,size=32}:{team:Team;size?:number}){return <span className="team-logo" style={{width:size,height:size}}>{team.logo?<img src={team.logo} alt="" width={size} height={size} loading="lazy" onError={e=>{e.currentTarget.style.display='none'}}/>:team.abbr}</span>}
export function download(name:string,rows:object[]){if(!rows.length)return;const keys=Object.keys(rows[0]);const q=(v:unknown)=>`"${String(v??'').replaceAll('"','""')}"`;const blob=new Blob([keys.map(q).join(',')+'\n'+rows.map(r=>keys.map(k=>q((r as Record<string,unknown>)[k])).join(',')).join('\n')],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}

"use client";
import {useState} from 'react';
import {Check,ChevronsUpDown} from 'lucide-react';
import type {Team} from './types';
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from '@/components/ui/select';
import {Popover,PopoverContent,PopoverTrigger} from '@/components/ui/popover';
import {Command,CommandEmpty,CommandGroup,CommandInput,CommandItem,CommandList} from '@/components/ui/command';
export const signed=(n:number|null,d=1)=>{if(n==null)return '—';const value=Math.abs(n)<.5*10**-d?0:n;return `${value>0?'+':''}${value.toFixed(d)}`};
export const fixed=(n:number|null|undefined,d=1)=>n==null?'—':n.toFixed(d);
export const pct=(n:number|null|undefined)=>n==null?'—':`${(n*100).toFixed(1)}%`;
export const weekName=(w:number)=>w===99?'Latest available':w>=30?`Before postseason ${w-30}`:`Before week ${w}`;
export const dateLabel=(v:string|null)=>v?new Date(v).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Preseason';
export function Picker({label,value,onChange,options}:{label:string;value:string;onChange:(v:string)=>void;options:{value:string;label:string}[]}){return <label className="picker"><span>{label}</span><Select value={value} onValueChange={onChange}><SelectTrigger aria-label={label}><SelectValue/></SelectTrigger><SelectContent>{options.map(o=><SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent></Select></label>}
export function SearchPicker({label,value,onChange,options,placeholder='Search teams…'}:{label:string;value:string;onChange:(v:string)=>void;options:{value:string;label:string}[];placeholder?:string}){
 const selected=options.find(option=>option.value===value)?.label??'';
 const [open,setOpen]=useState(false);
 const listId=`${label.toLowerCase().replace(/[^a-z0-9]+/g,'-')}-team-list`;
 return <div className="picker search-picker"><span>{label}</span><Popover open={open} onOpenChange={setOpen}><PopoverTrigger asChild><button type="button" className="search-picker-trigger" role="combobox" aria-controls={listId} aria-expanded={open} aria-label={`${label}: ${selected}`}><span>{selected||placeholder}</span><ChevronsUpDown size={16}/></button></PopoverTrigger><PopoverContent className="search-picker-panel" align="start"><Command><CommandInput placeholder={placeholder} autoFocus/><CommandList id={listId}><CommandEmpty>No teams found.</CommandEmpty><CommandGroup>{options.map(option=><CommandItem key={option.value} value={option.label} onSelect={()=>{onChange(option.value);setOpen(false)}}><Check className={option.value===value?'search-picker-check':'search-picker-check hidden-check'}/><span>{option.label}</span></CommandItem>)}</CommandGroup></CommandList></Command></PopoverContent></Popover></div>
}
export function Logo({team,size=32}:{team:Team;size?:number}){return <span className="team-logo" style={{width:size,height:size}}>{team.logo?<img src={team.logo} alt="" width={size} height={size} loading="lazy" onError={e=>{e.currentTarget.style.display='none'}}/>:team.abbr}</span>}
export function download(name:string,rows:object[]){if(!rows.length)return;const keys=Object.keys(rows[0]);const q=(v:unknown)=>`"${String(v??'').replaceAll('"','""')}"`;const blob=new Blob([keys.map(q).join(',')+'\n'+rows.map(r=>keys.map(k=>q((r as Record<string,unknown>)[k])).join(',')).join('\n')],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}

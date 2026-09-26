import type {GameRouteLike} from './routes';
import {gamePath} from './routes';

export type GameReturn={path:string;label:string};

const safeReturnPath=(value:string|null)=>{
  if(!value||!value.startsWith('/')||value.startsWith('//')||value.includes('\\'))return null;
  try{
    const parsed=new URL(value,'https://saturday-lab.local');
    return parsed.origin==='https://saturday-lab.local'?`${parsed.pathname}${parsed.search}${parsed.hash}`:null;
  }catch{return null}
};

export const gamePathFrom=(game:GameRouteLike,source:GameReturn)=>{
  const path=gamePath(game),from=safeReturnPath(source.path);
  if(!from)return path;
  const query=new URLSearchParams({from,fromLabel:source.label.slice(0,80)});
  return `${path}?${query.toString()}`;
};

const markerKey=(destination:string)=>`saturday-lab:game-origin:${destination.split('?')[0]}`;

const siteRelativePath=(pathname:string)=>{
  const base=process.env.NEXT_PUBLIC_BASE_PATH??'';
  if(base&&pathname.startsWith(`${base}/`))return pathname.slice(base.length);
  return pathname;
};

export const rememberGameOrigin=(destination:string,source:GameReturn)=>{
  if(typeof window==='undefined')return;
  const path=safeReturnPath(source.path);
  if(!path)return;
  try{sessionStorage.setItem(markerKey(destination),JSON.stringify({path,label:source.label.slice(0,80),at:Date.now()}))}catch{}
};

export const readGameReturn=():GameReturn&{canHistoryBack:boolean}=>{
  const fallback={path:'/games/',label:'Scores & schedule',canHistoryBack:false};
  if(typeof window==='undefined')return fallback;
  const query=new URLSearchParams(window.location.search),path=safeReturnPath(query.get('from'));
  if(!path)return fallback;
  const label=(query.get('fromLabel')??'Previous page').trim().slice(0,80)||'Previous page';
  let canHistoryBack=false;
  try{
    const marker=JSON.parse(sessionStorage.getItem(markerKey(siteRelativePath(window.location.pathname)))??'null') as {path?:string;at?:number}|null;
    canHistoryBack=Boolean(marker?.path===path&&marker.at&&Date.now()-marker.at<86400000&&window.history.length>1);
  }catch{}
  return {path,label,canHistoryBack};
};

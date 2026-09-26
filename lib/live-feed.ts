import {asset} from './paths';

export type LiveBoxValues=Record<string,number|null>;
export type LiveGame={id:string;season:number;week:number;date:string;home:string;away:string;homeName:string;awayName:string;neutral:boolean;fbs:boolean;status:string;state:'pre'|'in'|'post';statusDetail:string;completed:boolean;timeValid:boolean;hs:number|null;as:number|null;broadcast:string|null;source:string;pregame?:{homeWinProbability:number;modelVersion:string;snapshotThrough:string|null;calculatedAt:string;frozenAt?:string}|null;detail?:{periods:{away:number[];home:number[]}|null;box:Record<string,LiveBoxValues>|null;venue:{name:string|null;city:string|null;state:string|null}|null;attendance:number|null;broadcast?:string}};
export type LiveFeed={version:number;season:number;updatedAt:string;weeklySnapshotThrough:string|null;source:string;refreshPolicy:string;games:LiveGame[]};

const repositoryFeed=(season:number)=>`https://raw.githubusercontent.com/heimweh17/saturday-lab/main/public/data/live-${season}.json?minute=${Math.floor(Date.now()/300000)}`;

export async function fetchLiveFeed(season:number,signal?:AbortSignal):Promise<LiveFeed>{
 const remote=typeof window!=='undefined'&&window.location.hostname==='heimweh17.github.io';
 const urls=remote?[repositoryFeed(season),asset(`/data/live-${season}.json`)]:[asset(`/data/live-${season}.json`)];
 let lastError:unknown;
 for(const url of urls)try{const response=await fetch(url,{signal,cache:'no-store'});if(!response.ok)throw Error(`Live feed ${response.status}`);return await response.json() as LiveFeed}catch(error){lastError=error}
 throw lastError instanceof Error?lastError:Error('Live game data could not load.');
}

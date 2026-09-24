import 'server-only';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {gameSlug,teamSlug} from './routes';

export type CatalogTeam={id:string;name:string;short:string;abbr:string;conference:string;logo:string;color:string};
export type CatalogTeamAlias=CatalogTeam&{season:number};
export type CatalogGame={id:string;season:number;week:number;date:string;home:string;away:string;homeName:string;awayName:string;neutral:boolean;fbs:boolean;completed:boolean;hs:number|null;as:number|null;status:string;timeValid:boolean};

const years=[2018,2019,2020,2021,2022,2023,2024,2025,2026];
const cache=new Map<number,{games:CatalogGame[];teams:CatalogTeam[]}>();
const loadSeason=(season:number)=>{
  const cached=cache.get(season);if(cached)return cached;
  const raw=JSON.parse(readFileSync(join(process.cwd(),'public','data',`${season}.json`),'utf8')) as {games:Array<Omit<CatalogGame,'completed'|'status'|'timeValid'>>;snapshots:Record<string,{teams:CatalogTeam[]}>};
  const value={games:raw.games.map(g=>({...g,completed:true,status:'STATUS_FINAL',timeValid:true})),teams:raw.snapshots['99'].teams};cache.set(season,value);return value;
};
const loadFixtures=()=>JSON.parse(readFileSync(join(process.cwd(),'public','data','fixtures.json'),'utf8')) as {season:number;games:CatalogGame[]};

export const allTeams=()=>loadSeason(2026).teams.slice().sort((a,b)=>a.name.localeCompare(b.name));
export const allTeamAliases=()=>{
  const aliases=new Map<string,CatalogTeamAlias>();
  for(const season of years)for(const team of loadSeason(season).teams)aliases.set(teamSlug(team),{...team,season});
  return [...aliases.values()].sort((a,b)=>a.name.localeCompare(b.name));
};
export const allGames=()=>{
  const games=years.flatMap(year=>loadSeason(year).games),seen=new Set(games.map(g=>g.id));
  for(const game of loadFixtures().games)if(!seen.has(game.id)){games.push({...game,season:2026,hs:null,as:null});seen.add(game.id)}
  return games;
};
export const teamBySlug=(slug:string)=>allTeamAliases().find(team=>teamSlug(team)===slug);
export const teamParams=()=>allTeamAliases().map(team=>({team:teamSlug(team)}));
export const gameBySlug=(season:number,slug:string)=>allGames().find(game=>game.season===season&&gameSlug(game)===slug);
export const gameParams=()=>allGames().map(game=>({season:String(game.season),game:gameSlug(game)}));

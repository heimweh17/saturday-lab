import 'server-only';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {gameSlug,snapshotSlug,teamPath,teamSeasonPath,teamSlug} from './routes';

export type CatalogTeam={id:string;name:string;short:string;abbr:string;conference:string;logo:string;color:string};
export type CatalogTeamAlias=CatalogTeam&{season:number};
export type CatalogGame={id:string;season:number;week:number;date:string;home:string;away:string;homeName:string;awayName:string;neutral:boolean;fbs:boolean;completed:boolean;hs:number|null;as:number|null;status:string;timeValid:boolean};

const manifest=JSON.parse(readFileSync(join(process.cwd(),'public','data','manifest.json'),'utf8')) as {seasons:number[];latestSeason:number};
export const seasons=manifest.seasons;
export const latestSeason=manifest.latestSeason;
const cache=new Map<number,{games:CatalogGame[];teams:CatalogTeam[]}>();
const loadSeason=(season:number)=>{
  const cached=cache.get(season);if(cached)return cached;
  const raw=JSON.parse(readFileSync(join(process.cwd(),'public','data',`${season}.json`),'utf8')) as {games:Array<Omit<CatalogGame,'completed'|'status'|'timeValid'>>;snapshots:Record<string,{teams:CatalogTeam[]}>};
  const value={games:raw.games.map(g=>({...g,completed:true,status:'STATUS_FINAL',timeValid:true})),teams:raw.snapshots['99'].teams};cache.set(season,value);return value;
};
const loadFixtures=()=>JSON.parse(readFileSync(join(process.cwd(),'public','data','fixtures.json'),'utf8')) as {season:number;games:CatalogGame[]};

export const allTeams=()=>loadSeason(latestSeason).teams.slice().sort((a,b)=>a.name.localeCompare(b.name));
export const allTeamAliases=()=>{
  const aliases=new Map<string,CatalogTeamAlias>();
  for(const season of seasons)for(const team of loadSeason(season).teams)aliases.set(teamSlug(team),{...team,season});
  return [...aliases.values()].sort((a,b)=>a.name.localeCompare(b.name));
};
export const allGames=()=>{
  const games=seasons.flatMap(year=>loadSeason(year).games),seen=new Set(games.map(g=>g.id));
  for(const game of loadFixtures().games)if(!seen.has(game.id)){games.push({...game,season:2026,hs:null,as:null});seen.add(game.id)}
  return games;
};
export const teamBySlug=(slug:string)=>allTeamAliases().find(team=>teamSlug(team)===slug);
export const teamParams=()=>allTeamAliases().map(team=>({team:teamSlug(team)}));
export const teamBySlugSeason=(slug:string,season:number)=>loadSeason(season).teams.find(team=>teamSlug(team)===slug);
export const allTeamSeasons=()=>seasons.flatMap(season=>loadSeason(season).teams.map(team=>({...team,season})));
export const seasonsForTeam=(teamId:string)=>seasons.filter(season=>loadSeason(season).teams.some(team=>team.id===teamId));
export const routesForTeam=(teamId:string)=>Object.fromEntries(seasons.flatMap(season=>{const team=loadSeason(season).teams.find(row=>row.id===teamId);return team?[[String(season),season===latestSeason?teamPath(team):teamSeasonPath(team,season)]]:[]}));
export const teamSeasonParams=()=>seasons.flatMap(season=>loadSeason(season).teams.map(team=>({team:teamSlug(team),season:String(season)})));
const seasonWeeks=(season:number)=>{const raw=JSON.parse(readFileSync(join(process.cwd(),'public','data',`${season}.json`),'utf8')) as {weeks:number[]};return raw.weeks};
export const rankingSeasonParams=()=>seasons.map(season=>({season:String(season)}));
export const rankingSnapshotParams=()=>seasons.flatMap(season=>seasonWeeks(season).filter(week=>week!==99).map(week=>({season:String(season),snapshot:snapshotSlug(week)})));
export const weekFromSnapshotSlug=(value:string)=>{const match=/^(week|postseason)-(\d+)$/.exec(value);if(!match)return null;return match[1]==='week'?Number(match[2]):30+Number(match[2])};
export const hasSnapshot=(season:number,week:number)=>seasons.includes(season)&&seasonWeeks(season).includes(week);
export const gameBySlug=(season:number,slug:string)=>allGames().find(game=>game.season===season&&gameSlug(game)===slug);
export const gameParams=()=>allGames().map(game=>({season:String(game.season),game:gameSlug(game)}));
export const recentMeetings=(game:CatalogGame,limit=4)=>allGames().filter(other=>other.completed&&other.id!==game.id&&other.date<game.date&&other.season>=game.season-4&&((other.home===game.home&&other.away===game.away)||(other.home===game.away&&other.away===game.home))).sort((a,b)=>b.date.localeCompare(a.date)).slice(0,limit);

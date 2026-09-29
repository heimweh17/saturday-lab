import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

const root=resolve(import.meta.dirname,'..');
const read=name=>JSON.parse(readFileSync(resolve(root,'public','data',name),'utf8'));
const manifest=read('manifest.json');
const failures=[];
const requireValue=(condition,message)=>{if(!condition)failures.push(message)};
const finite=value=>typeof value==='number'&&Number.isFinite(value);

function checkConfig(config,label){
  requireValue(config&&typeof config==='object',`${label}: missing scoring configuration`);
  if(!config)return;
  for(const [path,value] of [
    ['elo.home',config.elo?.home],['scoring.home',config.scoring?.home],
    ['scoring.scale',config.scoring?.scale],['eloWeight',config.eloWeight],
  ])requireValue(finite(value),`${label}: ${path} must be finite`);
  requireValue((config.scoring?.scale??0)>0,`${label}: scoring.scale must be positive`);
}

checkConfig(manifest.config,'manifest.json');
requireValue(Array.isArray(manifest.seasons)&&manifest.seasons.length>0,'manifest.json: seasons must be nonempty');

for(const seasonNumber of manifest.seasons??[]){
  const label=`${seasonNumber}.json`,season=read(label);
  requireValue(season.season===seasonNumber,`${label}: season identity mismatch`);
  requireValue(Array.isArray(season.weeks)&&season.weeks.includes(99),`${label}: weeks must include current snapshot 99`);
  requireValue(season.snapshots&&typeof season.snapshots==='object',`${label}: snapshots missing`);
  requireValue(Array.isArray(season.games),`${label}: games missing`);
  requireValue(Array.isArray(season.predictions),`${label}: predictions missing`);
  checkConfig(season.scoringConfig,label);
  const current=season.snapshots?.['99'];
  requireValue(current&&Array.isArray(current.teams)&&current.teams.length>0,`${label}: snapshot 99 teams missing`);
  for(const week of season.weeks??[]){
    const snapshot=season.snapshots?.[String(week)];
    requireValue(snapshot&&Array.isArray(snapshot.teams),`${label}: snapshot ${week} missing`);
    if(!snapshot?.teams)continue;
    requireValue(finite(snapshot.mu),`${label}: snapshot ${week} mu must be finite`);
    const ids=new Set();
    for(const team of snapshot.teams){
      const where=`${label}: snapshot ${week} team ${team.id??'unknown'}`;
      requireValue(typeof team.id==='string'&&team.id.length>0,`${where}: id missing`);
      requireValue(!ids.has(team.id),`${where}: duplicate id`); ids.add(team.id);
      for(const key of ['offense','defense','power','elo','wins','losses'])requireValue(finite(team[key]),`${where}: ${key} must be finite`);
      if(team.modelState){
        requireValue(Array.isArray(team.modelState.q)&&team.modelState.q.length>0,`${where}: modelState.q missing`);
        requireValue(team.modelState.q?.every(finite),`${where}: modelState.q contains a non-finite value`);
      }
      if(team.ratingExplanation)requireValue(Array.isArray(team.ratingExplanation.drivers),`${where}: ratingExplanation.drivers missing`);
    }
  }
  const currentIds=new Set((current?.teams??[]).map(team=>team.id));
  for(const game of season.games??[]){
    const where=`${label}: game ${game.id??'unknown'}`;
    requireValue(typeof game.id==='string'&&game.id.length>0,`${where}: id missing`);
    requireValue(typeof game.date==='string'&&game.date.length>0,`${where}: date missing`);
    if(game.fbs){
      requireValue(currentIds.has(game.home),`${where}: FBS home team ${game.home} absent from snapshot 99`);
      requireValue(currentIds.has(game.away),`${where}: FBS away team ${game.away} absent from snapshot 99`);
    }
  }
  for(const prediction of season.predictions??[]){
    const where=`${label}: prediction ${prediction.id??'unknown'}`;
    for(const key of ['prob','margin','homeScore','awayScore'])requireValue(finite(prediction[key]),`${where}: ${key} must be finite`);
    requireValue(prediction.prob>=0&&prediction.prob<=1,`${where}: prob outside [0,1]`);
  }
}

for(const name of ['fixtures.json',`live-${manifest.latestSeason}.json`]){
  const feed=read(name),ids=new Set();
  requireValue(Array.isArray(feed.games)&&feed.games.length>0,`${name}: games must be nonempty`);
  for(const game of feed.games??[]){
    const where=`${name}: game ${game.id??'unknown'}`;
    requireValue(typeof game.id==='string'&&game.id.length>0,`${where}: id missing`);
    requireValue(!ids.has(game.id),`${where}: duplicate id`); ids.add(game.id);
    for(const key of ['date','home','away'])requireValue(typeof game[key]==='string'&&game[key].length>0,`${where}: ${key} missing`);
    if(name.startsWith('live-')){
      requireValue(['pre','in','post'].includes(game.state),`${where}: invalid state`);
      requireValue(!game.completed||(finite(game.hs)&&finite(game.as)),`${where}: completed game score missing`);
      if(game.pregame)requireValue(finite(game.pregame.homeWinProbability)&&game.pregame.homeWinProbability>=0&&game.pregame.homeWinProbability<=1,`${where}: invalid pregame probability`);
    }
  }
}

if(failures.length){
  console.error(`Published-data contract failed with ${failures.length} problem(s):`);
  for(const failure of failures.slice(0,100))console.error(`- ${failure}`);
  if(failures.length>100)console.error(`- …and ${failures.length-100} more`);
  process.exit(1);
}
console.log(`PASS: published-data contract across ${manifest.seasons.length} seasons.`);

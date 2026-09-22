export type Rating={id:string;name:string;offense:number;defense:number;elo:number};
export type ModelConfig={elo:{home:number};scoring:{home:number;scale:number};eloWeight:number};
export function predict(a:Rating,b:Rating,mu:number,venue:'a'|'b'|'neutral',config:ModelConfig){
if(a.id===b.id)throw new Error('Choose two different teams.');
const location=venue==='a'?1:venue==='b'?-1:0;
const home=location*config.scoring.home;
const aScore=mu+a.offense-b.defense+home/2;
const bScore=mu+b.offense-a.defense-home/2;
const margin=aScore-bScore;
const scoringProbability=1/(1+Math.exp(-margin/config.scoring.scale));
const eloProbability=1/(1+10**(-(a.elo-b.elo+location*config.elo.home)/400));
return {a:a.id,b:b.id,aName:a.name,bName:b.name,venue,probability:config.eloWeight*eloProbability+(1-config.eloWeight)*scoringProbability,scoringProbability,eloProbability,margin,aScore,bScore,offenseEdge:a.offense-b.offense,defenseEdge:a.defense-b.defense,homeEdge:home};}

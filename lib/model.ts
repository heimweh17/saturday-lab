export type ModelState={basePower:number;elo:number;box:number[];form:number;sos:number;sample:number;lastDate:string|null};
export type Model={version:string;coefficients:number[];weight:number;trainingThrough:number};
export const featureNames=['Scoring strength','Elo strength','Passing efficiency','Rushing efficiency','Third-down efficiency','Turnover control','Play volume','Completion rate','First-down efficiency','Penalty discipline','Fourth-down efficiency','Possession time','Recent form','Schedule strength','Experience','Rest','Passing matchup','Rushing matchup'];
export function modelFeatures(a:ModelState,b:ModelState,location:number,date?:string){
 const margin=a.basePower-b.basePower+3*location;const x=[margin,a.elo-b.elo+55*location];
 for(let j=0;j<10;j++)x.push(([3,7].includes(j)?-1:1)*(a.box[j*2]+a.box[j*2+1]-b.box[j*2]-b.box[j*2+1]));
 const rest=(t:ModelState)=>date&&t.lastDate?Math.max(3,Math.min(21,(Date.parse(date)-Date.parse(t.lastDate))/86400000)):7;
 return [...x,a.form-b.form,a.sos-b.sos,margin*Math.min(a.sample,b.sample)/12,rest(a)-rest(b),a.box[0]*b.box[1]-b.box[0]*a.box[1],a.box[2]*b.box[3]-b.box[2]*a.box[3]];
}
export function modelPredict(a:ModelState,b:ModelState,location:number,model:Model,date?:string){
 const x=modelFeatures(a,b,location,date);const contributions=x.map((v,i)=>v*model.coefficients[i]);
 const logit=contributions.reduce((a,b)=>a+b,0);const probability=model.weight/(1+Math.exp(-Math.max(-30,Math.min(30,logit))))+(1-model.weight)/(1+Math.exp(-Math.max(-30,Math.min(30,x[0]/8))));
 return {probability,contributions,scoringProbability:1/(1+Math.exp(-x[0]/8)),efficiencyProbability:1/(1+Math.exp(-logit))};
}
export function winDistribution(probabilities:number[]){
 let distribution=[1];
 for(const p of probabilities){const next=Array(distribution.length+1).fill(0) as number[];distribution.forEach((mass,k)=>{next[k]+=mass*(1-p);next[k+1]+=mass*p});distribution=next}
 return distribution;
}

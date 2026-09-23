import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const folder='public/first-model/2026-09-23/';
const d=JSON.parse(fs.readFileSync(folder+'forecast.json','utf8'));
const module={exports:{}};
vm.runInNewContext(fs.readFileSync(folder+'ledger.js','utf8'),{module,console});
const {validResult,evaluateGames}=module.exports;
assert.equal(validResult({home:0,away:7}),true);
for(const r of [{home:7,away:7},{home:-1,away:7},{home:2.5,away:7},{home:'7',away:0}])assert.equal(validResult(r),false);
const sample=[{id:'a',modeled:true,homeProbability:.8},{id:'b',modeled:true,homeProbability:.6},{id:'c',modeled:false,homeProbability:null},{id:'d',modeled:true,homeProbability:.9}];
const m=evaluateGames(sample,{a:{home:21,away:7},b:{home:10,away:14},c:{home:21,away:3},d:{home:7,away:7}});
assert.equal(m.n,2);assert.equal(m.correct,1);assert.equal(m.accuracy,.5);
assert.ok(Math.abs(m.brier-.2)<1e-12);assert.ok(Math.abs(m.logLoss-(-Math.log(.8)-Math.log(.4))/2)<1e-12);
assert.equal(evaluateGames(sample,{}).accuracy,null);
const teams=new Map(d.teams.map(t=>[t.id,t]));
for(const g of d.games){
 assert.ok(Date.parse(g.date)>Date.parse(d.sealedAt));assert.equal(g.completed,false);
 if(!g.modeled){assert.equal(g.homeProbability,null);assert.equal(g.pick,null);continue;}
 const a=teams.get(g.home),b=teams.get(g.away),margin=a.offense+a.defense-b.offense-b.defense+(g.neutral?0:2);
 assert.ok(Math.abs(margin-g.margin)<1e-12);
 assert.ok(Math.abs(1/(1+Math.exp(-margin/8))-g.homeProbability)<1e-12);
 assert.ok(Math.abs(g.homeProbability+g.awayProbability-1)<1e-12);
 assert.equal(g.pick,g.homeProbability>=.5?g.home:g.away);
}
assert.equal(d.benchmarkGamesVerified,2555);
console.log(`PASS: ${d.games.length} frozen future fixtures; original-model formula, picks, score validation, filtered metrics and missing-result handling.`);

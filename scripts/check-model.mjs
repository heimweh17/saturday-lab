import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import ts from 'typescript';
const module={exports:{}};
const code=ts.transpileModule(fs.readFileSync('lib/model.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
vm.runInNewContext(code,{module,exports:module.exports,Math,Date,Array});
const {modelPredict,winDistribution}=module.exports;
let checked=0;
for(const year of [2023,2024,2025,2026]){
 const data=JSON.parse(fs.readFileSync(`public/data/${year}.json`,'utf8'));
 for(const p of data.predictions){
  const teams=data.snapshots[String(p.week)].teams;const a=teams.find(t=>t.id===p.home).modelState,b=teams.find(t=>t.id===p.away).modelState,location=p.neutral?0:1;
  const result=modelPredict(a,b,location,data.model,p.date);
  assert.ok(Math.abs(result.probability-p.prob)<1e-12,`Python/TypeScript mismatch: ${p.id}`);
  assert.ok(Math.abs(result.probability+modelPredict(b,a,-location,data.model,p.date).probability-1)<1e-12);
  checked++;
 }
}
const probabilities=[.2,.6,.8];const exact=[0,0,0,0];
for(let mask=0;mask<8;mask++){let p=1,wins=0;probabilities.forEach((q,i)=>{const won=(mask>>i)&1;wins+=won;p*=won?q:1-q});exact[wins]+=p}
const distribution=winDistribution(probabilities);distribution.forEach((p,k)=>assert.ok(Math.abs(p-exact[k])<1e-14));
assert.ok(Math.abs(distribution.reduce((s,p,k)=>s+k*p,0)-probabilities.reduce((s,p)=>s+p,0))<1e-14);
assert.equal(winDistribution([])[0],1);
console.log(`PASS: ${checked} Python/TypeScript forecasts, complementary probabilities, exact win-count distribution.`);

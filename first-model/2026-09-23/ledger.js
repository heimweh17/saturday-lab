/* Frozen forecasts and local-only result bookkeeping. No production model imports. */
'use strict';
const $=id=>document.getElementById(id);
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const percent=n=>(n*100).toFixed(1)+'%';
const dateText=value=>new Intl.DateTimeFormat('zh-CN',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value));
const storageKey='saturday-lab:first-model:2026-09-23:results';
let data,results={},activeId=null;
function validResult(r){return r&&Number.isInteger(r.home)&&Number.isInteger(r.away)&&r.home>=0&&r.away>=0&&r.home<=200&&r.away<=200&&r.home!==r.away;}
function evaluateGames(games,records){
 const scored=games.filter(g=>g.modeled&&validResult(records[g.id]));
 let correct=0,brier=0,loss=0;
 for(const g of scored){const y=Number(records[g.id].home>records[g.id].away),p=g.homeProbability;correct+=Number((p>=.5)===(y===1));brier+=(p-y)**2;loss-=Math.log(Math.max(1e-9,y?p:1-p));}
 return {n:scored.length,correct,accuracy:scored.length?correct/scored.length:null,brier:scored.length?brier/scored.length:null,logLoss:scored.length?loss/scored.length:null};
}
function download(name,content){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type:'application/json'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function persist(next){try{localStorage.setItem(storageKey,JSON.stringify(next));results=next;return true;}catch{$('message').textContent='浏览器无法保存记录。请检查本地存储权限；本次修改未保存。';return false;}}
function acceptedRecords(raw){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('赛果格式不正确。');
 const clean={};
 for(const [id,r] of Object.entries(raw)){
  const g=data.games.find(g=>g.id===id);
  if(!g||!validResult(r)||Date.parse(g.date)>Date.now())throw Error('备份含未知比赛、未开赛比赛或无效比分，未导入。');
  clean[id]={home:r.home,away:r.away};
 }
 return clean;
}
function render(){
 const team=$('team').value,week=$('week').value,query=$('search').value.trim().toLowerCase(),filter=$('filter').value;
 const games=data.games.filter(g=>{
  if(team&&g.home!==team&&g.away!==team||week&&String(g.week)!==week||!`${g.homeName} ${g.awayName}`.toLowerCase().includes(query))return false;
  const scored=validResult(results[g.id]),correct=scored&&g.modeled&&((g.homeProbability>=.5)===(results[g.id].home>results[g.id].away));
  return filter==='all'||filter==='pending'&&!scored||filter==='scored'&&scored||filter==='correct'&&correct||filter==='wrong'&&scored&&g.modeled&&!correct||filter==='unmodeled'&&!g.modeled;
 });
 const m=evaluateGames(games,results);
 $('prob-heading').textContent=team?`${data.teams.find(t=>t.id===team)?.short??'所选球队'} 胜率`:'看好方胜率';
 $('summary').innerHTML=[['已核对 / 有预测的比赛',`${m.n} / ${games.filter(g=>g.modeled).length}`],['命中率',m.n?percent(m.accuracy):'等待赛果'],['Brier · 越低越好',m.n?m.brier.toFixed(4):'—'],['Log loss · 越低越好',m.n?m.logLoss.toFixed(4):'—']].map(([label,value])=>`<div><strong>${value}</strong><span>${label}</span></div>`).join('');
 $('scope').textContent=`当前筛选共 ${games.length} 场；统计仅依据本浏览器已录入赛果。${team?'胜率列显示所选球队的获胜概率。':'胜率列显示模型看好方的获胜概率。'}`;
 $('rows').innerHTML=games.map(g=>{
  const r=results[g.id],scored=validResult(r),correct=scored&&g.modeled&&((g.homeProbability>=.5)===(r.home>r.away));
  const p=!g.modeled?null:team?(g.home===team?g.homeProbability:g.awayProbability):g.pickProbability;
  const result=scored?`<strong class="${g.modeled?(correct?'good':'bad'):''}">${r.away} – ${r.home}${g.modeled?(correct?' · 猜对':' · 猜错'):''}</strong>`:'<small>等待最终比分</small>';
  return `<tr><td>${dateText(g.date)}<small>第 ${g.week} 周${g.timeValid?'':' / 开球时间待定'}</small></td><td class="match"><strong>${escapeHtml(g.awayName)}</strong><small>${g.neutral?'中立场地对阵':'客场挑战'}</small><strong>${escapeHtml(g.homeName)}</strong></td><td>${g.modeled?escapeHtml(g.pickName):'<small>非 FBS 对阵，不预测</small>'}</td><td>${p===null?'—':`<span class="prob">${percent(p)}</span><div class="bar"><i style="width:${p*100}%"></i></div>${team?`<small>${p>=.5?'预计胜':'预计负'}</small>`:''}`}</td><td>${result}<button class="entry" data-id="${escapeHtml(g.id)}" ${Date.parse(g.date)>Date.now()?'disabled title="开赛后可录入最终比分"':''}>${scored?'修改赛果':'录入赛果'}</button><small><a href="${escapeHtml(g.source)}" target="_blank" rel="noreferrer">ESPN 比赛页</a></small></td></tr>`;
 }).join('');
 $('empty').hidden=games.length>0;
}
function openEditor(id){
 const g=data.games.find(g=>g.id===id);if(!g||Date.parse(g.date)>Date.now())return;
 activeId=id;const r=results[id];$('fixture-label').textContent=`${dateText(g.date)} / 第 ${g.week} 周`;
 $('away-label').textContent=g.awayName;$('home-label').textContent=g.homeName;
 $('away-score').value=r?.away??'';$('home-score').value=r?.home??'';$('final-check').checked=false;$('form-error').textContent='';$('remove').hidden=!r;$('editor').showModal();
}
async function start(){
 try{
  const response=await fetch('forecast.json');if(!response.ok)throw Error('无法读取封存预测，请刷新重试。');data=await response.json();
  $('dates').textContent=`封存于 ${dateText(data.sealedAt)}；比赛结果使用至 ${dateText(data.ratingThrough)}；赛程读取于 ${dateText(data.scheduleFetchedAt)}（日期均为美国东部时间）。`;
  $('verification').textContent=`发布前逐场重算并核对了 ${data.benchmarkGamesVerified.toLocaleString()} 场第一版历史预测。完整参数、未四舍五入的概率及来源校验值保存在 JSON 中。`;
  for(const t of [...data.teams].sort((a,b)=>a.name.localeCompare(b.name))){const option=new Option(t.name,t.id);$('team').add(option);}
  for(const week of [...new Set(data.games.map(g=>g.week))].sort((a,b)=>a-b))$('week').add(new Option(`第 ${week} 周`,String(week)));
  try{const stored=localStorage.getItem(storageKey);if(stored)results=acceptedRecords(JSON.parse(stored));$('message').textContent='预测已封存。赛后在每场比赛旁录入最终比分，即可核对结果。';}
  catch{$('message').textContent='本地赛果无法读取，暂以空账本显示；可从备份恢复。';}
  for(const id of ['team','week','filter'])$(id).addEventListener('change',render);$('search').addEventListener('input',render);
  $('rows').addEventListener('click',e=>{const button=e.target.closest('button[data-id]');if(button)openEditor(button.dataset.id);});
  $('close').onclick=()=>$('editor').close();
  $('score-form').onsubmit=e=>{e.preventDefault();if(!$('away-score').value||!$('home-score').value||!$('final-check').checked)return;const r={away:Number($('away-score').value),home:Number($('home-score').value)};if(!validResult(r)){$('form-error').textContent='请填写 0–200 的整数最终比分，双方不能相同。';return;}if(persist({...results,[activeId]:r})){$('editor').close();$('message').textContent='赛果已保存在当前浏览器。建议导出备份。';render();}};
  $('remove').onclick=()=>{const next={...results};delete next[activeId];if(persist(next)){$('editor').close();render();$('message').textContent='已移除此场本地赛果；封存预测未改变。';}};
  $('export').disabled=false;$('import').disabled=false;
  $('export').onclick=()=>download('first-model-2026-results.json',JSON.stringify({edition:data.edition,exportedAt:new Date().toISOString(),results},null,2));
  $('import').onclick=()=>$('file').click();
  $('file').onchange=async()=>{const f=$('file').files[0];if(!f)return;try{if(f.size>1000000)throw Error('备份文件过大。');const backup=JSON.parse(await f.text());if(backup.edition!==data.edition)throw Error('这不是本期预测的赛果备份。');const imported=acceptedRecords(backup.results);if(Object.keys(imported).some(id=>results[id]&&(results[id].home!==imported[id].home||results[id].away!==imported[id].away)))throw Error('备份与当前比分有冲突，未导入。请先核对并移除冲突场次。');if(persist({...results,...imported})){$('message').textContent=`已合并 ${Object.keys(imported).length} 场赛果。`;render();}}catch(error){$('message').textContent=error.message||'文件无法读取，未导入。';}finally{$('file').value='';}};
  render();
 }catch(error){$('message').textContent=error.message||'页面数据无法加载，请刷新重试。';}
}
if(typeof document!=='undefined')start();
if(typeof module!=='undefined')module.exports={validResult,evaluateGames};

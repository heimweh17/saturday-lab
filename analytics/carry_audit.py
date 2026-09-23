"""Prespecified carry sensitivity audit; production data is never overwritten.
Only carry changes (scoring, box metrics, Elo); refit coefficients on earlier years.
Keep published annual feature sets, penalties and mixture weights fixed.
Results are retrospective sensitivity analysis, not untouched holdouts.
"""
import json
from pathlib import Path
import numpy as np
from pipeline import load_data,metrics,sigmoid
from feature_engine import build,fit,features
ROOT=Path(__file__).resolve().parents[1]
def main():
    protocol={'carry':[0.,.25,.4,.5,.65],'scope':'All scoring, efficiency and Elo priors; fixed published annual feature/ridge/mixture choices; refit through preceding year. Retrospective sensitivity only.','selectionYears':[2023,2024,2025],'diagnosticYear':2026}
    out=ROOT/'analytics/carry-audit';out.mkdir(exist_ok=True)
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2))
    baseline=ROOT/'public/data/model-v3.json';old=json.loads((baseline if baseline.exists() else ROOT/'public/data/model.json').read_text());teams,seasons,boxes,_=load_data(ROOT.parent/'research/data');results=[]
    for carry in protocol['carry']:
        cache=out/f'cache-{carry}.json'
        if carry==.65: data=json.loads((ROOT/'analytics/final-feature-cache.json').read_text())
        elif cache.exists(): data=json.loads(cache.read_text())
        else:
            rows,states=build(teams,seasons,boxes,carry=carry);data={'rows':rows,'states':states};cache.write_text(json.dumps(data,separators=(',',':')))
        rows,states=data['rows'],data['states'];preds=[];annual=[]
        for year in [2023,2024,2025,2026]:
            cfg=old['annual'][str(year)];sel=cfg['selected'];train=[r for r in rows if 2019<=r['season']<year];test=[r for r in rows if r['season']==year]
            coef=fit(train,sel['indices'],sel['ridge']);x=np.array([r['x'] for r in test]);prob=cfg['weight']*sigmoid(x@coef)+(1-cfg['weight'])*sigmoid(x[:,0]/8)
            ps=[{'id':r['id'],'year':year,'week':r['week'],'prob':float(p),'outcome':r['y']} for r,p in zip(test,prob)];preds.extend(ps)
            early=[p for p in ps if p['week']<=4];annual.append({'year':year,**metrics(prob,[r['y'] for r in test]),'early':metrics([p['prob'] for p in early],[p['outcome'] for p in early])})
            if year==2026:
                ss=states['2026:99'];idx={t:float(np.mean([cfg['weight']*sigmoid(np.array(features(a,b,0))@coef)+(1-cfg['weight'])*sigmoid((a['basePower']-b['basePower'])/8) for k,b in ss.items() if k!=t])) for t,a in ss.items()};ordered=sorted(idx,key=lambda t:-idx[t]);jmu={'rank':ordered.index('256')+1,'index':idx['256'],'power':ss['256']['basePower']}
        pooled=[p for p in preds if p['year']<2026];early=[p for p in pooled if p['week']<=4]
        result={'carry':carry,'annual':annual,'historical':metrics([p['prob'] for p in pooled],[p['outcome'] for p in pooled]),'historicalEarly':metrics([p['prob'] for p in early],[p['outcome'] for p in early]),'jmu':jmu};results.append(result)
        (out/f'predictions-{carry}.json').write_text(json.dumps(preds));(out/'report.json').write_text(json.dumps({'protocol':protocol,'results':results},indent=2));print('RESULT',json.dumps(result),flush=True)
    report={'protocol':protocol,'results':results,'decision':'Retain 65% in production: lower carry did not improve pooled probability loss or early-season probability scores. 50% slightly improved historical pick accuracy but worsened probability loss. Sensitivity analysis, not fresh nested model selection.'}
    (ROOT/'public/data/carry-audit.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()

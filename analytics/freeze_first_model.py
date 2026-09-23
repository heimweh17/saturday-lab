"""Seal the original model's future forecasts without modifying production data."""
import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from pipeline import ROOT, load_data, score_run, sigmoid
from ranking_review import verify_files

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=ROOT.parent/'research/data')
    parser.add_argument('--edition',default='2026-09-23')
    args=parser.parse_args()
    assert args.edition == '2026-09-23', 'Create a new reviewed edition explicitly.'
    out=ROOT/'public/first-model'/args.edition
    if (out/'forecast.json').exists():raise SystemExit('Already sealed; refusing to overwrite predictions.')
    verify_files(ROOT/'analytics/core-source-hashes.json',args.data)
    teams,seasons,_,_=load_data(args.data)
    config=json.loads((ROOT/'analytics/locked-config.json').read_text())['config']
    assert config['eloWeight']==0
    sc=config['scoring']
    predictions,states=score_run(teams,seasons,sc['shrinkage'],sc['home'],sc['decay'],carry=.65)
    benchmark=json.loads((ROOT/'public/data/model.json').read_text())['predictions']
    for p in benchmark:
        assert abs(float(sigmoid(predictions[p['id']]['margin']/sc['scale']))-p['benchmark'])<1e-12,p['id']
    now=datetime.now(timezone.utc)
    fixture_path=ROOT/'public/data/fixtures.json';fixtures=json.loads(fixture_path.read_text())
    snapshot=states[(2026,99)];ratings=snapshot['ratings']
    cutoff=max(g['date'] for g in seasons[2026]['games'])
    assert cutoff==fixtures['ratingThrough']
    future=[g for g in fixtures['games'] if not g['completed'] and datetime.fromisoformat(g['date'].replace('Z','+00:00'))>now]
    rows=[]
    for g in future:
        modeled=g['fbs'] and g['home'] in ratings and g['away'] in ratings
        p=margin=hs=aws=None
        if modeled:
            ao,ad=ratings[g['home']];bo,bd=ratings[g['away']]
            venue=0 if g['neutral'] else sc['home']
            hs=snapshot['mu']+ao-bd+venue/2;aws=snapshot['mu']+bo-ad-venue/2
            margin=hs-aws;p=float(sigmoid(margin/sc['scale']))
        pick=None if p is None else g['home'] if p>=.5 else g['away']
        rows.append({**g,'modeled':modeled,'homeProbability':p,'awayProbability':None if p is None else 1-p,'pick':pick,'pickName':None if pick is None else g['homeName'] if pick==g['home'] else g['awayName'],'pickProbability':None if p is None else max(p,1-p),'homeScoreEstimate':hs,'awayScoreEstimate':aws,'margin':margin})
    rows.sort(key=lambda g:(g['date'],g['id']))
    assert len({g['id'] for g in rows})==len(rows)
    payload={'edition':args.edition,'season':2026,'model':'Original v1 locked scoring model','sealedAt':now.isoformat(),'ratingThrough':cutoff,'scheduleFetchedAt':fixtures['fetchedAt'],'config':config,'scoringCarry':.65,'benchmarkGamesVerified':len(benchmark),'scheduleSha256':hashlib.sha256(fixture_path.read_bytes()).hexdigest(),'coreSourceHashes':json.loads((ROOT/'analytics/core-source-hashes.json').read_text()),'teams':[{**t,'offense':ratings[tid][0],'defense':ratings[tid][1],'power':sum(ratings[tid])} for tid,t in teams[2026].items()],'mu':snapshot['mu'],'games':rows}
    out.mkdir(parents=True,exist_ok=True)
    (out/'forecast.json').write_text(json.dumps(payload,ensure_ascii=True,separators=(',',':'),allow_nan=False),encoding='utf-8')
    fields=['id','date','week','awayName','homeName','neutral','modeled','pickName','pickProbability','homeProbability','awayProbability','homeScoreEstimate','awayScoreEstimate','margin']
    with (out/'forecast.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['sealedAt','ratingThrough',*fields]);writer.writeheader()
        writer.writerows({'sealedAt':payload['sealedAt'],'ratingThrough':cutoff,**{k:g[k] for k in fields}} for g in rows)
    print(f'Sealed {len(rows)} games, {sum(g["modeled"] for g in rows)} modeled; reproduced {len(benchmark)} original predictions.')

if __name__=='__main__':main()

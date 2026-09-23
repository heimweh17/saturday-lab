"""Saturday Lab: public-data ingestion, week-forward evaluation and export.
Run: python analytics/pipeline.py --data ../research/data
No target-week outcomes enter a target-week prediction. No holdout tuning.
"""
from __future__ import annotations
import argparse, csv, json, math, hashlib, statistics, urllib.request
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
YEARS = list(range(2018, 2027))
BASE = 'https://github.com/sportsdataverse/sportsdataverse-data/releases/download/'
SOURCES = {'schedules': ('espn_cfb_schedules', 'cfb_schedule'), 'teams': ('espn_cfb_teams', 'cfb_teams'), 'box': ('espn_cfb_team_box', 'team_box')}

def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def number(s, default=0):
    try: return float(s)
    except (ValueError, TypeError): return default
def truth(s): return str(s).lower() == 'true'
def identifier(s): return str(int(float(s)))
def sigmoid(x): return 1 / (1 + np.exp(-np.clip(x, -30, 30)))
def metrics(p, y, margins=None, actual=None):
    p, y = np.asarray(p), np.asarray(y)
    if len(y) == 0: return {'n': 0}
    q = np.clip(p, 1e-9, 1-1e-9)
    out = {'n': len(y), 'accuracy': float(np.mean((p >= .5) == (y >= .5))), 'brier': float(np.mean((p-y)**2)), 'logLoss': float(-np.mean(y*np.log(q)+(1-y)*np.log(1-q)))}
    if margins is not None: out['mae'] = float(np.mean(np.abs(np.asarray(margins)-np.asarray(actual))))
    return out

def load_data(folder):
    teams, seasons, boxes, audit = {}, {}, {}, []
    for year in YEARS:
        for kind, (release, name) in SOURCES.items():
            path = folder / f'{kind}_{year}.csv'
            if not path.exists():
                folder.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(f'{BASE}{release}/{name}_{year}.csv', path)
        tr = read(folder/f'teams_{year}.csv')
        members = {identifier(r['team_id']): r for r in tr if truth(r.get('is_fbs')) and not truth(r.get('is_all_star')) and not truth(r.get('is_exhibition'))}
        teams[year] = {tid: {'id': tid, 'name': r['display_name'], 'short': r.get('short_display_name') or r['display_name'], 'abbr': r.get('abbreviation', tid), 'conference': r.get('conference_name') or 'Independent', 'color': '#'+(r.get('color') or '1768ac').lstrip('#'), 'logo': r.get('team_logo', '')} for tid,r in members.items()}
        seen, games = set(), []
        rows = read(folder/f'schedules_{year}.csv')
        for r in rows:
            if r['status'] != 'STATUS_FINAL' or int(number(r['season_type'])) not in (2,3): continue
            h,a = identifier(r['home_id']), identifier(r['away_id'])
            if h not in members and a not in members: continue
            gid = identifier(r['game_id'])
            if gid in seen: raise ValueError('Duplicate game '+gid)
            seen.add(gid)
            hs,aws = int(number(r['home_score'],-1)), int(number(r['away_score'],-1))
            assert hs >= 0 and aws >= 0 and hs != aws and h != a, r
            week = int(number(r['week'])) + (30 if int(number(r['season_type'])) == 3 else 0)
            games.append({'id':gid,'season':year,'week':week,'date':r['game_date'],'home':h,'away':a,'homeName':r['home_team'],'awayName':r['away_team'],'hs':hs,'as':aws,'neutral':truth(r['neutral_site']),'fbs':h in members and a in members})
        # Every week is a frozen batch. Ordered by first kickoff, not file order.
        batches = {}
        for g in games: batches.setdefault(g['week'],[]).append(g)
        ordered = sorted(batches, key=lambda w:min(g['date'] for g in batches[w]))
        games.sort(key=lambda g:g['date'])
        seasons[year] = {'games':games,'weeks':ordered}
        boxes[year] = {(identifier(r['game_id']),identifier(r['team_id'])):r for r in read(folder/f'box_{year}.csv')}
        audit.append({'season':year,'teams':len(members),'games':len(games),'modelGames':sum(g['fbs'] for g in games),'sourceRows':len(rows),'lastGame':max(g['date'] for g in games), 'sha256':hashlib.sha256((folder/f'schedules_{year}.csv').read_bytes()).hexdigest()})
    return teams,seasons,boxes,audit

def elo_run(teams,seasons,k,h,carry,end=2026):
    ratings, preds, snapshots = {}, {}, {}
    for year in YEARS:
        if year>end: break
        ids = teams[year]
        ratings = {t:1500+carry*(ratings.get(t,1500)-1500) for t in ids}
        for week in seasons[year]['weeks']:
            batch=[g for g in seasons[year]['games'] if g['week']==week and g['fbs']]
            snapshots[(year,week)] = dict(ratings)
            updates={t:0. for t in ids}
            for g in batch:
                prob=float(sigmoid((ratings[g['home']]-ratings[g['away']]+(0 if g['neutral'] else h))*math.log(10)/400))
                preds[g['id']]=prob
                delta=k*((g['hs']>g['as'])-prob)
                updates[g['home']]+=delta; updates[g['away']]-=delta
            for t in ids: ratings[t]+=updates[t]
        snapshots[(year,99)] = dict(ratings)
    return preds,snapshots

def ridge_fit(history,ids,prior,lam,h,decay,carry=.65):
    n=len(ids); index={t:i for i,t in enumerate(ids)}
    po=np.array([prior.get(t,(0,0))[0]*carry for t in ids]); pd=np.array([prior.get(t,(0,0))[1]*carry for t in ids])
    o,d=po.copy(),pd.copy(); mu=28.
    if not history: return o,d,mu
    attack=[];defend=[];target=[];weight=[]
    latest=max(g['seq'] for g in history)
    for g in history:
        advantage=0 if g['neutral'] else h/2
        attack.extend([index[g['home']],index[g['away']]])
        defend.extend([index[g['away']],index[g['home']]])
        target.extend([g['hs']-advantage,g['as']+advantage])
        weight.extend([decay**(latest-g['seq'])]*2)
    ai,di=np.array(attack),np.array(defend); y=np.array(target); w=np.array(weight)
    ac=np.bincount(ai,weights=w,minlength=n); dc=np.bincount(di,weights=w,minlength=n)
    # Coordinate descent exactly minimizes a convex ridge objective.
    for _ in range(160):
        old=np.r_[o,d,mu]
        o=(np.bincount(ai,weights=w*(y-mu+d[di]),minlength=n)+lam*po)/(ac+lam)
        d=(np.bincount(di,weights=w*(mu+o[ai]-y),minlength=n)+lam*pd)/(dc+lam)
        mu=float((np.sum(w*(y-o[ai]+d[di]))+20*28)/(np.sum(w)+20))
        if np.max(np.abs(np.r_[o,d,mu]-old))<1e-7: break
    return o,d,mu

def score_run(teams,seasons,lam,h,decay,end=2026,carry=.65):
    prior,preds,snaps={},{},{}
    for year in YEARS:
        if year>end: break
        ids=list(teams[year]); idx={t:i for i,t in enumerate(ids)}; history=[]
        for seq,week in enumerate(seasons[year]['weeks']):
            o,d,mu=ridge_fit(history,ids,prior,lam,h,decay,carry=carry)
            snaps[(year,week)]={'ratings':{t:(float(o[i]),float(d[i])) for t,i in idx.items()},'mu':mu}
            cutoff=min(g['date'] for g in seasons[year]['games'] if g['week']==week)
            assert all(g['date']<cutoff for g in history), 'Overlapping week buckets: reject leakage'
            for g in seasons[year]['games']:
                if g['week']!=week or not g['fbs']: continue
                hi,ai=idx[g['home']],idx[g['away']]; adv=0 if g['neutral'] else h/2
                hs=mu+o[hi]-d[ai]+adv; aws=mu+o[ai]-d[hi]-adv
                preds[g['id']]={'margin':float(hs-aws),'homeScore':float(hs),'awayScore':float(aws),'cutoff':cutoff}
                history.append({**g,'seq':seq})
        o,d,mu=ridge_fit(history,ids,prior,lam,h,decay,carry=carry)
        prior={t:(float(o[i]),float(d[i])) for t,i in idx.items()}
        snaps[(year,99)]={'ratings':dict(prior),'mu':mu}
    return preds,snaps

def choose_models(teams,seasons):
    val=[g for g in seasons[2023]['games'] if g['fbs']]; y=[float(g['hs']>g['as']) for g in val]
    candidates=[]
    for k in (24,40,64):
        for h in (40,65):
            for carry in (.5,.75):
                p,_=elo_run(teams,seasons,k,h,carry,2023)
                m=metrics([p[g['id']] for g in val],y)
                candidates.append({'family':'Elo','params':{'k':k,'home':h,'carry':carry},**m})
    eb=min(candidates,key=lambda c:c['logLoss']); print('Elo validation',eb,flush=True)
    ec=eb['params']; ep,es=elo_run(teams,seasons,ec['k'],ec['home'],ec['carry'])
    scores=[]
    for lam in (2,5,9):
        for h in (2.,3.5):
            for decay in (1.,.94):
                p,_=score_run(teams,seasons,lam,h,decay,2023)
                for scale in (8.,12.,16.):
                    m=metrics([float(sigmoid(p[g['id']]['margin']/scale)) for g in val],y)
                    scores.append({'family':'Adjusted scoring','params':{'shrinkage':lam,'home':h,'decay':decay,'scale':scale},**m})
    sb=min(scores,key=lambda c:c['logLoss']); print('Scoring validation',sb,flush=True)
    candidates+=scores; sc=sb['params']; sp,ss=score_run(teams,seasons,sc['shrinkage'],sc['home'],sc['decay'])
    blend=[]
    for weight in (0.,.25,.5,.75,1.):
        p=[weight*ep[g['id']]+(1-weight)*float(sigmoid(sp[g['id']]['margin']/sc['scale'])) for g in val]
        blend.append({'family':'Blend','params':{'eloWeight':weight},**metrics(p,y)})
    best=min(blend,key=lambda c:c['logLoss']); print('Blend validation',best,flush=True)
    return {'elo':ec,'scoring':sc,'eloWeight':best['params']['eloWeight']},candidates+blend,ep,es,sp,ss

def box_summary(games,tid,boxes):
    own=[]; opp=[]
    for g in games:
        other=g['away'] if g['home']==tid else g['home']
        b=boxes.get((g['id'],tid)); ob=boxes.get((g['id'],other))
        if b: own.append(b)
        if ob: opp.append(ob)
    def avg(rs,key):
        vs=[number(r[key],None) for r in rs if r.get(key) not in ('',None)]
        vs=[v for v in vs if v is not None]
        return round(statistics.mean(vs),2) if vs else None
    def fraction(rs,key,sep):
        v=[r[key].split(sep) for r in rs if sep in r.get(key,'')]
        a=sum(number(x[0]) for x in v); b=sum(number(x[1]) for x in v)
        return round(a/b,4) if b else None
    return {'boxGames':len(own),'yards':avg(own,'totalYards'),'passYards':avg(own,'netPassingYards'),'rushYards':avg(own,'rushingYards'),'yardsAllowed':avg(opp,'totalYards'),'thirdDown':fraction(own,'thirdDownEff','-'),'completion':fraction(own,'completionAttempts','/'),'turnovers':avg(own,'turnovers'),'takeaways':avg(opp,'turnovers')}

def export(teams,seasons,boxes,audit,config,candidates,ep,es,sp,ss):
    out=ROOT/'public'/'data';out.mkdir(parents=True,exist_ok=True)
    def dump(name,data): (out/name).write_text(json.dumps(data,separators=(',',':'),allow_nan=False),encoding='utf-8')
    predictions=[]
    for year in YEARS:
        for g in seasons[year]['games']:
            if not g['fbs']: continue
            pscore=float(sigmoid(sp[g['id']]['margin']/config['scoring']['scale']))
            p=config['eloWeight']*ep[g['id']]+(1-config['eloWeight'])*pscore
            predictions.append({**g,**sp[g['id']],'elo':ep[g['id']],'scoreProb':pscore,'prob':p,'outcome':int(g['hs']>g['as'])})
    evaluation=[];calibration=[]
    for year in (2023,2024,2025,2026):
        rows=[p for p in predictions if p['season']==year];y=[p['outcome'] for p in rows]
        for name,key in [('Saturday model','prob'),('Elo','elo'),('Adjusted scoring','scoreProb'),('50/50 baseline',None)]:
            ps=[p[key] if key else .5 for p in rows]
            evaluation.append({'season':year,'model':name,**metrics(ps,y,[p['margin'] for p in rows] if key in ('prob','scoreProb') else None,[p['hs']-p['as'] for p in rows])})
        for i in range(10):
            rr=[p for p in rows if min(9,int(p['prob']*10))==i]
            calibration.append({'season':year,'bin':i,'n':len(rr),'predicted':statistics.mean(p['prob'] for p in rr) if rr else None,'actual':statistics.mean(p['outcome'] for p in rr) if rr else None})
    hold=[p for p in predictions if p['season'] in (2024,2025)]
    residual=sorted(abs(p['hs']-p['as']-p['margin']) for p in hold)
    report={'config':config,'candidates':sorted(candidates,key=lambda c:c['logLoss']),'evaluation':evaluation,'calibration':calibration,'holdout':metrics([p['prob'] for p in hold],[p['outcome'] for p in hold],[p['margin'] for p in hold],[p['hs']-p['as'] for p in hold]),'residual80':residual[int(.8*(len(residual)-1))],'validationSeason':2023,'testSeasons':[2024,2025]}
    dump('report.json',report)
    for year in YEARS:
        snapshots={};previous_ranks={}
        for week in seasons[year]['weeks']+[99]:
            before=seasons[year]['weeks'][:seasons[year]['weeks'].index(week)] if week!=99 else seasons[year]['weeks']
            past=[g for g in seasons[year]['games'] if g['week'] in before]
            rating=ss[(year,week)]; rows=[]
            for tid,t in teams[year].items():
                gs=[g for g in past if tid in (g['home'],g['away'])];fg=[g for g in gs if g['fbs']]
                o,d=rating['ratings'][tid];elo=es[(year,week)][tid]
                # Convert Elo to equivalent scoring points at the fitted logistic scale.
                elo_points=(elo-1500)*math.log(10)/400*config['scoring']['scale']
                power=config['eloWeight']*elo_points+(1-config['eloWeight'])*(o+d)
                wins=sum((g['hs']>g['as'])==(g['home']==tid) for g in gs)
                pf=[g['hs'] if g['home']==tid else g['as'] for g in gs];pa=[g['as'] if g['home']==tid else g['hs'] for g in gs]
                sos=[sum(rating['ratings'][g['away'] if g['home']==tid else g['home']]) for g in fg]
                rows.append({**t,'offense':round(o,3),'defense':round(d,3),'power':round(power,3),'elo':round(elo,2),'wins':wins,'losses':len(gs)-wins,'games':len(gs),'modelGames':len(fg),'pf':round(statistics.mean(pf),2) if pf else None,'pa':round(statistics.mean(pa),2) if pa else None,'sos':round(statistics.mean(sos),3) if sos else None,**box_summary(gs,tid,boxes[year])})
            rows.sort(key=lambda r:(-r['power'],r['name']))
            for i,r in enumerate(rows):r.update(rank=i+1,change=previous_ranks.get(r['id'],i+1)-(i+1))
            previous_ranks={r['id']:r['rank'] for r in rows}
            snapshots[str(week)]={'teams':rows,'mu':rating['mu'],'gamesUsed':len(past),'modelGames':sum(g['fbs'] for g in past),'through':max((g['date'] for g in past),default=None)}
        dump(f'{year}.json',{'season':year,'weeks':seasons[year]['weeks']+[99],'snapshots':snapshots,'games':seasons[year]['games'],'predictions':[p for p in predictions if p['season']==year]})
    manifest={'name':'Saturday Lab','version':'1.0.0','generatedAt':datetime.now(timezone.utc).isoformat(),'seasons':YEARS,'latestSeason':2026,'audit':audit,'sources':[{'kind':kind,'url':f'{BASE}{r}/{name}_{{year}}.csv'} for kind,(r,name) in SOURCES.items()],'config':config}
    dump('manifest.json',manifest)
    with open(out/'predictions.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(predictions[0]));w.writeheader();w.writerows(predictions)
    (ROOT/'analytics'/'model-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',default=str(ROOT/'analytics'/'raw'));args=p.parse_args()
    teams,seasons,boxes,audit=load_data(Path(args.data));print('Loaded',audit,flush=True)
    lock=ROOT/'analytics'/'locked-config.json'
    if lock.exists():
        frozen=json.loads(lock.read_text());config=frozen['config'];candidates=frozen['candidates']
        ec,sc=config['elo'],config['scoring']
        ep,es=elo_run(teams,seasons,ec['k'],ec['home'],ec['carry'])
        sp,ss=score_run(teams,seasons,sc['shrinkage'],sc['home'],sc['decay'])
        print('Using versioned, locked hyperparameters; no holdout tuning',flush=True)
    else:
        config,candidates,ep,es,sp,ss=choose_models(teams,seasons)
        lock.write_text(json.dumps({'config':config,'candidates':candidates,'selectedOn':'2023','version':'1.0.0'},indent=2),encoding='utf-8')
    report=export(teams,seasons,boxes,audit,config,candidates,ep,es,sp,ss)
    print('Holdout',report['holdout'],flush=True)
if __name__=='__main__':main()

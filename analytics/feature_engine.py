"""Causal feature engine for the final unified model.
No random splits. Yearly nested tuning never uses that target year. Only past weeks enter ratings.
"""
import argparse, json, math, hashlib
from pathlib import Path
from datetime import datetime
import numpy as np
from pipeline import ROOT, YEARS, load_data, ridge_fit, score_run, elo_run, metrics, sigmoid, number

NAMES=['scoring_margin','elo_delta','passing_efficiency','rushing_efficiency','third_down','turnover_control','play_volume','completion_rate','first_down_rate','penalty_discipline','fourth_down','possession_time','recent_form','schedule_strength','experience_interaction','rest_days','passing_matchup','rushing_matchup']
# Prespecified independently of v1's 2023 search. These parameters are not tuned here.
BASE={'shrinkage':5.,'home':3.,'decay':.94,'scale':8.}
BUNDLES={'scoring':[0], 'scoring_elo':[0,1], 'core_efficiency':list(range(7)), 'full_efficiency':list(range(12)), 'context':list(range(16)), 'matchup':list(range(18))}
RIDGES=[1.,10.,100.]

def values(b):
    from box_export import parse
    d=parse(b,0)
    if d is None:return [None]*10
    return [d[k] for k in ('passYpa','rushYpa','thirdRate','turnoverRate','plays','completionRate','firstDownRate','penaltyRate','fourthRate','possessionMinutes')]

def box_fit(history, ids, prior, carry=.65):
    """Joint offense/opponent-defense ridge for each metric; missing pairs omitted."""
    result={t:[] for t in ids}
    for j in range(10):
        hs=[{**g,'hs':g['hv'][j],'as':g['av'][j]} for g in history if g['hv'][j] is not None and g['av'][j] is not None]
        pr={t:(v[j*2],v[j*2+1]) for t,v in prior.items()}
        # Center input first because ridge_fit's intercept prior is points-specific.
        center=[7.,4.,.4,.025,68.,.6,.3,.7,.5,30.][j]
        hs=[{**g,'hs':g['hs']-center+28,'as':g['as']-center+28} for g in hs]
        o,d,_=ridge_fit(hs,ids,pr,5.,0.,.94,carry=carry)
        for i,t in enumerate(ids): result[t].extend([float(o[i]),float(d[i])])
    return result

def features(a,b,location,date=None):
    margin=a['basePower']-b['basePower']+3*location
    x=[margin,a['elo']-b['elo']+55*location]
    for j in range(10):
        sign=-1 if j in (3,7) else 1
        x.append(sign*(sum(a['box'][j*2:j*2+2])-sum(b['box'][j*2:j*2+2])))
    def rest(t):
        if not date or not t['lastDate']: return 7.
        return max(3.,min(21.,(datetime.fromisoformat(date.replace('Z','+00:00'))-datetime.fromisoformat(t['lastDate'].replace('Z','+00:00'))).total_seconds()/86400))
    x += [a['form']-b['form'],a['sos']-b['sos'],margin*(min(a['sample'],b['sample'])/12),rest(a)-rest(b),a['box'][0]*b['box'][1]-b['box'][0]*a['box'][1],a['box'][2]*b['box'][3]-b['box'][2]*a['box'][3]]
    return x

def build(teams,seasons,boxes,carry=.65):
    print('Building frozen-week ratings and opponent-adjusted box features',flush=True)
    sp,ss=score_run(teams,seasons,5.,3.,.94,carry=carry); ep,es=elo_run(teams,seasons,40,55,carry)
    rows=[]; snapshots={}; prior={}
    for year in YEARS:
        ids=list(teams[year]); history=[]
        for seq,week in enumerate(seasons[year]['weeks']+[99]):
            box=box_fit(history,ids,prior,carry=carry); ratings=ss[(year,week)]['ratings']; state={}
            for t in ids:
                gs=[g for g in history if t in (g['home'],g['away'])]
                form=[]; sos=[]
                for g in gs:
                    home=g['home']==t; opp=g['away'] if home else g['home']; strength=sum(ratings[opp]); sos.append(strength)
                    form.append((g['hs']-g['as'])*(1 if home else -1)+strength-(0 if g['neutral'] else 3*(1 if home else -1)))
                prior_weeks=set(seasons[year]['weeks'][:seq])
                last_date=max((g['date'] for g in seasons[year]['games'] if g['week'] in prior_weeks and t in (g['home'],g['away'])),default=None)
                state[t]={'offense':ratings[t][0],'defense':ratings[t][1],'mu':ss[(year,week)]['mu'],'basePower':sum(ratings[t]),'elo':es[(year,week)][t],'box':box[t],'form':sum(form[-3:])/(len(form[-3:])+3),'sos':sum(sos)/(len(sos)+3),'sample':len(gs),'lastDate':last_date}
            snapshots[f'{year}:{week}']=state
            if week==99: prior=box; break
            batch=[g for g in seasons[year]['games'] if g['week']==week and g['fbs']]
            cutoff=min(g['date'] for g in seasons[year]['games'] if g['week']==week)
            assert all(g['date']<cutoff for g in history)
            for g in batch:
                x=features(state[g['home']],state[g['away']],0 if g['neutral'] else 1,g['date'])
                rows.append({**g,'x':x,'y':int(g['hs']>g['as']),'baseMargin':sp[g['id']]['margin'],'homeScore':sp[g['id']]['homeScore'],'awayScore':sp[g['id']]['awayScore'],'cutoff':cutoff})
            for g in batch: history.append({**g,'seq':seq,'hv':values(boxes[year].get((g['id'],g['home']))),'av':values(boxes[year].get((g['id'],g['away'])))})
        print('Features',year,flush=True)
    return rows,snapshots

def fit(rows,indices,penalty):
    x=np.array([r['x'] for r in rows])[:,indices]; y=np.array([r['y'] for r in rows])
    # Antisymmetric features with no intercept guarantee P(A>B)=1-P(B>A).
    scale=np.sqrt(np.mean(x*x,axis=0)); scale=np.maximum(scale,1e-6); z=x/scale
    beta=np.zeros(len(indices))
    for _ in range(60):
        p=sigmoid(z@beta); gradient=z.T@(p-y)+penalty*beta
        hessian=(z.T*(p*(1-p)))@z+penalty*np.eye(len(indices))
        step=np.linalg.solve(hessian,gradient); beta-=step
        if max(abs(step))<1e-9: break
    full=np.zeros(len(NAMES)); full[indices]=beta/scale
    return full

def evaluate(rows,coef): return metrics(sigmoid(np.array([r['x'] for r in rows])@coef),[r['y'] for r in rows])

import unittest,copy,json,math
from pathlib import Path
import numpy as np
import pipeline as m

class MathematicsTests(unittest.TestCase):
    def setUp(self):
        self.old=m.YEARS;m.YEARS=[2018]
        self.teams={2018:{'a':{},'b':{},'c':{},'d':{}}}
        def game(i,w,h,a,hs,aws,neutral=False):return {'id':i,'week':w,'home':h,'away':a,'hs':hs,'as':aws,'neutral':neutral,'fbs':True,'date':f'2018-09-{w*7:02}T12:00Z','seq':w}
        self.games=[game('1',1,'a','b',30,10),game('2',1,'c','d',17,14),game('3',2,'a','c',24,21),game('4',2,'b','d',7,20),game('5',3,'a','d',21,28)]
        self.seasons={2018:{'games':self.games,'weeks':[1,2,3]}}
    def tearDown(self):m.YEARS=self.old
    def test_future_outcomes_do_not_change_earlier_predictions(self):
        original,_=m.score_run(self.teams,self.seasons,2,2,1)
        altered=copy.deepcopy(self.seasons)
        for g in altered[2018]['games']:
            if g['week']>=2:g['hs']=99;g['as']=0
        changed,_=m.score_run(self.teams,altered,2,2,1)
        for gid in ('1','2','3','4'):self.assertEqual(original[gid],changed[gid])
        ep,_=m.elo_run(self.teams,self.seasons,64,40,.75)
        eq,_=m.elo_run(self.teams,altered,64,40,.75)
        for gid in ('1','2','3','4'):self.assertEqual(ep[gid],eq[gid])
    def test_same_week_order_does_not_change_predictions(self):
        reordered=copy.deepcopy(self.seasons);reordered[2018]['games'].reverse()
        p,_=m.elo_run(self.teams,self.seasons,64,40,.75)
        q,_=m.elo_run(self.teams,reordered,64,40,.75)
        self.assertEqual(p,q)
        p,_=m.score_run(self.teams,self.seasons,2,2,1)
        q,_=m.score_run(self.teams,reordered,2,2,1)
        for gid in p:self.assertAlmostEqual(p[gid]['margin'],q[gid]['margin'],places=9)
    def test_neutral_preseason_is_symmetric(self):
        s=copy.deepcopy(self.seasons)
        for g in s[2018]['games']:g['neutral']=True
        p,_=m.score_run(self.teams,s,2,2,1)
        e,_=m.elo_run(self.teams,s,64,40,.75)
        self.assertEqual(p['1']['margin'],0);self.assertEqual(e['1'],.5)
    def test_ridge_matches_independent_linear_algebra(self):
        ids=['a','b','c','d'];n=len(ids);idx={t:i for i,t in enumerate(ids)};lam=2;h=2
        o,d,mu=m.ridge_fit(self.games,ids,{},lam,h,1)
        x=[];y=[]
        for g in self.games:
            for a,b,score,sign in [(g['home'],g['away'],g['hs'],1),(g['away'],g['home'],g['as'],-1)]:
                row=np.zeros(2*n+1);row[idx[a]]=1;row[n+idx[b]]=-1;row[-1]=1
                x.append(row);y.append(score-sign*h/2)
        for i in range(2*n):
            row=np.zeros(2*n+1);row[i]=math.sqrt(lam);x.append(row);y.append(0)
        row=np.zeros(2*n+1);row[-1]=math.sqrt(20);x.append(row);y.append(28*math.sqrt(20))
        answer=np.linalg.lstsq(np.array(x),np.array(y),rcond=None)[0]
        np.testing.assert_allclose(np.r_[o,d,mu],answer,atol=1e-5)
    def test_scoring_rules_known_values(self):
        metrics=m.metrics([.5,.5],[0,1]);self.assertEqual(metrics['brier'],.25);self.assertAlmostEqual(metrics['logLoss'],math.log(2))
        metrics=m.metrics([0,1],[0,1]);self.assertEqual(metrics['brier'],0);self.assertEqual(metrics['accuracy'],1)

class ExportTests(unittest.TestCase):
    def test_export_coverage_cutoffs_and_holdout_metrics(self):
        root=Path(__file__).resolve().parents[1]/'public'/'data';hold=[]
        manifest=json.loads((root/'manifest.json').read_text())
        for audit in manifest['audit']:
            data=json.loads((root/f"{audit['season']}.json").read_text())
            self.assertEqual(len(data['predictions']),audit['modelGames'])
            self.assertEqual(len({p['id'] for p in data['predictions']}),len(data['predictions']))
            for p in data['predictions']:
                self.assertTrue(0<p['prob']<1);self.assertLessEqual(p['cutoff'],p['date'])
            for i,week in enumerate(data['weeks']):
                snap=data['snapshots'][str(week)];allowed=set(data['weeks'][:i]);past=[g for g in data['games'] if g['week'] in allowed]
                self.assertEqual(snap['gamesUsed'],len(past))
                self.assertEqual(len(snap['teams']),audit['teams'])
                self.assertEqual(sorted(t['rank'] for t in snap['teams']),list(range(1,audit['teams']+1)))
                self.assertEqual(snap['through'],max((g['date'] for g in past),default=None))
                for t in snap['teams']:
                    own=[g for g in past if t['id'] in (g['home'],g['away'])]
                    self.assertEqual(t['games'],len(own));self.assertEqual(t['wins']+t['losses'],len(own))
            if data['season'] in (2024,2025):hold+=data['predictions']
        report=json.loads((root/'report.json').read_text())
        self.assertEqual(len(hold),1606)
        protocol=json.loads((root/'model.json').read_text())
        self.assertEqual(protocol['candidateCount'],96)
        self.assertEqual(protocol['earlierCandidateCounts'],[432,576,1056])
        brier=sum((p['prob']-p['outcome'])**2 for p in hold)/len(hold)
        self.assertAlmostEqual(brier,report['holdout']['brier'],places=12)
        self.assertEqual(report['config']['eloWeight'],0)

if __name__=='__main__':unittest.main(verbosity=2)

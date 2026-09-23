import unittest,json,copy,itertools
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
import feature_engine as f
import redesign as r4
import ranking_review as r5
import pipeline
from box_export import parse
ROOT=Path(__file__).resolve().parents[1]

class FinalModelTests(unittest.TestCase):
 def test_logistic_fit_against_independent_optimizer(self):
  rng=np.random.default_rng(42);x=rng.normal(size=(100,18));y=rng.integers(0,2,100)
  rows=[{'x':a.tolist(),'y':int(b)} for a,b in zip(x,y)];idx=[0,2,3,5];lam=10
  coef=f.fit(rows,idx,lam);z=x[:,idx];scale=np.sqrt(np.mean(z*z,axis=0));z/=scale
  def objective(b):return np.sum(np.logaddexp(0,z@b)-y*(z@b))+lam/2*np.sum(b*b)
  res=minimize(objective,np.zeros(4),method='BFGS',tol=1e-8)
  np.testing.assert_allclose(coef[idx],res.x/scale,atol=1e-6)
 def test_future_box_and_scores_cannot_change_earlier_features(self):
  old=f.YEARS;oldp=pipeline.YEARS;f.YEARS=[2018];pipeline.YEARS=[2018]
  try:
   teams={2018:{'a':{},'b':{}}};gs=[{'id':str(w),'week':w,'home':'a','away':'b','hs':20+w,'as':10,'neutral':False,'fbs':True,'date':f'2018-09-{w*7:02}T12:00Z','season':2018} for w in (1,2,3)]
   seasons={2018:{'games':gs,'weeks':[1,2,3]}};boxes={2018:{(str(w),t):{'netPassingYards':'200','completionAttempts':'15/25','rushingYards':'120','rushingAttempts':'30','thirdDownEff':'4-12','turnovers':'1'} for w in (1,2,3) for t in ('a','b')}}
   original,_=f.build(teams,seasons,boxes);altered=copy.deepcopy(seasons);changed=copy.deepcopy(boxes)
   for g in altered[2018]['games']:
    if g['week']>=2:g['hs']=90;g['as']=0;changed[2018][(g['id'],'a')]['netPassingYards']='999'
   after,_=f.build(teams,altered,changed)
   for i in (0,1):self.assertEqual(original[i]['x'],after[i]['x'])
  finally:f.YEARS=old;pipeline.YEARS=oldp
 def test_missing_and_zero_denominators_are_not_fabricated(self):
  self.assertIsNone(parse(None,0));d=parse({'completionAttempts':'0/0','fourthDownEff':'0-0'},7)
  self.assertIsNone(d['completionRate']);self.assertIsNone(d['fourthRate']);self.assertIsNone(d['turnovers'])
  self.assertEqual(f.values({'completionAttempts':'0/0','fourthDownEff':'0-0'}),[None]*10)
 def test_published_probabilities_reproduce_from_snapshots(self):
  report=json.loads((ROOT/'public/data/model.json').read_text());lookup={p['id']:p for p in report['predictions']}
  for year in range(2023,2027):
   data=json.loads((ROOT/f'public/data/{year}.json').read_text());config=data['model'];coef=np.array(config['coefficients'])
   self.assertEqual(config['trainingThrough'],year-1)
   annual=report['annual'][str(year)];self.assertTrue(all(y<year for y in annual['validationYears']))
   candidates=next(s['candidates'] for s in report['searches'] if s['targetSeason']==year);self.assertEqual(len(candidates),report['candidateCount']);self.assertEqual(annual['selected'],min(candidates,key=lambda c:c['logLoss']))
   for p in data['predictions']:
    snap=data['snapshots'][str(p['week'])];teams={t['id']:t for t in snap['teams']};a=teams[p['home']]['modelState'];b=teams[p['away']]['modelState'];loc=0 if p['neutral'] else 1
    feature=(lambda aa,bb,ll,dd:r5.features(aa,bb,ll,'prior',dd)) if 'q' in a else r4.features; x=np.array(feature(a,b,loc,p['date']));prob=config['weight']*pipeline.sigmoid(x@coef)+(1-config['weight'])*pipeline.sigmoid(x[0]/8)
    self.assertAlmostEqual(prob,p['prob'],places=12);self.assertAlmostEqual(prob,lookup[p['id']]['prob'],places=12)
    np.testing.assert_allclose(x,-np.array(feature(b,a,-loc,p['date'])),atol=1e-12)
    self.assertLess(a['lastDate'] or '',p['cutoff']);self.assertLess(b['lastDate'] or '',p['cutoff'])
   latest=data['snapshots']['99']['teams'];self.assertEqual(sorted(t['modelRank'] for t in latest),list(range(1,len(latest)+1)))
   self.assertAlmostEqual(np.mean([t['winIndex'] for t in latest]),.5,places=12)
 def test_fixture_coverage_and_game_boxes(self):
  fixtures=json.loads((ROOT/'public/data/fixtures.json').read_text());self.assertEqual(fixtures['teamsCovered'],138);self.assertEqual(fixtures['failedTeams'],[])
  self.assertEqual(len({g['id'] for g in fixtures['games']}),len(fixtures['games']))
  for year in range(2018,2027):
   box=json.loads((ROOT/f'public/data/box-{year}.json').read_text());self.assertEqual(len(box['definitions']),30)
   for row in box['rows']:
    for key,(a,b) in box['ratios'].items():
     d=row['own'];expected=d[a]/d[b] if d[a] is not None and d[b] else None
     self.assertEqual(d[key],expected)

if __name__=='__main__':unittest.main(verbosity=2)

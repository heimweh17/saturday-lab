import unittest,copy,json
import numpy as np
from scipy.optimize import minimize
import redesign as r
class RedesignTests(unittest.TestCase):
 def test_logistic_independent_optimizer(self):
  rng=np.random.default_rng(6);x=rng.normal(size=(150,13));y=rng.integers(0,2,150);idx=r.BUNDLES['epa_talent'];penalty=10.;b=r.fit(x,y,idx,penalty);scale=np.sqrt(np.mean(x[:,idx]**2,axis=0));z=x[:,idx]/scale
  q=minimize(lambda beta:np.sum(np.logaddexp(0,z@beta)-y*(z@beta))+penalty/2*np.sum(beta**2),np.zeros(len(idx)),method='BFGS',tol=1e-8)
  np.testing.assert_allclose(b[idx],q.x/scale,atol=1e-6)
 def test_new_score_history_is_causal(self):
  original=r.YEARS;r.YEARS=[2018]
  try:
   teams={2018:{'a':{},'b':{}}};games=[{'id':str(w),'week':w,'home':'a','away':'b','hs':20+w,'as':10,'neutral':False,'fbs':True,'date':f'2018-09-{w*7:02}T12:00Z','season':2018} for w in [1,2,3]];seasons={2018:{'weeks':[1,2,3],'games':games}};changed=copy.deepcopy(seasons);changed[2018]['games'][1]['hs']=99
   for cfg in r.CONFIGS:
    first=r.scoring(teams,seasons,cfg);second=r.scoring(teams,changed,cfg);self.assertEqual(first['2018:1'],second['2018:1']);self.assertEqual(first['2018:2'],second['2018:2']);self.assertNotEqual(first['2018:3'],second['2018:3'])
  finally:r.YEARS=original
 def test_future_epa_cannot_change_pregame_units(self):
  import tempfile,csv
  import pandas as pd
  from pathlib import Path
  oldyears,olddata=r.YEARS,r.DATA
  try:
   with tempfile.TemporaryDirectory() as folder:
    r.YEARS=[2018];r.DATA=Path(folder);pd.DataFrame([{'team_id':t,'talent_composite':100.,'blue_chip_ratio':.1} for t in ['a','b']]).to_parquet(r.DATA/'cfb_team_talent_2018.parquet')
    games=[{'id':str(w),'week':w,'home':'a','away':'b','hs':21,'as':14,'neutral':False,'fbs':True,'date':f'2018-09-{w*7:02}T12:00Z','season':2018} for w in [1,2,3]];seasons={2018:{'weeks':[1,2,3],'games':games}};teams={2018:{'a':{},'b':{}}};boxes={2018:{}};raw=[{'game_id':str(w),'team_id':t,'EPA_per_play':.1 if t=='a' else -.1,'EPA_passing_per_play':.1,'EPA_rushing_per_play':.1,'EPA_sp':1.} for w in [1,2,3] for t in ['a','b']]
    def write():
     with (r.DATA/'adv_team_gamelog_2018.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(raw[0]));w.writeheader();w.writerows(raw)
    write();before,_=r.unit_states(teams,seasons,boxes)
    for item in raw:
     if item['game_id']=='2' and item['team_id']=='a':item['EPA_per_play']=99.
    write();after,_=r.unit_states(teams,seasons,boxes)
    self.assertEqual(before['2018:1'],after['2018:1']);self.assertEqual(before['2018:2'],after['2018:2']);self.assertNotEqual(before['2018:3'],after['2018:3'])
  finally:r.YEARS,r.DATA=oldyears,olddata
 def test_compression_preserves_total_and_is_symmetric(self):
  for method in ['raw','cap28','soft28']:
   a=r.transformed({'hs':70,'as':7},method);b=r.transformed({'hs':7,'as':70},method)
   self.assertAlmostEqual(a['hs']+a['as'],77);self.assertAlmostEqual(a['hs'],b['as'])
   if method!='raw':self.assertLessEqual(abs(a['hs']-a['as']),28)
 def test_fpi_actual_timestamps_precede_cutoff(self):
  pairs=json.loads((r.ROOT/'public/data/fpi-paired-audit.json').read_text());self.assertGreater(len(pairs),2000)
  for p in pairs:self.assertLess(p['homeFpiTimestamp'],p['cutoff']);self.assertLess(p['awayFpiTimestamp'],p['cutoff'])
 def test_missing_talent_is_explicit_and_not_zero(self):
  d=json.loads((r.ROOT/'public/data/2026.json').read_text());h=next(t for t in d['snapshots']['99']['teams'] if t['id']=='62')['modelState'];self.assertTrue(h['talentMissing']);self.assertGreater(h['v'][6],0)
 def test_all_candidate_choices_follow_validation(self):
  report=json.loads((r.ROOT/'public/data/model.json').read_text())
  for year,a in report['annual'].items():
   search=next(s for s in report['searches'] if s['targetSeason']==int(year));self.assertEqual(len(search['candidates']),288);self.assertEqual(a['selected'],min(search['candidates'],key=lambda c:c['logLoss']));self.assertEqual(a['trainingThrough'],int(year)-1);self.assertEqual(a['validationYears'],list(range(int(year)-3,int(year))))
if __name__=='__main__':unittest.main()

import copy,json,unittest
import numpy as np
import ranking_review as r

class RankingReviewTests(unittest.TestCase):
 def test_weighted_ridge_matches_independent_normal_equations(self):
  ids=['a','b','c'];prior={'a':(2.,1.),'b':(-2.,-1.),'c':(3.,-2.)};lam=2.;carry=.35
  games=[dict(home='a',away='b',neutral=False,modelHome=30.,modelAway=20.,weight=.4,seq=0),dict(home='c',away='a',neutral=True,modelHome=25.,modelAway=28.,weight=1.,seq=1)]
  o,d,mu=r.fit_rating(games,ids,prior,lam,3.,carry)
  X=[];Y=[];W=[]
  for g in games:
   for atk,df,score,adv in [(g['home'],g['away'],g['modelHome'],0 if g['neutral'] else 1.5),(g['away'],g['home'],g['modelAway'],0 if g['neutral'] else -1.5)]:
    row=np.zeros(7);row[ids.index(atk)]=1;row[3+ids.index(df)]=-1;row[6]=1;X.append(row);Y.append(score-adv);W.append(g['weight']*.97**(1-g['seq']))
  X=np.array(X);Y=np.array(Y);W=np.array(W);penalty=np.diag([lam]*6+[20.]);target=np.array([prior[t][0]*carry for t in ids]+[prior[t][1]*carry for t in ids]+[28.])
  expected=np.linalg.solve(X.T@(W[:,None]*X)+penalty,X.T@(W*Y)+penalty@target)
  np.testing.assert_allclose(np.r_[o,d,mu],expected,atol=1e-6)

 def test_stronger_opponent_receives_more_credit(self):
  ids=['team','strong','weak'];prior={'strong':(15.,15.),'weak':(-15.,-15.)}
  def rating(opponent):
   g=dict(home='team',away=opponent,neutral=True,modelHome=30.,modelAway=20.,weight=1.,seq=0)
   o,d,_=r.fit_rating([g],ids,prior,2.,0.,.65);return o[0]+d[0]
  self.assertGreater(rating('strong'),rating('weak'))

 def test_future_scores_epa_and_dates_do_not_change_earlier_state(self):
  original=r.YEARS;r.YEARS=[2018]
  try:
   teams={2018:{'a':{},'b':{}}};tal={2018:{'a':[.2,.1,False],'b':[-.2,-.1,False]}}
   gs=[dict(id=str(w),season=2018,week=w,home='a',away='b',hs=25,**{'as':20},neutral=False,fbs=True,date=f'2018-09-{w*7:02}T12:00Z',units=[[.1,1.],[-.1,-1.]]) for w in [1,2,3]]
   seasons={2018:{'weeks':[1,2,3],'games':gs}};changed=copy.deepcopy(seasons);changed[2018]['games'][1]['hs']=99;changed[2018]['games'][1]['units'][0]=[9.,99.]
   for cfg in r.CONFIGS:
    before=r.build(teams,seasons,tal,cfg);after=r.build(teams,changed,tal,cfg)
    self.assertEqual(before['2018:1'],after['2018:1']);self.assertEqual(before['2018:2'],after['2018:2']);self.assertNotEqual(before['2018:3'],after['2018:3'])
  finally:r.YEARS=original

 def test_scalar_features_are_transitive_and_sample_independent(self):
  rng=np.random.default_rng(42)
  states=[dict(q=rng.normal(size=6).tolist(),calendar=i,sample=i,lastDate=None) for i in [1,2,3]]
  a,b,c=states
  for bundle in r.BUNDLES:
   np.testing.assert_allclose(np.array(r.features(a,b,0,bundle))+r.features(b,c,0,bundle),r.features(a,c,0,bundle),atol=1e-14)
   self.assertEqual(r.features(a,b,0,bundle),r.features({**a,'sample':100},b,0,bundle))

 def test_constrained_fit_cannot_reward_worse_strength(self):
  rng=np.random.default_rng(23);x=rng.normal(size=(300,8));y=(x[:,0]<0).astype(float)
  coef=r.fit(x,y,list(range(8)),1.)
  self.assertTrue(np.all(coef[:7]>=0));self.assertAlmostEqual(coef[0],0.,places=8)

 def test_selected_annual_configuration_uses_only_earlier_validation(self):
  if not r.CACHE.exists():self.skipTest('Research search still running')
  report=json.loads(r.CACHE.read_text())['report']
  for year,a in report['annual'].items():
   candidates=next(s['candidates'] for s in report['searches'] if s['targetSeason']==int(year))
   self.assertEqual(len(candidates),432);self.assertEqual(a['selected']['logLoss'],min(c['logLoss'] for c in candidates));self.assertEqual(a['trainingThrough'],int(year)-1)
   self.assertEqual(a['validationYears'],list(range(int(year)-3,int(year))))
if __name__=='__main__':unittest.main()

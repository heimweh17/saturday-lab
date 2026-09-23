import copy,json,unittest
import numpy as np
import ranking_review as r
from prior_review import CACHE

class PriorReviewTests(unittest.TestCase):
 def test_prior_is_updated_by_games_not_calendar_decay(self):
  ids=['a','b'];shift={'a':6.,'b':-6.}
  o,d,_=r.fit_rating([],ids,{},2.,0.,.65,prior_shift=shift)
  np.testing.assert_allclose(o+d,[6.,-6.])
  game=dict(home='a',away='b',neutral=True,modelHome=28.,modelAway=28.,weight=1.,seq=0)
  o2,d2,_=r.fit_rating([game]*12,ids,{},2.,0.,.65,prior_shift=shift)
  self.assertLess(abs(o2[0]+d2[0]),abs(o[0]+d[0]))
  same=r.fit_rating([{**game,'seq':99}]*12,ids,{},2.,0.,.65,prior_shift=shift)
  np.testing.assert_allclose(o2,same[0]);np.testing.assert_allclose(d2,same[1])

 def test_selected_model_has_no_direct_recruiting_or_sample_bonus(self):
  if not CACHE.exists():self.skipTest('Search still running')
  report=json.loads(CACHE.read_text())['report']
  for year,a in report['annual'].items():
   self.assertEqual(a['coefficients'][4:6],[0.,0.]);self.assertNotIn('calendar',a['selected']['bundle'])
   cs=next(s['candidates'] for s in report['searches'] if s['targetSeason']==int(year))
   self.assertEqual(len(cs),576);self.assertEqual(a['selected']['logLoss'],min(c['logLoss'] for c in cs))
   self.assertEqual(a['trainingThrough'],int(year)-1)

 def test_published_decomposition_adds_to_index_change(self):
  data=json.loads((r.ROOT/'public/data/2026.json').read_text())
  if data['model']['version']!='5.0.0':self.skipTest('New model not exported yet')
  previous={}
  for week in data['weeks']:
   for t in data['snapshots'][str(week)]['teams']:
    if previous:
     e=t['ratingExplanation'];self.assertAlmostEqual(e['ownIndexChange']+e['fieldIndexChange'],t['winIndex']-previous[t['id']],places=12)
   previous={t['id']:t['winIndex'] for t in data['snapshots'][str(week)]['teams']}
if __name__=='__main__':unittest.main()

import copy,json,unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import pandas as pd
import cohort_review as c
import qb_review as q

class CohortAndPasserTests(unittest.TestCase):
 def test_talent_standardization_preserves_order_and_missingness(self):
  result=c.standardize({'11':[2.,.1],'22':[3.,.3],'d':[4.,.5],'missing':None},['11','22','d','missing'])
  self.assertLess(result['11'][0],result['22'][0]);self.assertLess(result['22'][0],result['d'][0]);self.assertEqual(result['missing'],[0.,0.,True]);self.assertAlmostEqual(np.mean([result[t][0] for t in ['11','22','d']]),0.,places=12)

 def test_passer_schema_variants_and_malformed_rows(self):
  a={'athlete_id':1,'completions/passingAttempts':'20/30','passingYards':'250','passingTouchdowns':'2','interceptions':'1'}
  b={'athlete_id':1,'stat_1':'20/30','stat_2':'250','stat_4':'2','stat_5':'1'}
  self.assertEqual(q.parse_passer(a),q.parse_passer(b));self.assertEqual(q.parse_passer(a)['adjustedYards'],245.)
  self.assertIsNone(q.parse_passer({**a,'completions/passingAttempts':'35/30'}));self.assertIsNone(q.parse_passer({**a,'passingYards':None}));self.assertIsNone(q.parse_passer({**b,'stat_5':'--'}))

 def test_current_future_passer_cannot_change_earlier_membership(self):
  teams={y:{'11':{},'22':{}} for y in [2018,2019]};seasons={};boxes={};frames={}
  for year in teams:
   weeks=[1] if year==2018 else [1,2];games=[];rows=[];boxes[year]={}
   for week in weeks:
    gid=str(year*10+week);games.append({'id':gid,'week':week,'date':f'{year}-09-{week*7:02}T12:00Z','home':'11','away':'22','fbs':True})
    for t,aid,yards in [('11',1,300),('22',2,100)]:
     rows.append({'game_id':int(gid),'team_id':t,'athlete_id':aid,'category':'passing','completions/passingAttempts':'20/30','passingYards':str(yards),'passingTouchdowns':'1','interceptions':'0'})
     boxes[year][(gid,t)]={'completionAttempts':'20/30'}
   frames[year]=pd.DataFrame(rows);seasons[year]={'weeks':weeks,'games':games}
  old=q.YEARS;q.YEARS=[2018,2019]
  try:
   with patch.object(q.pd,'read_parquet',side_effect=lambda path:frames[int(Path(path).stem[-4:])].copy()):
    before,_=q.passer_states(teams,seasons,boxes)
    frames[2019].loc[(frames[2019].game_id==20192)&(frames[2019].team_id=='11'),'athlete_id']=99
    after,_=q.passer_states(teams,seasons,boxes)
   self.assertEqual(before['2019:1']['11']['values'],[0.,0.]);self.assertEqual(before['2019:2'],after['2019:2']);self.assertNotEqual(before['2019:99']['11']['values'],after['2019:99']['11']['values'])
  finally:q.YEARS=old

 def test_hierarchical_selection_is_earlier_only(self):
  if not q.CACHE.exists():self.skipTest('Final experiment still running')
  report=json.loads(q.CACHE.read_text())['report']
  for year,a in report['annual'].items():
   search=next(s for s in report['searches'] if s['targetSeason']==int(year));self.assertEqual(len(search['candidates']),96);self.assertEqual(a['selected']['logLoss'],min(v['logLoss'] for v in search['candidates']));self.assertEqual(a['trainingThrough'],int(year)-1)
   self.assertTrue(all(y<int(year) for y in a['validationYears']));self.assertEqual(a['coefficients'][4:6],[0.,0.])
if __name__=='__main__':unittest.main()

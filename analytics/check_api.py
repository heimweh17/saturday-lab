"""Read-only service integration checks. Usage: python analytics/check_api.py URL"""
import json,math,sys,urllib.request,urllib.error
base=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:5173'
def get(path):
    with urllib.request.urlopen(base+path) as r:return json.load(r)
q='/api/matchup?season=2026&week=99&'
a=get(q+'a=194&b=333&venue=neutral')['prediction']
b=get(q+'a=333&b=194&venue=neutral')['prediction']
h=get(q+'a=194&b=333&venue=a')['prediction']
assert abs(a['probability']+b['probability']-1)<1e-12
assert abs(a['margin']+b['margin'])<1e-12
assert abs(h['margin']-a['margin']-3)<1e-12
assert h['probability']>a['probability']
for query in ['a=194&b=194','a=missing&b=333','a=194&b=333&venue=invalid']:
    try:get(q+query);raise AssertionError('Expected validation failure')
    except urllib.error.HTTPError as e:assert e.code==400
for path in ['/api/ratings?season=__proto__&week=constructor','/api/matchup?season=2026&week=constructor&a=194&b=333']:
    try:get(path);raise AssertionError('Expected invalid lookup failure')
    except urllib.error.HTTPError as e:assert e.code==400
pre=get('/api/ratings?season=2026&week=1')['snapshot'];assert pre['through'] is None
assert get('/api/health')['status']=='ok'
print('PASS: service symmetry, home advantage, invalid inputs, preseason cutoff, health')

"""Make a small server-only ratings index from exported snapshots."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
index={}
for year in range(2018,2027):
    d=json.loads((root/'public'/'data'/f'{year}.json').read_text())
    index[str(year)]={}
    for week,s in d['snapshots'].items():
        index[str(year)][week]={'mu':s['mu'],'through':s['through'],'teams':[{k:t[k] for k in ('id','name','offense','defense','elo','power','rank')} for t in s['teams']]}
(root/'lib'/'model-index.json').write_text(json.dumps(index,separators=(',',':')),encoding='utf-8')
print('Wrote service index')

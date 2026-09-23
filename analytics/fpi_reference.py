"""Capture the public ESPN FPI table as a dated external ranking reference.
Never use this current snapshot in historical prediction features.
"""
import json,re,hashlib,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
URL='https://www.espn.co.uk/college-football/fpi/_/season/2026'
def main():
    raw=urllib.request.urlopen(URL,timeout=30).read();s=BeautifulSoup(raw,'html.parser');tables=s.select('table');names=tables[0].select('tbody tr');values=tables[1].select('tbody tr')
    assert len(names)==len(values) and len(names)>120
    rows=[]
    for a,b in zip(names,values):
        assert a.get('data-idx')==b.get('data-idx')
        link=a.select_one('.TeamLink__Name a');cells=[c.get_text(strip=True) for c in b.select('td')]
        rows.append({'id':re.search(r'/id/(\d+)',link['href'])[1],'name':link.get_text(strip=True),'record':cells[0],'fpi':float(cells[1]),'rank':int(cells[2])})
    assert len({r['id'] for r in rows})==len(rows)
    updated=next(t for t in s.stripped_strings if t.startswith('Last Updated:'))
    report={'source':URL,'retrievedAt':datetime.now(timezone.utc).isoformat(),'sourceUpdated':updated,'sourceSha256':hashlib.sha256(raw).hexdigest(),'season':2026,'scope':'External current ranking reference only. ESPN snapshot date differs from Saturday Lab results through September 20; not a matched-time accuracy benchmark or a historical model input.','teams':rows}
    (ROOT/'public/data/fpi-reference.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(updated,next(r for r in rows if r['id']=='256'))
if __name__=='__main__':main()

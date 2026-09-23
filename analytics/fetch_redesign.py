"""Download version-locked public sources. Refuse silently revised research data."""
import hashlib,json,urllib.request,concurrent.futures
from pathlib import Path
root=Path(__file__).resolve().parents[1];folder=root/'analytics/research-v4';folder.mkdir(exist_ok=True)
sources=json.loads((root/'analytics/redesign-sources.json').read_text())
def fetch(s):
 p=folder/s['file']
 if not p.exists():p.write_bytes(urllib.request.urlopen(s['url'],timeout=60).read())
 raw=p.read_bytes();raw=raw.replace(b'\r\n',b'\n') if s.get('hashNormalization')=='CRLF to LF' else raw
 if hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Source revised: '+s['file']+'. Create a new data version before rerunning the study.')
 return s['file']
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:print('Verified',len(list(pool.map(fetch,sources))),'research files')
(folder/'sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')

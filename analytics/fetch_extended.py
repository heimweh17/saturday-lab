"""Restore hash-pinned recruiting and player-box research inputs."""
import json,hashlib,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'analytics/research-roster';target.mkdir(exist_ok=True)
sources=json.loads((ROOT/'analytics/extended-sources.json').read_text())
for row in sources:
 name=row['file'];assert Path(name).name==name
 path=target/name
 if not path.exists():
  with urllib.request.urlopen(row['url'],timeout=90) as response:path.write_bytes(response.read())
 assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],f'Source revised: {name}; do not silently replace the research version.'
# Preserve the two manifests consumed by the frozen experiment protocols.
(target/'sources.json').write_text(json.dumps([s for s in sources if not s['file'].startswith('player_box_')],indent=2),encoding='utf-8')
(target/'qb-sources.json').write_text(json.dumps([s for s in sources if s['file'].startswith('player_box_')],indent=2),encoding='utf-8')
print(f'Verified {len(sources)} extended source files.')

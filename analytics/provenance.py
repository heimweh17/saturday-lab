"""Record checksums and source URLs for the exact input files used by a release."""
import argparse,hashlib,json
from pathlib import Path
from pipeline import ROOT,SOURCES,BASE
p=argparse.ArgumentParser();p.add_argument('--data',required=True);args=p.parse_args()
files=[]
for path in sorted(Path(args.data).glob('*.csv')):
 kind,year=path.stem.split('_');release,name=SOURCES[kind]
 files.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'url':f'{BASE}{release}/{name}_{year}.csv'})
result={'rawFiles':files,'featureEngineSha256':hashlib.sha256((ROOT/'analytics/feature_engine.py').read_bytes()).hexdigest(),'modelPipelineSha256':hashlib.sha256((ROOT/'analytics/final_model.py').read_bytes()).hexdigest()}
result['redesignEngineSha256']=hashlib.sha256((ROOT/'analytics/redesign.py').read_bytes()).hexdigest()
result['redesignExporterSha256']=hashlib.sha256((ROOT/'analytics/export_redesign.py').read_bytes()).hexdigest()
result['researchSources']=json.loads((ROOT/'analytics/redesign-sources.json').read_text())
(ROOT/'public/data/provenance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Recorded',len(files),'raw source checksums')

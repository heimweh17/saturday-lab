"""Fetch published ESPN schedules; preserve source files, status and coverage."""
import json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    season=json.loads((ROOT/'public/data/manifest.json').read_text())['latestSeason']
    data=json.loads((ROOT/f'public/data/{season}.json').read_text())
    teams=data['snapshots']['99']['teams']; ids={t['id'] for t in teams}
    cache=ROOT/'analytics/raw-fixtures'; cache.mkdir(exist_ok=True)
    def fetch(t):
        url=f'https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{t}/schedule?season={season}'
        for attempt in range(3):
            try:
                raw=urllib.request.urlopen(url,timeout=40).read(); d=json.loads(raw)
                assert int(d['season']['year'])==season
                (cache/f'{t}.json').write_bytes(raw)
                return t,d
            except Exception:
                if attempt==2: raise
                time.sleep(attempt+1)
    games={}; failures=[]; covered=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs={pool.submit(fetch,t):t for t in ids}
        for future in as_completed(jobs):
            try: tid,d=future.result(); covered.append(tid)
            except Exception as e: failures.append({'team':jobs[future],'error':str(e)}); continue
            for e in d.get('events',[]):
                c=e['competitions'][0]; status=c['status']['type']; cs=c['competitors']
                if len(cs)!=2: continue
                h=next(x for x in cs if x['homeAway']=='home'); a=next(x for x in cs if x['homeAway']=='away')
                g={'id':e['id'],'date':e['date'],'week':e.get('week',{}).get('number'), 'home':h['id'],'away':a['id'],'homeName':h['team']['displayName'],'awayName':a['team']['displayName'],'neutral':c.get('neutralSite',False),'status':status['name'],'completed':status.get('completed',False),'timeValid':c.get('timeValid',False),'fbs':h['id'] in ids and a['id'] in ids,'source':f'https://www.espn.com/college-football/game/_/gameId/{e["id"]}'}
                if g['id'] in games:
                    old=games[g['id']]
                    assert (old['home'],old['away'])==(g['home'],g['away'])
                games[g['id']]=g
    result={'season':season,'fetchedAt':datetime.now(timezone.utc).isoformat(),'ratingThrough':data['snapshots']['99']['through'],'teamsExpected':len(ids),'teamsCovered':len(covered),'failedTeams':failures,'games':sorted(games.values(),key=lambda x:x['date'])}
    (ROOT/'public/data/fixtures.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
    print({'teams':len(covered),'failures':failures,'games':len(games),'remaining':sum(not g['completed'] for g in games.values())})
if __name__=='__main__': main()

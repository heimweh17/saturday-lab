"""Inspectable game-level statistics and derived rates, with explicit denominators."""
import argparse,json
from pathlib import Path
from pipeline import ROOT,YEARS,load_data,number
DEFS=[
 ('points','Points','Scoring','raw','number',True,None),('firstDowns','First downs','Scoring','raw','number',True,None),
 ('totalYards','Total yards','Offense','raw','number',True,None),('passYards','Passing yards','Passing','raw','number',True,None),('rushYards','Rushing yards','Rushing','raw','number',True,None),
 ('passCompletions','Pass completions','Passing','raw','number',True,None),('passAttempts','Pass attempts','Passing','raw','number',None,None),('rushAttempts','Rush attempts','Rushing','raw','number',None,None),
 ('plays','Play-volume proxy','Offense','calculated','number',None,'Pass attempts + rush attempts; not a play-by-play count.'),
 ('completionRate','Completion rate','Passing','calculated','percent',True,'Pass completions / pass attempts.'),('passYpa','Passing yards / attempt','Passing','calculated','decimal',True,'Net passing yards / pass attempts; source sack conventions apply.'),('rushYpa','Rushing yards / attempt','Rushing','calculated','decimal',True,'Rushing yards / rushing attempts.'),
 ('yardsPerPlay','Yards / play proxy','Offense','calculated','decimal',True,'Total yards / (pass attempts + rush attempts).'),('pointsPerPlay','Points / play proxy','Scoring','calculated','decimal',True,'All team points / play-volume proxy; includes non-offensive scoring.'),('passShare','Pass-attempt share','Passing','calculated','percent',None,'Pass attempts / play-volume proxy.'),
 ('thirdMade','Third-down conversions','Situational','raw','number',True,None),('thirdAttempts','Third-down attempts','Situational','raw','number',None,None),('thirdRate','Third-down conversion','Situational','calculated','percent',True,'Third-down conversions / attempts.'),
 ('fourthMade','Fourth-down conversions','Situational','raw','number',True,None),('fourthAttempts','Fourth-down attempts','Situational','raw','number',None,None),('fourthRate','Fourth-down conversion','Situational','calculated','percent',True,'Fourth-down conversions / attempts; zero attempts is missing, not zero.'),
 ('turnovers','Turnovers','Ball security','raw','number',False,None),('fumblesLost','Fumbles lost','Ball security','raw','number',False,None),('interceptions','Interceptions thrown','Ball security','raw','number',False,None),('turnoverRate','Turnovers / play proxy','Ball security','calculated','percent',False,'Turnovers / play-volume proxy.'),
 ('penalties','Penalties','Discipline','raw','number',False,None),('penaltyYards','Penalty yards','Discipline','raw','number',False,None),('penaltyRate','Penalty yards / play proxy','Discipline','calculated','decimal',False,'Penalty yards / play-volume proxy.'),
 ('possessionMinutes','Possession minutes','Tempo','raw','decimal',None,'Possession time converted to minutes.'),('firstDownRate','First downs / play proxy','Offense','calculated','percent',True,'First downs / play-volume proxy.')]
RATIOS={'completionRate':['passCompletions','passAttempts'],'passYpa':['passYards','passAttempts'],'rushYpa':['rushYards','rushAttempts'],'yardsPerPlay':['totalYards','plays'],'pointsPerPlay':['points','plays'],'passShare':['passAttempts','plays'],'thirdRate':['thirdMade','thirdAttempts'],'fourthRate':['fourthMade','fourthAttempts'],'turnoverRate':['turnovers','plays'],'penaltyRate':['penaltyYards','plays'],'firstDownRate':['firstDowns','plays']}
def parse(b,points):
    if not b:return None
    def n(k):return number(b.get(k),None)
    def pair(k,sep):
        s=b.get(k,'').split(sep);return [number(v,None) for v in s] if len(s)==2 else [None,None]
    pc,pa=pair('completionAttempts','/');tm,ta=pair('thirdDownEff','-');fm,fa=pair('fourthDownEff','-');pen,py=pair('totalPenaltiesYards','-');mm,ss=pair('possessionTime',':');ra=n('rushingAttempts')
    d={'points':points,'firstDowns':n('firstDowns'),'totalYards':n('totalYards'),'passYards':n('netPassingYards'),'rushYards':n('rushingYards'),'passCompletions':pc,'passAttempts':pa,'rushAttempts':ra,'plays':pa+ra if pa is not None and ra is not None else None,'thirdMade':tm,'thirdAttempts':ta,'fourthMade':fm,'fourthAttempts':fa,'turnovers':n('turnovers'),'fumblesLost':n('fumblesLost'),'interceptions':n('interceptions'),'penalties':pen,'penaltyYards':py,'possessionMinutes':mm+ss/60 if mm is not None and ss is not None else None}
    for k,(a,b) in RATIOS.items():d[k]=d[a]/d[b] if d[a] is not None and d[b] else None
    return d
def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);args=p.parse_args();_,seasons,boxes,_=load_data(Path(args.data))
    definitions=[dict(zip(['key','label','group','kind','format','higher','description'],d)) for d in DEFS]
    for year in YEARS:
        gs={g['id']:g for g in seasons[year]['games']};rows=[]
        for (gid,tid),b in boxes[year].items():
            if gid not in gs:continue
            g=gs[gid];home=tid==g['home'];opponent=g['away'] if home else g['home']
            if tid not in (g['home'],g['away']):continue
            own=parse(b,g['hs'] if home else g['as']);opp=parse(boxes[year].get((gid,opponent)),g['as'] if home else g['hs'])
            rows.append({'gameId':gid,'teamId':tid,'opponentId':opponent,'date':g['date'],'week':g['week'],'home':home,'neutral':g['neutral'],'fbs':g['fbs'],'own':own,'opponent':opp})
        result={'season':year,'definitions':definitions,'ratios':RATIOS,'source':'SportsDataverse ESPN team box-score release; schedules supply final points. ESPN is the shared upstream source, not an independent corroboration.','rows':rows}
        (ROOT/f'public/data/box-{year}.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False),encoding='utf-8')
        print(year,len(rows),flush=True)
if __name__=='__main__':main()

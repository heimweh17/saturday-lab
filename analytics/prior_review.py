"""Second prespecified stage: talent belongs in the rating prior, not an additive time-decay bonus."""
import itertools,hashlib
import ranking_review as r
from pipeline import ROOT
CACHE=ROOT/'analytics/prior-review-cache.json'
def configure():
 r.CACHE=CACHE;r.RUN_NAME='prior-review'
 r.CONFIGS=[dict(carry=c,lam=l,method=m,weight=w,talentPrior=t,memory=1,decay=.97) for c,l,m,w,t in itertools.product([.35,.65],[1.,2.,4.],['raw','residual28'],['uniform','mismatch'],[0.,6.,12.])]
 r.BUNDLES={k:v for k,v in r.BUNDLES.items() if k in ['score','score_elo','score_epa','score_epa_elo']}
 r.PROTOCOL_EXTRA={'version':'5-research-2-prior-only','calendarDecay':'None. Recruiting affects preseason scoring prior only, never a direct probability input.', 'priorDefinition':'Net scoring prior = carry * previous final net rating + talentPrior * (centered recruiting composite/1000 + centered blue-chip share). Split equally between offense and defense. Current-season games replace prior through weighted ridge.', 'stageTwoReason':'First-stage additive calendar decay still mechanically reduces talent-rich teams after positive performances. This second stage was specified after inspecting stage one; all results remain exploratory retrospective evidence.', 'stageTwoBlueprintSha256':hashlib.sha256((ROOT/'analytics/PRIOR-REVIEW.md').read_bytes()).hexdigest()}
if __name__=='__main__':configure();r.main()

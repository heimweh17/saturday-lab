import scoreLayer from '@/public/data/score-layer.json';

export type ProjectedScore={aScore:number;bScore:number;margin:number;total:number};

export function fullModelScore(probability:number,baselineAScore:number,baselineBScore:number):ProjectedScore{
  const p=Math.min(.999999,Math.max(.000001,probability));
  const margin=scoreLayer.margin.scale*Math.log(p/(1-p));
  const calibratedTotal=scoreLayer.total.intercept+scoreLayer.total.slope*(baselineAScore+baselineBScore);
  const total=Math.max(Math.abs(margin),calibratedTotal);
  return {aScore:(total+margin)/2,bScore:(total-margin)/2,margin,total};
}

export const scoreLayerVersion=scoreLayer.version;

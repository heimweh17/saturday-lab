import manifest from '@/public/data/manifest.json';
export async function GET(){return Response.json({status:'ok',project:'Saturday Lab',modelVersion:manifest.version,snapshotBuilt:manifest.generatedAt,seasons:manifest.seasons,latestResult:manifest.audit.at(-1)?.lastGame,mode:'versioned snapshot'})}

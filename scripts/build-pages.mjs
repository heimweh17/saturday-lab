import {renameSync,existsSync,writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const api=resolve(root,'app/api'),backup=resolve(root,'.api-build-backup');
if(existsSync(backup))throw Error('Previous interrupted build left .api-build-backup. Restore it to app/api first.');
// GitHub Pages cannot host dynamic route handlers; keep them intact for normal Next deployments.
renameSync(api,backup);
try{
 const result=spawnSync(process.execPath,['node_modules/next/dist/bin/next','build','--webpack'],{cwd:root,stdio:'inherit',env:{...process.env,STATIC_EXPORT:'1',NEXT_PUBLIC_BASE_PATH:process.env.NEXT_PUBLIC_BASE_PATH??'/saturday-lab'}});
 if(result.status!==0)process.exitCode=result.status??1;
 else writeFileSync(resolve(root,'out/.nojekyll'),'');
}finally{renameSync(backup,api)}

import {spawnSync} from 'node:child_process';
import {existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=process.cwd(),out=resolve(root,'out');
if(!existsSync(resolve(out,'index.html'))||!existsSync(resolve(out,'.nojekyll')))throw Error('Run npm run build:pages successfully first.');
const expected='https://github.com/heimweh17/saturday-lab.git';
function git(args,cwd=out){const r=spawnSync('git',args,{cwd,encoding:'utf8',maxBuffer:64*1024*1024,env:{...process.env,GIT_TERMINAL_PROMPT:'0'}});if(r.status!==0)throw Error(r.stderr||r.stdout);return r.stdout.trim()}
const name=git(['config','user.name'],root),email=git(['config','user.email'],root);
if(!existsSync(resolve(out,'.git')))git(['init','-b','gh-pages']);
git(['config','user.name',name]);git(['config','user.email',email]);
git(['config','core.autocrlf','false']);
if(!git(['remote']).split('\n').includes('origin'))git(['remote','add','origin',expected]);
if(git(['remote','get-url','origin'])!==expected)throw Error('Unexpected publish remote; inspect it before proceeding.');
const exists=git(['ls-remote','--heads','origin','gh-pages']);
if(exists){git(['fetch','origin','gh-pages']);git(['reset','--soft','FETCH_HEAD'])}
git(['add','-A']);
if(git(['diff','--cached','--name-only']))git(['commit','-m','Publish Saturday Lab static site']);
console.log(git(['push','origin','HEAD:gh-pages']));
console.log('Published artifact commit '+git(['rev-parse','HEAD']));

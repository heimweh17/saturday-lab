import {spawnSync} from 'node:child_process';
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
const root=process.cwd(),out=resolve(root,'out');
if(!existsSync(resolve(out,'index.html'))||!existsSync(resolve(out,'.nojekyll')))throw Error('Run npm run build:pages successfully first.');
const expected='https://github.com/heimweh17/saturday-lab.git';
function git(args,cwd=out){const r=spawnSync('git',args,{cwd,encoding:'utf8',maxBuffer:64*1024*1024,env:{...process.env,GIT_TERMINAL_PROMPT:'0'}});if(r.status!==0)throw Error(r.stderr||r.stdout);return r.stdout.trim()}
function optionalGit(args,cwd=root){const r=spawnSync('git',args,{cwd,encoding:'utf8',env:{...process.env,GIT_TERMINAL_PROMPT:'0'}});return r.status===0?r.stdout.trim():''}
const name=git(['config','user.name'],root),email=git(['config','user.email'],root);
const checkoutAuth=optionalGit(['config','--get','http.https://github.com/.extraheader']);
if(!existsSync(resolve(out,'.git')))git(['init','-b','gh-pages']);
git(['config','user.name',name]);git(['config','user.email',email]);
git(['config','core.autocrlf','false']);
// actions/checkout keeps its short-lived GITHUB_TOKEN in the source repo's
// local extraheader. The exported Pages directory is a separate repository,
// so explicitly carry that header across without placing a token in its URL.
if(checkoutAuth)git(['config','http.https://github.com/.extraheader',checkoutAuth]);
if(!git(['remote']).split('\n').includes('origin'))git(['remote','add','origin',expected]);
if(git(['remote','get-url','origin'])!==expected)throw Error('Unexpected publish remote; inspect it before proceeding.');
const exists=git(['ls-remote','--heads','origin','gh-pages']);
if(exists){git(['fetch','origin','gh-pages']);git(['reset','--soft','FETCH_HEAD'])}
git(['add','-A']);
if(git(['diff','--cached','--name-only']))git(['commit','-m','Publish Saturday Lab static site']);
console.log(git(['push','origin','HEAD:gh-pages']));
console.log('Published artifact commit '+git(['rev-parse','HEAD']));

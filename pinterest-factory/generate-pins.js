const fs = require('fs'); const path = require('path');
const ROOT = __dirname;
const data = JSON.parse(fs.readFileSync(path.join(ROOT,'data','seed_posts.json'),'utf8'));
const outDir = path.join(ROOT,'output'); const pinDir = path.join(outDir,'pins'); fs.mkdirSync(pinDir,{recursive:true});
const count = parseInt(process.env.PIN_COUNT || '8',10);
const angles = ['Core title','Pain-point','How to','Quick wins'];
function slug(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80)}
function esc(s){return String(s).replace(/[&<>]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[m]))}
function makeTitle(post,angle){ if(angle==='Pain-point') return 'Struggling? '+post.title; if(angle==='How to') return 'How to: '+post.title; if(angle==='Quick wins') return post.title+' (Fast Fixes)'; return post.title; }
function makeDesc(post){return `Helpful ${post.category.toLowerCase()} ideas for busy families. Read more at The Modern Family Guide.`}
function makeSvg(title,sub,file){ const svg=`<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='1500'><rect width='100%' height='100%' fill='#f4f1ea'/><rect x='60' y='60' width='880' height='1380' rx='30' fill='white' stroke='#ddd'/><text x='80' y='220' font-size='64' font-family='Arial' font-weight='700' fill='#222'>${esc(title)}</text><text x='80' y='340' font-size='34' font-family='Arial' fill='#666'>${esc(sub)}</text><text x='80' y='1420' font-size='28' font-family='Arial' fill='#888'>The Modern Family Guide</text></svg>`; fs.writeFileSync(file,svg,'utf8'); }
let rows=[]; let n=1;
for (const post of data){ for(const angle of angles){ if(rows.length>=count) break; const title=makeTitle(post,angle); const file=`${String(n).padStart(3,'0')}-${slug(title)}.svg`; makeSvg(title,post.category,path.join(pinDir,file)); rows.push({published_ok:'',priority:'A',source_post:post.title,pin_angle:angle,pin_title:title,description:makeDesc(post),url:post.url,board:post.category,image_file:'pins/'+file,status:'Ready'}); n++; } if(rows.length>=count) break; }
fs.writeFileSync(path.join(outDir,'pinterest_queue.json'),JSON.stringify(rows,null,2));
const headers=Object.keys(rows[0]||{published_ok:'',priority:'',source_post:'',pin_angle:'',pin_title:'',description:'',url:'',board:'',image_file:'',status:''});
const csv=[headers.join(',')].concat(rows.map(r=>headers.map(h=>'"'+String(r[h]).replace(/"/g,'""')+'"').join(','))).join('\n'); fs.writeFileSync(path.join(outDir,'pinterest_queue.csv'),csv);
console.log(`Generated ${rows.length} pins`);

const fs=require('fs'); const path=require('path');
const ROOT=__dirname;
const data=JSON.parse(fs.readFileSync(path.join(ROOT,'data','seed_posts.json'),'utf8'));
const outDir=path.join(ROOT,'output'); const pinDir=path.join(outDir,'pins'); fs.mkdirSync(pinDir,{recursive:true});
const count=parseInt(process.env.PIN_COUNT||'20',10);
const angles=['Primary Keyword','List Post','Pain Point','How To','Quick Wins','Beginner Friendly'];
function slug(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80)}
function esc(s){return String(s).replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]))}
function kw(post){return post.primaryKeyword||post.title.toLowerCase()}
function makeTitle(post,angle){const k=kw(post); if(angle==='Primary Keyword') return k.replace(/\b\w/g,m=>m.toUpperCase()); if(angle==='List Post') return post.title; if(angle==='Pain Point') return 'Need Help? '+post.title; if(angle==='How To') return 'How to '+k.replace(/\b\w/g,m=>m.toUpperCase()); if(angle==='Quick Wins') return post.title+' (Easy Wins)'; return 'Beginner Guide: '+post.title;}
function makeDesc(post){const kws=(post.secondaryKeywords||[]).slice(0,3).join(', '); return `Practical ideas for busy families. Topics: ${kws}. Read more at The Modern Family Guide.`;}
function makeSvg(title,sub,file){const svg=`<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='1500'><rect width='100%' height='100%' fill='#f3f0ea'/><rect x='40' y='40' width='920' height='1420' rx='28' fill='white'/><text x='70' y='180' font-size='58' font-family='Arial' font-weight='700' fill='#1f2d3d'>${esc(title)}</text><text x='70' y='320' font-size='30' font-family='Arial' fill='#5b6570'>${esc(sub)}</text><rect x='70' y='1180' width='860' height='180' rx='18' fill='#eef2f5'/><text x='90' y='1260' font-size='28' font-family='Arial' fill='#445'>Save for later • Click for full guide</text><text x='70' y='1430' font-size='24' font-family='Arial' fill='#888'>The Modern Family Guide</text></svg>`; fs.writeFileSync(file,svg,'utf8');}
let rows=[]; let n=1;
for(const post of data){for(const angle of angles){if(rows.length>=count) break; const title=makeTitle(post,angle); const file=`${String(n).padStart(3,'0')}-${slug(title)}.svg`; makeSvg(title,post.category,path.join(pinDir,file)); rows.push({published_ok:'',priority:n<=8?'A':'B',source_post:post.title,pin_angle:angle,pin_title:title,description:makeDesc(post),url:post.url,board:post.category,keywords:(post.secondaryKeywords||[]).join(' | '),image_file:'pins/'+file,status:'Ready'}); n++;} if(rows.length>=count) break;}
fs.writeFileSync(path.join(outDir,'pinterest_queue.json'),JSON.stringify(rows,null,2));
const headers=Object.keys(rows[0]); const csv=[headers.join(',')].concat(rows.map(r=>headers.map(h=>'"'+String(r[h]).replace(/"/g,'""')+'"').join(','))).join('\n'); fs.writeFileSync(path.join(outDir,'pinterest_queue.csv'),csv);
console.log(`Generated ${rows.length} monster pins`);

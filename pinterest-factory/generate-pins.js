const fs = require('fs');
const path = require('path');
const https = require('https');

const ROOT = __dirname;
const SITE = process.env.WP_SITE_URL || 'https://themodernfamilyguide.wordpress.com';
const USE_LIVE = String(process.env.USE_LIVE_WORDPRESS || 'true').toLowerCase() !== 'false';
const PIN_COUNT = parseInt(process.env.PIN_COUNT || '24', 10);
const WP_POST_LIMIT = parseInt(process.env.WP_POST_LIMIT || '20', 10);

const outDir = path.join(ROOT, 'output');
const pinDir = path.join(outDir, 'pins');
fs.mkdirSync(pinDir, { recursive: true });

const runInfo = { generatedAt: new Date().toISOString(), site: SITE, useLive: USE_LIVE, liveAttempted: false, liveSuccess: false, liveError: '', wpV2Error: '', wpComError: '', sourceUsed: 'seed', postCount: 0, pinCount: 0 };
const angles = ['Primary Keyword', 'List Post', 'Pain Point', 'How To', 'Quick Wins', 'Beginner Friendly'];

function httpJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'TMFG-Pinterest-Factory/3.2' } }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode < 200 || res.statusCode >= 300) return reject(new Error(`HTTP ${res.statusCode}: ${url} :: ${data.slice(0, 250)}`));
        try { resolve(JSON.parse(data)); } catch (e) { reject(new Error(`JSON parse failed: ${e.message}`)); }
      });
    }).on('error', reject);
  });
}

function stripHtml(s) {
  return String(s || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&#8217;/g, '’')
    .replace(/&#8220;/g, '“')
    .replace(/&#8221;/g, '”')
    .replace(/&#038;/g, '&')
    .replace(/&#8211;/g, '–')
    .replace(/&#8212;/g, '—')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizePost(title, url, date, source) {
  title = stripHtml(title);
  const category = inferCategory(title);
  return { title, url, category, primaryKeyword: inferPrimaryKeyword(title, category), secondaryKeywords: inferKeywords(title, category), date, source };
}

function inferCategory(title) {
  const t = title.toLowerCase();
  if (/meal|dinner|cook|food|picky|kitchen|recipe|grocery/.test(t)) return 'Easy Meals';
  if (/kid|kids|activity|activities|bored|rainy|screen|play/.test(t)) return 'Kids Activities';
  if (/home|organ|reset|tidy|mess|entryway|declutter|counter|backpack/.test(t)) return 'Home Organization';
  if (/money|budget|cheap|saving|spend|finance/.test(t)) return 'Family Finance';
  if (/listen|parent|routine|voice|yell|behavior/.test(t)) return 'Parenting';
  return 'Parenting';
}

function inferKeywords(title, category) {
  if (category === 'Easy Meals') return ['easy family meals', 'weeknight dinner ideas', 'family dinner ideas', 'quick family dinners'];
  if (category === 'Kids Activities') return ['indoor kids activities', 'screen free activities for kids', 'kids activities at home', 'boredom busters for kids'];
  if (category === 'Home Organization') return ['home organization ideas', 'home organization hacks', 'organized home', 'simple home systems'];
  if (category === 'Family Finance') return ['family budget tips', 'money saving tips', 'budgeting tips for families', 'frugal living tips'];
  return ['parenting tips', 'positive parenting tips', 'gentle parenting tips', 'family routines'];
}

function inferPrimaryKeyword(title, category) {
  const clean = title.replace(/[:–—].*$/, '').replace(/[?!.]+$/,'').trim();
  if (clean.length <= 48) return clean.toLowerCase();
  return inferKeywords(title, category)[0];
}

async function fetchWpV2() {
  const api = `${SITE.replace(/\/$/, '')}/wp-json/wp/v2/posts?per_page=${WP_POST_LIMIT}&status=publish&_fields=link,title,excerpt,date`;
  const posts = await httpJson(api);
  return posts.map(p => normalizePost(p.title && p.title.rendered, p.link, p.date, 'wordpress-wp-json')).filter(p => p.title && p.url);
}

async function fetchWpCom() {
  const host = SITE.replace(/^https?:\/\//, '').replace(/\/$/, '');
  const api = `https://public-api.wordpress.com/rest/v1.1/sites/${encodeURIComponent(host)}/posts/?number=${WP_POST_LIMIT}&fields=URL,title,date,status`;
  const data = await httpJson(api);
  const posts = Array.isArray(data.posts) ? data.posts : [];
  return posts.filter(p => !p.status || p.status === 'publish').map(p => normalizePost(p.title, p.URL || p.short_URL, p.date, 'wordpress-com-api')).filter(p => p.title && p.url);
}

async function loadPosts() {
  const seedPath = path.join(ROOT, 'data', 'seed_posts.json');
  const seed = JSON.parse(fs.readFileSync(seedPath, 'utf8')).map(p => ({ ...p, source: p.source || 'seed' }));
  if (!USE_LIVE) return seed;
  runInfo.liveAttempted = true;
  try {
    const live = await fetchWpV2();
    if (!live.length) throw new Error('WP v2 returned zero usable posts');
    runInfo.liveSuccess = true;
    runInfo.sourceUsed = 'wordpress-wp-json';
    return live;
  } catch (e) {
    runInfo.wpV2Error = e.message;
  }
  try {
    const live = await fetchWpCom();
    if (!live.length) throw new Error('WordPress.com API returned zero usable posts');
    runInfo.liveSuccess = true;
    runInfo.sourceUsed = 'wordpress-com-api';
    return live;
  } catch (e) {
    runInfo.wpComError = e.message;
    runInfo.liveError = `${runInfo.wpV2Error} || ${runInfo.wpComError}`;
    console.warn('All live WordPress fetches failed, using seed posts:', runInfo.liveError);
    return seed;
  }
}

function slug(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 80); }
function esc(s) { return String(s).replace(/[&<>]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m])); }
function titleCase(s) { return String(s).replace(/\b\w/g, m => m.toUpperCase()); }
function kw(post) { return post.primaryKeyword || post.title.toLowerCase(); }
function gerundPhrase(k) { return titleCase(k.replace(/^how to\s+/i,'').replace(/^the\s+/i,'')); }

function makeTitle(post, angle) {
  const k = gerundPhrase(kw(post));
  if (angle === 'Primary Keyword') return k;
  if (angle === 'List Post') return post.title;
  if (angle === 'Pain Point') return `Struggling With ${k}? Try This`;
  if (angle === 'How To') return `How to Make ${k} Easier`;
  if (angle === 'Quick Wins') return `${k}: Easy Wins for Busy Parents`;
  return `Beginner Guide to ${k}`;
}

function makeDesc(post) {
  const kws = (post.secondaryKeywords || []).slice(0, 4).join(', ');
  return `Practical, realistic help for busy families. Includes ideas around ${kws}. Read the full guide at The Modern Family Guide.`;
}

function makeSvg(title, sub, file) {
  const safeTitle = esc(title.length > 84 ? title.slice(0, 81) + '…' : title);
  const safeSub = esc(sub);
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='1500'>
  <rect width='100%' height='100%' fill='#f4f1ea'/>
  <rect x='45' y='45' width='910' height='1410' rx='34' fill='white'/>
  <rect x='45' y='45' width='910' height='190' rx='34' fill='#152536'/>
  <text x='80' y='165' font-size='50' font-family='Arial' font-weight='700' fill='white'>${safeTitle}</text>
  <text x='80' y='330' font-size='34' font-family='Arial' fill='#334'>${safeSub}</text>
  <rect x='80' y='440' width='840' height='600' rx='28' fill='#eef2f5'/>
  <text x='120' y='720' font-size='44' font-family='Arial' font-weight='700' fill='#223'>Save this idea</text>
  <text x='120' y='790' font-size='32' font-family='Arial' fill='#556'>Simple family life help</text>
  <rect x='80' y='1140' width='840' height='160' rx='22' fill='#152536'/>
  <text x='120' y='1238' font-size='34' font-family='Arial' font-weight='700' fill='white'>Click for the full guide</text>
  <text x='80' y='1405' font-size='26' font-family='Arial' fill='#777'>The Modern Family Guide</text>
</svg>`;
  fs.writeFileSync(file, svg, 'utf8');
}

(async function main() {
  const posts = await loadPosts();
  let rows = [];
  let n = 1;
  for (const post of posts) {
    for (const angle of angles) {
      if (rows.length >= PIN_COUNT) break;
      const title = makeTitle(post, angle);
      const file = `${String(n).padStart(3, '0')}-${slug(title)}.svg`;
      makeSvg(title, post.category, path.join(pinDir, file));
      rows.push({ published_ok: '', priority: n <= 10 ? 'A' : 'B', source: post.source || 'seed', source_post: post.title, pin_angle: angle, pin_title: title, description: makeDesc(post), url: post.url, board: post.category, primary_keyword: post.primaryKeyword || '', keywords: (post.secondaryKeywords || []).join(' | '), image_file: 'pins/' + file, status: 'Ready' });
      n++;
    }
    if (rows.length >= PIN_COUNT) break;
  }
  fs.writeFileSync(path.join(outDir, 'pinterest_queue.json'), JSON.stringify(rows, null, 2));
  const headers = Object.keys(rows[0]);
  const csv = [headers.join(',')].concat(rows.map(r => headers.map(h => '"' + String(r[h]).replace(/"/g, '""') + '"').join(','))).join('\n');
  fs.writeFileSync(path.join(outDir, 'pinterest_queue.csv'), csv);
  runInfo.postCount = posts.length;
  runInfo.pinCount = rows.length;
  fs.writeFileSync(path.join(outDir, 'run_summary.json'), JSON.stringify(runInfo, null, 2));
  console.log(`Generated ${rows.length} Monster V3.2 pins from ${posts.length} posts using ${runInfo.sourceUsed}`);
})();

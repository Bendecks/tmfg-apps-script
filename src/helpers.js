/****************************************************
 * TMFG V2 — HELPERS
 * Shared helpers for links, hubs, utils, WP site info
 ****************************************************/

/***********************
 * INTERNAL LINKING
 ***********************/
function getInternalLinkCandidates_(rows, plan, maxLinks) {
  maxLinks = maxLinks || 3;
  var pool = [];

  for (var i = 1; i < rows.length; i++) {
    var title = String(rows[i][0] || "").trim();
    var status = String(rows[i][1] || "").trim().toLowerCase();
    var url = String(rows[i][2] || "").trim();
    var type = String(rows[i][4] || "").trim().toUpperCase();
    var cat = String(rows[i][5] || "").trim();
    var angle = String(rows[i][6] || "").trim();

    if (status !== "done") continue;
    if (!title || !url) continue;
    if (title.toLowerCase() === String(plan.title || "").trim().toLowerCase()) continue;

    pool.push({
      title: title,
      url: isInternalUrl_(url) ? makeRelativeUrl_(url) : url,
      type: type,
      categorySlug: cat,
      angle: angle,
      idx: i
    });
  }

  if (!pool.length) return [];
  pool.sort(function(a, b) { return b.idx - a.idx; });

  var picked = [];
  var used = {};

  function score(it) {
    var s = 0;
    if (it.categorySlug === plan.categorySlug) s += 50;
    if (it.type === plan.type) s += 20;
    if (it.angle === plan.angle) s += 20;
    s += Math.min(10, Math.floor(it.idx / 50));

    var overlap = titleJaccardLite_(it.title, plan.title);
    if (overlap >= 0.35) s -= 30;

    return s;
  }

  while (picked.length < maxLinks) {
    var best = null;
    var bestScore = -999999;

    for (var j = 0; j < pool.length; j++) {
      var it = pool[j];
      if (used[it.url]) continue;

      var sc = score(it);
      if (sc > bestScore) {
        bestScore = sc;
        best = it;
      }
    }

    if (!best) break;
    used[best.url] = true;
    picked.push(best);
  }

  return picked;
}

function titleJaccardLite_(t1, t2) {
  var a = normalizeTitleTokens_(t1);
  var b = normalizeTitleTokens_(t2);
  if (!a.length || !b.length) return 0;

  var setA = {}, setB = {};
  for (var i = 0; i < a.length; i++) setA[a[i]] = 1;
  for (var j = 0; j < b.length; j++) setB[b[j]] = 1;

  var inter = 0, uni = 0;
  for (var k in setA) {
    uni++;
    if (setB[k]) inter++;
  }
  for (var k2 in setB) {
    if (!setA[k2]) uni++;
  }

  return uni ? (inter / uni) : 0;
}

/***********************
 * URL HELPERS
 ***********************/
function makeRelativeUrl_(url) {
  var s = String(url || "").trim();
  if (!s) return s;
  if (s.indexOf("/") === 0 && s.indexOf("//") !== 0) return s;

  var m = s.match(/^https?:\/\/[^\/]+(\/.*)$/i);
  return (m && m[1]) ? m[1] : s;
}

function isInternalUrl_(url) {
  var s = String(url || "").trim();
  if (!s) return false;
  if (s.indexOf("/") === 0 && s.indexOf("//") !== 0) return true;

  try {
    var siteInfo = getWpSiteHomeCached_();
    if (!siteInfo || !siteInfo.host) return false;

    var m = s.match(/^https?:\/\/([^\/]+)(\/.*)?$/i);
    if (!m) return false;

    return String(m[1] || "").toLowerCase() === siteInfo.host;
  } catch (e) {
    return false;
  }
}

function getWpSiteHomeCached_() {
  var cache = CacheService.getScriptCache();
  var cached = cache.get("WP_SITE_HOME_INFO");
  if (cached) return JSON.parse(cached);

  var res = UrlFetchApp.fetch(
    "https://public-api.wordpress.com/rest/v1.1/sites/" + encodeURIComponent(WP_SITE_ID),
    {
      headers: { Authorization: "Bearer " + WP_OAUTH_TOKEN },
      muteHttpExceptions: true
    }
  );

  if (res.getResponseCode() !== 200) {
    throw new Error("Could not fetch WP site info.");
  }

  var json = JSON.parse(res.getContentText());
  var siteUrl = String(json.URL || json.url || "").trim();
  var hostMatch = siteUrl.match(/^https?:\/\/([^\/]+)$/i) || siteUrl.match(/^https?:\/\/([^\/]+)\//i);

  var info = {
    url: siteUrl,
    host: hostMatch ? String(hostMatch[1] || "").toLowerCase() : ""
  };

  cache.put("WP_SITE_HOME_INFO", JSON.stringify(info), 21600);
  return info;
}

/***********************
 * HUBS
 ***********************/
function ensureHubsSheet_(ss) {
  var sh = ss.getSheetByName(HUBS_SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(HUBS_SHEET_NAME);
    sh.getRange(1, 1, 1, 5).setValues([["CategorySlug", "HubPostId", "HubUrl", "HubTitle", "UpdatedAt"]]);
  }
  return sh;
}

function ensureCategoryHub_(ss, categorySlug) {
  var hubs = ensureHubsSheet_(ss);
  var data = hubs.getDataRange().getValues();

  for (var i = 1; i < data.length; i++) {
    var slug = String(data[i][0] || "").trim();
    var hubId = String(data[i][1] || "").trim();
    var hubUrl = String(data[i][2] || "").trim();
    if (slug === categorySlug && hubId && hubUrl) {
      return { id: hubId, url: hubUrl, title: String(data[i][3] || "").trim() };
    }
  }

  var hubTitle = hubTitleForCategory_(categorySlug);
  var hubHtml = buildHubHtml_(categorySlug, ss.getActiveSheet());
  var created = createWpPost_(hubTitle, hubHtml, null, DEFAULT_STATUS, categorySlug);

  var hubIdNew = String(created.ID || created.id || "");
  var hubUrlNew = String(created.URL || created.url || "");
  if (!hubIdNew || !hubUrlNew) throw new Error("Hub created but missing ID/URL.");

  hubs.appendRow([categorySlug, hubIdNew, hubUrlNew, hubTitle, new Date()]);
  return { id: hubIdNew, url: hubUrlNew, title: hubTitle };
}

function updateCategoryHub_(ss, categorySlug, mainSheet) {
  var hubs = ensureHubsSheet_(ss);
  var data = hubs.getDataRange().getValues();

  var hubRow = -1;
  var hubId = "";
  var hubTitle = "";

  for (var i = 1; i < data.length; i++) {
    if (String(data[i][0] || "").trim() === categorySlug) {
      hubRow = i + 1;
      hubId = String(data[i][1] || "").trim();
      hubTitle = String(data[i][3] || "").trim();
      break;
    }
  }

  if (!hubRow || !hubId) return;

  var hubHtml = buildHubHtml_(categorySlug, mainSheet);

  var url = "https://public-api.wordpress.com/rest/v1.1/sites/" + encodeURIComponent(WP_SITE_ID) + "/posts/" + encodeURIComponent(hubId);
  var res = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: { Authorization: "Bearer " + WP_OAUTH_TOKEN },
    payload: JSON.stringify({
      content: hubHtml,
      title: hubTitle || hubTitleForCategory_(categorySlug)
    }),
    muteHttpExceptions: true
  });

  var code = res.getResponseCode();
  if (code !== 200 && code !== 201) {
    throw new Error("Hub update failed HTTP " + code + ": " + truncate_(res.getContentText(), 900));
  }

  hubs.getRange(hubRow, 5).setValue(new Date());
}

function hubTitleForCategory_(slug) {
  var pretty = String(slug || "").replace(/-/g, " ");
  pretty = pretty.charAt(0).toUpperCase() + pretty.slice(1);
  return "The Modern Family Guide to " + pretty;
}

function buildHubHtml_(categorySlug, mainSheet) {
  var rows = mainSheet.getDataRange().getValues();
  var posts = [];

  for (var i = 1; i < rows.length; i++) {
    var title = String(rows[i][0] || "").trim();
    var status = String(rows[i][1] || "").trim().toLowerCase();
    var url = String(rows[i][2] || "").trim();
    var cat = String(rows[i][5] || "").trim();

    if (status !== "done") continue;
    if (!title || !url) continue;
    if (cat !== categorySlug) continue;

    posts.push({ title: title, url: url, idx: i });
  }

  posts.sort(function(a, b) { return b.idx - a.idx; });

  var list = posts.slice(0, 40).map(function(p) {
    var href = isInternalUrl_(p.url) ? makeRelativeUrl_(p.url) : p.url;
    return '<li style="margin:8px 0;"><a href="' + escapeAttr_(href) + '">' + escapeHtml_(p.title) + '</a></li>';
  }).join("");

  return (
    '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.65;color:#333;max-width:720px;margin:0 auto;">' +
    '<p style="font-size:18px;color:#555;">This hub collects our best posts on <strong>' + escapeHtml_(categorySlug.replace(/-/g, " ")) + '</strong>.</p>' +
    '<ul style="padding-left:18px;margin:10px 0;">' + list + '</ul>' +
    '<p style="font-size:12px;color:#999;margin-top:26px;">Updated automatically as new posts are published.</p>' +
    '</div>'
  );
}

/***********************
 * TITLE SIMILARITY
 ***********************/
function isTitleTooSimilar_(title, recentTitles) {
  var t = normalizeTitleTokens_(title);
  if (!t.length) return false;

  for (var i = 0; i < recentTitles.length; i++) {
    var r = normalizeTitleTokens_(recentTitles[i]);
    if (!r.length) continue;
    if (jaccard_(t, r) >= 0.55) return true;
  }
  return false;
}

function normalizeTitleTokens_(s) {
  var stop = {
    "a":1,"an":1,"and":1,"the":1,"to":1,"of":1,"for":1,"in":1,"on":1,"with":1,
    "our":1,"my":1,"your":1,"simple":1,"quiet":1,"calm":1,"week":1,"sunday":1,"routine":1,"reset":1
  };

  var clean = String(s || "").toLowerCase().replace(/[^a-z0-9\s]/g, " ");
  var parts = clean.split(/\s+/).filter(Boolean);

  var out = [];
  var seen = {};

  for (var i = 0; i < parts.length; i++) {
    var w = parts[i];
    if (w.length < 3) continue;
    if (stop[w]) continue;
    if (seen[w]) continue;
    seen[w] = 1;
    out.push(w);
  }

  return out;
}

function jaccard_(a, b) {
  var setA = {}, setB = {};

  for (var i = 0; i < a.length; i++) setA[a[i]] = 1;
  for (var j = 0; j < b.length; j++) setB[b[j]] = 1;

  var inter = 0, uni = 0;

  for (var k in setA) {
    uni++;
    if (setB[k]) inter++;
  }

  for (var k2 in setB) {
    if (!setA[k2]) uni++;
  }

  return uni ? (inter / uni) : 0;
}

/***********************
 * GENERIC UTILS
 ***********************/
function mustProp_(key) {
  var v = PROPS.getProperty(key);
  if (!v) throw new Error("Missing Script Property: " + key);
  return v;
}

function slugify_(s) {
  return String(s || "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "item";
}

function escapeHtml_(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr_(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function truncate_(s, n) {
  var x = String(s || "");
  return x.length > n ? x.slice(0, n) + "..." : x;
}

function uniq_(arr) {
  var seen = {};
  var out = [];
  for (var i = 0; i < arr.length; i++) {
    var v = String(arr[i] || "").trim();
    if (!v) continue;
    if (seen[v]) continue;
    seen[v] = 1;
    out.push(v);
  }
  return out;
}
function cleanSeoTitle_(title, keyword) {
  var t = String(title || "").trim();

  // fallback hvis tom
  if (!t) {
    return keyword;
  }

  // fjern for fancy tegn
  t = t.replace(/[|:]/g, " ");

  // hvis keyword ikke er først → flyt det
  var lower = t.toLowerCase();
  var kw = String(keyword || "").toLowerCase();

  if (kw && lower.indexOf(kw) !== 0) {
    t = keyword + " " + t;
  }

  // begræns længde
  if (t.length > 65) {
    t = t.slice(0, 65).trim();
  }

  return t;
}
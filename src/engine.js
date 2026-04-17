/****************************************************
 * TMFG PERSONAL MACHINE — engine.js (FULL + HUMANIZER)
 *
 * Sensitive values stay in Script Properties:
 *   GEMINI_API_KEY
 *   WP_OAUTH_TOKEN
 *   WP_SITE_ID
 *   AMAZON_TAG (optional)
 *
 * Non-sensitive values are read from sheet tab: Config
 *
 * Main sheet headers:
 * A Title | B Status | C Post URL | D Notes | E Type | F CategorySlug | G Angle
 *
 * Hubs sheet headers:
 * A CategorySlug | B HubPostId | C HubUrl | D HubTitle | E UpdatedAt
 *
 * Config sheet headers:
 * A Key | B Value
 ****************************************************/

/***********************
 * SENSITIVE CONFIG (Script Properties only)
 ***********************/
var PROPS = PropertiesService.getScriptProperties();
var GEMINI_API_KEY = mustProp_("GEMINI_API_KEY");
var WP_OAUTH_TOKEN = mustProp_("WP_OAUTH_TOKEN");
var WP_SITE_ID = mustProp_("WP_SITE_ID");
var AMAZON_TAG = String(PROPS.getProperty("AMAZON_TAG") || "").trim();

/***********************
 * NON-SENSITIVE CONFIG (read from Config sheet)
 ***********************/
function getConfigMap_() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Config");
  if (!sheet) return {};

  var data = sheet.getDataRange().getValues();
  var map = {};

  for (var i = 1; i < data.length; i++) {
    var key = String(data[i][0] || "").trim();
    var value = String(data[i][1] || "").trim();
    if (!key) continue;
    map[key] = value;
  }

  return map;
}

function getConfig_(key, fallback) {
  return CONFIG[key] !== undefined ? CONFIG[key] : fallback;
}

var CONFIG = getConfigMap_();

var PERSONAL_DEFAULT_STATUS = String(getConfig_("PERSONAL_DEFAULT_STATUS", "publish")).toLowerCase();
var PERSONAL_MAX_POSTS_PER_RUN = parseInt(getConfig_("PERSONAL_MAX_POSTS_PER_RUN", "1"), 10) || 1;
var PERSONAL_INCLUDE_FEATURED_IMAGE = String(getConfig_("PERSONAL_INCLUDE_FEATURED_IMAGE", "true")).toLowerCase() === "true";

var SITE_HOME_URL = String(getConfig_("SITE_HOME_URL", "https://themodernfamilyguide.wordpress.com")).replace(/\/+$/, "");
var AMAZON_DOMAIN = String(getConfig_("AMAZON_DOMAIN", "de")).trim();

var GEMINI_TEXT_MODEL = "models/gemini-2.5-flash";
var GEMINI_IMAGE_MODEL = String(getConfig_("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")).trim();

var BLOG_VOICE = String(getConfig_("BLOG_VOICE",
  "Warm, honest, slightly reflective but practical modern Scandinavian family voice. Calm, grounded, lightly humorous. Short paragraphs. No fluff. No corporate tone. No therapy jargon."
)).trim();

var FAMILY_VISUAL_PROFILE = String(getConfig_("FAMILY_VISUAL_PROFILE", "")).trim();
var FAMILY_IMAGE_LOCK_STYLE = String(getConfig_("FAMILY_IMAGE_LOCK_STYLE",
  "clean cartoon caricature, soft shading, modern family illustration, consistent character design across images"
)).trim();

/***********************
 * STATIC ENUMS
 ***********************/
var CATEGORY_SLUGS = [
  "family-finance-life",
  "home-organization",
  "kids-activities-fun",
  "parenting-hacks-tips",
  "recipes-meals",
  "relationship",
  "stuff-that-doesnt-fit-in-a-box",
  "travel-outings",
  "work-life-balance"
];

var POST_TYPES = [
  "PERSONAL_STORY",
  "SUNDAY_RESET",
  "REAL_LIFE_HACKS",
  "FAMILY_ACTIVITY",
  "RELATIONSHIP_MINI",
  "RECIPE_NOTE"
];

var ANGLES = [
  "SYSTEMS_AND_ROUTINES",
  "LOW_ENERGY_MODE",
  "TIME_SAVING",
  "MONEY_SAVING",
  "CONFLICT_REDUCTION",
  "KID_BEHAVIOR",
  "HOME_RESET",
  "MEAL_SIMPLIFICATION",
  "TRAVEL_PREP",
  "EMOTIONAL_REFLECTION",
  "MINIMALISM",
  "REAL_WORLD_EXAMPLE"
];

var HUBS_SHEET_NAME = "Hubs";
var CONFIG_SHEET_NAME = "Config";

/***********************
 * ENTRY POINT
 ***********************/
function runPersonalMachine() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(25000)) return;

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();

    if (sheet.getName() === HUBS_SHEET_NAME || sheet.getName() === CONFIG_SHEET_NAME) {
      throw new Error("runPersonalMachine() must be run from your main content sheet, not Hubs or Config.");
    }

    var rows = sheet.getDataRange().getValues();

    ensureHubsSheet_(ss);

    var processed = 0;

    for (var i = 1; i < rows.length; i++) {
      if (processed >= PERSONAL_MAX_POSTS_PER_RUN) break;

      var rowIndex = i + 1;
      var status = String(rows[i][1] || "").trim().toLowerCase();

      if (status !== "queued") continue;

      try {
        sheet.getRange(rowIndex, 3).setValue("");
        sheet.getRange(rowIndex, 4).setValue("");

        var history = getHistory_(rows, 40);
        var plan = generateEditorialPlan_(history);

        // Write plan to sheet
        sheet.getRange(rowIndex, 1).setValue(plan.title);
        sheet.getRange(rowIndex, 5).setValue(plan.type);
        sheet.getRange(rowIndex, 6).setValue(plan.categorySlug);
        sheet.getRange(rowIndex, 7).setValue(plan.angle);

        // Ensure hub exists
        var hub = ensureCategoryHub_(ss, plan.categorySlug, sheet);

        // Generate article JSON
        var ai = generatePersonalPostJson_(plan, history);

        // Featured image
        var mediaId = null;
        if (PERSONAL_INCLUDE_FEATURED_IMAGE) {
          var heroKeyword = String(ai.imageKeyword || ai.keyword || plan.title).trim();
          var heroBlob = generateHeroImage_(plan.title, heroKeyword, plan.categorySlug, plan.angle);
          mediaId = uploadWpMedia_(heroBlob, "featured-" + slugify_(plan.title));
        }

        // Internal links
        var candidates = getInternalLinkCandidates_(rows, plan, 2);

        // Build HTML
        var html = buildPersonalHtml_(plan, ai, hub, candidates);

        // Create post
        var post = createWpPost_(plan.title, html, mediaId, PERSONAL_DEFAULT_STATUS, plan.categorySlug);

        // Mark done
        sheet.getRange(rowIndex, 2).setValue("Done");
        sheet.getRange(rowIndex, 3).setValue(post.URL || post.url || "");
        sheet.getRange(rowIndex, 4).setValue(
          "OK | " + plan.type + " | " + plan.categorySlug + " | " + plan.angle + " | Img:" + (mediaId ? "yes" : "no")
        );

        // Update hub after post exists
        updateCategoryHub_(ss, plan.categorySlug, sheet);

        processed += 1;

      } catch (e) {
        sheet.getRange(rowIndex, 2).setValue("Error");
        sheet.getRange(rowIndex, 4).setValue(truncate_(String((e && e.message) ? e.message : e), 900));
        processed += 1;
      }
    }

  } finally {
    lock.releaseLock();
  }
}

/***********************
 * HISTORY
 ***********************/
function getHistory_(rows, limit) {
  var hist = { titles: [], types: [], categories: [], angles: [] };

  for (var i = rows.length - 1; i >= 1; i--) {
    var title = String(rows[i][0] || "").trim();
    var status = String(rows[i][1] || "").trim().toLowerCase();
    var type = String(rows[i][4] || "").trim().toUpperCase();
    var cat = String(rows[i][5] || "").trim();
    var angle = String(rows[i][6] || "").trim();

    if (!title) continue;
    if (status !== "done" && status !== "queued") continue;

    hist.titles.push(title);
    if (type) hist.types.push(type);
    if (cat) hist.categories.push(cat);
    if (angle) hist.angles.push(angle);

    if (hist.titles.length >= limit) break;
  }

  return hist;
}

/***********************
 * EDITORIAL PLAN
 ***********************/
function generateEditorialPlan_(history) {
  var bannedTypes = uniq_(history.types.slice(0, 2));
  var bannedCats = uniq_(history.categories.slice(0, 2));
  var bannedAngles = uniq_(history.angles.slice(0, 2));
  var recentTitles = history.titles.slice(0, 15);

  var prompt =
    "Return ONLY valid JSON. No markdown.\n\n" +
    "{\n" +
    '  "title": "Max 70 chars. Concrete + specific. Not generic.",\n' +
    '  "type": "ONE of: ' + POST_TYPES.join(", ") + '",\n' +
    '  "categorySlug": "ONE of: ' + CATEGORY_SLUGS.join(", ") + '",\n' +
    '  "angle": "ONE of: ' + ANGLES.join(", ") + '",\n' +
    '  "hook": "One sentence: what makes this different / why now",\n' +
    '  "scenario": "One sentence: a concrete real-life situation"\n' +
    "}\n\n" +

    "HARD RULES:\n" +
    "- Avoid mentioning any family member names.\n" +
    "- Do NOT create a synonym rewrite of recent titles.\n" +
    "- Avoid title patterns like:\n" +
    "  'Our ... routine'\n" +
    "  'Simple ... for a better ...'\n" +
    "  'How we ...'\n" +
    "  'Quiet ... week'\n" +
    "- Prefer specificity: time limit, friction point, conflict, low-energy moment, real scenario.\n" +
    "- Make the idea genuinely different.\n\n" +

    "BANNED (do not pick):\n" +
    "- type: " + (bannedTypes.length ? bannedTypes.join(", ") : "(none)") + "\n" +
    "- categorySlug: " + (bannedCats.length ? bannedCats.join(", ") : "(none)") + "\n" +
    "- angle: " + (bannedAngles.length ? bannedAngles.join(", ") : "(none)") + "\n\n" +

    "Recent titles to avoid imitating:\n" +
    recentTitles.map(function(t){ return "- " + t; }).join("\n") + "\n\n" +

    "Voice:\n" + BLOG_VOICE + "\n";

  for (var attempt = 1; attempt <= 3; attempt++) {
    var raw = geminiText_(prompt);
    var plan = JSON.parse(extractJsonObject_(raw));

    plan.title = String(plan.title || "").trim().slice(0, 70);
    plan.type = String(plan.type || "").trim().toUpperCase();
    plan.categorySlug = String(plan.categorySlug || "").trim();
    plan.angle = String(plan.angle || "").trim();
    plan.hook = String(plan.hook || "").trim();
    plan.scenario = String(plan.scenario || "").trim();

    if (!plan.title) continue;
    if (POST_TYPES.indexOf(plan.type) === -1) continue;
    if (CATEGORY_SLUGS.indexOf(plan.categorySlug) === -1) continue;
    if (ANGLES.indexOf(plan.angle) === -1) continue;

    if (bannedTypes.indexOf(plan.type) !== -1) continue;
    if (bannedCats.indexOf(plan.categorySlug) !== -1) continue;
    if (bannedAngles.indexOf(plan.angle) !== -1) continue;

    if (isTitleTooSimilar_(plan.title, history.titles.slice(0, 10))) continue;

    return plan;
  }

  throw new Error("Could not generate a diverse editorial plan after 3 attempts.");
}

// Backward-compatible alias
function generateEditorialPlanV2_(history) {
  return generateEditorialPlan_(history);
}

function isTitleTooSimilar_(title, recentTitles) {
  var lower = String(title || "").toLowerCase();
  if (lower.indexOf("our ") === 0 && lower.indexOf("sunday") !== -1 && lower.indexOf(" week") !== -1) return true;

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
    "our":1,"my":1,"your":1,"simple":1,"quiet":1,"calm":1,"week":1,"sunday":1,"routine":1,"reset":1,"rhythms":1
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
  var A = {}, B = {};
  for (var i = 0; i < a.length; i++) A[a[i]] = 1;
  for (var j = 0; j < b.length; j++) B[b[j]] = 1;

  var inter = 0, uni = 0;
  for (var k in A) { uni++; if (B[k]) inter++; }
  for (var k2 in B) { if (!A[k2]) uni++; }

  return uni ? inter / uni : 0;
}

/***********************
 * HUMANIZER LAYER
 ***********************/
function humanizeText_(text) {
  if (!text) return text;

  if (Math.random() < 0.4) {
    var openers = [
      "This started out pretty simple.",
      "We didn't plan this at all.",
      "This came from a slightly messy situation.",
      "Not something we thought much about at first.",
      "This was more accidental than planned."
    ];
    text = openers[Math.floor(Math.random() * openers.length)] + " " + text;
  }

  return text;
}

function humanizeSections_(sections) {
  if (!sections || !sections.length) return sections;

  return sections.map(function(s) {
    var text = String(s.p || "");

    if (Math.random() < 0.3) {
      var friction = [
        "At first, this didn't really stick.",
        "Honestly, we almost gave up on this.",
        "It felt like extra work in the beginning.",
        "We forgot to use it the first few days.",
        "It didn't work perfectly right away."
      ];
      text = friction[Math.floor(Math.random() * friction.length)] + " " + text;
    }

    if (Math.random() < 0.25) {
      text = text.replace(/\.$/, "") + ", which helped more than expected.";
    }

    if (Math.random() < 0.2) {
      var details = [
        "Usually right after getting home.",
        "Most days around dinner time.",
        "Especially on the more chaotic days.",
        "When everyone is a bit tired.",
        "On the days where everything feels rushed."
      ];
      text += " " + details[Math.floor(Math.random() * details.length)];
    }

    return {
      h2: s.h2,
      p: text
    };
  });
}

/***********************
 * ARTICLE JSON
 ***********************/
function generatePersonalPostJson_(plan, history) {
  var recentTitles = history.titles.slice(0, 15).map(function(t){ return "- " + t; }).join("\n");

  var prompt =
    "Return ONLY valid JSON. No markdown.\n\n" +
    "{\n" +
    '  "keyword": "1-3 words",\n' +
    '  "imageKeyword": "1-3 words",\n' +
    '  "intro": "1-2 sentences",\n' +
    '  "sections": [\n' +
    '    {"h2":"Heading","p":"Max 2 sentences"},\n' +
    '    {"h2":"Heading","p":"Max 2 sentences"},\n' +
    '    {"h2":"Heading","p":"Max 2 sentences"}\n' +
    "  ],\n" +
    '  "takeaway": "1 short sentence",\n' +
    '  "cta": "1 natural sentence",\n' +
    '  "softAffiliate": {\n' +
    '    "enabled": false,\n' +
    '    "item": {"name":"","query":"","why":""}\n' +
    "  }\n" +
    "}\n\n" +

    "STRICT RULES:\n" +
    "- Keep the post SHORT. Do NOT expand simple ideas.\n" +
    "- Sound like a real parent, not a content machine.\n" +
    "- Include a small friction, hesitation, or imperfect moment.\n" +
    "- No names.\n" +
    "- No URLs.\n" +
    "- NEVER use: 'game changer', 'this changed everything'.\n" +
    "- No corporate phrases.\n" +
    "- Short paragraphs only.\n\n" +

    "MANDATORY HUMAN ELEMENTS:\n" +
    "- Include one small moment where something didn't work immediately.\n" +
    "- Include one slightly imperfect or messy situation.\n" +
    "- Avoid sounding too clean or perfectly structured.\n\n" +

    "AFFILIATE RULE:\n" +
    "- Only enable if the product is naturally used in the story.\n" +
    "- Max 1 product.\n\n" +

    "CONTEXT:\n" +
    "Title: " + plan.title + "\n" +
    "Type: " + plan.type + "\n" +
    "Category: " + plan.categorySlug + "\n" +
    "Angle: " + plan.angle + "\n" +
    "Hook: " + plan.hook + "\n" +
    "Scenario: " + plan.scenario + "\n\n" +

    "Recent titles (avoid similarity):\n" + recentTitles + "\n\n" +
    "Voice: " + BLOG_VOICE;

  var ai = JSON.parse(extractJsonObject_(geminiText_(prompt)));

  if (!Array.isArray(ai.sections)) ai.sections = [];
  ai.sections = ai.sections.slice(0, 3);

  if (!ai.softAffiliate || typeof ai.softAffiliate !== "object") {
    ai.softAffiliate = { enabled: false, item: { name: "", query: "", why: "" } };
  }

  ai.intro = humanizeText_(ai.intro);
  ai.takeaway = humanizeText_(ai.takeaway);
  ai.sections = humanizeSections_(ai.sections);

  return ai;
}

/***********************
 * GEMINI TEXT
 ***********************/
function geminiText_(prompt) {
  var url = "https://generativelanguage.googleapis.com/v1beta/" + GEMINI_TEXT_MODEL + ":generateContent?key=" + encodeURIComponent(GEMINI_API_KEY);

  var res = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
    muteHttpExceptions: true
  });

  var code = res.getResponseCode();
  var body = res.getContentText();

  if (code !== 200) throw new Error("Gemini(text) HTTP " + code + ": " + truncate_(body, 800));

  var json = JSON.parse(body);
  var text = json && json.candidates && json.candidates[0] && json.candidates[0].content &&
    json.candidates[0].content.parts && json.candidates[0].content.parts[0]
      ? json.candidates[0].content.parts[0].text
      : "";

  if (!text) throw new Error("Gemini returned empty response.");
  return text;
}

/***********************
 * GEMINI IMAGE
 ***********************/
function generateHeroImage_(title, keyword, categorySlug, angle) {
  var familyLine = FAMILY_VISUAL_PROFILE ? ("Family reference: " + FAMILY_VISUAL_PROFILE + "\n") : "";

  var prompt =
    "Create a 16:9 blog featured image.\n" +
    "Style: " + FAMILY_IMAGE_LOCK_STYLE + ". Modern Scandinavian home vibe.\n" +
    familyLine +
    "Scene: " + keyword + " in a modern family-life setting.\n" +
    "Context: \"" + title + "\". Category: " + categorySlug + ". Angle: " + angle + ".\n" +
    "Rules: no text, no watermarks, no logos, no recognizable brands, avoid names.\n" +
    "Important: consistent character design across images.\n";

  var url = "https://generativelanguage.googleapis.com/v1beta/models/" + encodeURIComponent(GEMINI_IMAGE_MODEL) + ":generateContent";

  var res = UrlFetchApp.fetch(url, {
    method: "post",
    headers: { "x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json" },
    payload: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { responseModalities: ["Image"], imageConfig: { aspectRatio: "16:9" } }
    }),
    muteHttpExceptions: true
  });

  var code = res.getResponseCode();
  var body = res.getContentText();

  if (code !== 200) throw new Error("Gemini(image) HTTP " + code + ": " + truncate_(body, 900));

  var json = JSON.parse(body);
  var parts = json && json.candidates && json.candidates[0] && json.candidates[0].content
    ? (json.candidates[0].content.parts || [])
    : [];

  for (var i = 0; i < parts.length; i++) {
    var inline = parts[i].inlineData || parts[i].inline_data;
    if (inline && inline.data) {
      var mime = inline.mimeType || inline.mime_type || "image/png";
      var bytes = Utilities.base64Decode(inline.data);
      return Utilities.newBlob(bytes, mime, "hero-" + slugify_(keyword) + ".png");
    }
  }

  throw new Error("Gemini(image) returned no inline image data.");
}

/***********************
 * INTERNAL LINKS
 ***********************/
function getInternalLinkCandidates_(rows, plan, maxLinks) {
  maxLinks = maxLinks || 2;
  var pool = [];

  for (var i = 1; i < rows.length; i++) {
    var title = String(rows[i][0] || "").trim();
    var status = String(rows[i][1] || "").trim().toLowerCase();
    var url = String(rows[i][2] || "").trim();
    var cat = String(rows[i][5] || "").trim();
    var angle = String(rows[i][6] || "").trim();

    if (status !== "done") continue;
    if (!title || !url) continue;
    if (title === plan.title) continue;

    if (cat === plan.categorySlug || angle === plan.angle) {
      pool.push({ title: title, url: url, categorySlug: cat, angle: angle });
    }
  }

  pool.reverse();
  return pool.slice(0, maxLinks);
}

function buildInternalLinksBlock_(candidates) {
  if (!candidates || !candidates.length) return "";

  var items = candidates.map(function(it) {
    var href = toRelativeIfSameSite_(stripQueryAndHash_(it.url));

    return '<li style="margin:10px 0;">' +
      '<a href="' + escapeAttr_(href) + '" style="font-weight:600;text-decoration:none;">' +
      escapeHtml_(it.title) +
      "</a></li>";
  }).join("");

  return '<div style="margin-top:24px;">' +
    '<h3 style="margin-bottom:10px;">Related reads</h3>' +
    '<ul style="padding-left:18px;">' + items + "</ul>" +
    "</div>";
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

function ensureCategoryHub_(ss, categorySlug, mainSheet) {
  var hubs = ensureHubsSheet_(ss);
  var data = hubs.getDataRange().getValues();

  for (var i = 1; i < data.length; i++) {
    var slug = String(data[i][0] || "").trim();
    var hubId = String(data[i][1] || "").trim();
    var hubUrl = String(data[i][2] || "").trim();
    var hubTitle = String(data[i][3] || "").trim();

    if (slug === categorySlug && hubId && hubUrl) {
      return { id: hubId, url: hubUrl, title: hubTitle };
    }
  }

  var newHubTitle = hubTitleForCategory_(categorySlug);
  var hubHtml = buildHubHtml_(categorySlug, mainSheet);

  var created = createWpPost_(newHubTitle, hubHtml, null, PERSONAL_DEFAULT_STATUS, categorySlug);
  var newHubId = String(created.ID || created.id || "");
  var newHubUrl = String(created.URL || created.url || "");

  if (!newHubId || !newHubUrl) throw new Error("Hub created but missing ID/URL.");

  hubs.appendRow([categorySlug, newHubId, newHubUrl, newHubTitle, new Date()]);
  return { id: newHubId, url: newHubUrl, title: newHubTitle };
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

  if (hubRow === -1 || !hubId) return;

  var hubHtml = buildHubHtml_(categorySlug, mainSheet);

  var url = "https://public-api.wordpress.com/rest/v1.1/sites/" + encodeURIComponent(WP_SITE_ID) + "/posts/" + encodeURIComponent(hubId);
  var res = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: { Authorization: "Bearer " + WP_OAUTH_TOKEN },
    payload: JSON.stringify({ title: hubTitle || hubTitleForCategory_(categorySlug), content: hubHtml }),
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
    var angle = String(rows[i][6] || "").trim();

    if (status !== "done") continue;
    if (!title || !url) continue;
    if (cat !== categorySlug) continue;

    posts.push({ title: title, url: url, angle: angle || "OTHER", idx: i });
  }

  posts.sort(function(a, b){ return b.idx - a.idx; });

  var grouped = {};
  for (var j = 0; j < posts.length; j++) {
    var a = posts[j].angle || "OTHER";
    if (!grouped[a]) grouped[a] = [];
    grouped[a].push(posts[j]);
  }

  var intro =
    '<p style="font-size:18px;color:#555;">This hub collects our best posts on <strong>' +
    escapeHtml_(categorySlug.replace(/-/g, " ")) +
    '</strong> — grouped by angle, so you can find what you need fast.</p>';

  var sections = "";
  var angleKeys = Object.keys(grouped);

  angleKeys.sort(function(x, y) {
    var ix = ANGLES.indexOf(x);
    var iy = ANGLES.indexOf(y);
    if (ix === -1) ix = 999;
    if (iy === -1) iy = 999;
    return ix - iy;
  });

  for (var k = 0; k < angleKeys.length; k++) {
    var angle = angleKeys[k];
    var nice = angle.replace(/_/g, " ").toLowerCase();
    nice = nice.charAt(0).toUpperCase() + nice.slice(1);

    var list = grouped[angle].slice(0, 30).map(function(p) {
      var href = toRelativeIfSameSite_(stripQueryAndHash_(p.url));
      return '<li style="margin:8px 0;"><a href="' + escapeAttr_(href) + '">' + escapeHtml_(p.title) + "</a></li>";
    }).join("");

    sections += '<h2 style="margin-top:26px;">' + escapeHtml_(nice) + "</h2>" +
      '<ul style="padding-left:18px;margin:10px 0;">' + list + "</ul>";
  }

  var footer = '<p style="font-size:12px;color:#999;margin-top:26px;">Updated automatically as new posts are published.</p>';

  return '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.65;color:#333;max-width:720px;margin:0 auto;">' +
    intro + sections + footer + "</div>";
}

/***********************
 * HTML BUILDER
 ***********************/
function buildPersonalHtml_(plan, ai, hub, candidates) {
  var hubLink = "";
  if (hub && hub.url) {
    var hubHref = toRelativeIfSameSite_(stripQueryAndHash_(hub.url));
    hubLink =
      '<div style="margin:16px 0;padding:14px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
      '<strong>Start here:</strong> ' +
      '<a href="' + escapeAttr_(hubHref) + '" style="text-decoration:none;font-weight:700;">' +
      escapeHtml_(hub.title || "Explore the hub") +
      "</a></div>";
  }

  var intro = '<p style="font-size:18px;color:#555;margin:0 0 16px 0;">' + escapeHtml_(ai.intro || "") + "</p>";

  var sections = (ai.sections || []).map(function(s) {
    return '<h2 style="margin:22px 0 8px 0;">' + escapeHtml_(s.h2 || "") + "</h2>" +
      '<p style="margin:0 0 10px 0;color:#444;">' + escapeHtml_(s.p || "") + "</p>";
  }).join("");

  var takeaway = ai.takeaway
    ? '<div style="background:#f8f8f8;padding:18px;border-radius:12px;border:1px solid #eee;margin:24px 0;"><strong>Takeaway:</strong> ' +
      escapeHtml_(ai.takeaway) + "</div>"
    : "";

  var affiliateBlock = buildSoftAffiliateBlock_(ai.softAffiliate);
  var cta = ai.cta ? ('<p style="margin-top:18px;color:#444;"><em>' + escapeHtml_(ai.cta) + "</em></p>") : "";
  var related = buildInternalLinksBlock_(candidates);

  return '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.65;color:#333;max-width:650px;margin:0 auto;">' +
    hubLink + intro + sections + takeaway + affiliateBlock + cta + related + "</div>";
}

function buildSoftAffiliateBlock_(softAffiliate) {
  if (!softAffiliate || !softAffiliate.enabled || !softAffiliate.item) return "";

  var item = softAffiliate.item;
  var name = String(item.name || "").trim();
  var query = String(item.query || "").trim();
  var why = String(item.why || "").trim();

  if (!name || !query) return "";

  var url = buildAmazonSearchUrl_(query);

  return '<div style="margin-top:24px;padding:16px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
    '<h3 style="margin:0 0 10px 0;">What made it easier</h3>' +
    '<div style="font-weight:600;">' + escapeHtml_(name) + '</div>' +
    (why ? ('<div style="margin-top:6px;color:#666;">' + escapeHtml_(why) + '</div>') : '') +
    '<div style="margin-top:10px;"><a href="' + escapeAttr_(url) + '" target="_blank" rel="nofollow sponsored" style="font-weight:600;text-decoration:none;">Check it on Amazon</a></div>' +
    '</div>';
}

function buildAmazonSearchUrl_(query) {
  var q = encodeURIComponent(String(query || "").trim());
  if (!AMAZON_TAG) {
    return "https://www.amazon." + AMAZON_DOMAIN + "/s?k=" + q;
  }
  return "https://www.amazon." + AMAZON_DOMAIN + "/s?k=" + q + "&tag=" + encodeURIComponent(AMAZON_TAG);
}

/***********************
 * WP HELPERS
 ***********************/
function uploadWpMedia_(blob, title) {
  var safe = slugify_(title || "upload");
  var ct = String(blob.getContentType() || "image/png").toLowerCase();
  var ext = (ct.indexOf("jpeg") !== -1 || ct.indexOf("jpg") !== -1) ? "jpg" : "png";
  blob.setName(safe + "." + ext);

  var res = UrlFetchApp.fetch(
    "https://public-api.wordpress.com/rest/v1.1/sites/" + encodeURIComponent(WP_SITE_ID) + "/media/new",
    {
      method: "post",
      headers: { Authorization: "Bearer " + WP_OAUTH_TOKEN },
      payload: { "media[]": blob, title: title || "upload" },
      muteHttpExceptions: true
    }
  );

  var code = res.getResponseCode();
  var body = res.getContentText();

  if (code !== 200 && code !== 201) {
    throw new Error("Media upload failed HTTP " + code + ": " + truncate_(body, 900));
  }

  var json = JSON.parse(body);
  var id = json && json.media && json.media[0] ? json.media[0].ID : null;
  if (!id) throw new Error("Media upload ok but no ID returned.");
  return id;
}

function createWpPost_(title, html, featuredMediaId, status, categorySlug) {
  var payload = { title: title, content: html, status: status };
  if (featuredMediaId) payload.featured_image = featuredMediaId;

  if (categorySlug) payload.categories = [categorySlug];

  var res = UrlFetchApp.fetch(
    "https://public-api.wordpress.com/rest/v1.1/sites/" + encodeURIComponent(WP_SITE_ID) + "/posts/new",
    {
      method: "post",
      contentType: "application/json",
      headers: { Authorization: "Bearer " + WP_OAUTH_TOKEN },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    }
  );

  var code = res.getResponseCode();
  var body = res.getContentText();

  if (code !== 200 && code !== 201) {
    throw new Error("Create post failed HTTP " + code + ": " + truncate_(body, 1000));
  }

  return JSON.parse(body);
}

/***********************
 * RELATIVE LINK HELPERS
 ***********************/
function stripQueryAndHash_(u) {
  var s = String(u || "").trim();
  return s.split("#")[0].split("?")[0];
}

function toRelativeIfSameSite_(absoluteUrl) {
  var u = String(absoluteUrl || "").trim();
  if (!u) return u;

  if (u.indexOf(SITE_HOME_URL) === 0) {
    var rel = u.slice(SITE_HOME_URL.length);
    if (!rel) return "/";
    return rel.charAt(0) === "/" ? rel : ("/" + rel);
  }

  return u;
}

/***********************
 * UTILS
 ***********************/
function mustProp_(key) {
  var v = PROPS.getProperty(key);
  if (!v) throw new Error("Missing Script Property: " + key);
  return v;
}

function extractJsonObject_(text) {
  var cleaned = String(text || "").replace(/```json/gi, "").replace(/```/g, "").trim();
  var a = cleaned.indexOf("{");
  var b = cleaned.lastIndexOf("}");
  if (a < 0 || b <= a) throw new Error("Could not extract JSON.");
  return cleaned.slice(a, b + 1);
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
    if (!v || seen[v]) continue;
    seen[v] = 1;
    out.push(v);
  }

  return out;
}
/****************************************************
 * TMFG PERSONAL mMACHINE — SEO + HUMANIZED + ROBUST V1
 *
 * Purpose:
 * - Generate personal, human-feeling blog posts
 * - Improve Google ranking potential with:
 *   - clearer topical relevance
 *   - stronger lived-experience signals
 *   - better internal linking
 *   - category hubs
 *   - cleaner heading structure
 *   - lower AI-feel
 *
 * Sheet headers (row 1):
 * A Title | B Status | C Post URL | D Notes | E Type | F CategorySlug | G Angle
 *
 * Usage:
 * - Put "Queued" in column B on empty rows
 * - Run runPersonalMachine()
 ****************************************************/

var PROPS = PropertiesService.getScriptProperties();

// ===== Required =====
var GEMINI_API_KEY = mustProp_("GEMINI_API_KEY");
var WP_OAUTH_TOKEN = mustProp_("WP_OAUTH_TOKEN");
var WP_SITE_ID = mustProp_("WP_SITE_ID");

// ===== Controls =====
var PERSONAL_DEFAULT_STATUS = String(PROPS.getProperty("PERSONAL_DEFAULT_STATUS") || "publish").toLowerCase();
var PERSONAL_MAX_POSTS_PER_RUN = parseInt(PROPS.getProperty("PERSONAL_MAX_POSTS_PER_RUN") || "1", 10) || 1;
var PERSONAL_INCLUDE_FEATURED_IMAGE = String(PROPS.getProperty("PERSONAL_INCLUDE_FEATURED_IMAGE") || "true").toLowerCase() === "true";

var GEMINI_TEXT_MODEL = "models/gemini-2.5-flash";
var GEMINI_IMAGE_MODEL = String(PROPS.getProperty("GEMINI_IMAGE_MODEL") || "gemini-3.1-flash-image-preview").trim();

var BLOG_VOICE = String(PROPS.getProperty("BLOG_VOICE") ||
  "Warm, honest, practical modern family voice. Calm, grounded, lightly human, sometimes lightly funny. Short paragraphs. No fluff. No corporate tone. No therapy jargon."
).trim();

var FAMILY_VISUAL_PROFILE = String(PROPS.getProperty("FAMILY_VISUAL_PROFILE") || "").trim();
var FAMILY_IMAGE_LOCK_STYLE = String(PROPS.getProperty("FAMILY_IMAGE_LOCK_STYLE") ||
  "clean cartoon caricature, soft shading, modern family illustration, consistent character design across images"
).trim();

var HUBS_SHEET_NAME = "Hubs";

// ===== Taxonomy =====
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

var TONE_MODES = [
  "PRACTICAL",
  "TIRED",
  "LIGHTLY_FUNNY",
  "REFLECTIVE",
  "RELIEVED"
];

// ===== Retry controls =====
var GEMINI_TEXT_MAX_RETRIES = 3;
var GEMINI_IMAGE_MAX_RETRIES = 3;

/***********************
 * ENTRY
 ***********************/
function runPersonalMachine() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(25000)) return;

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();
    var rows = sheet.getDataRange().getValues();

    ensureHubsSheet_(ss);

    var processed = 0;

    for (var i = 1; i < rows.length; i++) {
      if (processed >= PERSONAL_MAX_POSTS_PER_RUN) break;

      var status = String(rows[i][1] || "").trim().toLowerCase();
      var rowIndex = i + 1;

      if (status !== "queued") continue;

      try {
        sheet.getRange(rowIndex, 3).setValue("");
        sheet.getRange(rowIndex, 4).setValue("");

        var history = getHistory_(rows, 50);

        // 1) Plan
        var plan = generateEditorialPlan_(history);

        sheet.getRange(rowIndex, 1).setValue(plan.title);
        sheet.getRange(rowIndex, 5).setValue(plan.type);
        sheet.getRange(rowIndex, 6).setValue(plan.categorySlug);
        sheet.getRange(rowIndex, 7).setValue(plan.angle);

        // 2) Ensure hub exists
        var hub = ensureCategoryHub_(ss, plan.categorySlug);

        // 3) Generate content JSON
        var ai = generatePersonalPostJson_(plan, history);

        // 4) Try image, but do not fail whole post if image fails
        var mediaId = null;
        var imageStatus = "no";
        if (PERSONAL_INCLUDE_FEATURED_IMAGE) {
          try {
            var heroKeyword = String(ai.imageKeyword || ai.keyword || plan.title).trim();
            var heroBlob = generateHeroImage_(plan, heroKeyword, plan.categorySlug, plan.angle);
            mediaId = uploadWpMedia_(heroBlob, "featured-" + slugify_(plan.title));
            imageStatus = "yes";
          } catch (imgErr) {
            imageStatus = "fallback-no-image";
          }
        }

        // 5) Internal links
        var candidates = getInternalLinkCandidates_(rows, plan, 3);

        // 6) Build content
        var html = buildPersonalHtml_(plan, ai, hub, candidates);

        // 7) Create post
        var post = createWpPost_(plan.title, html, mediaId, PERSONAL_DEFAULT_STATUS, plan.categorySlug);

        // 8) Update row
        sheet.getRange(rowIndex, 2).setValue("Done");
        sheet.getRange(rowIndex, 3).setValue(post.URL || post.url || "");
        sheet.getRange(rowIndex, 4).setValue(
          "OK | " + plan.type +
          " | " + plan.categorySlug +
          " | " + plan.angle +
          " | " + plan.toneMode +
          " | Img:" + imageStatus
        );

        // 9) Update hub
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
 * PLANNING
 ***********************/
function generateEditorialPlan_(history) {
  var bannedTypes = uniq_(history.types.slice(0, 2));
  var bannedCats = uniq_(history.categories.slice(0, 2));
  var bannedAngles = uniq_(history.angles.slice(0, 2));
  var recentTitles = history.titles.slice(0, 25);

  var prompt =
    "Return ONLY valid JSON. No markdown.\n\n" +
    "{\n" +
    '  "title": "Max 70 chars. Concrete, searchable, specific, natural.",\n' +
    '  "type": "ONE of: ' + POST_TYPES.join(", ") + '",\n' +
    '  "categorySlug": "ONE of: ' + CATEGORY_SLUGS.join(", ") + '",\n' +
    '  "angle": "ONE of: ' + ANGLES.join(", ") + '",\n' +
    '  "hook": "One sentence: why this post is worth reading",\n' +
    '  "scenario": "One sentence: a concrete real-life family situation",\n' +
    '  "friction": "One concrete frustration or problem",\n' +
    '  "smallWin": "One small practical thing that helped",\n' +
    '  "sceneDetail": "One specific sensory or household detail",\n' +
    '  "toneMode": "ONE of: ' + TONE_MODES.join(", ") + '"\n' +
    "}\n\n" +
    "Rules:\n" +
    "- Avoid naming any family member names.\n" +
    "- Avoid generic content-marketing titles.\n" +
    "- Avoid obvious AI title patterns.\n" +
    "- Prefer lived, practical, searchable titles.\n" +
    "- Title must feel like something a real parent would search or click.\n" +
    "- Do NOT reuse recent title patterns.\n" +
    "- Avoid these overused openings: Our..., Simple..., Calm..., Quiet..., Easy....\n" +
    "- Ground the idea in a real family moment.\n\n" +
    "Banned:\n" +
    "- type: " + (bannedTypes.length ? bannedTypes.join(", ") : "(none)") + "\n" +
    "- categorySlug: " + (bannedCats.length ? bannedCats.join(", ") : "(none)") + "\n" +
    "- angle: " + (bannedAngles.length ? bannedAngles.join(", ") : "(none)") + "\n\n" +
    "Recent titles to avoid copying:\n" + recentTitles.map(function(t){ return "- " + t; }).join("\n") + "\n\n" +
    "Voice:\n" + BLOG_VOICE;

  for (var attempt = 1; attempt <= 4; attempt++) {
    var raw = geminiText_(prompt);
    var plan = parseJsonObjectWithRepair_(raw);

    plan.title = String(plan.title || "").trim().slice(0, 70);
    plan.type = String(plan.type || "").trim().toUpperCase();
    plan.categorySlug = String(plan.categorySlug || "").trim();
    plan.angle = String(plan.angle || "").trim();
    plan.hook = String(plan.hook || "").trim();
    plan.scenario = String(plan.scenario || "").trim();
    plan.friction = String(plan.friction || "").trim();
    plan.smallWin = String(plan.smallWin || "").trim();
    plan.sceneDetail = String(plan.sceneDetail || "").trim();
    plan.toneMode = String(plan.toneMode || "").trim().toUpperCase();

    if (!plan.title) continue;
    if (POST_TYPES.indexOf(plan.type) === -1) continue;
    if (CATEGORY_SLUGS.indexOf(plan.categorySlug) === -1) continue;
    if (ANGLES.indexOf(plan.angle) === -1) continue;
    if (TONE_MODES.indexOf(plan.toneMode) === -1) continue;
    if (bannedTypes.indexOf(plan.type) !== -1) continue;
    if (bannedCats.indexOf(plan.categorySlug) !== -1) continue;
    if (bannedAngles.indexOf(plan.angle) !== -1) continue;
    if (isTitleTooSimilar_(plan.title, history.titles.slice(0, 12))) continue;

    return plan;
  }

  throw new Error("Could not generate a valid editorial plan.");
}

/***********************
 * CONTENT GENERATION
 ***********************/
function generatePersonalPostJson_(plan, history) {
  var recentTitles = history.titles.slice(0, 25).map(function(t){ return "- " + t; }).join("\n");

  var schema =
    "Return ONLY valid JSON. No markdown.\n\n" +
    "{\n" +
    '  "keyword": "1-3 words",\n' +
    '  "imageKeyword": "1-3 words",\n' +
    '  "seoSummary": "1-2 short sentences that clearly state the topic and practical value",\n' +
    '  "intro": "2-3 sentences",\n' +
    '  "experienceBox": {\n' +
    '    "title": "Short heading",\n' +
    '    "text": "2-4 sentences describing what actually happened in our home"\n' +
    "  },\n" +
    '  "sections": [\n' +
    '    {"h2":"Heading","p":"Short paragraph"},\n' +
    '    {"h2":"Heading","p":"Short paragraph"},\n' +
    '    {"h2":"Heading","p":"Short paragraph"}\n' +
    "  ],\n" +
    '  "whatChanged": ["short practical change 1","short practical change 2","short practical change 3"],\n' +
    '  "takeaway": "1 short paragraph",\n' +
    '  "cta": "1 sentence encouraging a comment or share",\n' +
    '  "faq": [\n' +
    '    {"q":"Question","a":"2-4 sentences"},\n' +
    '    {"q":"Question","a":"2-4 sentences"},\n' +
    '    {"q":"Question","a":"2-4 sentences"}\n' +
    "  ]\n" +
    "}\n\n" +
    "Rules:\n" +
    "- No URLs.\n" +
    "- Avoid naming family members.\n" +
    "- Short paragraphs.\n" +
    "- Use 'we' and 'our' naturally.\n" +
    "- This must feel lived, not generated.\n" +
    "- Include one small failure, one emotional truth, and one practical adjustment.\n" +
    "- Avoid generic filler like 'family life can be busy' or 'it is important to'.\n" +
    "- Prefer concrete details: shoes by the door, cold pasta, a rushed school morning, a cluttered counter.\n" +
    "- Match the title, category, angle and tone closely.\n" +
    "- Make the post helpful and rankable for Google by being specific and relevant.\n\n" +
    "Recent titles to avoid overlapping with:\n" + recentTitles + "\n\n" +
    "Voice:\n" + BLOG_VOICE;

  var prompt =
    "Blog: The Modern Family Guide\n" +
    "Title: " + plan.title + "\n" +
    "Type: " + plan.type + "\n" +
    "CategorySlug: " + plan.categorySlug + "\n" +
    "Angle: " + plan.angle + "\n" +
    "ToneMode: " + plan.toneMode + "\n" +
    "Hook: " + plan.hook + "\n" +
    "Scenario: " + plan.scenario + "\n" +
    "Friction: " + plan.friction + "\n" +
    "SmallWin: " + plan.smallWin + "\n" +
    "SceneDetail: " + plan.sceneDetail + "\n\n" +
    "ANGLE directive:\n" + angleDirective_(plan.angle) + "\n\n" +
    "TYPE directive:\n" + postTypeDirective_(plan.type) + "\n\n" +
    "TONE directive:\n" + toneDirective_(plan.toneMode) + "\n\n" +
    schema;

  for (var attempt = 1; attempt <= 4; attempt++) {
    var raw = geminiText_(prompt);
    var ai = parseJsonObjectWithRepair_(raw);

    if (!ai || typeof ai !== "object") continue;

    ai.keyword = String(ai.keyword || "").trim();
    ai.imageKeyword = String(ai.imageKeyword || "").trim();
    ai.seoSummary = String(ai.seoSummary || "").trim();
    ai.intro = String(ai.intro || "").trim();
    ai.takeaway = String(ai.takeaway || "").trim();
    ai.cta = String(ai.cta || "").trim();

    if (!ai.experienceBox || typeof ai.experienceBox !== "object") ai.experienceBox = {};
    ai.experienceBox.title = String(ai.experienceBox.title || "").trim();
    ai.experienceBox.text = String(ai.experienceBox.text || "").trim();

    if (!Array.isArray(ai.sections)) ai.sections = [];
    if (!Array.isArray(ai.faq)) ai.faq = [];
    if (!Array.isArray(ai.whatChanged)) ai.whatChanged = [];

    ai.sections = ai.sections.slice(0, 4).map(function(s) {
      return {
        h2: String((s && s.h2) ? s.h2 : "").trim(),
        p: String((s && s.p) ? s.p : "").trim()
      };
    }).filter(function(s) { return s.h2 && s.p; });

    ai.faq = ai.faq.slice(0, 3).map(function(f) {
      return {
        q: String((f && f.q) ? f.q : "").trim(),
        a: String((f && f.a) ? f.a : "").trim()
      };
    }).filter(function(f) { return f.q && f.a; });

    ai.whatChanged = ai.whatChanged.slice(0, 5).map(function(x) {
      return String(x || "").trim();
    }).filter(Boolean);

    if (!ai.intro) continue;
    if (!ai.sections.length) continue;

    return ai;
  }

  throw new Error("Could not generate valid post JSON.");
}

/***********************
 * PROMPT DIRECTIVES
 ***********************/
function angleDirective_(angle) {
  switch (angle) {
    case "SYSTEMS_AND_ROUTINES": return "Focus on repeatable systems. Show a tiny habit or rule that makes the system stick.";
    case "LOW_ENERGY_MODE": return "Write for tired parents. Keep the solution small, realistic and forgiving.";
    case "TIME_SAVING": return "Show exactly where the time is saved. Use time boxes and specific moments of the day.";
    case "MONEY_SAVING": return "Give practical savings without sounding cheap or joyless.";
    case "CONFLICT_REDUCTION": return "Reduce friction with one boundary, one phrase, one shift in setup or expectation.";
    case "KID_BEHAVIOR": return "Focus on cues, environment, rhythm and one practical response when it goes wrong.";
    case "HOME_RESET": return "Emphasise visible relief, one contained reset area, and realistic upkeep.";
    case "MEAL_SIMPLIFICATION": return "Make the meal system feel easy, flexible and weeknight-friendly.";
    case "TRAVEL_PREP": return "Focus on prep, leaving the house, and the little thing that prevents chaos later.";
    case "EMOTIONAL_REFLECTION": return "Ground the feeling in a real moment and end with something practical.";
    case "MINIMALISM": return "Less but better. Show relief, clearer space and reduced mental noise.";
    case "REAL_WORLD_EXAMPLE":
    default: return "Use one clear household moment and extract a repeatable lesson from it.";
  }
}

function postTypeDirective_(type) {
  switch (type) {
    case "SUNDAY_RESET": return "Include a realistic 20-45 minute reset, a low-pressure rhythm, and a practical carry-over into the week.";
    case "REAL_LIFE_HACKS": return "Write as a practical family tip post, but keep it grounded in one real use case.";
    case "FAMILY_ACTIVITY": return "Keep the activity realistic, low-cost, and clear about why it worked.";
    case "RELATIONSHIP_MINI": return "Keep it practical and respectful. Focus on one small relational shift, not a grand lesson.";
    case "RECIPE_NOTE": return "Keep it practical, flexible, weeknight-friendly, and based on real kitchen constraints.";
    case "PERSONAL_STORY":
    default: return "Write like a short lived story that turns into useful advice.";
  }
}

function toneDirective_(toneMode) {
  switch (toneMode) {
    case "TIRED": return "Tone: slightly worn out, gentle, honest, low-energy.";
    case "LIGHTLY_FUNNY": return "Tone: lightly funny, warm, dry, never silly.";
    case "REFLECTIVE": return "Tone: reflective and grounded, but still useful.";
    case "RELIEVED": return "Tone: small relief, calm, 'this finally helped' energy.";
    case "PRACTICAL":
    default: return "Tone: practical, direct, quietly reassuring.";
  }
}

/***********************
 * GEMINI HELPERS
 ***********************/
function geminiText_(prompt) {
  var lastErr = null;

  for (var attempt = 1; attempt <= GEMINI_TEXT_MAX_RETRIES; attempt++) {
    try {
      var url = "https://generativelanguage.googleapis.com/v1beta/" + GEMINI_TEXT_MODEL + ":generateContent?key=" + encodeURIComponent(GEMINI_API_KEY);

      var res = UrlFetchApp.fetch(url, {
        method: "post",
        contentType: "application/json",
        payload: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }]
        }),
        muteHttpExceptions: true
      });

      var code = res.getResponseCode();
      var body = res.getContentText();

      if (code === 200) {
        var json = JSON.parse(body);
        var text = json &&
          json.candidates &&
          json.candidates[0] &&
          json.candidates[0].content &&
          json.candidates[0].content.parts &&
          json.candidates[0].content.parts[0]
            ? json.candidates[0].content.parts[0].text
            : "";

        if (!text) throw new Error("Gemini returned empty response.");
        return text;
      }

      if (code === 429 || code === 503) {
        lastErr = new Error("Gemini(text) HTTP " + code + ": " + truncate_(body, 400));
        Utilities.sleep(1500 * attempt);
        continue;
      }

      throw new Error("Gemini(text) HTTP " + code + ": " + truncate_(body, 800));

    } catch (e) {
      lastErr = e;
      Utilities.sleep(1200 * attempt);
    }
  }

  throw lastErr || new Error("Gemini(text) failed after retries.");
}

function generateHeroImage_(plan, keyword, categorySlug, angle) {
  var familyLine = FAMILY_VISUAL_PROFILE ? ("Family reference: " + FAMILY_VISUAL_PROFILE + "\n") : "";
  var prompt =
    "Create a 16:9 blog featured image.\n" +
    "Style: " + FAMILY_IMAGE_LOCK_STYLE + ". Friendly, modern family illustration.\n" +
    familyLine +
    "Scene: " + keyword + " in a modern family-life setting.\n" +
    "Context: \"" + plan.title + "\". Category: " + categorySlug + ". Angle: " + angle + ".\n" +
    "Rules: no text, no watermarks, no logos, no recognizable brands, avoid names.\n" +
    "Consistent character design across images.\n";

  var lastErr = null;

  for (var attempt = 1; attempt <= GEMINI_IMAGE_MAX_RETRIES; attempt++) {
    try {
      var url = "https://generativelanguage.googleapis.com/v1beta/models/" + encodeURIComponent(GEMINI_IMAGE_MODEL) + ":generateContent";
      var res = UrlFetchApp.fetch(url, {
        method: "post",
        headers: { "x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json" },
        payload: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: {
            responseModalities: ["Image"],
            imageConfig: { aspectRatio: "16:9" }
          }
        }),
        muteHttpExceptions: true
      });

      var code = res.getResponseCode();
      var body = res.getContentText();

      if (code === 200) {
        var json = JSON.parse(body);
        var parts = (json && json.candidates && json.candidates[0] && json.candidates[0].content)
          ? (json.candidates[0].content.parts || [])
          : [];

        for (var i = 0; i < parts.length; i++) {
          var part = parts[i];
          var inline = part.inlineData || part.inline_data;
          if (inline && inline.data) {
            var mime = inline.mimeType || inline.mime_type || "image/png";
            var bytes = Utilities.base64Decode(inline.data);
            return Utilities.newBlob(bytes, mime, "hero-" + slugify_(keyword) + ".png");
          }
        }
        throw new Error("Gemini(image) returned no inline image data.");
      }

      if (code === 429 || code === 503) {
        lastErr = new Error("Gemini(image) HTTP " + code + ": " + truncate_(body, 500));
        Utilities.sleep(2000 * attempt);
        continue;
      }

      throw new Error("Gemini(image) HTTP " + code + ": " + truncate_(body, 900));

    } catch (e) {
      lastErr = e;
      Utilities.sleep(1600 * attempt);
    }
  }

  throw lastErr || new Error("Gemini(image) failed after retries.");
}

/***********************
 * JSON ROBUSTNESS
 ***********************/
function parseJsonObjectWithRepair_(text) {
  var cleaned = cleanModelText_(text);

  try {
    return JSON.parse(extractJsonObject_(cleaned));
  } catch (e1) {}

  try {
    var repaired = repairCommonJsonIssues_(extractJsonObject_(cleaned));
    return JSON.parse(repaired);
  } catch (e2) {}

  throw new Error("Could not parse model JSON.");
}

function cleanModelText_(text) {
  return String(text || "")
    .replace(/```json/gi, "")
    .replace(/```/g, "")
    .trim();
}

function extractJsonObject_(text) {
  var cleaned = String(text || "").trim();
  var start = cleaned.indexOf("{");
  if (start < 0) throw new Error("JSON start not found.");

  var depth = 0;
  var inString = false;
  var escape = false;
  var end = -1;

  for (var i = start; i < cleaned.length; i++) {
    var ch = cleaned.charAt(i);

    if (escape) {
      escape = false;
      continue;
    }

    if (ch === "\\") {
      if (inString) escape = true;
      continue;
    }

    if (ch === "\"") {
      inString = !inString;
      continue;
    }

    if (!inString) {
      if (ch === "{") depth++;
      if (ch === "}") {
        depth--;
        if (depth === 0) {
          end = i;
          break;
        }
      }
    }
  }

  if (end < 0) throw new Error("JSON end not found.");
  return cleaned.substring(start, end + 1);
}

function repairCommonJsonIssues_(jsonText) {
  var s = String(jsonText || "");

  // smart quotes
  s = s.replace(/[“”]/g, "\"").replace(/[‘’]/g, "'");

  // trailing commas before } or ]
  s = s.replace(/,\s*([}\]])/g, "$1");

  // remove control chars except newline tab carriage return
  s = s.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "");

  return s;
}

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
    if (it.categorySlug && it.categorySlug === plan.categorySlug) s += 50;
    if (it.angle && it.angle === plan.angle) s += 35;
    if (it.type && it.type === plan.type) s += 10;
    if (it.angle && it.angle !== plan.angle && isTypeFamilyRelated_(it.type, plan.type)) s += 18;
    s += Math.min(10, Math.floor(it.idx / 50));

    var overlap = titleJaccardLite_(it.title, plan.title);
    if (overlap >= 0.35) s -= 25;
    if (overlap >= 0.50) s -= 60;

    return s;
  }

  function tryPick(filterFn) {
    if (picked.length >= maxLinks) return;
    var best = null;
    var bestScore = -999999;

    for (var j = 0; j < pool.length; j++) {
      var it = pool[j];
      if (used[it.url]) continue;
      if (!filterFn(it)) continue;

      var sc = score(it);
      if (sc > bestScore) {
        bestScore = sc;
        best = it;
      }
    }

    if (best) {
      used[best.url] = true;
      picked.push(best);
    }
  }

  tryPick(function(it) { return it.categorySlug && it.categorySlug === plan.categorySlug; });
  tryPick(function(it) { return it.angle && it.angle === plan.angle; });
  tryPick(function(it) { return it.angle && it.angle !== plan.angle && isTypeFamilyRelated_(it.type, plan.type); });

  while (picked.length < maxLinks) {
    var best2 = null;
    var bestScore2 = -999999;

    for (var k = 0; k < pool.length; k++) {
      var it2 = pool[k];
      if (used[it2.url]) continue;
      var sc2 = score(it2);
      if (sc2 > bestScore2) {
        bestScore2 = sc2;
        best2 = it2;
      }
    }

    if (!best2) break;
    used[best2.url] = true;
    picked.push(best2);
  }

  return picked.slice(0, maxLinks);
}

function isTypeFamilyRelated_(a, b) {
  a = String(a || "").toUpperCase();
  b = String(b || "").toUpperCase();

  var SYSTEMS = { "SUNDAY_RESET":1, "REAL_LIFE_HACKS":1, "PERSONAL_STORY":1 };
  var HOMEKIDS = { "FAMILY_ACTIVITY":1, "REAL_LIFE_HACKS":1, "PERSONAL_STORY":1 };
  var FOOD = { "RECIPE_NOTE":1, "REAL_LIFE_HACKS":1, "PERSONAL_STORY":1 };
  var REL = { "RELATIONSHIP_MINI":1, "PERSONAL_STORY":1 };

  function which(x) {
    if (SYSTEMS[x]) return "SYSTEMS";
    if (HOMEKIDS[x]) return "HOMEKIDS";
    if (FOOD[x]) return "FOOD";
    if (REL[x]) return "REL";
    return "OTHER";
  }

  return which(a) === which(b) && which(a) !== "OTHER";
}

function titleJaccardLite_(t1, t2) {
  var a = normalizeTitleTokensLite_(t1);
  var b = normalizeTitleTokensLite_(t2);
  if (!a.length || !b.length) return 0;

  var setA = {}, setB = {};
  for (var i = 0; i < a.length; i++) setA[a[i]] = 1;
  for (var j = 0; j < b.length; j++) setB[b[j]] = 1;

  var inter = 0, uni = 0;
  for (var k in setA) { uni++; if (setB[k]) inter++; }
  for (var k2 in setB) { if (!setA[k2]) uni++; }

  return uni ? (inter / uni) : 0;
}

function normalizeTitleTokensLite_(s) {
  var stop = {
    "a":1,"an":1,"and":1,"the":1,"to":1,"of":1,"for":1,"in":1,"on":1,"with":1,
    "our":1,"my":1,"your":1,"week":1,"sunday":1,"routine":1,"reset":1
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

function buildInternalLinksBlock_(candidates, plan) {
  if (!candidates || !candidates.length) return "";

  var items = candidates.slice(0, 3).map(function(it) {
    var reason = internalReason_(it, plan);
    var href = isInternalUrl_(it.url) ? makeRelativeUrl_(it.url) : it.url;

    return '<li style="margin:10px 0;">' +
      '<a href="' + escapeAttr_(href) + '" style="text-decoration:none;font-weight:700;">' + escapeHtml_(it.title) + '</a>' +
      (reason ? ('<div style="color:#666;font-size:13px;margin-top:3px;">' + escapeHtml_(reason) + '</div>') : "") +
      '</li>';
  }).join("");

  return (
    '<div style="margin-top:28px;padding:18px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
    '<h2 style="margin:0 0 10px 0;">You might also find helpful</h2>' +
    '<ul style="margin:0;padding-left:18px;">' + items + '</ul>' +
    '</div>'
  );
}

function internalReason_(it, plan) {
  if (it.categorySlug && it.categorySlug === plan.categorySlug) return "Same topic cluster — a natural next read.";
  if (it.angle && it.angle === plan.angle) return "Same angle — a deeper cut on the same kind of solution.";
  return "A helpful bridge — connected, but not more of the exact same.";
}

/***********************
 * URL HELPERS
 ***********************/
function makeRelativeUrl_(url) {
  var s = String(url || "").trim();
  if (!s) return s;
  if (s.indexOf("/") === 0 && s.indexOf("//") !== 0) return s;

  var m = s.match(/^https?:\/\/[^\/]+(\/.*)$/i);
  if (m && m[1]) return m[1];
  return s;
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
  var created = createWpPost_(hubTitle, hubHtml, null, PERSONAL_DEFAULT_STATUS, categorySlug);

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
    var angle = String(rows[i][6] || "").trim();

    if (status !== "done") continue;
    if (!title || !url) continue;
    if (cat !== categorySlug) continue;

    posts.push({ title: title, url: url, angle: angle || "OTHER", idx: i });
  }

  posts.sort(function(a, b) { return b.idx - a.idx; });

  var grouped = {};
  for (var j = 0; j < posts.length; j++) {
    var a = posts[j].angle || "OTHER";
    if (!grouped[a]) grouped[a] = [];
    grouped[a].push(posts[j]);
  }

  var intro =
    '<p style="font-size:18px;color:#555;">' +
    'This hub collects our best posts on <strong>' + escapeHtml_(categorySlug.replace(/-/g, " ")) +
    '</strong> so you can explore the topic more easily.</p>';

  var sections = "";
  var angleKeys = Object.keys(grouped);

  angleKeys.sort(function(x, y) {
    var ix = ANGLES.indexOf(x); if (ix === -1) ix = 999;
    var iy = ANGLES.indexOf(y); if (iy === -1) iy = 999;
    return ix - iy;
  });

  for (var k = 0; k < angleKeys.length; k++) {
    var angle = angleKeys[k];
    var nice = angle.replace(/_/g, " ").toLowerCase();
    nice = nice.charAt(0).toUpperCase() + nice.slice(1);

    var list = grouped[angle].slice(0, 30).map(function(p) {
      var href = isInternalUrl_(p.url) ? makeRelativeUrl_(p.url) : p.url;
      return '<li style="margin:8px 0;"><a href="' + escapeAttr_(href) + '">' + escapeHtml_(p.title) + '</a></li>';
    }).join("");

    sections += '<h2 style="margin-top:26px;">' + escapeHtml_(nice) + '</h2>' +
      '<ul style="padding-left:18px;margin:10px 0;">' + list + '</ul>';
  }

  return (
    '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.65;color:#333;max-width:720px;margin:0 auto;">' +
    intro +
    sections +
    '<p style="font-size:12px;color:#999;margin-top:26px;">Updated automatically as new posts are published.</p>' +
    '</div>'
  );
}

/***********************
 * HTML OUTPUT
 ***********************/
function buildPersonalHtml_(plan, ai, hub, candidates) {
  var seoSummary = ai.seoSummary
    ? '<p style="font-size:17px;color:#4b4b4b;margin:0 0 14px 0;">' + escapeHtml_(ai.seoSummary) + '</p>'
    : '';

  var hubLink = "";
  if (hub && hub.url) {
    var hubHref = isInternalUrl_(hub.url) ? makeRelativeUrl_(hub.url) : hub.url;
    hubLink =
      '<div style="margin:16px 0;padding:14px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
      '<strong>Start here:</strong> ' +
      '<a href="' + escapeAttr_(hubHref) + '" style="text-decoration:none;font-weight:700;">' +
      escapeHtml_(hub.title || "Explore the hub") +
      '</a>' +
      '</div>';
  }

  var intro = '<p style="font-size:18px;color:#555;margin:0 0 16px 0;">' + escapeHtml_(ai.intro || "") + '</p>';

  var experienceBox = "";
  if (ai.experienceBox && ai.experienceBox.title && ai.experienceBox.text) {
    experienceBox =
      '<div style="background:#f8f8f8;padding:18px;border-radius:12px;border:1px solid #eee;margin:20px 0;">' +
      '<strong>' + escapeHtml_(ai.experienceBox.title) + '</strong>' +
      '<p style="margin:8px 0 0 0;color:#444;">' + escapeHtml_(ai.experienceBox.text) + '</p>' +
      '</div>';
  }

  var inline = (candidates || []).slice(0, 2);

  var sections = (ai.sections || []).map(function(s, idx) {
    var h2 = escapeHtml_(s.h2 || "");
    var pText = String(s.p || "");
    var pHtml = escapeHtml_(pText);

    if (inline[idx] && shouldInlineLink_(pText)) {
      pHtml = injectInlineLinkIntoEscapedParagraph_(pHtml, inline[idx]);
    }

    return '<h2 style="margin:22px 0 8px 0;">' + h2 + '</h2>' +
      '<p style="margin:0 0 10px 0;color:#444;">' + pHtml + '</p>';
  }).join("");

  var whatChanged = "";
  if (ai.whatChanged && ai.whatChanged.length) {
    whatChanged =
      '<div style="margin:20px 0;">' +
      '<h2 style="margin:0 0 8px 0;">What changed for us</h2>' +
      '<ul style="padding-left:20px;margin:0;">' +
      ai.whatChanged.map(function(x) {
        return '<li>' + escapeHtml_(x) + '</li>';
      }).join("") +
      '</ul></div>';
  }

  var takeaway = ai.takeaway
    ? '<div style="background:#f8f8f8;padding:18px;border-radius:12px;border:1px solid #eee;margin:24px 0;">' +
      '<strong>Takeaway:</strong> ' + escapeHtml_(ai.takeaway) +
      '</div>'
    : '';

  var faqItems = (ai.faq || []).slice(0, 3).map(function(f) {
    return '<h3 style="margin:16px 0 6px 0;font-size:16px;">' + escapeHtml_(f.q || "") + '</h3>' +
      '<p style="margin:0 0 10px 0;color:#444;">' + escapeHtml_(f.a || "") + '</p>';
  }).join("");

  var faq = faqItems ? '<h2 style="margin-top:26px;">FAQ</h2>' + faqItems : '';
  var cta = ai.cta ? '<p style="margin-top:18px;color:#444;"><em>' + escapeHtml_(ai.cta) + '</em></p>' : '';
  var related = buildInternalLinksBlock_(candidates, plan);

  return (
    '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.65;color:#333;max-width:650px;margin:0 auto;">' +
    seoSummary +
    hubLink +
    intro +
    experienceBox +
    sections +
    whatChanged +
    takeaway +
    faq +
    cta +
    related +
    '</div>'
  );
}

function shouldInlineLink_(plainText) {
  var t = String(plainText || "");
  if (t.length < 180) return false;
  if (t.indexOf("http") !== -1) return false;
  return true;
}

function injectInlineLinkIntoEscapedParagraph_(escapedParagraph, candidate) {
  var text = String(escapedParagraph || "");
  var parts = text.split(". ");
  if (parts.length < 2) return text;

  var href = isInternalUrl_(candidate.url) ? makeRelativeUrl_(candidate.url) : candidate.url;
  var link = ' <a href="' + escapeAttr_(href) + '" style="text-decoration:underline;">' +
    escapeHtml_(candidate.title) + '</a>';

  parts[0] = parts[0] + "." + link;
  return parts.join(". ");
}

/***********************
 * WORDPRESS
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
  var id = (json && json.media && json.media[0]) ? json.media[0].ID : null;
  if (!id) throw new Error("Media upload ok but no ID returned.");
  return id;
}

function createWpPost_(title, html, featuredMediaId, status, categorySlug) {
  var payload = {
    title: title,
    content: html,
    status: status
  };

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
 * TITLE SIMILARITY
 ***********************/
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
  var setA = {}, setB = {};
  for (var i = 0; i < a.length; i++) setA[a[i]] = 1;
  for (var j = 0; j < b.length; j++) setB[b[j]] = 1;

  var inter = 0, uni = 0;
  for (var k in setA) { uni++; if (setB[k]) inter++; }
  for (var k2 in setB) { if (!setA[k2]) uni++; }
  return uni ? (inter / uni) : 0;
}

/***********************
 * UTILS
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

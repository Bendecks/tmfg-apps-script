/****************************************************
 * TMFG V2 — MAIN
 * Entry points + high-level orchestration
 ****************************************************/

var PROPS = PropertiesService.getScriptProperties();

// ===== Required =====
var GEMINI_API_KEY = mustProp_("GEMINI_API_KEY");
var WP_OAUTH_TOKEN = mustProp_("WP_OAUTH_TOKEN");
var WP_SITE_ID = mustProp_("WP_SITE_ID");

// ===== Controls =====
var DEFAULT_STATUS = String(PROPS.getProperty("PERSONAL_DEFAULT_STATUS") || "publish").toLowerCase();
var MAX_POSTS_PER_RUN = parseInt(PROPS.getProperty("PERSONAL_MAX_POSTS_PER_RUN") || "1", 10) || 1;
var INCLUDE_FEATURED_IMAGE = String(PROPS.getProperty("PERSONAL_INCLUDE_FEATURED_IMAGE") || "true").toLowerCase() === "true";
var INCLUDE_INLINE_IMAGES = String(PROPS.getProperty("INCLUDE_INLINE_IMAGES") || "true").toLowerCase() === "true";
var IMAGE_STYLE_MODE = String(PROPS.getProperty("IMAGE_STYLE_MODE") || "realistic").trim().toLowerCase();

var GEMINI_TEXT_MODEL = "models/gemini-2.5-flash";
var GEMINI_IMAGE_MODEL = String(PROPS.getProperty("GEMINI_IMAGE_MODEL") || "gemini-3.1-flash-image-preview").trim();

var BLOG_VOICE = String(PROPS.getProperty("BLOG_VOICE") ||
  "Warm, practical, grounded family voice. Helpful first. Specific, lived, clear, lightly human. No fluff. No corporate tone. No therapy jargon."
).trim();

var FAMILY_VISUAL_PROFILE = String(PROPS.getProperty("FAMILY_VISUAL_PROFILE") || "").trim();

var HUBS_SHEET_NAME = "Hubs";

// Cluster taxonomy
var CLUSTERS = [
  "HOME_SYSTEMS",
  "LOW_EFFORT_FOOD",
  "PROBLEM_SOLVERS",
  "EXPERIENCE_POSTS"
];

// Content formats
var POST_TYPES = [
  "SYSTEM_POST",
  "RECIPE_SEO",
  "PROBLEM_SOLVER",
  "EXPERIENCE_POST"
];

// WordPress category mapping
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

// Angles
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
  "REAL_WORLD_EXAMPLE",
  "BUYING_DECISION"
];

// Tone
var TONE_MODES = [
  "PRACTICAL",
  "TIRED",
  "LIGHTLY_FUNNY",
  "REFLECTIVE",
  "RELIEVED"
];

// Retries
var GEMINI_TEXT_MAX_RETRIES = 3;
var GEMINI_IMAGE_MAX_RETRIES = 3;

/***********************
 * ENTRY
 ***********************/
function runContentMachineV2() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(25000)) return;

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();
    var rows = sheet.getDataRange().getValues();

    ensureHubsSheet_(ss);

    var processed = 0;

    for (var i = 1; i < rows.length; i++) {
      if (processed >= MAX_POSTS_PER_RUN) break;

      var status = String(rows[i][1] || "").trim().toLowerCase();
      var rowIndex = i + 1;
      if (status !== "queued") continue;

      try {
        sheet.getRange(rowIndex, 3).setValue("");
        sheet.getRange(rowIndex, 4).setValue("");

        var history = getHistory_(rows, 80);
        var plan = generateEditorialPlanV2_(history);

        sheet.getRange(rowIndex, 1).setValue(plan.title);
        sheet.getRange(rowIndex, 5).setValue(plan.type);
        sheet.getRange(rowIndex, 6).setValue(plan.categorySlug);
        sheet.getRange(rowIndex, 7).setValue(plan.angle);

        var hub = ensureCategoryHub_(ss, plan.categorySlug);
        var ai = generateSearchFirstPostJson_(plan, history);

        var mediaId = null;
        var inlineMediaMap = {};
        var imageStatus = "no";

        if (INCLUDE_FEATURED_IMAGE) {
          try {
            var heroPromptObj = buildHeroImageBrief_(plan, ai);
            var heroBlob = generateImageFromBrief_(heroPromptObj.prompt, "hero-" + slugify_(plan.title) + ".png");
            mediaId = uploadWpMedia_(heroBlob, "featured-" + slugify_(plan.title));
            imageStatus = "hero";
          } catch (e1) {
            imageStatus = "hero-failed";
          }
        }

        if (INCLUDE_INLINE_IMAGES && ai.imageSlots && ai.imageSlots.length) {
          try {
            inlineMediaMap = uploadInlineImages_(plan, ai.imageSlots);
            if (imageStatus === "hero") imageStatus = "hero+inline";
            else if (Object.keys(inlineMediaMap).length) imageStatus = "inline-only";
          } catch (e2) {
            if (imageStatus === "no") imageStatus = "inline-failed";
          }
        }

        var candidates = getInternalLinkCandidates_(rows, plan, 3);
        var html = buildHtmlV2_(plan, ai, hub, candidates, inlineMediaMap);
        var post = createWpPost_(plan.title, html, mediaId, DEFAULT_STATUS, plan.categorySlug);

        sheet.getRange(rowIndex, 2).setValue("Done");
        sheet.getRange(rowIndex, 3).setValue(post.URL || post.url || "");
        sheet.getRange(rowIndex, 4).setValue(
          "OK | " + plan.cluster +
          " | " + plan.type +
          " | " + plan.categorySlug +
          " | " + plan.angle +
          " | " + plan.primaryKeyword +
          " | Img:" + imageStatus
        );

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
  var hist = { titles: [], types: [], categories: [], angles: [], urls: [] };

  for (var i = rows.length - 1; i >= 1; i--) {
    var title = String(rows[i][0] || "").trim();
    var status = String(rows[i][1] || "").trim().toLowerCase();
    var type = String(rows[i][4] || "").trim().toUpperCase();
    var cat = String(rows[i][5] || "").trim();
    var angle = String(rows[i][6] || "").trim();
    var url = String(rows[i][2] || "").trim();

    if (!title) continue;
    if (status !== "done" && status !== "queued") continue;

    hist.titles.push(title);
    if (type) hist.types.push(type);
    if (cat) hist.categories.push(cat);
    if (angle) hist.angles.push(angle);
    if (url) hist.urls.push(url);

    if (hist.titles.length >= limit) break;
  }
  return hist;
}

/***********************
 * SIMPLE TEST
 ***********************/
function testPlanV2() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  var rows = sheet.getDataRange().getValues();
  var history = getHistory_(rows, 80);
  var plan = generateEditorialPlanV2_(history);
  Logger.log(JSON.stringify(plan, null, 2));
}

function testPostJsonV2() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  var rows = sheet.getDataRange().getValues();
  var history = getHistory_(rows, 80);
  var plan = generateEditorialPlanV2_(history);
  var ai = generateSearchFirstPostJson_(plan, history);
  Logger.log(JSON.stringify({ plan: plan, ai: ai }, null, 2));
}

function testOneDraftV2() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  var rows = sheet.getDataRange().getValues();
  var history = getHistory_(rows, 80);

  var plan = generateEditorialPlanV2_(history);
  var hub = ensureCategoryHub_(ss, plan.categorySlug);
  var ai = generateSearchFirstPostJson_(plan, history);

  var mediaId = null;
  var inlineMediaMap = {};

  if (INCLUDE_FEATURED_IMAGE) {
    try {
      var heroPromptObj = buildHeroImageBrief_(plan, ai);
      var heroBlob = generateImageFromBrief_(heroPromptObj.prompt, "hero-" + slugify_(plan.title) + ".png");
      mediaId = uploadWpMedia_(heroBlob, "featured-" + slugify_(plan.title));
    } catch (e1) {}
  }

  if (INCLUDE_INLINE_IMAGES && ai.imageSlots && ai.imageSlots.length) {
    try {
      inlineMediaMap = uploadInlineImages_(plan, ai.imageSlots);
    } catch (e2) {}
  }

  var candidates = getInternalLinkCandidates_(rows, plan, 3);
  var html = buildHtmlV2_(plan, ai, hub, candidates, inlineMediaMap);
  var post = createWpPost_(plan.title, html, mediaId, "draft", plan.categorySlug);

  Logger.log(JSON.stringify({
    title: plan.title,
    url: post.URL || post.url || "",
    type: plan.type,
    category: plan.categorySlug
  }, null, 2));
}
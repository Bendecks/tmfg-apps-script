var PROPS = PropertiesService.getScriptProperties();
var GEMINI_API_KEY = mustProp_("GEMINI_API_KEY");
var WP_OAUTH_TOKEN = mustProp_("WP_OAUTH_TOKEN");
var WP_SITE_ID = mustProp_("WP_SITE_ID");
var AMAZON_TAG = String(PROPS.getProperty("AMAZON_TAG") || "").trim();

var CONFIG_SHEET_NAME = "Config";
var HUBS_SHEET_NAME = "Hubs";
var AUTHORITY_SHEET_NAME = "Authority";

var CONFIG = {};
var PERSONAL_DEFAULT_STATUS = "publish";
var PERSONAL_MAX_POSTS_PER_RUN = 1;
var PERSONAL_INCLUDE_FEATURED_IMAGE = true;
var SITE_HOME_URL = "https://themodernfamilyguide.wordpress.com";
var AMAZON_DOMAIN = "de";
var GEMINI_TEXT_MODEL = "models/gemini-2.5-flash";
var GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview";
var BLOG_VOICE = "";
var FAMILY_VISUAL_PROFILE = "";
var FAMILY_IMAGE_LOCK_STYLE = "";

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

var AUTHORITY_BLUEPRINTS = {
  "kids-activities-fun": {
    title: "Bored Kids at Home? 25 Zero-Cost Activities That Actually Work",
    query: "bored kids at home activities free",
    intro: "A practical roundup of genuinely useful, low-cost or zero-cost ideas for bored kids at home."
  },
  "parenting-hacks-tips": {
    title: "How to Reduce Screen Time Without Daily Fights",
    query: "reduce screen time without fights kids",
    intro: "A parent-friendly guide to lowering screen time without turning every afternoon into a battle."
  },
  "work-life-balance": {
    title: "Simple Family Systems That Save Time Every Day",
    query: "family systems save time every day",
    intro: "Small systems that reduce friction, save time and make ordinary family life easier."
  },
  "home-organization": {
    title: "Easy Home Organization Fixes That Actually Stick",
    query: "easy home organization fixes family",
    intro: "Low-effort home organization ideas that make daily life feel lighter instead of more complicated."
  },
  "recipes-meals": {
    title: "Easy Family Meal Ideas for Tired Weeknights",
    query: "easy family meal ideas weeknights",
    intro: "A practical collection of realistic family meal ideas for nights when energy is low."
  },
  "family-finance-life": {
    title: "Simple Money Habits That Make Family Life Easier",
    query: "simple money habits family life",
    intro: "Small money-saving habits and systems that reduce pressure in everyday family life."
  }
};

function getConfigMap_() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG_SHEET_NAME);
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

function refreshConfig_() {
  CONFIG = getConfigMap_();

  PERSONAL_DEFAULT_STATUS = String(getConfig_("PERSONAL_DEFAULT_STATUS", "publish")).toLowerCase();
  PERSONAL_MAX_POSTS_PER_RUN = parseInt(getConfig_("PERSONAL_MAX_POSTS_PER_RUN", "1"), 10) || 1;
  PERSONAL_INCLUDE_FEATURED_IMAGE = String(getConfig_("PERSONAL_INCLUDE_FEATURED_IMAGE", "true")).toLowerCase() === "true";

  SITE_HOME_URL = String(getConfig_("SITE_HOME_URL", "https://themodernfamilyguide.wordpress.com")).replace(/\/+$/, "");
  AMAZON_DOMAIN = String(getConfig_("AMAZON_DOMAIN", "de")).trim();
  GEMINI_IMAGE_MODEL = String(getConfig_("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")).trim();

  BLOG_VOICE = String(getConfig_("BLOG_VOICE",
    "Warm, honest, slightly reflective but practical modern Scandinavian family voice. Calm, grounded, lightly humorous. Short paragraphs. No fluff. No corporate tone. No therapy jargon."
  )).trim();

  FAMILY_VISUAL_PROFILE = String(getConfig_("FAMILY_VISUAL_PROFILE", "")).trim();
  FAMILY_IMAGE_LOCK_STYLE = String(getConfig_("FAMILY_IMAGE_LOCK_STYLE",
    "clean cartoon caricature, soft shading, modern family illustration, consistent character design across images"
  )).trim();
}

function ensureConfigSheet_(ss) {
  var sh = ss.getSheetByName(CONFIG_SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(CONFIG_SHEET_NAME);
  }
  var desired = [
    ["Key", "Value"],
    ["PERSONAL_DEFAULT_STATUS", "publish"],
    ["PERSONAL_MAX_POSTS_PER_RUN", "1"],
    ["PERSONAL_INCLUDE_FEATURED_IMAGE", "true"],
    ["SITE_HOME_URL", "https://themodernfamilyguide.wordpress.com"],
    ["GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview"],
    ["BLOG_VOICE", "Warm, honest, slightly reflective but practical modern Scandinavian family voice. Calm, grounded, lightly humorous. Short paragraphs. No fluff. No corporate tone. No therapy jargon."],
    ["FAMILY_VISUAL_PROFILE", "A modern Scandinavian family with one confident father in his late 30s (short dark brown hair, trimmed beard, warm smile) and four boys of different ages (young child to pre-teen). Bright wooden home interior, large windows, natural daylight. Warm, authentic, playful but grounded energy. Consistent character design across images. No text, no logos, no brand names."],
    ["FAMILY_IMAGE_LOCK_STYLE", "clean cartoon caricature, soft shading, modern family illustration, consistent character design across images"],
    ["AMAZON_DOMAIN", "de"]
  ];
  var current = sh.getDataRange().getValues();
  if (!current.length) {
    sh.getRange(1, 1, desired.length, 2).setValues(desired);
    return sh;
  }
  if (String(current[0][0] || "").trim() !== "Key" || String(current[0][1] || "").trim() !== "Value") {
    sh.getRange(1, 1, desired.length, 2).setValues(desired);
    return sh;
  }
  var existingKeys = {};
  for (var i = 1; i < current.length; i++) {
    existingKeys[String(current[i][0] || "").trim()] = true;
  }
  var rowsToAppend = [];
  for (var j = 1; j < desired.length; j++) {
    if (!existingKeys[desired[j][0]]) rowsToAppend.push(desired[j]);
  }
  if (rowsToAppend.length) {
    sh.getRange(sh.getLastRow() + 1, 1, rowsToAppend.length, 2).setValues(rowsToAppend);
  }
  return sh;
}

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

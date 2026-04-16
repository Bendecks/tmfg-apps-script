/****************************************************
 * TMFG V2 — ENGINE
 * Search-first content engine
 ****************************************************/

/***********************
 * EDITORIAL PLAN V2
 ***********************/
function generateEditorialPlanV2_(history) {
  var recentTitles = history.titles.slice(0, 25);
  var recentTypes = uniq_(history.types.slice(0, 3));
  var recentCats = uniq_(history.categories.slice(0, 3));
  var recentAngles = uniq_(history.angles.slice(0, 3));

  var prompt =
    "Return ONLY valid JSON. No markdown.\n\n" +
    "{\n" +
    '  "cluster": "ONE of: ' + CLUSTERS.join(", ") + '",\n' +
    '  "type": "ONE of: ' + POST_TYPES.join(", ") + '",\n' +
    '  "categorySlug": "ONE of: ' + CATEGORY_SLUGS.join(", ") + '",\n' +
    '  "angle": "ONE of: ' + ANGLES.join(", ") + '",\n' +
    '  "toneMode": "ONE of: ' + TONE_MODES.join(", ") + '",\n' +
    '  "primaryKeyword": "clear search phrase, 2-6 words",\n' +
    '  "secondaryKeyword": "supporting search phrase, 2-6 words",\n' +
    '  "intent": "what the reader wants solved or decided",\n' +
    'title": "SEO title using real search phrasing (max 65 chars). Must start with the main keyword. No creative or vague phrasing.",\n' +
    '  "readerProblem": "one sentence",\n' +
    '  "whyThisCanRank": "one sentence explaining specificity/usefulness",\n' +
    '  "experienceSeed": "one concrete lived detail"\n' +
    "}\n\n" +
    "Rules:\n" +
    "- Title MUST sound like something people actually type into Google\n" +
"- Avoid clever or poetic phrasing\n" +
"- Use formats like:\n" +
"  • 'How to...'\n" +
"  • 'Best way to...'\n" +
"  • 'Simple ... system'\n" +
"  • '... without ...'\n" +
"- Put the most important keyword in the first 4 words\n" +
"- Prefer clarity over creativity\n" +
    "- Avoid vague lifestyle titles.\n" +
    "- Prefer problem-solving, recipe, system, or buying-decision intent.\n" +
    "- Title should feel like a realistic Google result.\n" +
    "- Never mention family member names.\n" +
    "- Avoid repeating recent patterns.\n" +
    "- Avoid polished AI-sounding phrasing.\n\n" +
    "Recent titles:\n" + recentTitles.map(function(t){ return "- " + t; }).join("\n") + "\n\n" +
    "Recent type/category/angle to avoid repeating too much:\n" +
    "- types: " + (recentTypes.length ? recentTypes.join(", ") : "(none)") + "\n" +
    "- categories: " + (recentCats.length ? recentCats.join(", ") : "(none)") + "\n" +
    "- angles: " + (recentAngles.length ? recentAngles.join(", ") : "(none)") + "\n\n" +
    "Voice:\n" + BLOG_VOICE;

  for (var attempt = 1; attempt <= 4; attempt++) {
    var raw = geminiText_(prompt);
    var plan = parseJsonObjectWithRepair_(raw);

    plan.cluster = String(plan.cluster || "").trim();
    plan.type = String(plan.type || "").trim();
    plan.categorySlug = String(plan.categorySlug || "").trim();
    plan.angle = String(plan.angle || "").trim();
    plan.toneMode = String(plan.toneMode || "").trim().toUpperCase();
    plan.primaryKeyword = String(plan.primaryKeyword || "").trim();
    plan.secondaryKeyword = String(plan.secondaryKeyword || "").trim();
    plan.intent = String(plan.intent || "").trim();
    plan.title = cleanSeoTitle_(plan.title, plan.primaryKeyword);
    plan.readerProblem = String(plan.readerProblem || "").trim();
    plan.whyThisCanRank = String(plan.whyThisCanRank || "").trim();
    plan.experienceSeed = String(plan.experienceSeed || "").trim();

    if (CLUSTERS.indexOf(plan.cluster) === -1) continue;
    if (POST_TYPES.indexOf(plan.type) === -1) continue;
    if (CATEGORY_SLUGS.indexOf(plan.categorySlug) === -1) continue;
    if (ANGLES.indexOf(plan.angle) === -1) continue;
    if (TONE_MODES.indexOf(plan.toneMode) === -1) continue;
    if (!plan.primaryKeyword || !plan.title) continue;
    if (isTitleTooSimilar_(plan.title, recentTitles)) continue;

    return plan;
  }

  throw new Error("Could not generate valid editorial plan v2.");
}

/***********************
 * CONTENT GENERATION V2
 ***********************/
function generateSearchFirstPostJson_(plan, history) {
  var recentTitles = history.titles.slice(0, 20).map(function(t){ return "- " + t; }).join("\n");

  var schema =
    "Return ONLY valid JSON. No markdown.\n\n" +
    "{\n" +
    '  "hook": "short raw human opening, max 5 lines",\n' +
    '  "seoSummary": "1-2 short sentences stating exactly what the post helps with",\n' +
    '  "intro": "2-3 short sentences max",\n' +
    '  "system": {\n' +
    '    "title": "name of simple system",\n' +
    '    "steps": ["step 1","step 2","step 3","step 4"]\n' +
    "  },\n" +
    '  "experienceBox": {\n' +
    '    "title": "short heading",\n' +
    '    "text": "2-4 sentences with a real household moment"\n' +
    "  },\n" +
    '  "sections": [\n' +
    '    {"h2":"Heading","p":"Short paragraph"},\n' +
    '    {"h2":"Heading","p":"Short paragraph"},\n' +
    '    {"h2":"Heading","p":"Short paragraph"}\n' +
    "  ],\n" +
    '  "mistake": "one real mistake parents make",\n' +
    '  "whatChanged": ["short practical takeaway 1","short practical takeaway 2","short practical takeaway 3"],\n' +
    '  "faq": [\n' +
    '    {"q":"Question","a":"2-4 sentences"},\n' +
    '    {"q":"Question","a":"2-4 sentences"}\n' +
    "  ],\n" +
    '  "cta": "1 sentence",\n' +
    '  "affiliate": {\n' +
    '    "enabled": true,\n' +
    '    "label": "What we would buy",\n' +
    '    "items": [\n' +
    '      {"query":"specific product search","reason":"why it helps"},\n' +
    '      {"query":"specific product search","reason":"why it helps"}\n' +
    "    ]\n" +
    "  },\n" +
    '  "imageSlots": [\n' +
    '    {"slot":"after_intro","brief":"realistic image brief"},\n' +
    '    {"slot":"mid_post","brief":"realistic image brief"}\n' +
    "  ]\n" +
    "}\n\n" +
    "CRITICAL RULES:\n" +
    "- Start with a REAL human situation, not a generic intro.\n" +
    "- Write like a tired but practical parent, not an expert.\n" +
    "- Keep sentences slightly imperfect and natural.\n" +
    "- Introduce ONE simple system early.\n" +
    "- Remove over-explaining.\n" +
    "- No generic advice.\n" +
    "- No 'in today's world' phrasing.\n" +
    "- Add ONE real-life mistake.\n" +
    "- Keep it short and useful.\n" +
    "- Make it feel lived, not written.\n" +
    "- Use the primary and secondary keyword naturally.\n" +
    "- No URLs.\n" +
    "- Never mention family member names.\n" +
    "- For RECIPE_SEO include ingredients, steps, timing and substitutions inside sections.\n" +
    "- For PROBLEM_SOLVER include who it's for, tradeoffs and practical recommendation.\n" +
    "- For SYSTEM_POST include setup, rule, failure point and how to keep it going.\n" +
    "- For EXPERIENCE_POST keep it tighter and more personal but still useful.\n" +
    "- Amazon queries must be specific product searches, not vague category words.\n" +
    "- imageSlots max 2 and only if helpful.\n\n" +
    "Recent titles:\n" + recentTitles + "\n\n" +
    "Voice:\n" + BLOG_VOICE;

  var prompt =
    "Blog: The Modern Family Guide\n" +
    "Cluster: " + plan.cluster + "\n" +
    "Type: " + plan.type + "\n" +
    "CategorySlug: " + plan.categorySlug + "\n" +
    "Angle: " + plan.angle + "\n" +
    "ToneMode: " + plan.toneMode + "\n" +
    "PrimaryKeyword: " + plan.primaryKeyword + "\n" +
    "SecondaryKeyword: " + plan.secondaryKeyword + "\n" +
    "Intent: " + plan.intent + "\n" +
    "Title: " + plan.title + "\n" +
    "ReaderProblem: " + plan.readerProblem + "\n" +
    "WhyThisCanRank: " + plan.whyThisCanRank + "\n" +
    "ExperienceSeed: " + plan.experienceSeed + "\n\n" +
    "Type directive:\n" + postTypeDirectiveV2_(plan.type) + "\n\n" +
    "Angle directive:\n" + angleDirectiveV2_(plan.angle) + "\n\n" +
    "Tone directive:\n" + toneDirective_(plan.toneMode) + "\n\n" +
    schema;

  for (var attempt = 1; attempt <= 4; attempt++) {
    var raw = geminiText_(prompt);
    var ai = parseJsonObjectWithRepair_(raw);

    if (!ai || typeof ai !== "object") continue;

    ai.hook = String(ai.hook || "").trim();
    ai.seoSummary = String(ai.seoSummary || "").trim();
    ai.intro = String(ai.intro || "").trim();
    ai.cta = String(ai.cta || "").trim();
    ai.mistake = String(ai.mistake || "").trim();

    ai.system = ai.system && typeof ai.system === "object" ? ai.system : {};
    ai.system.title = String(ai.system.title || "").trim();
    if (!Array.isArray(ai.system.steps)) ai.system.steps = [];
    ai.system.steps = ai.system.steps.slice(0, 4).map(function(x){ return String(x || "").trim(); }).filter(Boolean);

    ai.experienceBox = ai.experienceBox && typeof ai.experienceBox === "object" ? ai.experienceBox : {};
    ai.experienceBox.title = String(ai.experienceBox.title || "").trim();
    ai.experienceBox.text = String(ai.experienceBox.text || "").trim();

    if (!Array.isArray(ai.sections)) ai.sections = [];
    if (!Array.isArray(ai.faq)) ai.faq = [];
    if (!Array.isArray(ai.whatChanged)) ai.whatChanged = [];
    if (!ai.affiliate || typeof ai.affiliate !== "object") ai.affiliate = { enabled: false, items: [] };
    if (!Array.isArray(ai.affiliate.items)) ai.affiliate.items = [];
    if (!Array.isArray(ai.imageSlots)) ai.imageSlots = [];

    ai.sections = ai.sections.slice(0, 5).map(function(s){
      return {
        h2: String((s && s.h2) ? s.h2 : "").trim(),
        p: String((s && s.p) ? s.p : "").trim()
      };
    }).filter(function(s){ return s.h2 && s.p; });

    ai.faq = ai.faq.slice(0, 3).map(function(f){
      return {
        q: String((f && f.q) ? f.q : "").trim(),
        a: String((f && f.a) ? f.a : "").trim()
      };
    }).filter(function(f){ return f.q && f.a; });

    ai.whatChanged = ai.whatChanged.slice(0, 5).map(function(x){
      return String(x || "").trim();
    }).filter(Boolean);

    ai.affiliate.enabled = !!ai.affiliate.enabled;
    ai.affiliate.label = String(ai.affiliate.label || "What we would buy").trim();
    ai.affiliate.items = ai.affiliate.items.slice(0, 2).map(function(it){
      return {
        query: String((it && it.query) ? it.query : "").trim(),
        reason: String((it && it.reason) ? it.reason : "").trim()
      };
    }).filter(function(it){ return it.query && it.reason; });

    ai.imageSlots = ai.imageSlots.slice(0, 2).map(function(it){
      return {
        slot: String((it && it.slot) ? it.slot : "").trim(),
        brief: String((it && it.brief) ? it.brief : "").trim()
      };
    }).filter(function(it){ return it.slot && it.brief; });

    if (!ai.intro || !ai.sections.length) continue;

    if (plan.type !== "PROBLEM_SOLVER") {
      ai.affiliate.enabled = false;
      ai.affiliate.items = [];
    }

    return ai;
  }

  throw new Error("Could not generate valid search-first post JSON.");
}

/***********************
 * DIRECTIVES
 ***********************/
function postTypeDirectiveV2_(type) {
  switch (type) {
    case "RECIPE_SEO":
      return "Write like a recipe post that should rank. Include ingredients, steps, timing, substitutions, and what makes this recipe convenient.";
    case "PROBLEM_SOLVER":
      return "Write like a buyer/problem-solving article. Include who it is for, why it works, tradeoffs, and a practical recommendation.";
    case "SYSTEM_POST":
      return "Write like a practical system article. Include setup, rule, failure point, and how to keep it working.";
    case "EXPERIENCE_POST":
    default:
      return "Write as an experience-led but useful post. Keep it grounded in a real moment and end with practical value.";
  }
}

function angleDirectiveV2_(angle) {
  switch (angle) {
    case "BUYING_DECISION": return "Make the choice practical. Emphasise tradeoffs, best fit, and why someone would choose one solution over another.";
    case "LOW_ENERGY_MODE": return "Keep the solution realistic for tired parents. No idealized routines.";
    case "TIME_SAVING": return "Show exactly where time is saved and in what part of the day.";
    case "MONEY_SAVING": return "Show practical savings without sounding cheap or deprived.";
    case "CONFLICT_REDUCTION": return "Reduce friction with one clear boundary, one phrase, or one environmental change.";
    case "HOME_RESET": return "Emphasise visible relief and the smallest workable reset.";
    case "MEAL_SIMPLIFICATION": return "Make the food system feel easier to repeat on a hard weekday.";
    case "EMOTIONAL_REFLECTION": return "Ground the emotion in a real moment and keep it useful.";
    case "REAL_WORLD_EXAMPLE": return "Use one concrete household moment as the base for the advice.";
    default: return "Keep the advice specific, grounded and repeatable.";
  }
}

function toneDirective_(toneMode) {
  switch (toneMode) {
    case "TIRED": return "Tone: tired but capable, low-drama, honest.";
    case "LIGHTLY_FUNNY": return "Tone: warm, dry, lightly funny, never cheesy.";
    case "REFLECTIVE": return "Tone: thoughtful and grounded, but still direct.";
    case "RELIEVED": return "Tone: calm relief after something finally helped.";
    case "PRACTICAL":
    default: return "Tone: practical, direct, quietly reassuring.";
  }
}

/***********************
 * HTML BUILDING
 ***********************/
function buildHtmlV2_(plan, ai, hub, candidates, inlineMediaMap) {
  var parts = [];

  parts.push('<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.68;color:#333;max-width:680px;margin:0 auto;">');

  if (ai.hook) {
    parts.push('<p style="font-size:20px;font-weight:600;color:#333;margin:0 0 12px 0;">' + escapeHtml_(ai.hook) + '</p>');
  }

  if (ai.seoSummary) {
    parts.push('<p style="font-size:17px;color:#4b4b4b;margin:0 0 14px 0;">' + escapeHtml_(ai.seoSummary) + '</p>');
  }

  if (hub && hub.url) {
    var hubHref = isInternalUrl_(hub.url) ? makeRelativeUrl_(hub.url) : hub.url;
    parts.push(
      '<div style="margin:16px 0;padding:14px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
      '<strong>Start here:</strong> ' +
      '<a href="' + escapeAttr_(hubHref) + '" style="text-decoration:none;font-weight:700;">' +
      escapeHtml_(hub.title || "Explore the hub") +
      '</a></div>'
    );
  }

  if (ai.intro) {
    parts.push('<p style="font-size:18px;color:#555;margin:0 0 16px 0;">' + escapeHtml_(ai.intro) + '</p>');
  }

  if (inlineMediaMap && inlineMediaMap.after_intro) {
    parts.push(renderImageBlock_(inlineMediaMap.after_intro));
  }

  if (ai.system && ai.system.steps && ai.system.steps.length) {
    parts.push('<h2>' + escapeHtml_(ai.system.title || "The simple system we use") + '</h2>');
    parts.push('<ol style="padding-left:22px;margin:0 0 16px 0;">');
    for (var si = 0; si < ai.system.steps.length; si++) {
      parts.push('<li style="margin:8px 0;">' + escapeHtml_(ai.system.steps[si]) + '</li>');
    }
    parts.push('</ol>');
  }

  if (ai.experienceBox && ai.experienceBox.title && ai.experienceBox.text) {
    parts.push(
      '<div style="background:#f8f8f8;padding:18px;border-radius:12px;border:1px solid #eee;margin:20px 0;">' +
      '<strong>' + escapeHtml_(ai.experienceBox.title) + '</strong>' +
      '<p style="margin:8px 0 0 0;color:#444;">' + escapeHtml_(ai.experienceBox.text) + '</p>' +
      '</div>'
    );
  }

  if (ai.mistake) {
    parts.push('<div style="background:#fff3cd;padding:12px;border-radius:8px;margin:16px 0;">');
    parts.push('<strong>What we got wrong:</strong> ' + escapeHtml_(ai.mistake));
    parts.push('</div>');
  }

  var inlineLinks = (candidates || []).slice(0, 2);

  for (var i = 0; i < ai.sections.length; i++) {
    var s = ai.sections[i];
    var pText = String(s.p || "");
    var pHtml = escapeHtml_(pText);

    if (inlineLinks[i] && shouldInlineLink_(pText)) {
      pHtml = injectInlineLinkIntoEscapedParagraph_(pHtml, inlineLinks[i]);
    }

    parts.push('<h2 style="margin:24px 0 8px 0;">' + escapeHtml_(s.h2) + '</h2>');
    parts.push('<p style="margin:0 0 12px 0;color:#444;">' + pHtml + '</p>');

    if (i === 1 && inlineMediaMap && inlineMediaMap.mid_post) {
      parts.push(renderImageBlock_(inlineMediaMap.mid_post));
    }
  }

  if (ai.whatChanged && ai.whatChanged.length) {
    parts.push('<div style="margin:20px 0;">');
    parts.push('<h2 style="margin:0 0 8px 0;">What changed for us</h2>');
    parts.push('<ul style="padding-left:20px;margin:0;">');
    for (var j = 0; j < ai.whatChanged.length; j++) {
      parts.push('<li>' + escapeHtml_(ai.whatChanged[j]) + '</li>');
    }
    parts.push('</ul></div>');
  }

  if (ai.affiliate && ai.affiliate.enabled && ai.affiliate.items && ai.affiliate.items.length) {
    parts.push(renderAffiliateBlock_(ai.affiliate));
  }

  if (ai.faq && ai.faq.length) {
    parts.push('<h2 style="margin-top:28px;">FAQ</h2>');
    for (var k = 0; k < ai.faq.length; k++) {
      parts.push('<h3 style="margin:16px 0 6px 0;font-size:16px;">' + escapeHtml_(ai.faq[k].q) + '</h3>');
      parts.push('<p style="margin:0 0 10px 0;color:#444;">' + escapeHtml_(ai.faq[k].a) + '</p>');
    }
  }

  if (ai.cta) {
    parts.push('<p style="margin-top:18px;color:#444;"><em>' + escapeHtml_(ai.cta) + '</em></p>');
  }

  if (candidates && candidates.length) {
    parts.push(buildInternalLinksBlock_(candidates, plan));
  }

  parts.push('</div>');
  return parts.join("");
}

function renderAffiliateBlock_(affiliate) {
  var items = affiliate.items.slice(0, 2).map(function(it){
    var url = makeAmazonSearchLink_(it.query);
    return (
      '<div style="padding:14px;border:1px solid #eee;border-radius:12px;margin:12px 0;background:#fff;">' +
      '<div style="font-weight:700;margin-bottom:6px;">' + escapeHtml_(it.query) + '</div>' +
      '<p style="margin:0 0 10px 0;color:#444;">' + escapeHtml_(it.reason) + '</p>' +
      '<a href="' + escapeAttr_(url) + '" style="display:inline-block;padding:10px 14px;border-radius:10px;background:#111;color:#fff;text-decoration:none;font-weight:700;">View on Amazon</a>' +
      '</div>'
    );
  }).join("");

  return (
    '<div style="margin:28px 0;padding:18px;border:1px solid #eee;border-radius:14px;background:#fafafa;">' +
      '<h2 style="margin:0 0 10px 0;">' + escapeHtml_(affiliate.label || "What we would buy") + '</h2>' +
      items +
    '</div>'
  );
}

function renderImageBlock_(url) {
  return (
    '<div style="margin:18px 0;">' +
      '<img src="' + escapeAttr_(url) + '" style="width:100%;height:auto;border-radius:14px;display:block;" />' +
    '</div>'
  );
}

function buildInternalLinksBlock_(candidates, plan) {
  var items = candidates.slice(0, 3).map(function(it){
    var href = isInternalUrl_(it.url) ? makeRelativeUrl_(it.url) : it.url;
    return '<li style="margin:10px 0;"><a href="' + escapeAttr_(href) + '" style="text-decoration:none;font-weight:700;">' + escapeHtml_(it.title) + '</a></li>';
  }).join("");

  return (
    '<div style="margin-top:28px;padding:18px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
      '<h2 style="margin:0 0 10px 0;">You might also find helpful</h2>' +
      '<ul style="margin:0;padding-left:18px;">' + items + '</ul>' +
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
  var link = ' <a href="' + escapeAttr_(href) + '" style="text-decoration:underline;">' + escapeHtml_(candidate.title) + '</a>';

  parts[0] = parts[0] + "." + link;
  return parts.join(". ");
}

/***********************
 * IMAGES
 ***********************/
function buildHeroImageBrief_(plan, ai) {
  var realism =
    IMAGE_STYLE_MODE === "realistic"
      ? "A realistic everyday family-life image in a modern Scandinavian home. Natural light. Slightly imperfect. No text, no logos, no stock-photo vibe."
      : "A clean family-life image. Natural and helpful. No text, no logos.";

  var familyLine = FAMILY_VISUAL_PROFILE ? ("Family visual note: " + FAMILY_VISUAL_PROFILE + ". ") : "";

  var prompt =
    realism + " " +
    familyLine +
    "Topic: " + plan.primaryKeyword + ". " +
    "Intent: " + plan.intent + ". " +
    "Article title: " + plan.title + ". " +
    "Scene should feel useful and believable, not stylized.";

  return { prompt: prompt };
}

function uploadInlineImages_(plan, imageSlots) {
  var out = {};
  for (var i = 0; i < imageSlots.length; i++) {
    var slot = imageSlots[i];
    try {
      var brief = buildInlineImageBrief_(plan, slot.brief);
      var blob = generateImageFromBrief_(brief, "inline-" + slugify_(plan.title) + "-" + (i + 1) + ".png");
      var media = uploadWpMediaAndReturnMeta_(blob, "inline-" + slugify_(plan.title) + "-" + (i + 1));
      if (media && media.url) out[slot.slot] = media.url;
    } catch (e) {}
  }
  return out;
}

function buildInlineImageBrief_(plan, brief) {
  var realism =
    IMAGE_STYLE_MODE === "realistic"
      ? "Create a realistic, helpful, natural-light family-life image in a Scandinavian home. Slightly imperfect. No text. No logos."
      : "Create a natural family-life image. No text. No logos.";
  return realism + " Context: " + plan.title + ". Brief: " + brief;
}

function generateImageFromBrief_(prompt, fileName) {
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
            return Utilities.newBlob(bytes, mime, fileName || "image.png");
          }
        }
        throw new Error("Gemini(image) returned no inline image data.");
      }

      if (code === 429 || code === 503) {
        lastErr = new Error("Gemini(image) HTTP " + code + ": " + truncate_(body, 500));
        Utilities.sleep(2000 * attempt);
        continue;
      }

      throw new Error("Gemini(image) HTTP " + code + ": " + truncate_(body, 800));
    } catch (e) {
      lastErr = e;
      Utilities.sleep(1500 * attempt);
    }
  }

  throw lastErr || new Error("Image generation failed after retries.");
}

/***********************
 * WORDPRESS
 ***********************/
function uploadWpMedia_(blob, title) {
  var meta = uploadWpMediaAndReturnMeta_(blob, title);
  return meta.id;
}

function uploadWpMediaAndReturnMeta_(blob, title) {
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
  var item = (json && json.media && json.media[0]) ? json.media[0] : null;
  if (!item || !item.ID) throw new Error("Media upload ok but no ID returned.");

  return { id: item.ID, url: item.URL || item.url || "" };
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
 * GEMINI / JSON
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
        Utilities.sleep(1400 * attempt);
        continue;
      }

      throw new Error("Gemini(text) HTTP " + code + ": " + truncate_(body, 700));
    } catch (e) {
      lastErr = e;
      Utilities.sleep(1000 * attempt);
    }
  }

  throw lastErr || new Error("Gemini(text) failed after retries.");
}

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
  return String(text || "").replace(/```json/gi, "").replace(/```/g, "").trim();
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
    if (escape) { escape = false; continue; }
    if (ch === "\\") { if (inString) escape = true; continue; }
    if (ch === "\"") { inString = !inString; continue; }
    if (!inString) {
      if (ch === "{") depth++;
      if (ch === "}") {
        depth--;
        if (depth === 0) { end = i; break; }
      }
    }
  }

  if (end < 0) throw new Error("JSON end not found.");
  return cleaned.substring(start, end + 1);
}

function repairCommonJsonIssues_(jsonText) {
  var s = String(jsonText || "");
  s = s.replace(/[“”]/g, "\"").replace(/[‘’]/g, "'");
  s = s.replace(/,\s*([}\]])/g, "$1");
  s = s.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "");
  return s;
}
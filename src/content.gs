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

function generateSearchFirstPostJson_(plan, history) {
  return generatePersonalPostJson_(plan, history);
}

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

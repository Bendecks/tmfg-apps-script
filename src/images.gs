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

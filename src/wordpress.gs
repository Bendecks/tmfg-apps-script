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

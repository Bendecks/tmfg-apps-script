function ensureAuthoritySheet_(ss) {
  var sh = ss.getSheetByName(AUTHORITY_SHEET_NAME);
  if (!sh) sh = ss.insertSheet(AUTHORITY_SHEET_NAME);

  var headers = [["CategorySlug", "AuthorityPostId", "AuthorityUrl", "AuthorityTitle", "Query", "UpdatedAt"]];
  var current = sh.getRange(1, 1, 1, 6).getValues()[0];
  var desired = headers[0];
  var mismatch = false;
  for (var i = 0; i < desired.length; i++) {
    if (String(current[i] || "").trim() !== desired[i]) { mismatch = true; break; }
  }
  if (mismatch) sh.getRange(1, 1, 1, 6).setValues(headers);
  return sh;
}

function maybeBuildAuthorityPage_(ss, mainSheet, plan) {
  if (!AUTHORITY_BLUEPRINTS[plan.categorySlug]) return;
  ensureAuthorityPage_(ss, mainSheet, plan.categorySlug);
}

function ensureAuthorityPage_(ss, mainSheet, categorySlug) {
  var sh = ensureAuthoritySheet_(ss);
  var data = sh.getDataRange().getValues();
  var blueprint = AUTHORITY_BLUEPRINTS[categorySlug];
  if (!blueprint) return null;

  var existingRow = -1;
  var existingId = "";
  var existingTitle = "";

  for (var i = 1; i < data.length; i++) {
    if (String(data[i][0] || "").trim() === categorySlug) {
      existingRow = i + 1;
      existingId = String(data[i][1] || "").trim();
      existingTitle = String(data[i][3] || "").trim();
      break;
    }
  }

  var html = buildAuthorityHtml_(mainSheet, categorySlug, blueprint);

  if (existingId) {
    var updateUrl = "https://public-api.wordpress.com/rest/v1.1/sites/" + encodeURIComponent(WP_SITE_ID) + "/posts/" + encodeURIComponent(existingId);
    var res = UrlFetchApp.fetch(updateUrl, {
      method: "post",
      contentType: "application/json",
      headers: { Authorization: "Bearer " + WP_OAUTH_TOKEN },
      payload: JSON.stringify({ title: existingTitle || blueprint.title, content: html }),
      muteHttpExceptions: true
    });
    if (![200, 201].includes(res.getResponseCode())) {
      throw new Error("Authority update failed HTTP " + res.getResponseCode() + ": " + truncate_(res.getContentText(), 900));
    }
    sh.getRange(existingRow, 6).setValue(new Date());
    return { id: existingId, title: existingTitle || blueprint.title };
  }

  var created = createWpPost_(blueprint.title, html, null, PERSONAL_DEFAULT_STATUS, categorySlug);
  var newId = String(created.ID || created.id || "");
  var newUrl = String(created.URL || created.url || "");
  if (!newId || !newUrl) throw new Error("Authority page created but missing ID/URL.");

  sh.appendRow([categorySlug, newId, newUrl, blueprint.title, blueprint.query, new Date()]);
  return { id: newId, title: blueprint.title };
}

function buildAuthorityHtml_(mainSheet, categorySlug, blueprint) {
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
    posts.push({ title: title, url: url, angle: angle || "OTHER" });
  }

  var grouped = {};
  for (var j = 0; j < posts.length; j++) {
    var a = posts[j].angle;
    if (!grouped[a]) grouped[a] = [];
    grouped[a].push(posts[j]);
  }

  var blocks = [];
  var keys = Object.keys(grouped);
  keys.sort();

  for (var k = 0; k < keys.length; k++) {
    var angle = keys[k];
    var nice = angle.replace(/_/g, " ").toLowerCase();
    nice = nice.charAt(0).toUpperCase() + nice.slice(1);
    var items = grouped[angle].map(function(p) {
      return '<li style="margin:8px 0;"><a href="' + escapeAttr_(toRelativeIfSameSite_(stripQueryAndHash_(p.url))) + '">' + escapeHtml_(p.title) + '</a></li>';
    }).join("");
    blocks.push('<h2 style="margin-top:26px;">' + escapeHtml_(nice) + '</h2><ul style="padding-left:18px;">' + items + '</ul>');
  }

  return '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.65;color:#333;max-width:720px;margin:0 auto;">' +
    '<p style="font-size:18px;color:#555;">' + escapeHtml_(blueprint.intro) + '</p>' +
    '<p style="color:#444;">This page pulls together the most useful posts on this topic, so it is easier to find practical ideas without digging through the whole site.</p>' +
    blocks.join("") +
    '<p style="font-size:12px;color:#999;margin-top:26px;">Updated automatically as new posts are published.</p>' +
    '</div>';
}

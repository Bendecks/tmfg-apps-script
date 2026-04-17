function ensureHubsSheet_(ss) {
  var sh = ss.getSheetByName(HUBS_SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(HUBS_SHEET_NAME);
  }
  var headers = [["CategorySlug", "HubPostId", "HubUrl", "HubTitle", "UpdatedAt"]];
  var current = sh.getRange(1, 1, 1, 5).getValues()[0];
  var desired = headers[0];
  var mismatch = false;
  for (var i = 0; i < desired.length; i++) {
    if (String(current[i] || "").trim() !== desired[i]) { mismatch = true; break; }
  }
  if (mismatch) sh.getRange(1, 1, 1, 5).setValues(headers);
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

function getInternalLinkCandidates_(rows, plan, maxLinks) {
  maxLinks = maxLinks || 2;
  var pool = [];

  for (var i = 1; i < rows.length; i++) {
    var title = String(rows[i][0] || "").trim();
    var status = String(rows[i][1] || "").trim().toLowerCase();
    var url = String(rows[i][2] || "").trim();
    var cat = String(rows[i][5] || "").trim();
    var angle = String(rows[i][6] || "").trim();

    if (status !== "done") continue;
    if (!title || !url) continue;
    if (title === plan.title) continue;

    if (cat === plan.categorySlug || angle === plan.angle) {
      pool.push({ title: title, url: url, categorySlug: cat, angle: angle });
    }
  }

  pool.reverse();
  return pool.slice(0, maxLinks);
}

function buildInternalLinksBlock_(candidates) {
  if (!candidates || !candidates.length) return "";

  var items = candidates.map(function(it) {
    var href = toRelativeIfSameSite_(stripQueryAndHash_(it.url));

    return '<li style="margin:10px 0;">' +
      '<a href="' + escapeAttr_(href) + '" style="font-weight:600;text-decoration:none;">' +
      escapeHtml_(it.title) +
      "</a></li>";
  }).join("");

  return '<div style="margin-top:24px;">' +
    '<h3 style="margin-bottom:10px;">Related reads</h3>' +
    '<ul style="padding-left:18px;">' + items + "</ul>" +
    "</div>";
}

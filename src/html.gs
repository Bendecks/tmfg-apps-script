function buildPersonalHtml_(plan, ai, hub, candidates) {
  var hubLink = "";
  if (hub && hub.url) {
    var hubHref = toRelativeIfSameSite_(stripQueryAndHash_(hub.url));
    hubLink =
      '<div style="margin:16px 0;padding:14px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
      '<strong>Start here:</strong> ' +
      '<a href="' + escapeAttr_(hubHref) + '" style="text-decoration:none;font-weight:700;">' +
      escapeHtml_(hub.title || "Explore the hub") +
      "</a></div>";
  }

  var intro = '<p style="font-size:18px;color:#555;margin:0 0 16px 0;">' + escapeHtml_(ai.intro || "") + "</p>";

  var sections = (ai.sections || []).map(function(s) {
    return '<h2 style="margin:22px 0 8px 0;">' + escapeHtml_(s.h2 || "") + "</h2>" +
      '<p style="margin:0 0 10px 0;color:#444;">' + escapeHtml_(s.p || "") + "</p>";
  }).join("");

  var takeaway = ai.takeaway
    ? '<div style="background:#f8f8f8;padding:18px;border-radius:12px;border:1px solid #eee;margin:24px 0;"><strong>Takeaway:</strong> ' +
      escapeHtml_(ai.takeaway) + "</div>"
    : "";

  var affiliateBlock = buildSoftAffiliateBlock_(ai.softAffiliate);
  var cta = ai.cta ? ('<p style="margin-top:18px;color:#444;"><em>' + escapeHtml_(ai.cta) + "</em></p>") : "";
  var related = buildInternalLinksBlock_(candidates);

  return '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Helvetica,Arial,sans-serif;line-height:1.65;color:#333;max-width:650px;margin:0 auto;">' +
    hubLink + intro + sections + takeaway + affiliateBlock + cta + related + "</div>";
}

function buildSoftAffiliateBlock_(softAffiliate) {
  if (!softAffiliate || !softAffiliate.enabled || !softAffiliate.item) return "";

  var item = softAffiliate.item;
  var name = String(item.name || "").trim();
  var query = String(item.query || "").trim();
  var why = String(item.why || "").trim();

  if (!name || !query) return "";

  var url = buildAmazonSearchUrl_(query);

  return '<div style="margin-top:24px;padding:16px;border:1px solid #eee;border-radius:12px;background:#fafafa;">' +
    '<h3 style="margin:0 0 10px 0;">What made it easier</h3>' +
    '<div style="font-weight:600;">' + escapeHtml_(name) + '</div>' +
    (why ? ('<div style="margin-top:6px;color:#666;">' + escapeHtml_(why) + '</div>') : '') +
    '<div style="margin-top:10px;"><a href="' + escapeAttr_(url) + '" target="_blank" rel="nofollow sponsored" style="font-weight:600;text-decoration:none;">Check it on Amazon</a></div>' +
    '</div>';
}

function buildAmazonSearchUrl_(query) {
  var q = encodeURIComponent(String(query || "").trim());
  if (!AMAZON_TAG) return "https://www.amazon." + AMAZON_DOMAIN + "/s?k=" + q;
  return "https://www.amazon." + AMAZON_DOMAIN + "/s?k=" + q + "&tag=" + encodeURIComponent(AMAZON_TAG);
}

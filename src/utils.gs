function mustProp_(key) {
  var v = PROPS.getProperty(key);
  if (!v) throw new Error("Missing Script Property: " + key);
  return v;
}

function extractJsonObject_(text) {
  var cleaned = String(text || "").replace(/```json/gi, "").replace(/```/g, "").trim();
  var a = cleaned.indexOf("{");
  var b = cleaned.lastIndexOf("}");
  if (a < 0 || b <= a) throw new Error("Could not extract JSON.");
  return cleaned.slice(a, b + 1);
}

function slugify_(s) {
  return String(s || "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "item";
}

function escapeHtml_(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr_(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function truncate_(s, n) {
  var x = String(s || "");
  return x.length > n ? x.slice(0, n) + "..." : x;
}

function uniq_(arr) {
  var seen = {};
  var out = [];
  for (var i = 0; i < arr.length; i++) {
    var v = String(arr[i] || "").trim();
    if (!v || seen[v]) continue;
    seen[v] = 1;
    out.push(v);
  }
  return out;
}

function stripQueryAndHash_(u) {
  var s = String(u || "").trim();
  return s.split("#")[0].split("?")[0];
}

function toRelativeIfSameSite_(absoluteUrl) {
  var u = String(absoluteUrl || "").trim();
  if (!u) return u;
  if (u.indexOf(SITE_HOME_URL) === 0) {
    var rel = u.slice(SITE_HOME_URL.length);
    if (!rel) return "/";
    return rel.charAt(0) === "/" ? rel : ("/" + rel);
  }
  return u;
}

function getMainSheetHeaders_() {
  return [["Title", "Status", "Post URL", "Notes", "Type", "CategorySlug", "Angle"]];
}

function ensureMainSheetHeaders_(sheet) {
  var current = sheet.getRange(1, 1, 1, 7).getValues()[0];
  var desired = getMainSheetHeaders_()[0];
  var mismatch = false;
  for (var i = 0; i < desired.length; i++) {
    if (String(current[i] || "").trim() !== desired[i]) {
      mismatch = true;
      break;
    }
  }
  if (mismatch) {
    sheet.getRange(1, 1, 1, 7).setValues(getMainSheetHeaders_());
  }
}

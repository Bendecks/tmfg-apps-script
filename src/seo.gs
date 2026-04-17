function rewriteTitleForSEO_(title, categorySlug, angle) {
  var t = String(title || "").trim();
  if (!t) return t;

  t = t
    .replace(/\bmagic\b/ig, "fix")
    .replace(/\bquiet\b/ig, "easy")
    .replace(/\bcalm\b/ig, "easier")
    .replace(/\bantidote\b/ig, "answer");

  if (categorySlug === "kids-activities-fun") {
    if (!/(kids|child|outdoor|play|bored)/i.test(t)) {
      t = "Bored Kids? " + t;
    }
  } else if (categorySlug === "recipes-meals") {
    if (!/(dinner|meal|lunch|snack|weeknight|kids)/i.test(t)) {
      t = t + " for Family Dinners";
    }
  } else if (categorySlug === "parenting-hacks-tips") {
    if (!/(parents|kids|screen|morning|tantrum|meltdown|refuse)/i.test(t)) {
      t = t + " for Parents";
    }
  }

  if (t.length > 70) t = t.slice(0, 70).replace(/\s+\S*$/, "");
  return t;
}

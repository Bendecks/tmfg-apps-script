function runPersonalMachine() {
  refreshConfig_();

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(25000)) return;

  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();

    if (sheet.getName() === HUBS_SHEET_NAME || sheet.getName() === CONFIG_SHEET_NAME || sheet.getName() === AUTHORITY_SHEET_NAME) {
      throw new Error("Run runPersonalMachine() from your main content sheet, not Hubs, Config or Authority.");
    }

    ensureMainSheetHeaders_(sheet);
    ensureConfigSheet_(ss);
    ensureHubsSheet_(ss);
    ensureAuthoritySheet_(ss);

    var rows = sheet.getDataRange().getValues();
    var processed = 0;

    for (var i = 1; i < rows.length; i++) {
      if (processed >= PERSONAL_MAX_POSTS_PER_RUN) break;

      var rowIndex = i + 1;
      var status = String(rows[i][1] || "").trim().toLowerCase();
      if (status !== "queued") continue;

      try {
        sheet.getRange(rowIndex, 3).setValue("");
        sheet.getRange(rowIndex, 4).setValue("");

        var history = getHistory_(rows, 40);
        var plan = generateEditorialPlan_(history);
        plan.title = rewriteTitleForSEO_(plan.title, plan.categorySlug, plan.angle);

        sheet.getRange(rowIndex, 1).setValue(plan.title);
        sheet.getRange(rowIndex, 5).setValue(plan.type);
        sheet.getRange(rowIndex, 6).setValue(plan.categorySlug);
        sheet.getRange(rowIndex, 7).setValue(plan.angle);

        var hub = ensureCategoryHub_(ss, plan.categorySlug, sheet);
        var ai = generatePersonalPostJson_(plan, history);

        var mediaId = null;
        if (PERSONAL_INCLUDE_FEATURED_IMAGE) {
          var heroKeyword = String(ai.imageKeyword || ai.keyword || plan.title).trim();
          var heroBlob = generateHeroImage_(plan.title, heroKeyword, plan.categorySlug, plan.angle);
          mediaId = uploadWpMedia_(heroBlob, "featured-" + slugify_(plan.title));
        }

        var candidates = getInternalLinkCandidates_(rows, plan, 2);
        var html = buildPersonalHtml_(plan, ai, hub, candidates);
        var post = createWpPost_(plan.title, html, mediaId, PERSONAL_DEFAULT_STATUS, plan.categorySlug);

        sheet.getRange(rowIndex, 2).setValue("Done");
        sheet.getRange(rowIndex, 3).setValue(post.URL || post.url || "");
        sheet.getRange(rowIndex, 4).setValue(
          "OK | " + plan.type + " | " + plan.categorySlug + " | " + plan.angle + " | Img:" + (mediaId ? "yes" : "no")
        );

        updateCategoryHub_(ss, plan.categorySlug, sheet);
        maybeBuildAuthorityPage_(ss, sheet, plan);

        processed += 1;
      } catch (e) {
        sheet.getRange(rowIndex, 2).setValue("Error");
        sheet.getRange(rowIndex, 4).setValue(truncate_(String((e && e.message) ? e.message : e), 900));
        processed += 1;
      }
    }
  } finally {
    lock.releaseLock();
  }
}

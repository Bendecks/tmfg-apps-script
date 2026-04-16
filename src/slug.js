function listWpCategoriesToSheet_() {
  const props = PropertiesService.getScriptProperties();
  const siteId = props.getProperty("WP_SITE_ID");
  const token = props.getProperty("WP_OAUTH_TOKEN");

  if (!siteId || !token) {
    throw new Error("Missing WP_SITE_ID or WP_OAUTH_TOKEN in Script Properties.");
  }

  const res = UrlFetchApp.fetch(
    `https://public-api.wordpress.com/rest/v1.1/sites/${siteId}/categories`,
    { method: "get", headers: { Authorization: "Bearer " + token }, muteHttpExceptions: true }
  );

  const code = res.getResponseCode();
  const text = res.getContentText();
  if (code !== 200) {
    throw new Error(`List categories failed HTTP ${code}: ${text}`);
  }

  const json = JSON.parse(text);
  const cats = (json.categories || []);

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName("WP_Categories");
  if (!sheet) sheet = ss.insertSheet("WP_Categories");

  sheet.clearContents();

  const values = [
    ["Name", "Slug", "ID"],
    ...cats.map(c => [c.name || "", c.slug || "", c.ID || ""])
  ];

  sheet.getRange(1, 1, values.length, 3).setValues(values);
}
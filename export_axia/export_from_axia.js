const puppeteer = require("puppeteer");
const path = require("path");
const fs = require("fs");

(async () => {
  // 1. Pick the folder where you want your files to go
  const myDownloadFolder = path.resolve("./downloads");
  const filePath = path.resolve("./downloads/ListeVersements.xlsx");

  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
    console.log("File deleted!");
  } else {
    console.log("File not found, nothing to delete.");
  }

  const browser = await puppeteer.launch({
    headless: false,
    browser: "firefox",
    extraPrefsFirefox: {
      // 2 = Save to a custom folder directory
      "browser.download.folderList": 2,
      // Provide the folder path
      "browser.download.dir": myDownloadFolder,
      // Prevent Firefox from asking where to save the file
      "browser.download.useDownloadDir": true,
      "browser.helperApps.neverAsk.saveToDisk":
        "application/octet-stream,application/pdf,text/plain",
    },
  });

  const page = await browser.newPage();
  await page.goto(
    "http://easybee.bee.net.tn/GestionFactures/NewListeVersement?Annee=2026#",
    { waitUntil: "networkidle2" },
  );
  await page.setDefaultTimeout(99999999);
  await page.waitForSelector("#UserName");
  await page.type("#UserName", "S.MEJRI");
  await page.type("#Password", "a99Ih193D9DN");
  await page.click('button[class="btn btn-purplebee block full-width m-b"]');
  await page.waitForSelector(
    'a[class="btn btn-default buttons-excel buttons-html5"]',
  );
  await page.click('a[class="btn btn-default buttons-excel buttons-html5"]');
  // await page.waitForTimeout(500000); // Attendre que le téléchargement soit terminé

  await new Promise((r) => setTimeout(r, 5000));

  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

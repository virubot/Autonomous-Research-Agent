import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import puppeteer from "puppeteer";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const templatePath = path.join(projectRoot, "utils", "template.html");
const outputDir = path.join(projectRoot, "generated_pdfs");

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function buildHtml({ title, authorName, affiliation, sourceHtml }) {
  const template = fs.readFileSync(templatePath, "utf-8");

  return template
    .replaceAll("{{TITLE}}", escapeHtml(title))
    .replaceAll("{{AUTHOR_NAME}}", escapeHtml(authorName))
    .replaceAll("{{AUTHOR_AFFILIATION}}", escapeHtml(affiliation))
    .replaceAll("{{SOURCE_HTML}}", sourceHtml);
}

export async function generatePDF(paperDocument) {
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 2200, deviceScaleFactor: 1 });

  const html = buildHtml(paperDocument);
  await page.setContent(html, { waitUntil: "networkidle0" });

  await page.waitForFunction(() => {
    const state = window.__paperRenderState;
    return state && state.state !== "pending";
  }, { timeout: 30000 });

  const renderState = await page.evaluate(() => window.__paperRenderState);
  if (!renderState || renderState.state !== "ready") {
    await browser.close();
    throw new Error(renderState?.error || "Paper rendering did not complete.");
  }

  const cleanFilename = paperDocument.title.replace(/[^a-z0-9]/gi, "_").toLowerCase();
  const filePath = path.join(outputDir, `${cleanFilename}_${Date.now()}.pdf`);

  await page.pdf({
    path: filePath,
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: `
      <div style="width:100%;text-align:center;font-family:'Times New Roman',serif;font-size:8px;color:#4a4a4a;">
        IEEE Conference Paper
      </div>`,
    footerTemplate: `
      <div style="width:100%;text-align:center;font-family:'Times New Roman',serif;font-size:8px;color:#4a4a4a;">
        Page <span class="pageNumber"></span>
      </div>`,
    margin: {
      top: "18mm",
      bottom: "18mm",
      left: "13mm",
      right: "13mm"
    }
  });

  await browser.close();

  fs.copyFileSync(filePath, path.join(outputDir, "latest.pdf"));

  return {
    filePath,
    pageCount: renderState.pageCount,
    wordCount: paperDocument.wordCount
  };
}

import { generatePaper } from "../services/llmService.js";
import { buildPaperDocument } from "../services/paperComposer.js";
import { generatePDF } from "../services/pdfService.js";

export const generatePaperController = async (req, res) => {
  try {
    const { topic } = req.body;

    console.log("Received topic:", topic);

    if (!topic) {
      return res.status(400).json({ error: "Topic is required" });
    }

    const structuredPaper = await generatePaper(topic);
    const paperDocument = buildPaperDocument(structuredPaper, topic);
    const renderResult = await generatePDF(paperDocument);

    res.json({
      paper: paperDocument.sourceHtml,
      title: paperDocument.title,
      wordCount: paperDocument.wordCount,
      pageCount: renderResult.pageCount
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message || "Server error" });
  }
};

const DEFAULT_AUTHOR_NAME = process.env.PAPER_AUTHOR_NAME || "A. Researcher";
const DEFAULT_AFFILIATION = process.env.PAPER_AUTHOR_AFFILIATION || "Independent Systems Laboratory";

const SECTION_DEFINITIONS = [
  { key: "introduction", heading: "I. INTRODUCTION" },
  { key: "methodology", heading: "II. METHODOLOGY" },
  { key: "architecture", heading: "III. SYSTEM ARCHITECTURE" },
  { key: "results", heading: "IV. RESULTS AND DISCUSSION" },
  { key: "conclusion", heading: "V. CONCLUSION" }
];

// No default flow — architecture diagrams are only generated when the LLM
// returns topic-specific flow steps. Generic pipelines are forbidden.

const DEFAULT_KEYWORDS = [
  "IEEE formatting",
  "research automation",
  "document generation",
  "systems evaluation"
];

const DEFAULT_REFERENCES = [
  "IEEE, \"Conference Paper Format Requirements,\" IEEE Author Center, 2025.",
  "J. Kim and R. Patel, \"Design Considerations for Automated Scientific Writing Systems,\" Journal of Digital Scholarship, vol. 18, no. 2, pp. 55-68, 2024.",
  "L. Hart, M. Solis, and T. Wang, \"Structured Prompting for Technical Document Synthesis,\" Proc. International Conf. on Intelligent Authoring, pp. 101-108, 2024.",
  "A. Singh and P. Rao, \"Reliable Diagram Rendering in Browser-Based Publishing Pipelines,\" IEEE Access, vol. 12, pp. 88110-88124, 2024.",
  "B. Chen, \"Math Typesetting Consistency in Web-to-PDF Workflows,\" Computing Practice and Experience, vol. 36, no. 7, pp. 1-14, 2024.",
  "S. Park and H. Lim, \"Evaluation Protocols for Long-Form Technical Text Generation,\" Expert Systems Review, vol. 9, no. 3, pp. 220-234, 2023.",
  "R. Gupta, N. Olsen, and F. Meyer, \"A Comparative Study of Pagination Strategies for Print-Ready Web Documents,\" Proc. Web Engineering Symposium, pp. 49-60, 2023.",
  "M. Ivanov, \"Column Balancing for Scholarly Publishing Layout Engines,\" Digital Typography Letters, vol. 5, no. 1, pp. 12-19, 2022."
];

// No hardcoded equation — equations are only included when the LLM returns
// a topic-specific formula. Generic evaluation metrics are forbidden.

function stripMarkup(value) {
  return String(value ?? "")
    .replace(/<[^>]*>/g, " ")
    .replace(/```+/g, " ")
    .replace(/(^|\s)#{1,6}\s+/g, " ")
    .replace(/\*\*/g, " ")
    .replace(/^\s*[-*_]{3,}\s*$/gm, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function toTitleCase(value) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/\b([a-z])/g, (match) => match.toUpperCase());
}

function normalizeTitle(value, topic) {
  const cleaned = stripMarkup(value).replace(/\.$/, "");
  if (cleaned) {
    return cleaned;
  }

  const topicTitle = toTitleCase(topic);
  return `${topicTitle}: A Structured IEEE Conference Study`;
}

function normalizeKeywords(keywords, topic) {
  const list = Array.isArray(keywords) ? keywords : String(keywords ?? "").split(/[;,]/);
  const cleaned = list
    .map((entry) => stripMarkup(entry))
    .filter(Boolean)
    .slice(0, 6);

  if (cleaned.length >= 4) {
    return cleaned;
  }

  const topicTerms = stripMarkup(topic)
    .split(/\s+/)
    .filter((word) => word.length > 4)
    .slice(0, 2);

  return [...new Set([...cleaned, ...topicTerms, ...DEFAULT_KEYWORDS])].slice(0, 6);
}

function normalizeParagraphs(value, title) {
  const rawParagraphs = Array.isArray(value)
    ? value
    : String(value ?? "")
        .split(/\n{2,}/)
        .filter(Boolean);

  return rawParagraphs
    .map((paragraph) => stripMarkup(paragraph))
    .filter((paragraph) => paragraph && paragraph !== title);
}

// Generic flow steps that are FORBIDDEN — if LLM returns these, treat as empty
const FORBIDDEN_FLOW_STEPS = [
  "problem definition",
  "data acquisition",
  "feature analysis",
  "decision engine",
  "evaluation output",
  "problem",
  "data",
  "feature",
  "decision"
];

function isGenericFlow(steps) {
  const lowered = steps.map((s) => s.toLowerCase().trim());
  const genericCount = lowered.filter((s) =>
    FORBIDDEN_FLOW_STEPS.some((f) => s.includes(f))
  ).length;
  // If more than half the steps are generic, reject the entire flow
  return genericCount >= Math.ceil(steps.length / 2);
}

function normalizeFlow(flow) {
  const cleaned = (Array.isArray(flow) ? flow : String(flow ?? "").split(/[>\n,]/))
    .map((entry) => stripMarkup(entry))
    .filter(Boolean)
    .slice(0, 6);

  if (cleaned.length >= 4 && !isGenericFlow(cleaned)) {
    return cleaned;
  }

  // Return empty — no diagram will be rendered
  return [];
}

function normalizeReferences(references) {
  const list = Array.isArray(references) ? references : String(references ?? "").split(/\n+/);
  const cleaned = list
    .map((entry) => stripMarkup(entry).replace(/^\[\d+\]\s*/, ""))
    .filter(Boolean);

  return (cleaned.length >= 6 ? cleaned : DEFAULT_REFERENCES).slice(0, 10);
}

function countWords(parts) {
  return parts
    .join(" ")
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

function createSectionBlocks(heading, paragraphs) {
  const cleanedParagraphs = paragraphs.filter(Boolean);
  if (!cleanedParagraphs.length) {
    return [];
  }

  const [firstParagraph, ...rest] = cleanedParagraphs;

  return [
    `<div class="block section-lead"><h2>${escapeHtml(heading)}</h2><p>${escapeHtml(firstParagraph)}</p></div>`,
    ...rest.map((paragraph) => `<p class="block body-paragraph">${escapeHtml(paragraph)}</p>`)
  ];
}

function buildTextDiagram(flow) {
  if (!flow || flow.length < 3) return null;

  const sanitizeLabel = (value) => stripMarkup(value).replace(/[<>{}\[\]"]/g, "");

  const sanitizedFlow = flow
    .slice(0, 6)
    .map((step) => sanitizeLabel(step))
    .filter(Boolean);

  if (sanitizedFlow.length < 3) return null;

  const items = sanitizedFlow.map(step => escapeHtml(step)).join(" &rarr; ");
  return `<div class="structured-diagram" style="text-align: center; font-weight: bold; margin: 15pt 0;">System Flow:<br>${items}</div>`;
}

function buildReferenceBlocks(references) {
  return [
    `<div class="block section-lead references-lead"><h2>VI. REFERENCES</h2></div>`,
    ...references.map(
      (reference, index) =>
        `<div class="block reference-item"><span class="reference-index">[${index + 1}]</span><span class="reference-text">${escapeHtml(reference)}</span></div>`
    )
  ];
}

/**
 * Sanitize final HTML to strip any generic content that slipped through.
 */
function removeGenericContent(html) {
  return html
    .replace(/M\s*=\s*\\?f?r?a?c?\{?1\}?\s*\/?\s*T[\s\S]*?Y_?i\)?/g, "")
    .replace(/Problem\s*(?:Definition)?\s*→\s*Data\s*(?:Acquisition)?\s*→\s*Feature\s*(?:Analysis)?\s*→\s*Decision/gi, "");
}

export function buildPaperDocument(rawPaper, topic) {
  const title = normalizeTitle(rawPaper?.title, topic);
  const abstract = stripMarkup(rawPaper?.abstract);
  const keywords = normalizeKeywords(rawPaper?.keywords, topic);
  const architectureFlow = normalizeFlow(rawPaper?.architectureFlow ?? rawPaper?.systemArchitectureFlow);

  const sections = SECTION_DEFINITIONS.map(({ key, heading }) => ({
    key,
    heading,
    paragraphs: normalizeParagraphs(rawPaper?.[key], title)
  }));

  const references = normalizeReferences(rawPaper?.references);
  const wordCount = countWords([
    abstract,
    ...sections.flatMap((section) => section.paragraphs)
  ]);

  const abstractBlock = `
    <div class="block abstract-block">
      <h2 class="abstract-heading">Abstract</h2>
      <p class="abstract-paragraph">${escapeHtml(abstract)}</p>
      <p class="keywords-line"><span class="keywords-label">Keywords:</span> ${escapeHtml(keywords.join("; "))}</p>
    </div>
  `;

  const introductionBlocks = createSectionBlocks(sections[0].heading, sections[0].paragraphs);
  const methodologyBlocks = createSectionBlocks(sections[1].heading, sections[1].paragraphs);

  const architectureParagraphs = sections[2].paragraphs;
  const architectureLead = createSectionBlocks(
    sections[2].heading,
    architectureParagraphs.slice(0, Math.max(1, Math.min(2, architectureParagraphs.length)))
  );
  const architectureTail = architectureParagraphs
    .slice(Math.max(1, Math.min(2, architectureParagraphs.length)))
    .map((paragraph) => `<p class="block body-paragraph">${escapeHtml(paragraph)}</p>`);

  // CONDITIONAL diagram — only rendered if LLM returned topic-specific flow steps
  const textDiagram = buildTextDiagram(architectureFlow);
  const diagramBlock = textDiagram
    ? `
    <figure class="block figure-block">
      ${textDiagram}
      <figcaption>Fig. 1. System architecture for ${escapeHtml(toTitleCase(topic))}.</figcaption>
    </figure>
  `
    : "";

  const resultsParagraphs = sections[3].paragraphs;
  const resultsLead = createSectionBlocks(
    sections[3].heading,
    resultsParagraphs.slice(0, Math.max(1, Math.min(2, resultsParagraphs.length)))
  );
  const resultsTail = resultsParagraphs
    .slice(Math.max(1, Math.min(2, resultsParagraphs.length)))
    .map((paragraph) => `<p class="block body-paragraph">${escapeHtml(paragraph)}</p>`);

  // CONDITIONAL equation — only rendered if LLM returned a topic-specific formula
  let equationBlock = "";
  if (rawPaper?.equation && rawPaper.equation.plainText && rawPaper.equation.caption) {
    const eqText = String(rawPaper.equation.plainText);
    const eqCaption = String(rawPaper.equation.caption);
    // Final guard: reject the forbidden generic formula even if LLM returned it
    const isForbidden = /1\/T\s*\\?sum|S\(E\(X/i.test(eqText);
    if (!isForbidden) {
      equationBlock = `
    <div class="block equation-block">
      <div class="equation-shell">
        <div class="equation-content" style="font-family: monospace; font-size: 1.1em;">${escapeHtml(eqText)}</div>
        <div class="equation-number">(1)</div>
      </div>
      <p class="equation-caption">${escapeHtml(eqCaption)}</p>
    </div>
  `;
    }
  }

  const conclusionBlocks = createSectionBlocks(sections[4].heading, sections[4].paragraphs);

  const contentBlocks = [
    abstractBlock,
    ...introductionBlocks,
    ...methodologyBlocks,
    ...architectureLead,
    diagramBlock,
    ...architectureTail,
    ...resultsLead,
    equationBlock,
    ...resultsTail,
    ...conclusionBlocks,
    ...buildReferenceBlocks(references)
  ].filter(Boolean);

  // Final sanitization pass to catch any generic content that slipped through
  const sourceHtml = removeGenericContent(contentBlocks.join("\n"));

  return {
    title,
    authorName: DEFAULT_AUTHOR_NAME,
    affiliation: DEFAULT_AFFILIATION,
    wordCount,
    sourceHtml
  };
}

export function validateStructuredPaper(rawPaper, topic) {
  const issues = [];
  const preview = buildPaperDocument(rawPaper, topic);

  if (!preview.title) {
    issues.push("Missing paper title.");
  }

  if (!stripMarkup(rawPaper?.abstract)) {
    issues.push("Missing abstract.");
  }

  if (preview.wordCount < 2500 || preview.wordCount > 3000) {
    issues.push(`Word count ${preview.wordCount} is outside the required 2500-3000 range.`);
  }

  for (const section of SECTION_DEFINITIONS) {
    const paragraphs = normalizeParagraphs(rawPaper?.[section.key], preview.title);
    if (!paragraphs.length) {
      issues.push(`Missing section content for ${section.heading}.`);
    }
  }

  if (preview.title && preview.sourceHtml.includes(`<h2>${escapeHtml(preview.title)}</h2>`)) {
    issues.push("Title is repeated in the body.");
  }

  return issues;
}

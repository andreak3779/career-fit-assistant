/**
 * Resume Template — Sarah Ashford  (JD-tailored version)
 * Matches the standard resume format used across all application documents.
 * Format: centered header · blue ALL CAPS sections · round bullets · italic right-tab dates
 *         Word native page-2 header · natural page flow (no forced breaks)
 *
 * Fill all // FILL: sections. Do NOT change BLUE, margins, or helpers.
 * Output: outputs/SarahAshford_Resume_CompanyName.docx
 *
 * Page limits: 1–2 pages. Trim in this order if over:
 *   1. Oldest role — keep 2 JD-relevant bullets
 *   2. Short-tenure roles — keep 2 bullets
 *   3. Tighten sp(0,30) → sp(0,20) on bullets in oldest 2 roles only
 *   4. Body font: 20 → 19 hp (never below 19 body)
 *   5. Skills: remove categories with no JD match
 */

const {
  Document, Packer, Paragraph, TextRun, BorderStyle,
  TabStopType, AlignmentType, Header
} = require('docx');
const fs = require('fs');

// ─── FILL: Output path ───────────────────────────────────────────────────────
const OUTPUT_PATH = 'outputs/SarahAshford_Resume_FILL_CompanyName.docx';

// ─── FILL: Contact info — copy exactly from Resume_Snapshot.md ───────────────
const name        = 'SARAH ASHFORD';           // ALL CAPS
const tagline     = 'FILL_Tagline';            // derive from JD role e.g. 'Senior .NET Developer | C# · ASP.NET Core · Azure'
const email       = 'FILL_email';
const phone       = 'FILL_phone';              // with parentheses: (XXX) XXX-XXXX
const location    = 'Winnipeg, MB \u00b7 CST';   // city · province · timezone — fixed value
const linkedin    = 'FILL_linkedinUrl';
const github      = 'FILL_githubUrl';
const pluralsight = 'FILL_pluralsightUrl';
const mslearn     = 'FILL_mslearnUrl';

// ─── FILL: Summary (2 lines — JD-tailored) ───────────────────────────────────
// Line 1: Exact JD role title + 2–3 ATS keywords + years experience + domain
// Line 2: Cert status (from profile-facts.md) + strongest differentiator for this JD
const summary = [
  'FILL_summary_line_1',
  'FILL_summary_line_2',
];

// ─── FILL: Skills — ordered by JD relevance, ATS keywords first ──────────────
// Mirror JD phrasing exactly. Remove irrelevant categories.
// Lead each list with the most JD-recognisable keyword.
const skillCategories = [
  { label: 'FILL_Category_1', skills: 'FILL_skills_1' },
  { label: 'FILL_Category_2', skills: 'FILL_skills_2' },
  { label: 'FILL_Category_3', skills: 'FILL_skills_3' },
  { label: 'FILL_Category_4', skills: 'FILL_skills_4' },
  // Add/remove as needed — 5–7 categories max
];

// ─── FILL: Experience — reverse chronological, bullets reordered by JD ───────
// company: use '' to omit the | separator (self-directed roles)
// Most JD-relevant bullet goes first within each role.
const experience = [
  {
    title:   'FILL_Job_Title',
    company: 'FILL_Company, FILL_City, FILL_Province',
    dates:   'FILL_Month YYYY – FILL_Month YYYY',
    bullets: [
      'FILL_bullet_1',
      'FILL_bullet_2',
      'FILL_bullet_3',
    ],
  },
  {
    title:   'FILL_Job_Title_2',
    company: 'FILL_Company_2, FILL_City, FILL_Province',
    dates:   'FILL_Month YYYY – FILL_Month YYYY',
    bullets: [
      'FILL_bullet_1',
      'FILL_bullet_2',
    ],
  },
  // Add remaining roles — keep only JD-relevant bullets
];

// ─── FILL: Education ─────────────────────────────────────────────────────────
// Format: 'Degree – School, City'
const educationItems = [
  'FILL_Degree – FILL_School, FILL_City',
  'FILL_Degree – FILL_School, FILL_City',
];

// ─── FILL: Cert status — use exact strings from profile-facts.md ─────────────
const az900Status        = 'Certified \u2014 April 2026';
const ai200Status        = 'In progress \u2014 exam available July 2026; 11 courses + 1 lab (4 completed, 7 in progress)';
const pluralsightSummary = '151 courses + 31 in progress, 21 labs completed + 1 in progress (182 total) across Azure, ASP.NET Core, Angular, GitHub Copilot, Docker, Kubernetes, CI/CD, Python, and leadership';

// ════════════════════════════════════════════════════════════════════════════
// DO NOT EDIT BELOW — shared format constants, helpers, document structure
// (Now imported from _layout.js; if you need a layout-only change, edit _layout.js)
// Resume-specific helpers (skillLine, jobHeader, bullet, etc.) live below.
// ════════════════════════════════════════════════════════════════════════════

const {
  BLUE, MARGIN_TOP_BOT, MARGIN_SIDES,
  sp, run, blueBorder,
  sectionHeading, headingContentSpacer, sectionSpacer,
} = require('./_layout');

const CONTENT_WIDTH  = 12240 - (MARGIN_SIDES * 2);  // 10080 DXA

function skillLine(label, skills) {
  return new Paragraph({
    spacing: sp(0, 45),
    children: [run(label + ': ', 20, true), run(skills, 20)],
  });
}

function summaryLine(text) {
  return new Paragraph({
    spacing: sp(0, 50),
    children: [run(text, 21)],
  });
}

// Single-line job entry: bold "Title | Company, Location" + right-tab + italic dates
// company = '' omits the | separator for self-directed roles
function jobHeader(title, company, dates) {
  const leftText = company ? `${title} | ${company}` : title;
  return new Paragraph({
    spacing: sp(60, 0),
    keepNext: true,
    tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_WIDTH }],
    children: [
      run(leftText, 21, true),
      new TextRun({ text: '\t', font: 'Carlito', size: 21 }),
      run(dates, 20, false, true),
    ],
  });
}

// Round bullet with hanging indent — ATS-safe plain-text bullet character
function bullet(text) {
  return new Paragraph({
    spacing: sp(0, 30),
    indent: { left: 360, hanging: 200 },
    children: [run('\u2022  ' + text, 20)],
  });
}

// Small spacer with keepNext so it travels with the job below, not the job above
function jobSpacer() {
  return new Paragraph({ spacing: sp(60, 0), keepNext: true, children: [run('', 20)] });
}

// keepNext chained through all bullets except last — prevents job splitting across pages
function buildExperience(jobs) {
  const paras = [];
  jobs.forEach((job, i) => {
    if (i > 0) paras.push(jobSpacer());
    paras.push(jobHeader(job.title, job.company, job.dates));
    job.bullets.forEach((b, bi) => {
      const isLast = bi === job.bullets.length - 1;
      paras.push(new Paragraph({
        spacing: sp(0, 30),
        indent: { left: 360, hanging: 200 },
        keepNext: !isLast,
        children: [run('\u2022  ' + b, 20)],
      }));
    });
  });
  return paras;
}

// Page-2+ running header — extracted as factory so default and even share identical content
// evenAndOddHeaderAndFooters: true is REQUIRED; without it LibreOffice skips the page-2 header
function headerContent() {
  return new Header({
    children: [
      new Paragraph({
        spacing: { before: 0, after: 60, line: 240, lineRule: 'auto' },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '888888', space: 2 } },
        children: [run(`${name}  |  ${email}  |  ${phone}  |  ${location}  |  ${linkedin}  |  ${github}  |  ${pluralsight}`, 18)],
      }),
    ],
  });
}

const doc = new Document({
  evenAndOddHeaderAndFooters: true,   // needed so page 2 (even) inherits the running header
  sections: [{
    properties: {
      titlePage: true,   // "Different First Page" — page 1 gets empty header
      page: {
        size: { width: 12240, height: 15840 },
        margin: {
          top:    MARGIN_TOP_BOT,
          bottom: MARGIN_TOP_BOT,
          left:   MARGIN_SIDES,
          right:  MARGIN_SIDES,
          header: 360,   // 0.25" from top — sits within the top margin
        },
      },
    },
    headers: {
      first:   new Header({ children: [new Paragraph({ children: [] })] }),
      default: headerContent(),   // odd pages (3+)
      even:    headerContent(),   // page 2 — explicit even header for LibreOffice compat
    },
    children: [

      // ── NAME — centered, bold, ALL CAPS ──────────────────────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: sp(0, 120),   // 6pt after — prevents bold 16pt text bleeding into tagline
        children: [run(name, 32, true)],
      }),

      // ── TAGLINE — centered, derived from JD role ──────────────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: sp(0, 30),
        children: [run(tagline, 20)],
      }),

      // ── CONTACT LINE 1 — email · phone · location (no border) ───────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: sp(0, 0),
        children: [run(`${email}  |  ${phone}  |  ${location}`, 19)],
      }),

      // ── CONTACT LINE 2 — links · bottom border ───────────────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: sp(0, 0),
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '888888', space: 2 } },
        children: [run(`${linkedin}  |  ${github}  |  ${pluralsight}`, 19)],
      }),

      // ── PROFESSIONAL SUMMARY ─────────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('PROFESSIONAL SUMMARY'),
      headingContentSpacer(),
      ...summary.map(line => summaryLine(line)),

      // ── TECHNICAL SKILLS ─────────────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('TECHNICAL SKILLS'),
      headingContentSpacer(),
      ...skillCategories.map(c => skillLine(c.label, c.skills)),

      // ── PROFESSIONAL EXPERIENCE ──────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('PROFESSIONAL EXPERIENCE'),
      headingContentSpacer(),
      ...buildExperience(experience),

      // ── EDUCATION ────────────────────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('EDUCATION'),
      headingContentSpacer(),
      ...educationItems.map(e => bullet(e)),

      // ── CERTIFICATIONS ───────────────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('CERTIFICATIONS'),
      headingContentSpacer(),
      bullet(`Microsoft Azure Fundamentals (AZ-900) \u2014 ${az900Status}`),
      bullet(`Azure AI Cloud Developer Associate (AI-200) \u2014 ${ai200Status}`),
      bullet(`Pluralsight: ${pluralsight} \u2014 ${pluralsightSummary}`),
      bullet(`Microsoft Learn: ${mslearn}`),

    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUTPUT_PATH, buf);
  console.log('Resume written:', OUTPUT_PATH);
});

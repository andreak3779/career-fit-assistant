/**
 * Cold Outreach Letter Template — Sarah Ashford
 * Matches the standard resume/cover-letter format for a consistent identity.
 * Format: centered header · blue ALL CAPS sections · round bullets · 1 page
 *
 * Fill all // FILL: sections. Do NOT change BLUE, margins, or helpers.
 * Output: outputs/SarahAshford_ColdOutreach_CompanyName.docx
 */

const {
  Document, Packer, Paragraph, TextRun, BorderStyle, AlignmentType
} = require('docx');
const fs = require('fs');

// ─── FILL: Output path ───────────────────────────────────────────────────────
const OUTPUT_PATH = 'outputs/SarahAshford_ColdOutreach_FILL_Agency.docx';

// ─── FILL: Contact info — copy exactly from Resume_Snapshot.md ───────────────
const name     = 'SARAH ASHFORD';   // ALL CAPS
const tagline  = 'FILL_Tagline';    // match resume tagline for this application
const email    = 'FILL_email';
const phone    = 'FILL_phone';      // with parentheses: (XXX) XXX-XXXX
const location = 'Winnipeg, MB · CST';   // city · province · timezone — fixed value
const linkedin = 'FILL_linkedinUrl';
const github   = 'FILL_githubUrl';
const pluralsight = 'FILL_pluralsightUrl';

// ─── FILL: Letter metadata ───────────────────────────────────────────────────
const date   = 'FILL_Month DD, YYYY';                        // e.g. 'April 19, 2026'
const reLine = 'FILL_Re: [Target Role Type] Opportunities';  // e.g. 'Re: Senior .NET Developer Opportunities'

// ─── FILL: Hook paragraph ────────────────────────────────────────────────────
// 1–2 sentences. Brief professional intro + the type of role being sought.
// This is a cold introduction, NOT a response to a specific posting —
// do not reference "your posting" or a specific job req.
const hookText = 'FILL_hook_paragraph_text';

// ─── FILL: WHAT I BRING bullets (3–4 items) ──────────────────────────────────
// Each: { label: 'Bold label', body: 'plain body text.' }  Max 2 lines each.
// Pull from app-engine-bundle.md differentiators — same source as the tailored
// cover letter, not new content invented for this letter.
const bringItems = [
  { label: 'FILL_Label_1', body: 'FILL_body_1' },
  { label: 'FILL_Label_2', body: 'FILL_body_2' },
  { label: 'FILL_Label_3', body: 'FILL_body_3' },
  // { label: 'FILL_Label_4', body: 'FILL_body_4' },  // uncomment if needed
];

// ─── FILL: Availability paragraph (plain text, not bulleted) ────────────────
// Remote/location preference + notice period or availability timeline.
const availabilityText = 'FILL_availability_paragraph_text';

// ─── FILL: Closing paragraph ─────────────────────────────────────────────────
// 2 sentences: direct CTA to connect/call + note that resume is attached.
const closingText = 'FILL_closing_paragraph_text';

// ════════════════════════════════════════════════════════════════════════════
// DO NOT EDIT BELOW — shared format constants, helpers, document structure
// (Now imported from _layout.js; if you need a layout-only change, edit _layout.js)
// ════════════════════════════════════════════════════════════════════════════

const {
  BLUE, MARGIN_TOP_BOT, MARGIN_SIDES,
  sp, run, blueBorder,
  sectionHeading, headingContentSpacer, blankLineContentSpacer, sectionSpacer,
  bulletPara,
} = require('./_layout');

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: {
          top:    MARGIN_TOP_BOT,
          bottom: MARGIN_TOP_BOT,
          left:   MARGIN_SIDES,
          right:  MARGIN_SIDES,
        },
      },
    },
    children: [

      // ── NAME — centered, bold, ALL CAPS — matches resume ─────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: sp(0, 30),
        children: [run(name, 32, true)],
      }),

      // ── TAGLINE — centered — matches resume ───────────────────────────────
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

      // ── DATE ─────────────────────────────────────────────────────────────
      new Paragraph({ spacing: sp(160, 40), children: [run(date, 21)] }),
      blankLineContentSpacer(),
      // ── RE: LINE ─────────────────────────────────────────────────────────
      new Paragraph({ spacing: sp(0, 120), children: [run(reLine, 21, true)] }),
      blankLineContentSpacer(),
      // ── HOOK ─────────────────────────────────────────────────────────────
      new Paragraph({ spacing: sp(0, 0), children: [run(hookText, 21)] }),

      // ── WHAT I BRING ─────────────────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('WHAT I BRING'),
      headingContentSpacer(),
      ...bringItems.map(i => bulletPara(i.label, i.body)),

      // ── AVAILABILITY ─────────────────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('AVAILABILITY'),
      headingContentSpacer(),
      new Paragraph({ spacing: sp(0, 0), children: [run(availabilityText, 21)] }),

      // ── CLOSING ──────────────────────────────────────────────────────────
      sectionSpacer(),
      new Paragraph({ spacing: sp(0, 0), children: [run(closingText, 21)] }),
      blankLineContentSpacer(),
      // ── SIGN-OFF ─────────────────────────────────────────────────────────
      new Paragraph({ spacing: sp(120, 40), children: [run('Sincerely,', 21)] }),
      blankLineContentSpacer(),
      blankLineContentSpacer(),
      new Paragraph({ spacing: sp(120, 0),  children: [run(name, 21)] }),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUTPUT_PATH, buf);
  console.log('Cold outreach letter written:', OUTPUT_PATH);
});

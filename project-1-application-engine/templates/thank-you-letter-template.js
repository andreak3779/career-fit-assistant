/**
 * Post-Interview Thank You Letter Template — Sarah Ashford
 * Matches the standard resume/cover-letter format for a consistent identity.
 * Format: centered header · blue ALL CAPS sections · round bullets · 1 page
 * Shortest of the four letter types — send within 24 hours of the interview.
 *
 * Fill all // FILL: sections. Do NOT change BLUE, margins, or helpers.
 * Output: outputs/SarahAshford_ThankYou_CompanyName.docx
 */

const {
  Document, Packer, Paragraph, TextRun, BorderStyle, AlignmentType
} = require('docx');
const fs = require('fs');

// ─── FILL: Output path ───────────────────────────────────────────────────────
const OUTPUT_PATH = 'outputs/SarahAshford_ThankYou_FILL_CompanyName.docx';

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
const date   = 'FILL_Month DD, YYYY';   // e.g. 'April 19, 2026' — date the letter is sent
const reLine = 'FILL_Re: Thank You — [Role] Interview, [Company]';

// ─── FILL: Opening paragraph ──────────────────────────────────────────────────
// 1–2 sentences. Thank the interviewer(s) by name + reference the specific
// interview date. These details are per-application inputs from the user,
// not pulled from app-engine-bundle.md.
const openingText = 'FILL_opening_paragraph_text';

// ─── FILL: KEY TAKEAWAYS bullets (2–3 items) ─────────────────────────────────
// Each: { label: 'Bold label', body: 'plain body text.' }  Max 2 lines each.
// Tie specific discussion points from the interview to fit — per-application
// content the user supplies, not generic differentiators from the bundle.
const takeawayItems = [
  { label: 'FILL_Label_1', body: 'FILL_body_1' },
  { label: 'FILL_Label_2', body: 'FILL_body_2' },
  // { label: 'FILL_Label_3', body: 'FILL_body_3' },  // uncomment if needed
];

// ─── FILL: Closing paragraph ─────────────────────────────────────────────────
// 2 sentences: reiterate interest + mention next steps/availability for follow-up.
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
      // ── OPENING ──────────────────────────────────────────────────────────
      new Paragraph({ spacing: sp(0, 0), children: [run(openingText, 21)] }),

      // ── KEY TAKEAWAYS ─────────────────────────────────────────────────────
      sectionSpacer(),
      sectionHeading('KEY TAKEAWAYS'),
      headingContentSpacer(),
      ...takeawayItems.map(i => bulletPara(i.label, i.body)),

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
  console.log('Thank you letter written:', OUTPUT_PATH);
});

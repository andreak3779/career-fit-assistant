/**
 * Shared DOCX layout helpers — extracted from resume-template.js and copied
 * to all four document templates. Edit once, used everywhere.
 *
 * Used by: resume-template.js, cover-letter-template.js,
 *          cold-outreach-letter-template.js, thank-you-letter-template.js
 *
 * CommonJS (require / module.exports) — matches existing template imports.
 */

const { Paragraph, TextRun, BorderStyle } = require('docx');

// ── Constants ───────────────────────────────────────────────────────────────
const BLUE           = '2E6DA4';   // matches resume section heading color
const MARGIN_TOP_BOT = 720;        // 0.5" — matches resume
const MARGIN_SIDES   = 1080;       // 0.75" — matches resume

// ── Spacing + run helpers ───────────────────────────────────────────────────
const sp = (before, after) => ({ before, after, line: 240, lineRule: 'auto' });
const run = (text, size, bold = false, italic = false, color = '000000') =>
  new TextRun({ text, font: 'Carlito', size, bold, italics: italic, color });

const blueBorder = {
  bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 1 },
};

// ── Section + spacer primitives ─────────────────────────────────────────────
// ALL CAPS blue section heading — matches resume exactly
function sectionHeading(text) {
  return new Paragraph({
    spacing: sp(160, 0),
    border: blueBorder,
    children: [run(text, 22, true, false, BLUE)],
  });
}

function headingContentSpacer() {
  return new Paragraph({ spacing: sp(0, 60), children: [run('', 20)] });
}

function blankLineContentSpacer() {
  return new Paragraph({ spacing: sp(0, 60), children: [run('', 20)] });
}

function sectionSpacer() {
  return new Paragraph({ spacing: sp(0, 0), children: [run('', 20)] });
}

// ── Bullet primitive ────────────────────────────────────────────────────────
// Round bullet with bold label — matches resume bullet style
function bulletPara(label, body) {
  return new Paragraph({
    spacing: sp(0, 50),
    indent: { left: 360, hanging: 200 },
    children: [
      run('•  ', 21),
      run(label + ': ', 21, true),
      run(body, 21),
    ],
  });
}

module.exports = {
  BLUE,
  MARGIN_TOP_BOT,
  MARGIN_SIDES,
  sp,
  run,
  blueBorder,
  sectionHeading,
  headingContentSpacer,
  blankLineContentSpacer,
  sectionSpacer,
  bulletPara,
};

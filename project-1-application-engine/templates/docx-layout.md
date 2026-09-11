# DOCX Layout Reference — Cover Letter & Resume

**Last Updated:** May 2026 - **Based on Sarah Ashford's production resume**

> **Only read this file when debugging spacing issues or creating new documents.**
> Normal usage: copy the templates and fill `// FILL:` sections.

---

## Measurement Reference

- **Font**: Carlito (default LibreOffice) or Calibri (Microsoft)
- **Size values**: Points (pt). docx.js uses half-points (hp): 22=11pt, 21=10.5pt, 20=10pt
- **Spacing values**: Twips (DXA units) — 914 twips ≈ 9pt line spacing · 19050 twips ≈ 1.5pt
- **Conversion**: DXA to pt: divide by 12.74 (approximation)

---

## Core docx.js Rules

- `•` (bullet) and `–` (en dash) are literal TextRun characters — do NOT use `LevelFormat.BULLET`
- Never use `\n` inside a TextRun — use separate Paragraph elements
- Always set page size explicitly (docx.js defaults to A4, not US Letter)
- PageBreak must be inside a Paragraph — standalone PageBreak creates invalid XML
- Font defaults: Use font name from template; both Carlito and Calibri are acceptable

---

## Resume Formatting Standards

**Sarah's proven layout** (used in production since May 2025):

| Element | Size | Bold | Before (DXA) | After (DXA) | Before (pt) | After (pt) | Notes |
|---------|------|------|---|---|---|---|---|
| **Header Section** | | | | | | | |
| Name (header) | — | — | — | — | — | — | Varies; see cover letter section if needed |
| Contact line | 10pt | — | 0 | 12700 | 0 | 1.0 | Name · Phone · Email on one line |
| **Body Sections** | | | | | | | |
| Section heading (SUMMARY, SKILLS, EXPERIENCE, EDUCATION, CERTS) | 11pt | **bold** | 76200 | 38100 | 6.3 | 3.1 | **Bottom border: 1pt solid black** |
| Body paragraph | 10.5pt | — | 0 | 25400 | 0 | 2.0 | Text content; multiple paragraphs per section |
| Job title (Role \| Company, Location) | 10.5pt | **bold** | 25400 | 0 | 2.1 | 0 | `keepNext: true` to stay with bullets |
| Job bullets | 10.5pt | — | 0 | 12700 | 0 | 1.0 | Prefix: `• ` (bullet + space) or `– ` (en dash + space) |
| Skill category line | 10pt | **bold** | 0 | 19050 | 0 | 1.5 | Format: `**Category:**  list of skills` on same line |
| Education lines | 10.5pt | — | 0 | 19050 | 0 | 1.5 | Degree · School · Year |
| Cert lines | 10pt | **bold** | 0 | 12700 | 0 | 1.0 | Cert name · Status · Date |

---

## Resume Page Layout

```text
┌─────────────────────────────────────────────────────┐
│  SARAH ASHFORD (header text)                        │  ← varies per doc
│  Title · Skills summary                             │
│  Email | Phone | LinkedIn | GitHub | Location      │
├─────────────────────────────────────────────────────┤
│                                                     │
│ SUMMARY (section heading with border)              │
│ Body text (3–4 lines max)                           │
│                                                     │
│ TECHNICAL SKILLS (section heading with border)     │
│ Backend: C#, ASP.NET Core, ...                     │  ← skill lines
│ Frontend: Angular, TypeScript, ...                 │
│ Database: SQL Server, T-SQL, ...                   │
│                                                     │
│ PROFESSIONAL EXPERIENCE (section heading)          │
│ Senior Full-Stack Developer                        │  ← job title
│ • Bullet 1 describing achievement                  │  ← bullets
│ • Bullet 2 describing achievement                  │
│                                                     │
│ Software Developer                                 │
│ • Bullet 1 describing achievement                  │
│ • Bullet 2 describing achievement                  │
│                                                     │
│ EDUCATION (section heading with border)            │
│ Degree – School – Year                             │
│ Diploma – School – Year                            │
│                                                     │
│ CERTIFICATIONS & LEARNING (section heading)        │
│ **Cert Name** — Status — Date                      │
│ **Pluralsight** — Course count, labs, topics       │
└─────────────────────────────────────────────────────┘
```

---

## Common Spacing Patterns

### Section Spacing Pattern

```text
Before section heading: 76200 twips (6pt gap)
Section heading line: 11pt bold + bottom border
After section heading: 38100 twips (3pt gap)
Body content follows
```

### Job Entry Pattern

```text
Job title (bold, 10.5pt): before=25400, after=0
Bullet 1 (regular, 10.5pt): before=0, after=12700
Bullet 2 (regular, 10.5pt): before=0, after=12700
...
[Next job title or section]
```

### Skill Category Pattern

```text
Category (bold, 10pt): before=0, after=19050
**Backend:** C#, ASP.NET Core, ...
**Frontend:** Angular, React, ...
```

---

## DXA (Twip) Unit Reference

**For developers using `docx.js`:** All spacing values above are in **DXA (twips)** — 1440 DXA = 1 inch.

### Quick Reference

- 12700 DXA ≈ 1.0 pt spacing
- 19050 DXA ≈ 1.5 pt spacing
- 25400 DXA ≈ 2.0 pt spacing
- 76200 DXA ≈ 6.3 pt spacing (before section headings)

### Conversion Formula

```text
DXA to pt: DXA ÷ 12.74 ≈ points
pt to DXA: pt × 12.74 ≈ DXA
```

---

## Template Integration

**Official templates:**

- `resume-template.js` — Uses DXA values from table above
- `cover-letter-template.js` — Uses DXA values from table above

All spacing in templates should match the DXA column exactly. If generating a new document and spacing looks off, compare against this table first.

---
name: profile-resume-pdf
description: >
  Generates a platform-ready PDF resume for Sarah Ashford's Senior Full-Stack
  .NET Developer identity — formatted for upload to Canadian Job Bank, Indeed,
  LinkedIn, and similar job boards. No specific job description required.
  Use whenever the user says "create a PDF resume", "resume as PDF",
  "upload to Indeed / LinkedIn / Job Bank as PDF", "platform PDF resume",
  "baseline PDF resume", or "create a PDF I can upload to job sites."
  Also trigger when the user asks to "refresh my resume as PDF" without
  supplying a JD, or says "I want a PDF ready to post."
  Always use this skill — do NOT generate ad hoc.
  Output: one PDF file ready to upload or print.
---

# Senior Full-Stack .NET Developer — Profile Resume PDF

Generates a canonical, ATS-safe PDF resume rooted in Sarah's core identity:
**C#, ASP.NET Core Web API, Entity Framework Core, Angular (v12–21), TypeScript,
MS SQL Server.**

> **Source files** (load before Step 1):
> - `app-engine-bundle.md` — employment history, dates, metrics
> - `app-engine-bundle.md` — cert status, differentiators, genuine gaps
>
> **ATS note:** DOCX parses more reliably than PDF on most job boards. Use PDF
> when the platform explicitly requires it, or for printing/emailing. For
> Canadian Job Bank, Indeed, and LinkedIn uploads, DOCX is preferred.

---

## Inputs

No job description required. Load automatically:

1. `app-engine-bundle.md` — source of truth for employment history, dates, metrics
2. `app-engine-bundle.md` — cert status, differentiators, resolved/genuine gaps

---

## Step 1 — Establish the Identity Anchor

Lead with **Senior Full-Stack .NET Developer**. Every content decision
(summary wording, skills ordering, bullet selection) reinforces this.

Core stack to foreground:

| Layer | Technologies |
|---|---|
| Language / Runtime | C#, .NET / .NET Core |
| API / Backend | ASP.NET Core Web API, REST, Entity Framework Core |
| Frontend | Angular (v12–21), TypeScript, RxJS |
| Data | MS SQL Server, T-SQL, SSIS |
| Cloud | Microsoft Azure (AZ-900 certified; AI-200 in progress) |
| DevOps / Tooling | GitHub Copilot Enterprise, Azure DevOps, Docker, GitHub Actions |

---

## Step 2 — Build Resume Content

### Summary (2 sentences max)
Pattern: `[Years] of experience building [identity] · [top differentiator] · [cert / cloud signal]`

### Skills Section
Order: Core .NET stack → Frontend → Data → Cloud/DevOps → Testing → AI/Automation
**No tables in output.** Use `Label:  items` inline format for ATS compatibility.

### Experience Bullets
- Lead with impact — metrics, scale, modernization outcomes
- Always include 7× SSIS performance story (Riverside Pharmacy)
- Always include at least one Angular modernization bullet per relevant employer
- Always include at least one ASP.NET Core Web API bullet per relevant employer
- Cap at 4–5 bullets per role — PDF must stay ≤ 2 pages
- Vantage: trim to 2–3 bullets (oldest role)

### Certifications
Use cert status **exactly** as in `app-engine-bundle.md`:
- AZ-900 certified → `Microsoft Azure Fundamentals (AZ-900) — Certified April 18, 2026`
- AI-200 in progress → `Azure AI Cloud Developer Associate (AI-200) — In Progress`
- Do NOT display certs without a credential ID as earned

---

## Step 3 — Generate PDF

Install dependencies if needed:
```bash
pip install reportlab --break-system-packages -q
```

Copy the generation script from project or write inline using these rules:

### Design constants (must match project identity)
```python
BLUE = "#2E6DA4"  # section headings — must match project BLUE
DARK = "#1A1A1A"  # body text
MED = "#444444"  # employer / secondary text
LGRAY = "#CCCCCC"  # divider lines
```

### Layout rules (ATS-safe)
- Page size: US Letter (`letter` from reportlab.lib.pagesizes)
- Margins: 0.65" left/right, 0.55" top/bottom
- Name: 22pt Helvetica-Bold, centered
- Tagline: 10pt Helvetica, centered, color MED
- Contact: 8.5pt Helvetica, centered, bullet separators
- Section headings: 10.5pt Helvetica-Bold, color BLUE, ALL CAPS
- Divider line after each heading: 0.8pt, color BLUE
- Body text: 9pt Helvetica, leading 13
- Bullets: `•` prefix with 12pt left indent, 8pt first-line indent
- Job title: 9.5pt Helvetica-Bold, 6pt space before
- Employer line: 8.5pt Helvetica, color MED

### Critical rules
- **NEVER use `ROWPADDING` in `TableStyle`** — causes banner spacing bugs
  Use explicit `TOPPADDING` / `BOTTOMPADDING` per row instead
- No tables in content (only use Table for layout if needed)
- No columns — single column throughout (ATS-safe)
- No headers/footers, no graphics, no text boxes
- Use `KeepTogether` for each job block to prevent mid-role page breaks
- Use `•` (`\u2022`) for bullets — literal character, not HTML entity

### Output filename
```
SarahAshford_Resume_SeniorFullStackNET.pdf
```

Copy to `outputs/` and run.

---

## Step 4 — Verify and Present

```python
from pypdf import PdfReader

r = PdfReader("outputs/SarahAshford_Resume_SeniorFullStackNET.pdf")
print("Pages:", len(r.pages))  # Must be ≤ 2
```

If page count > 2: trim Vantage to 2 bullets, trim Professional Development to 2 bullets.

Tell the user the PDF's path under `outputs/`.

**Inline summary after presenting:**
- Cert status applied (AZ-900 certified; AI-200 in progress)
- 7× SSIS differentiator included
- Legacy modernization track record surfaced
- Page count confirmed
- ATS upload recommendation: DOCX preferred on most platforms; use this PDF for printing, email, or platforms that explicitly require PDF

---

## Platform Notes

| Platform | Recommended format |
|---|---|
| Canadian Job Bank | DOCX preferred; PDF accepted |
| Indeed | DOCX preferred; PDF accepted |
| LinkedIn | DOCX for Easy Apply; PDF for Featured section |
| Email / Print | PDF is ideal |
| Company portals | Check platform — most accept both |

---
name: create-a-cover-letter-and-tailored-resume-for-job-description
description: "Generates a tailored cover letter and resume for a specific job posting. Use whenever the user provides a job description, job posting, or job listing and wants application documents created. Also triggers when the user says 'apply for this job', 'help me apply', 'write a cover letter for', 'tailor my resume for', or uploads a job posting. **ALWAYS checks for a prior application to this exact posting first, then runs fit assessment; only generates documents if fit is Strong or better.** Resume is loaded automatically from app-engine-bundle.md in the project. Job description may be provided as a .md file, pasted text, or URL. Output as DOCX files only"
---

# Cover Letter & Tailored Resume Generator

Creates tailored cover letter + ATS-optimized resume as DOCX files.
Uses pre-built JS scaffold templates — fill variables, do not rewrite structure.

> **Templates** (read before writing any code): `cover-letter-template.js` · `resume-template.js`
> **Cert status + differentiators**: `app-engine-bundle.md` — load before fit assessment
> **Portfolio projects**: `app-engine-bundle.md` — load before fit assessment; use for cover letter highlights and resume bullets
> **Layout** (only if debugging spacing): `docx-layout.md`
> Do NOT load `pluralsight-courses.md` — use `app-engine-bundle.md` for ATS keyword reference if needed.
>
> **Grounding rule:** every claim in the resume and cover letter — employers, titles,
> dates, projects, skills, cert status — must trace to `app-engine-bundle.md`. Never
> invent, infer, or embellish a claim that isn't there; if a strong-sounding detail
> would help but isn't in the bundle, leave it out rather than making it up.

---

## 🚨 MANDATORY Step 0 — Fit Assessment Gate

**Run this step FIRST, before any other inputs. Do NOT skip. Do NOT generate documents unless fit is Strong.**

### 0a — Check for a prior application

Before assessing fit, ask (don't assume the user will volunteer it): **"Have you already applied to this exact posting — not just this company generally — recently?"** Companies re-post the same req, and a cold re-application days or weeks later reads as a duplicate, not renewed interest.

- If this is a **new req** or a **different role** at a company applied to before, proceed normally — a repeat employer with a genuinely new posting isn't a duplicate.
- If it's the **same posting** applied to within the last ~60 days, or the company has a pattern of repeat cold applications with no response, stop and ask instead of generating documents: has this or a prior attempt gotten any response (screen, interview, silence)? Is there a referral or a named recruiter contact available this time? Default to **not** resubmitting cold — surface the option to find a warmer path in instead (referral, direct recruiter outreach) or to skip it.
- If the user has no application tracker to check against, ask directly rather than skipping the question — don't rely on memory of "have I mentioned this before" as the only check.

### 0b — Load inputs for assessment
- **Job description**: pasted text, `.md` file, or URL (`web_fetch` if URL). Ask if missing.
- **Resume**: load `app-engine-bundle.md` from project automatically.
- **Profile facts**: load `app-engine-bundle.md` — use the Resolved Framing Gaps and Known Genuine Gaps lists.
- **Portfolio projects**: load `app-engine-bundle.md` — use the Quick Reference table to identify portfolio-level evidence for skills that appear in the JD.

### 0c — Parse the JD
Extract and hold in working memory:
- **Required skills** — anything marked must / required / strong / essential / years of experience in
- **Nice-to-have skills** — anything marked nice to have / asset / preferred / bonus

### 0d — Run quick match
For each required and nice-to-have skill, assign one of:

| Status | Meaning |
|---|---|
| ✅ | Production experience in resume, OR resolved framing gap from `app-engine-bundle.md` |
| 🟡 | Portfolio-level (GitHub project), course-level only (Pluralsight / MS Learn), or framing gap needing surface |
| 🔴 | Not present in resume, portfolio, or coursework — genuine gap |

Rules:
- Never re-flag items in the Resolved Framing Gaps list from `app-engine-bundle.md` — those are always ✅.
- Check `app-engine-bundle.md` before assigning 🔴 — portfolio projects can elevate a skill from course-only to 🟡 Portfolio-level.
- Distinguish production vs. portfolio vs. course-level honestly. Do not soften 🔴 to 🟡 to make the fit look better.
- Nice-to-haves only affect the fit rating, not the gate decision.

### 0e — Display the assessment inline

Output a compact table in this format:

```
## ✅ / 🔴 Fit Assessment — [Job Title] at [Company]

**Required Skills**
| Skill | Status | Evidence |
|---|---|---|
| [skill from JD] | ✅ / 🟡 / 🔴 | [one-phrase source — employer or course] |

**Nice-to-Haves**
| Skill | Status | Evidence |
|---|---|---|
| [skill from JD] | ✅ / 🟡 / 🔴 | [one-phrase source] |

**Fit Rating: [Strong / Good / Stretch / Pass]**
[One sentence rationale.]
```

Keep the Evidence column to ≤ 6 words (e.g. "Fieldstone Benefits Administrators, production", "RecipeBox, portfolio", or "Pluralsight, 3 courses"). Only cite a portfolio project that appears as an active entry in `app-engine-bundle.md`'s Portfolio Projects table — a project commented out or omitted there isn't real evidence, even if it's mentioned elsewhere in this file as an example.

Fit rating definitions:
- **Strong** — All required skills ✅; 0–2 required skills are 🟡; at least 2 nice-to-haves present
- **Good** — All required skills ✅ or 🟡; 1–2 genuine 🔴 gaps in nice-to-haves only
- **Stretch** — 1–2 required skills are 🔴; or 3+ required skills are 🟡 (course-only)
- **Pass** — 3+ required skills are 🔴; or critical domain/tech mismatch

### 0f — Apply the gate (MANDATORY)

**If fit is Strong or Good:**
→ Bold statement: **"✅ Strong fit — proceeding to generate documents."** (or **"Good fit with selective tailoring — proceeding."**)
→ Continue to Step 1 immediately. Generate documents.

**If fit is Stretch or Pass:**
→ State the specific concerns clearly (name the 🔴 gaps, which required skills are missing, what they mean for the application).
→ **Do NOT ask if the user wants to proceed.**
→ **Do NOT generate documents.**
→ State: **"This role is not a strong fit. I recommend focusing on roles that align with your core strengths. Would you like me to:"**
   - **Option A:** Help you find better-matched positions?
   - **Option B:** Suggest a learning plan to close the primary gap?
   - **Option C:** Show you a gap analysis if you want to apply anyway (requires your confirmation)?

---

## Step 1 — Gather Remaining Inputs
(Runs only after the gate passes)

- **Job description**: already loaded in Step 0.
- **Resume**: already loaded in Step 0.
- **Profile facts**: already loaded in Step 0.
- **Portfolio projects**: already loaded in Step 0.

---

## Step 2 — Analyze the JD
Extract and keep in working memory: job title + company · **5–8 ATS keywords** (copy JD wording exactly) · 3–5 nice-to-haves · tone (startup vs enterprise) · key responsibilities · must-haves/disqualifiers.

---

## Step 3 — Extract Contact Info
Use values exactly as written in `app-engine-bundle.md`. Do not paraphrase, reformat, or infer:
`name · email · phone · linkedin · github · pluralsightUrl`

---

## Step 4 — Plan Content

**Resume:** Summary (2 lines, exact role + 2–3 ATS keywords) · Skills (ATS keywords first, remove irrelevant categories) · Experience bullets (reorder/reword by JD relevance) · Cert status: use values from `app-engine-bundle.md`.

**Page 2:** Run the script first, then open the output and check page count. If it spills to page 2, uncomment `page2Header()` and position it before the job that starts on page 2.

**Cover letter — STRICT ONE PAGE MAXIMUM. No exceptions.**
Hook (strongest match to top JD requirement, NOT "I am writing…") · WHAT I BRING (4–5 items max: ATS keyword → evidence, 1 line each — never 2) · TWO HIGHLIGHTS (2 most relevant employers + concrete detail, 1–2 lines each) · Closing (company/role interest + direct CTA, 2 sentences max) · Tone: enterprise = formal, startup = direct.

**Cover letter content budget — enforce before writing any bullet:**
- Hook: 2 sentences max
- WHAT I BRING bullets: 4–5 items; each body text must fit on one line (≤ 120 chars) — cut ruthlessly if needed
- TWO HIGHLIGHTS bullets: 1–2 lines each; combine detail into a single sentence where possible
- Closing: 2 sentences max
- If content feels tight, cut a WHAT I BRING bullet entirely rather than letting any bullet run long

When selecting cover letter highlights and WHAT I BRING evidence, check `app-engine-bundle.md`'s Portfolio Projects table for active projects that demonstrate the JD's key requirements — use only what's listed there (e.g. PortfolioSite for GitHub Actions CI/CD, job-app-copilot for Python/AI tooling, RecipeBox for .NET/Blazor/testing discipline), and confirm each one still appears before citing it, since projects get added or retired. Prefer production employers for highlights, but use portfolio projects as secondary evidence when they directly address a required skill. Do not invent a highlight, metric, or project detail not present in `app-engine-bundle.md` — cut a bullet rather than fabricate one.

---

## Step 5 — Generate DOCX

```bash
node -e "require('docx')" 2>/dev/null || npm install docx
```

1. Copy `cover-letter-template.js` → `outputs/tmp/cover-letter.js`
2. Copy `resume-template.js` → `outputs/tmp/resume.js`
3. Fill all `// FILL:` sections. Do not alter spacing, margins, or helpers.
4. Set `az900Status` from `app-engine-bundle.md` cert table (Certified or In progress).
5. Run: `node outputs/tmp/cover-letter.js && node outputs/tmp/resume.js`

**ATS rules:** no tables · no columns · no text boxes · no headers/footers · no graphics · standard section headings · en dash prefix (–) · no Unicode in bullet body · no color · Arial throughout · resume ≤ 2 pages · cover letter = 1 page.

---

## Step 5.5 — Optional Audit Pass (script cross-check)

`generate_resume.py`/`generate_cover_letter.py` (the deterministic scripts
behind `python -m cli.career_fit_api generate-resume`/`generate-cover-letter`)
pull the same profile bundle this skill does, but select ATS keywords,
skills, and bullets by simpler rule-based logic — not full parity with this
skill's JD-tailored judgment (no per-bullet character-budget enforcement, no
startup-vs-enterprise tone switching, and `generate_resume.py` currently has
no equivalent of this skill's manual page-2 check in Step 4). **This step
does not replace the documents you just generated** — it's an optional,
advisory second pass to catch coverage gaps, not a content source.

If you want the extra confidence, run it against a scratch path (not the
real deliverable filenames):

```bash
python -m cli.career_fit_api generate-resume <jd_path> --out outputs/tmp/audit_resume.docx
python -m cli.career_fit_api generate-cover-letter <jd_path> --out outputs/tmp/audit_cover_letter.docx
```

Open both and compare against the documents from Step 5 — not for wording
parity (expected to differ), but for **structural coverage**: does the
audit version reference a required or nice-to-have skill that's genuinely
missing from your version entirely? Does it include a section heading yours
lacks? If something material surfaces, fix it in the real deliverable, not
by substituting the audit copy. Delete the `outputs/tmp/audit_*` files
afterward — they're a check, not a keeper.

---

## Step 6 — Validate and Present

No automated DOCX validator is available locally (the sandbox's `/mnt/skills/public/docx/scripts/office/validate.py` doesn't exist in Claude Code). Open `outputs/[filename].docx` and visually confirm formatting — page count, section headings, no broken layout — before delivering it.

Fix errors before presenting. Naming: `SarahAshford_CoverLetter_CompanyName.docx` · `SarahAshford_Resume_CompanyName.docx`
Confirm the files are in `outputs/` and tell the user their paths.

Inline summary: ATS keywords incorporated · gaps excluded · assumptions made.
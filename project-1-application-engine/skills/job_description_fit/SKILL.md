---
name: job-description-fit
description: >
  Quick fit check against a specific job posting — produces a fit rating and
  inline skills table only; no gap analysis report is generated. Use whenever
  the user pastes or uploads a job description and wants a fast yes/no on fit
  before committing to a full gap analysis or application documents. Trigger
  phrases: "quick fit check", "am I a fit for this", "does this match my skills",
  "what's my fit rating", "rate my fit", "check this job", or any job description
  pasted without an explicit request for a full report. Also trigger when the user
  says "should I apply?" and has not yet run a gap analysis. If Strong or Good,
  prompts the user to generate a cover letter and resume. If Stretch or Pass,
  states the fit and stops — no document generation. Always use this skill for
  quick fit checks — do not handle ad hoc.
---

# Job Description Fit — Quick Check

Produces a compact fit rating + skills table in one step. No gap analysis
report is written. If the fit is Strong or Good, offers to generate tailored
cover letter and resume via the `create-a-cover-letter-and-tailored-resume-for-job-description` skill.

> **Fit computation is deterministic — don't re-derive it by hand.** Run
> `python -m cli.career_fit_api fit-check <jd_path>` (backed by
> `shared/fit_engine.py`, which already implements the ✅/🟡/🔴 rules and the
> Strong/Good/Stretch/Pass thresholds below) and present its output directly.
> This reads the profile from `outputs/profile-bundle.json` itself — you
> don't need to load `app-engine-bundle.md` for this skill at all.

---

## Step 1 — Load Inputs

- **Job description**: pasted text, `.md` file, or URL (`web_fetch` if URL).
  If missing, ask before proceeding. If the JD is pasted text or fetched from
  a URL rather than an existing file, write it to a scratch `.md` file first
  — `fit-check` takes a file path, not stdin.

---

## Step 2 — Run the Fit Check

Run `python -m cli.career_fit_api fit-check <jd_path>` from the repo root and
take its printed markdown table as the fit assessment — do not manually
re-parse the JD or re-derive the ✅/🟡/🔴 statuses.

**Sanity-check the result before presenting it.** The underlying JD parser is
heading-and-bullet-driven and can miss atypically-formatted postings (no
recognizable "Requirements" heading, prose-only requirements, etc.) — if the
required-skills table looks implausibly short or empty for how detailed the
posting actually is, fall back to reading the JD yourself, parsing required
and nice-to-have skills manually, and note to the user that the automated
parse looked off. Do not silently present a table you don't believe reflects
the actual posting.

For reference, the status meanings and rating thresholds the script applies:

| Status | Meaning |
|---|---|
| ✅ | Production experience in resume, OR resolved framing gap |
| 🟡 | Portfolio-level (GitHub project) or course-level only (Pluralsight / MS Learn) |
| 🔴 | Not present in resume, portfolio, or coursework — genuine gap |

- **Strong** — All required skills ✅; 0–2 required skills are 🟡; at least 2 nice-to-haves present
- **Good** — All required skills ✅ or 🟡, short of Strong's bar
- **Stretch** — 1–2 required skills are 🔴; or 3+ required skills are 🟡 (course-only, no genuine gaps)
- **Pass** — 3+ required skills are 🔴

---

## Step 3 — Apply the Gate

### If fit is Strong or Good:

State: **"✅ [Strong / Good] fit — would you like me to generate a tailored cover letter and resume for this role?"**

- If the user says **yes** (or equivalent) → hand off to `create-a-cover-letter-and-tailored-resume-for-job-description`. The fit assessment above satisfies the fit-check portion of that skill's Step 0, but its Step 0a (prior-application check) still hasn't run here — ask it before proceeding, then skip straight to Step 1.
- If the user says **no** → stop. Offer no further output.

### If fit is Stretch or Pass:

State the specific blockers clearly — name each 🔴 required skill gap and what it means for candidacy.

Then state: **"This role is not a strong fit right now. Focus on roles that align with your core strengths."**

**Do NOT offer to generate application documents.**
**Do NOT ask if the user wants to proceed anyway.**

Stop here.

---

## What This Skill Does NOT Do

- Does not write a gap analysis markdown file
- Does not emit a GapAnalysis_Bridge.md (no genuine-gap report is generated here — run the full `gap-analysis-job-description` skill if a Bridge file is needed for learning plan generation)
- Does not generate cover letters or resumes directly — it hands off to the cover letter skill after the user confirms
- Does not produce a resume tailoring strategy or application angle — use `gap-analysis-job-description` for that level of detail

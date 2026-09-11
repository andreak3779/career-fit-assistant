---
name: gap-analysis-job-description
description: >
  Produces a structured gap analysis comparing Sarah Ashford's resume and skills
  against a specific job description. Use this skill whenever the user shares a
  job posting and asks how well they match, what gaps exist, whether to apply,
  or how to frame the application. Also trigger when the user pastes a job
  description without an explicit question — the implied ask is always "how do
  I fit this?" Trigger phrases: "gap analysis", "how do I fit", "should I apply",
  "what am I missing for this role", "analyze this job", "evaluate this posting",
  "this is another example job description", or any substantial job description
  pasted into the conversation. Always use this skill — do not handle ad hoc.
  Output: downloadable markdown file + inline summary.
---

# Gap Analysis — Job Description Skill

Compares Sarah's profile against a job posting. Output: markdown file + inline
summary covering fit rating, strengths, gaps, and application strategy.

> **The report is generated deterministically — don't build it by hand.** Run
> `python -m cli.career_fit_api gap-analysis <jd_path> --out outputs/<file>.md`
> (backed by `shared/fit_engine.py`, the same engine `job_description_fit`
> uses) and read the written file back before summarizing it. This reads the
> profile from `outputs/profile-bundle.json` itself — you don't need to load
> `app-engine-bundle.md` for this skill.

---

## Inputs

1. **Job description** — pasted text, uploaded file, or URL (`web_fetch` if
   URL). If it's not already a file, write it to a scratch `.md` file first —
   `gap-analysis` takes a file path, not stdin.

If the job description is missing, ask before proceeding.

---

## Step 1 — Generate the Report

Run `python -m cli.career_fit_api gap-analysis <jd_path> --out
outputs/<Company>_<Role>_GapAnalysis.md` and read the file it writes.

**Sanity-check the result before summarizing it.** Same caveat as
`job_description_fit`: the JD parser is heading-and-bullet-driven and can
miss atypically-formatted postings. If the Summary Table looks implausibly
short or empty for how detailed the posting actually is, fall back to
reading the JD yourself and flag to the user that the automated parse looked
off — don't silently summarize a report you don't believe reflects the
actual posting.

For reference, the status meanings and rating thresholds the script applies:

| Status | Meaning |
|---|---|
| ✅ Match | Production experience in resume, OR resolved framing gap |
| 🟡 Portfolio | Demonstrated in own GitHub project; no production employment use |
| 🟡 Coursework | Pluralsight only; no production or project use |
| 🔴 Gap | Not in resume, portfolio, or coursework |

| Rating | Meaning |
|---|---|
| **Strong** | All required skills ✅; 0–2 required skills are 🟡; at least 2 nice-to-haves present. → Proceed to cover letter/resume generation OR learning plan for depth. |
| **Good** | All required skills ✅ or 🟡, short of Strong's bar. → Proceed to cover letter/resume with selective tailoring. |
| **Stretch** | 1–2 required skills are 🔴; or 3+ required skills are 🟡 (course-only, no genuine gaps). → Do NOT apply yet; recommend learning plan to close primary gaps first. |
| **Pass** | 3+ required skills are 🔴. → Not a fit; focus on better-matched roles or significant reskilling. |

**Gate behavior for this skill:**
- **Strong/Good:** Analysis informs next steps — proceed to cover letter/resume generation (via `create-a-cover-letter-and-tailored-resume-for-job-description` skill) OR learning plan if reskilling needed
- **Stretch/Pass:** Recommend learning plan to close gaps before applying. Do NOT proceed to cover letter/resume generation without explicit gap closure and user confirmation of the gap closure plan.

State the output file's path under `outputs/` for the user.

---

## Step 2 — Inline Summary

6–8 sentences covering: fit rating · top 2 strengths · primary gap + mitigation ·
single most important resume action · whether to apply. Draw these from the
generated report's Strong Matches / Genuine Gaps / How to Frame the
Application sections — don't re-derive them independently.

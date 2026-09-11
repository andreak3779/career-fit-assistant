---
name: cold-outreach-recruiter-letter
description: >
  Generates a cold-outreach letter introducing Sarah Ashford to a recruiter or
  staffing agency — not tied to a specific job posting. Use whenever the user
  says "cold email a recruiter", "reach out to a recruiter", "write a recruiter
  outreach letter", "cold call letter", "introduce myself to an agency", or
  wants to proactively contact a recruiter without a specific job description
  in hand. Different from create-a-cover-letter-and-tailored-resume-for-job-description
  (which requires a JD) and from fullstack-net-profile-resume (which produces a
  job-board-upload cover letter with [Company Name]/[Role Title] placeholders).
  This skill's letter targets a person/agency directly and asks about their
  open roles. Output: one DOCX file.
---

# Cold Outreach Letter to a Recruiter

Creates a short, non-JD-specific cover letter introducing Sarah to a recruiter
or agency, as a DOCX file.

> **Generated deterministically — don't build it by hand or fill a template.**
> Run `python -m cli.career_fit_api generate-cold-call --recruiter-name "..."
> --role-type "..." [--company "..."]` (backed by
> `shared/docx_layout.py`/`generate_cold_call_letter.py`, which already pulls
> cert status, differentiators, and portfolio evidence straight from
> `outputs/profile-bundle.json`). No JD file is needed or expected — this is
> the one letter-generation skill in this project with no JD in hand by
> design, and the script's `jd` argument is genuinely optional to match.
> **Layout** (only if debugging spacing): `docx-layout.md`

---

## Inputs

Ask the user for anything not already provided:

- **Recruiter name** (or omit — defaults to "Hiring Team")
- **Agency/company name** (optional — omit to default to "Your Company"; ask if it materially changes the letter)
- **Target role type** — e.g. "Senior .NET Developer roles", "cloud/Azure-focused roles" (omit the Re: line entirely if not provided)
- **Contact channel** (optional context only — email vs LinkedIn message; doesn't change the letter content)

---

## Step 1 — Generate the Letter

Run:

```bash
python -m cli.career_fit_api generate-cold-call \
  --recruiter-name "[Recruiter Name or omit]" \
  --role-type "[Target Role Type or omit]" \
  --company "[Agency/Company or omit]"
```

The script handles contact info, the Re: line, salutation, hook, "Why I'm a
Fit" bullets (from Key Differentiators/Cert Registry), an optional portfolio
highlight, and the closing — all grounded in the profile bundle, capped to
letter length by design. Do not invent claims beyond what it generates.

If the differentiator/portfolio evidence is thin, the script prints a stderr
warning ("draft is generic — manually review before sending") — surface that
warning to the user rather than silently presenting a generic letter as if it
were fully grounded.

---

## Step 2 — Validate and Present

No automated DOCX validator is available locally (the sandbox's
`/mnt/skills/public/docx/scripts/office/validate.py` doesn't exist in Claude
Code). Open the generated file and visually confirm formatting — page count,
section headings, no broken layout — before delivering it.

The script names the file `SarahAshford_ColdCall_<Company>.docx` under
`outputs/` automatically (pass `--out` to override). Confirm the file's path
and tell the user.

Inline summary: differentiators/portfolio evidence used · any low-confidence
warning from Step 1 · assumptions made (e.g. recruiter name defaulted to
"Hiring Team", company defaulted to "Your Company").

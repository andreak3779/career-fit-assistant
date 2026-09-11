# Project 1 — Job Search: Application Engine

Generates tailored job-application artifacts — gap analyses, resumes, cover letters, interview prep, and salary research — for Sarah Ashford. Skills read `app-engine-bundle.md` as the single source of truth instead of loading Project 2's individual source files directly.

## Setup

Resume/cover-letter/cold-outreach/thank-you-letter generation shells out to
Node.js at generation time via `templates/*.js` — this isn't just a build-time
lint dependency, so skip this section only if you'll never generate a DOCX
from this project.

**1. Check Node.js is installed:**

```bash
node --version
```

Any Node ≥10 satisfies the `docx` package's `engines` constraint. If it's
missing, install via your distro's package manager (e.g.
`sudo apt install nodejs npm` on Debian/Ubuntu) or
[nodesource](https://github.com/nodesource/distributions) for a newer version.

**2. Install dependencies:**

```bash
cd project-1-application-engine
npm install
```

This installs `docx` (the only listed dependency in `package.json`), used by
`templates/resume-template.js` and `templates/cover-letter-template.js` and
their DOCX-generating siblings.

**3. Verify the templates parse:**

```bash
npm run check-templates
```

Each template should print a `✓`. A syntax error here means something's
wrong with the install or the template file, not a missing dependency.

Generated documents are written to `outputs/` at the repo root (gitignored).
There's no automated DOCX validator available locally — visually check
generated `.docx` files before delivering them.

## Contents

- `app-engine-bundle.md` — generated bundle (profile facts + resume snapshot + skills summary + GitHub repos) regenerated from `project-2-profile-learning-hub` via "generate bundles." Replaces loading `profile-facts.md`, `Resume_Snapshot.md`, `skills-summary.md`, and `github-repos.md` individually — skills should read this bundle, not the Project 2 source files.
- `skills/` — 13 skills:
  - `gap_analysis_job_description_SKILL.md` — structured gap analysis against a job description
  - `job_description_fit_SKILL.md` — quick fit check only (no full gap report)
  - `create-a-cover-letter-and-tailored-resume-for-job-description_SKILL.md` — tailored DOCX cover letter + resume for a specific posting
  - `interview-prep-SKILL.md` — role-specific interview prep DOCX
  - `azure-focused-net-developer-SKILL.md` — specialized Azure/.NET job search
  - `job-search-SKILL.md` — fallback job search assistant when no specialized skill applies
  - `salary-research-SKILL.md` — CAD salary/contract rate research
  - `employment-research-SKILL.md` — screens for high-confidence, low-gap opportunities
  - `job-fit-advisor-SKILL.md` — recommends job types/titles to target
  - `fullstack-net-profile-resume-SKILL.md` — platform resume/cover letter template
  - `profile-resume-pdf-SKILL.md` — platform-ready PDF resume
  - `cold-outreach-recruiter-letter_SKILL.md` — cold-outreach DOCX letter introducing Sarah to a recruiter/agency, not tied to a posting
  - `post-interview-thank-you-letter_SKILL.md` — post-interview thank-you DOCX letter, sent within 24 hours
- `reference/` — supporting material loaded by skills mid-workflow:
  - `gap-coaching.md` — coaching notes for any 🟡/🔴 gap item (gap analysis Step 2)
  - `star-bank.md` — STAR story bank for interview prep (Step 5)
  - `interview-prep.md` — .NET/Azure interview prep reference
  - `recruiter-briefing-template.md` — recruiter briefing template
  - `JobSearch_KeywordStrategy.md` — job alert keyword strategy for LinkedIn/Indeed (tracked here rather than in `project-3-presence-identity` since it's job search strategy, not presence content)
- `templates/` — `cover-letter-template.js`, `resume-template.js`, `cold-outreach-letter-template.js`, `thank-you-letter-template.js`, `docx-layout.md`
- `.gitignore` — excludes generated output (`node_modules/`, `*.docx`, `*.pdf`, `.DS_Store`)

## Data flow

`project-2-profile-learning-hub` is the source of truth for career facts and learning history. Running "generate bundles" there regenerates `app-engine-bundle.md` here — re-run it after updating profile facts, resume content, skills, or GitHub repos in Project 2.

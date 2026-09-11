# Project 2 — Profile & Learning Hub

Source-of-truth project for Sarah Ashford's career facts, skills, and learning history. Other projects (`project-1-application-engine`, `project-3-presence-identity`) consume bundles generated from this data rather than re-deriving facts themselves.

## Setup

Only needed to run `parse_pluralsight_html.py` (Pluralsight HTML export
parser) or `pdf-template.py` (learning-plan PDF generator) directly from this
project. There's no separate venv or `requirements.txt` for this project —
it shares the repo-root install: complete the [repo-root quick-start
setup](../README.md) with the `parser` and `pdf` extras
(`pip install -e ".[docx,parser,yaml,schema,pdf]"`), then run the scripts
from this directory:

```bash
cd project-2-profile-learning-hub
python3 parse_pluralsight_html.py
python3 pdf-template.py roles/<role-slug>.json
```

Verify the install:

```bash
python3 -c "import bs4, lxml, orjson, reportlab, docx; print('deps OK')"
```

Staged/generated output goes to `outputs/` at the repo root (gitignored) —
drop a Pluralsight HTML export in `outputs/uploads/` before running the
parser. `pdf-template.py` is data-driven: copy `roles/_example.json` as a
starting point for a new role config.

## Contents

- `profile-facts.md` — cert status, key differentiators, portfolio impact on known gaps, resolved vs. genuine skill gaps. Load in Step 2 of gap analysis.
- `skills-summary.md` — resume-ready skills by category, AI-200 domain coverage, Pluralsight course summary by category, recent highlights.
- `pluralsight-courses.md` — full Pluralsight course list, rebuilt entirely from `data/pluralsight_learning_history.json` as sole source of truth. See `skills-summary.md` header for current totals — don't hardcode a count here, it goes stale immediately.
- `data/pluralsight_learning_history.json` — raw exported Pluralsight learning history (course name, URL, progress, duration, completion date, summary). Authoritative source for course rebuilds.
- `data/ms-learn-courses.md` — completed Microsoft Learn training (75 modules, 11 learning paths, 55h 49m).
- `course-urls.md` — verified, live Pluralsight course URLs organized by skill gap (Full-Stack .NET, Azure/AI-200, Kubernetes). Load in Step 3 before recommending any course.
- `github-repos.md` — portfolio repo details (PortfolioSite, job-app-copilot, shell-ops-toolkit, RecipeBox; OldApp tracked but commented out) with evidence-tier ratings for gap analysis.
- `Resume_Snapshot.md` — current resume content and contact info, including a "Key Differentiators" section with an "AI-Assisted Development / Claude Code" subsection covering skills demonstrated through building and maintaining this project's own Claude Code Skill system.

## Current Status

Check `skills-summary.md`'s header line for current course/lab totals and last-sync date — this README intentionally doesn't restate the number, since it goes stale the moment a new course is logged (see Notes below for the exact failure mode this caused). AZ-900 certified April 18, 2026; AI-200 (Azure AI Cloud Developer Associate) is the active certification target.

## Bundle generation

`skills/profile-hub-bundle-generator_SKILL.md` compiles `app-engine-bundle.md` (Project 1) and `presence-bundle.md` (Project 3) from the four files above, gated behind 6 consistency checks. It also computes a `## Copy Fragments` block (pre-formatted sentences like course counts and cert status) written into both bundles, so downstream skills that write ready-to-paste platform copy can reference a fragment field instead of hand-embedding a number that drifts out of sync.

## Notes

- `pluralsight-courses.md` and `skills-summary.md` are rebuilt from `data/pluralsight_learning_history.json` as the sole source of truth.
- MS Learn and Pluralsight overlap on GitHub Copilot and C#; Azure coverage in `data/ms-learn-courses.md` is conceptual (AZ-900 path) while hands-on Azure labs live in `pluralsight-courses.md` — don't double-count.
- An Aug 2026 audit found several downstream skill/reference files (in Project 1 and 3) had hardcoded course counts and cert-status wording that drifted out of sync with this project's data over several bundle regenerations — e.g. Project 3's LinkedIn/GitHub skills still described AZ-900 as "in progress" long after it was certified. Fixed at the source, and the Copy Fragments mechanism above exists to prevent a repeat.
- Downstream bundle files (`app-engine-bundle.md` in Project 1, `presence-bundle.md` in Project 3) are generated from this project's data via "generate bundles."

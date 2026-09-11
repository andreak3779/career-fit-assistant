# Project 2 — Profile & Learning Hub

## Local setup (Claude Code)

This project's origin is claude.ai Projects, which provided a sandboxed environment with preinstalled packages and fixed paths (`/mnt/user-data/outputs/`, `/home/claude/`). In Claude Code, create a virtualenv and install dependencies from the repo root — this system's Python is externally-managed, so a global `pip install` will be refused. There is no separate `requirements.txt` for this project; it uses the monorepo's `pyproject.toml` extras like everything else, to avoid a second dependency list drifting out of sync with the real one (the same failure mode this project's own `check_skill_hardcoding.py` guards against for skill content):

- macOS/Linux: `python3 -m venv .venv && .venv/bin/pip install -e ".[parser,pdf]"`
- Windows: `python -m venv .venv && .venv\Scripts\pip.exe install -e ".[parser,pdf]"`

`parser` (`beautifulsoup4`, `lxml`) covers `parse_pluralsight_html.py`; `pdf` (`reportlab`) covers `pdf-template.py`. If you're also running `build`/`validate`/the bundle generator from here, add `docx,yaml,schema` too: `pip install -e ".[parser,pdf,docx,yaml,schema]"`. Staged/generated output goes to `outputs/` at the repo root (gitignored): drop a Pluralsight HTML export in `outputs/uploads/` before running the parser.

`pdf-template.py` is a **data-driven engine** — it reads a role config from `roles/[role-slug].json` and renders the PDF. To generate a learning plan, write a JSON config (copy `roles/_example.json` as a starting point) and run `python pdf-template.py roles/[role-slug].json`. The old per-role Python snapshot workflow has been retired; the migration helper has been removed now that all active roles are in JSON.

## Purpose

Source-of-truth project for Sarah Ashford's career facts, skills, and learning history. Project 1 (Application Engine) and Project 3 (Presence & Identity) consume generated bundles from here — they never re-derive facts themselves.

## Source of truth

This project is authoritative. Edits flow **out** of here via bundles; nothing should be edited here to match Project 1/3 content. If a downstream bundle looks wrong, fix the source file here, then regenerate — don't patch the bundle directly.

Canonical chain for course data specifically:
`data/pluralsight_learning_history.json` (raw export, authoritative) → `pluralsight-courses.md` and `skills-summary.md` (rebuilt from it). Never hand-edit the two derived files directly — re-run the rebuild from JSON.

## Folder / file responsibilities

| File | Role |
|---|---|
| `profile-facts.md` | Cert status, differentiators, known gaps, resolved framing gaps |
| `Resume_Snapshot.md` | Resume baseline, all sections. Contains real contact info (email, phone) and is **intentionally tracked in git** — this is the canonical source-of-truth resume, versioned here on purpose (repo is private). Not a PII leak; don't untrack it. `## Professional Experience` entries, including "Professional Development & Portfolio Building," must stay in strict reverse-chronological order by start date — an entry with an open-ended "Present" end date is the most recent and belongs at the top, not appended after older entries. |
| `skills-summary.md` | Resume-ready skills, AI-200 domain coverage, course summary |
| `pluralsight-courses.md` | Full course list — rebuilt from JSON only |
| `data/pluralsight_learning_history.json` | Raw Pluralsight export — authoritative source for course rebuilds |
| `data/ms-learn-courses.md` | Completed MS Learn training |
| `course-urls.md` | Verified course URLs by skill gap |
| `github-repos.md` | Portfolio repo details with evidence-tier ratings |
| `skills/` | `*_SKILL.md` files — one workflow each |

## Bundle generation trigger

Skill: `skills/profile-hub-bundle-generator_SKILL.md`. Lives in Project 2 only — never copy to P1/P3.

**Run it whenever the user says:** "generate bundles", "update bundles", "sync profiles", "publish bundles", "run the bundle generator".

**Also run it proactively after any of these edits** (per the sync protocol in that skill):

| Event | Regenerate | Which bundle |
|---|---|---|
| Certification earned | Always | Both |
| Gap status changes in `profile-facts.md` | Yes | `app-engine-bundle` |
| Resume section edited | Yes | `app-engine-bundle` (+ presence if bio-relevant) |
| Portfolio project added/updated in `github-repos.md` | Yes | Both |
| Pluralsight course closes a known gap | Yes | `app-engine-bundle` |
| Course count update only, no gap change | No | — |

The skill runs 6 sequential consistency checks (cert sync, AI-200 wording sync, gap closure, differentiator coverage, course count regression, badge URL format) before writing anything, and blocks on any failure — do not bypass this gate or hand-write bundle content to work around a failed check.

Before writing either bundle, Step 2.5 computes a `## Copy Fragments` block (`course_count_sentence`, `cert_status_short`, `azure_course_lab_sentence`, `github_copilot_course_count`, `leadership_course_count`) from the same source files, recomputed fresh every run — never carried forward from the prior version. This exists so P1/P3 skills that write ready-to-paste platform copy (LinkedIn About, resume bullet options, etc.) reference a fragment field instead of hand-embedding a number that goes stale.

Output: `app-engine-bundle.md` and `presence-bundle.md` to `outputs/`, for manual reimport into Project 1 and Project 3 respectively. `presence-bundle.md` is GitHub-safe (no PII) and gets committed to `claude-projects` (under `project-3-presence-identity/presence-bundle.md`); `app-engine-bundle.md` contains contact info and must never be committed to GitHub — it's gitignored in Project 1, and the same rule applies here: never `git add` a local copy of it in this project either.

## Guardrail — hardcoded facts in skill files

Skills across all three projects sometimes state a cert status, GitHub Copilot
course count, leadership course count, or Azure Functions course count as literal
prose instead of a `{fragment_name}` placeholder or a "derive this at generation
time" instruction — and it silently goes stale as `profile-facts.md` /
`pluralsight-courses.md` change underneath it. This has happened more than once
(see Project 1's CLAUDE.md "Known limitations" for the history), so don't rely on
memory or a one-time audit to catch it again.

Run `python project-2-profile-learning-hub/scripts/check_skill_hardcoding.py` from
the repo root after editing any `SKILL.md` — it re-derives the current truth from
`profile-facts.md` and `pluralsight-courses.md` and flags any skill text that no
longer matches. It's a heuristic prose scanner, not a bundle-validation gate like
the 6-check gate below: false positives are possible (e.g. a deliberately-preserved
historical date, or a "once AI-200 is passed" conditional callout), so read each
finding rather than trusting the exit code blindly. Exit code 0 means clean.

## Data pipeline scripts

`parse_pluralsight_html.py` and `pdf-template.py` are personal utility scripts, not wired into the GitHub Actions workflow (it covers `.js` templates and PII, not Python) — but both have pytest coverage (`tests/test_parse_pluralsight_html.py`, `tests/test_pdf_template.py`) that runs locally via `python -m pytest`. `parse_pluralsight_html.py` hardcodes its I/O paths (`JSON_FILE`, `MD_FILE`, `OUTPUT_JSON`) relative to its own `SCRIPT_DIR` rather than taking a repo-root argument, so its tests monkeypatch those module attributes to a tmp dir before calling `main()` — never call `main()` in a test without doing that, or it will read/write the real personal learning-history data. Any change to `parse_pluralsight_html.py`'s output shape should still be manually spot-checked against `pluralsight-courses.md` before running "generate bundles," since the bundle generator's consistency checks validate cross-file facts, not the JSON→markdown rebuild itself.

`scripts/query_learning_history.py` (`lookup` / `list` / `missing-summary` subcommands) exists specifically so skills never instruct "load `data/pluralsight_learning_history.json`" — the raw file is ~298 entries / ~44K tokens, dominated by the `summary` and `url` fields most lookups don't need. `pluralsight-updater`, `pluralsight-summary-enricher`, and `learning-plan-gap-analysis` all route their JSON access through it. If a future skill needs course/lab data from this file, add a subcommand here rather than telling Claude to read the file directly — that's the guardrail this script exists to enforce. It takes `--root` for testability (see `tests/test_query_learning_history.py`); tests must point it at a fixture, never the real file.

## Roles config schema

`pdf-template.py` accepts JSON configs with this shape (see `roles/_example.json` for the canonical template):

| Key | Type | Notes |
|---|---|---|
| `output` | string path | Where to write the PDF (parent dirs created automatically) |
| `banner` | object with `title`, `subtitle`, `meta` | Three-line page header |
| `urgency_text` | string or `null` | Optional red banner; omit if no cert deadline |
| `about_text` | string | Free-form intro paragraph |
| `legend` | array of `{label, color}` | Optional priority colour guide |
| `plan` | array of entries | Mixed `head` (section divider) and `course` (card) |
| `key_links` | array of `{label, url}` | Optional, rendered on the last page |
| `footer` | string | One-line footer |

Allowed colors: `NAVY`, `RED`, `AMBER`, `GREEN`, `PURP`, `BLUE`, `LGRAY`, `MGRAY`, `WHITE` (whitelisted by the engine — anything else is rejected at runtime).

## Notes

- MS Learn and Pluralsight overlap on GitHub Copilot/C#; MS Learn Azure coverage is conceptual (AZ-900 path) while hands-on Azure labs live in Pluralsight — don't double-count when writing skills content.
- Log provenance changes (e.g. dropped legacy entries, rebuild dates) in the project README, not silently.

## Known limitations

- The 6 consistency checks in the bundle generator and the reimport step are manual/prompt-driven — there's no script that verifies bundle *content* is correct beyond those 6 checks. Bundle *freshness* (has a P2 source changed since the bundle was last written?) is checked by `scripts/check_bundle_freshness.py`, wired into the local pre-commit hook — it compares each bundle file's own mtime against `profile-facts.md`/`Resume_Snapshot.md`/`skills-summary.md`/`github-repos.md`'s mtimes and flags any source newer than the bundle. It's mtime-based (stable across a fresh clone, since checkout stamps everything with the same moment) but only catches "a source changed," not "the bundle content is wrong" — still treat `bundle_version`/`generated` as something to spot-check, not a full guarantee.

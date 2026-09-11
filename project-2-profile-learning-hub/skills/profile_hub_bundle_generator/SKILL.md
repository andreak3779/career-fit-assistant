---
name: profile-hub-bundle-generator
description: >
  Compiles the two downstream bundles (app-engine-bundle.md and
  presence-bundle.md) from the four canonical source files in Project 2, by
  running the build/validate/render script pipeline — not by hand-authoring
  markdown. Runs 6 sequential consistency checks before generating any
  output; stops with a failure report if any check fails.
  Use whenever the user says "generate bundles", "update bundles",
  "sync profiles", "publish bundles", or "run the bundle generator".
  Also trigger after any cert status change, gap status change, Resume_Snapshot
  edit, or new portfolio project — per the sync protocol in v3 architecture.
  Lives in: Project 2 — Profile & Learning Hub only.
  Output: two .md files written to their canonical locations + completion summary.
---

# Profile Hub Bundle Generator

Compiles `app-engine-bundle.md` and `presence-bundle.md` from the four
canonical P2 source files, via three scripts run in sequence — **not** by
reading the source files yourself and hand-writing the bundles. The scripts
compute facts and consistency-check them in code; that's strictly less
error-prone (and cheaper) than re-deriving the same logic from prose on every
run, which is how this skill worked before and how it twice drifted out of
sync with its own source data.

`app-engine-bundle.md` → `project-1-application-engine/` (gitignored — contains PII)
`presence-bundle.md`   → `project-3-presence-identity/` (committed — GitHub-safe)

> **Architecture reference:** Job Search AI System — Architecture v3: Sequential Bundle Model
> **Skill location:** Project 2 — Profile & Learning Hub (never move to P1 or P3)
> **PII rule:** `app-engine-bundle.md` may contain contact info. `presence-bundle.md` must NOT contain phone or email — it is GitHub-safe.

---

## Inputs (read by the scripts — you don't need to load these yourself)

| File | Role |
|---|---|
| `profile-facts.md` | Cert status (YAML frontmatter) · differentiators · known gaps · resolved framing gaps |
| `Resume_Snapshot.md` | Resume baseline — all sections |
| `skills-summary.md` | Course counts · Key Skills · AI-200 domain coverage |
| `github-repos.md` | Portfolio project details · evidence tiers · repo URLs |

If any of these four files is missing or unreadable, the first script fails with a clear error — surface that to Sarah rather than trying to work around it.

---

## Step 1 — Run the pipeline

From the repo root, run these three scripts **in order**. Each one gates the next — do not skip a step or run them out of order.

```bash
python project-2-profile-learning-hub/skills/profile_hub_bundle_generator/scripts/build_bundles.py .
python project-2-profile-learning-hub/scripts/validate.py .
python project-2-profile-learning-hub/skills/profile_hub_bundle_generator/scripts/render_md_bundles.py .
```

1. **`build_bundles.py`** — parses the four source files and writes typed, schema-validated `outputs/profile-bundle.json` and `outputs/presence-bundle.json`. This is the single computed source of truth; both .md bundles are rendered from it, so they can no longer drift apart.
2. **`validate.py`** — runs the 6 consistency checks (below) against the JSON it just wrote. **If it exits non-zero, stop here** — print its output verbatim, do not proceed to step 3, and tell Sarah which check(s) failed and what to fix in which source file.
3. **`render_md_bundles.py`** — reads the validated JSON and deterministically writes `app-engine-bundle.md` and `presence-bundle.md` to their canonical locations, including the `## Copy Fragments` block both files share (`course_count_sentence`, `cert_status_short`, `azure_course_lab_sentence`, `github_copilot_course_count`, `leadership_course_count`) and a single shared `bundle_version` (the JSON bundle's version) — the two .md files can never end up on different version numbers.

### The 6 consistency checks (enforced by `validate.py`, not prose)

| # | Check | Rule |
|---|---|---|
| 1 | Cert sync | Bundle's cert registry matches `profile-facts.md`'s YAML `certs:` list exactly |
| 2 | AI-200 sync | AI-200 status is `in_progress` and its Azure course count is consistent with `skills-summary.md` |
| 3 | Gap closure | Every known genuine gap has at least course/portfolio evidence |
| 4 | Differentiator coverage | Expected differentiator signals (full-stack, legacy, SQL Server, TDD, GitHub Copilot, prompt engineering, AI/LLM, communication, pace of learning) are all present |
| 5 | Course count regression | Total course count didn't drop compared to the differentiators bullet's own internal arithmetic |
| 6 | Badge URL format | AZ-900 credential URL matches the expected `learn.microsoft.com/.../sharingId=...` shape |

If you need to see *why* a check failed in more detail than the script's stdout gives, read `scripts/validate.py` — each check function has a docstring explaining its rule.

---

## Step 2 — Guardrail: check for hardcoded facts in skills

If any cert status changed in this run (e.g. a cert moved from `in_progress` to `certified`), also run:

```bash
python project-2-profile-learning-hub/scripts/check_skill_hardcoding.py .
```

This scans every project's `SKILL.md` files for cert-status claims and course counts that now contradict the refreshed source data — catching skills that hardcoded a value instead of using a `{fragment_name}` placeholder. See Project 2's CLAUDE.md for details. It's a heuristic prose scanner: read each finding rather than trusting the exit code blindly.

---

## Step 3 — Print Completion Summary

Report the actual output of the three scripts — don't invent a summary. At minimum surface:

- The `bundle_version` both files now share (from `render_md_bundles.py`'s stdout)
- `validate.py`'s pass/fail line for each of the 6 checks
- The two file paths written, and that `presence-bundle.md` needs to be committed to GitHub (`app-engine-bundle.md` does not — it's gitignored, contains PII)
- Whether `check_skill_hardcoding.py` found anything (if you ran it)

---

## Sync Protocol — When to Regenerate Bundles

| Event | Regenerate? | Which bundle |
|---|---|---|
| Pluralsight course closes a known gap | Yes | `app-engine-bundle` |
| Certification earned | Yes — always | Both |
| Resume section edited | Yes | `app-engine-bundle` (+ presence if bio-relevant) |
| Gap status changes in `profile-facts` | Yes | `app-engine-bundle` |
| Portfolio project added or updated | Yes | Both |
| Course count update only (no gap changes) | No | — |

Even when the table above says "only regenerate one bundle," running the full 3-script pipeline is still correct and cheap — it always (re)writes both files from the same JSON, which is what keeps their `bundle_version` numbers from skewing apart. There's no partial-pipeline mode; don't try to hand-edit just one of the two .md files to avoid re-running the other.

---

## Distribution Model

`presence-bundle.md` is **local-only** and stays inside this workspace's git repo (`claude-projects`). It is **not** published to a public URL.

The repo (`andreak3779/claude-projects`) is private, so `raw.githubusercontent.com` returns 404 for anonymous skill fetchers. Project 3 skills therefore read the local `project-3-presence-identity/presence-bundle.md` file directly — no fetch step, no drift between local and remote.

```
Location: project-3-presence-identity/presence-bundle.md
Consumer: Project 3 skills (update-linkedin-profile, update-github-profile)
Mode:     local file read, no network fetch
```

> `app-engine-bundle.md` must NOT be committed to a public repo (contains PII). The `claude-projects` repo is private so the .gitignore exclusion is belt-and-suspenders, not strictly required for that case.

---

## Error Reference

| Error condition | Action |
|---|---|
| Source file missing | `build_bundles.py` exits non-zero — report which file is missing |
| Any of the 6 validation checks fails | `validate.py` exits non-zero — report all failures verbatim; do not run `render_md_bundles.py` |
| `render_md_bundles.py` run without a fresh JSON bundle | It reads whatever is currently in `outputs/*.json` — always run `build_bundles.py` (and let `validate.py` gate) immediately before it in the same session |
| Course count lower than prior bundle | Flagged by Check 5; blocks the gate |
| Badge URL missing `sharingId` param | Flagged by Check 6; blocks the gate |

---

## Editing what the bundles contain

Don't hand-edit `app-engine-bundle.md` or `presence-bundle.md` — they're overwritten on every run. To change what they contain:

- A **fact** (cert status, a differentiator, a gap) → edit `profile-facts.md`, `Resume_Snapshot.md`, `skills-summary.md`, or `github-repos.md`, then re-run the pipeline.
- The **rendering** (section order, table format, which fields appear) → edit `scripts/render_md_bundles.py`.
- A **Copy Fragment**'s wording or source → edit `compute_copy_fragments()` in `scripts/render_md_bundles.py`.
- A **consistency rule** → edit the corresponding `check_*` function in `project-2-profile-learning-hub/scripts/validate.py`.

---

## Notes

- This skill lives in **Project 2 only**. Do not copy to P1 or P3.
- `bundle_version` is computed by `build_bundles.py` (increments from the prior `outputs/profile-bundle.json`, or starts at 1) and shared by both .md files — there is no separate manual version-tracking step.
- `presence-bundle.md` and `GapAnalysis_Bridge.md` are GitHub-safe. `app-engine-bundle.md` is not.
- The old workflow (Claude reading the 4 source files and hand-writing ~300 lines of bundle markdown from a template in this file) is retired. If you find yourself about to write bundle content by hand instead of running the scripts, stop — that's the failure mode this rewrite exists to prevent.

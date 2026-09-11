---
name: pluralsight-summary-enricher
description: >
  Adds/updates a "summary" property on entries in data/pluralsight_learning_history.json,
  giving each Pluralsight course or lab a short, paraphrased description of what it
  covers. Also flags (advisory only) when a summary reveals a course may be
  miscategorized in pluralsight-courses.md's section headings — it never moves
  entries itself. Runs automatically as the final step of the pluralsight-updater
  skill, processing only the entries that were just added or changed in that
  session. Can also be triggered manually with phrases like "add summaries to my
  Pluralsight history", "backfill course summaries", "update the JSON summaries",
  or "generate descriptions for my Pluralsight courses/labs". Do NOT use this
  skill to add descriptions to pluralsight-courses.md — that file stays
  title-only by design; this skill only ever writes to
  data/pluralsight_learning_history.json.
---

# Pluralsight Summary Enricher

Adds a `"summary"` field to each entry in `data/pluralsight_learning_history.json` —
a short, original-wording description of what the course or lab covers. This is
metadata for the candidate's own reference (e.g. quick-scanning their history, powering
future gap-analysis prompts); it is never surfaced verbatim on the resume or in
job-facing documents.

> **File to update:** `data/pluralsight_learning_history.json`
> **Lookup method:** `web_search` only (site-scoped) — never `web_fetch` the course URL directly
> **Runs after:** `pluralsight-updater` (Workflows A, B, and C all end by handing off here)
> **Never edits:** `pluralsight-courses.md` — this skill may *flag* a possible section miscategorization (Step 5) but the actual row move is always made by `pluralsight-updater`, never here
> **Never triggers:** `profile-hub-bundle-generator`, `skills-summary.md` edits, or `Resume_Snapshot.md` edits — those remain separate workflows the user must invoke explicitly

---

## When This Runs

1. **Automatic (default):** Immediately after `pluralsight-updater` finishes writing
   `pluralsight-courses.md` in any workflow, call this skill with the list of
   entries that were newly added or edited in that same session. Only those
   entries get summarized — this is an incremental, not a full, pass.
2. **Manual backfill:** When the user explicitly asks to backfill or regenerate
   summaries (e.g. "add summaries to everything," "backfill the JSON"), process
   **all** entries in `data/pluralsight_learning_history.json` that are missing a
   `summary` field, using the batching approach in Step 3 below.
3. **Manual single-entry fix:** If the user flags one course/lab's summary as
   wrong, regenerate just that entry.

---

## Step 1 — Build the Work List

**Never load the raw `data/pluralsight_learning_history.json` (~44K tokens) directly.**

1. Build the work list:
   - Incremental run → the entry list `pluralsight-updater` already passed for this session — no file access needed, it's already in context
   - Backfill run → `python project-2-profile-learning-hub/scripts/query_learning_history.py missing-summary` — returns just the name/type/url of entries still missing a summary, not the whole file
2. Report the count to the user before doing any lookups (e.g. "6 new entries need summaries" or "235 of 241 entries are missing summaries — this will take several batches").

---

## Step 2 — Look Up Each Course/Lab

For each entry in the work list:

1. Run `web_search` scoped to the source site — e.g. `site:pluralsight.com "[course/lab name]"` (use `site:app.pluralsight.com` for hands-on labs, since lab pages live there, not on the marketing site).
2. Read the top result(s) to understand what the course/lab actually covers.
3. Write a **1–2 sentence summary in the candidate's own words** — never copy course-page marketing copy verbatim, never quote more than a short phrase, and never lift the page's exact sentence structure. State what skill/tool/concept the course teaches and at what level (e.g. "Introduces Azure Service Bus messaging patterns, covering queues, topics, and dead-lettering for building decoupled .NET services.").
4. If search returns nothing usable (dead slug, no indexed description, generic/ambiguous title):
   - Fall back to a summary inferred from the course **title + type (Course/Lab) + adjacent entries in the same technology area**
   - Prefix these with `[inferred]` in an internal note (not stored in the JSON) so they can be flagged to Sarah Ashford in the diff for confirmation
5. Never fabricate specific technical claims (specific API names, version numbers, tool features) that aren't backed by the search result or a confident inference from the title — if unsure, keep the summary generic rather than specific.

---

## Step 3 — Batch Processing (Backfill Runs Only)

Full backfills (200+ entries) are processed in checkpointed batches so no progress is lost:

1. Process in batches of ~25 entries.
2. After each batch, write just that batch's `{name: summary}` pairs to a small temp JSON file (e.g. `outputs/tmp/batch-summaries.json`) — never re-emit the full 298-entry file. Merge it in with `python project-2-profile-learning-hub/scripts/update_learning_history.py apply --summaries-file outputs/tmp/batch-summaries.json`, which writes directly to `data/pluralsight_learning_history.json` (see Step 4 for the dry-run-first sequence).
3. Report progress after each batch (e.g. "Batch 3 of 10 done — 75/241 summarized").
4. If the session is interrupted, the next run picks up wherever `summary` fields are still missing — no need to restart from zero. Because each batch is merged into `data/pluralsight_learning_history.json` immediately (not staged elsewhere), `scripts/query_learning_history.py missing-summary` always reflects true remaining progress.
5. Collect all `[inferred]` low-confidence entries into a single list and show them to Sarah Ashford at the end for a quick confirm/correct pass, rather than interrupting per-entry.

---

## Step 4 — Diff-First Write

Before merging each batch:

1. Run `python project-2-profile-learning-hub/scripts/update_learning_history.py apply --summaries-file <batch.json> --dry-run` and show the user its printed diff (old→new summary per matched entry) — this is the sample diff, no need to also hand-copy entries into the chat.
2. Explicitly call out the count of `[inferred]` (low-confidence) summaries and list those titles separately for review.
3. On approval, re-run the same command without `--dry-run` to commit the batch. The script preserves every existing field and key order, adding/overwriting only the `summary` key on each matched entry:

```json
{
  "name": "Advanced Claude Code",
  "type": "Course",
  "url": "https://app.pluralsight.com/library/courses/advanced-claude-code",
  "view_time": "1h 52m",
  "progress": "1h 27m",
  "duration": "1h 27m",
  "completion_percentage": "100.0%",
  "completed_date": "Jul 04, 2026",
  "timing_profile": "Full Course",
  "summary": "Covers advanced techniques for using Claude Code as an agentic coding assistant, including custom workflows and complex multi-step tasks."
}
```

4. Never hand-write the JSON file yourself — always go through `update_learning_history.py`, which never removes or reorders existing keys. Never touch `pluralsight-courses.md` — that file has no description column by design and this skill does not add one.

---

## Step 5 — Section Consistency Check (Advisory Only)

After a summary is written for an entry, compare what the summary reveals about
the course's actual topic against the section it currently sits in on
`pluralsight-courses.md`, using the same keyword table `pluralsight-updater`
uses (Section Mapping). This catches cases where the title alone was too vague
or generic for accurate keyword matching, but the summary makes the real topic
clear.

1. Run this check only for entries that just received a new or changed summary
   in this session — not a full re-scan of all 241 entries on every run.
2. If the summary strongly implies a **different** section than the one the
   course currently lives in, add it to a **Possible Miscategorization** list —
   don't move it, don't edit `pluralsight-courses.md`, don't ask per-entry.
3. Skip this check for entries that are genuinely cross-cutting (e.g. an
   "Azure Kubernetes Service" course reasonably lives under either ☁️ Azure or
   🔁 Docker & Kubernetes) — only flag clear mismatches, not defensible
   judgment calls.
4. At the end of the run, present the Possible Miscategorization list (if any)
   alongside the normal diff in Step 4 — course name, current section, summary-
   implied section, one-line reason. Sarah Ashford approves or rejects each one.
5. Any approved move is then made by `pluralsight-updater`, not this skill —
   hand the approved list back so the section header counts and Summary table
   in `pluralsight-courses.md` get updated correctly in one place.

---

## Copyright Guardrails (non-negotiable)

- Summaries are **paraphrases only** — never copy sentences or distinctive phrasing from the course page or search snippet.
- No quotation marks reproducing source text.
- Keep each summary short (roughly 15–35 words) — long enough to be useful, short enough that it can't function as a displacive substitute for the course description.
- One summary per entry, generated fresh per course — don't template multiple summaries off a single search result across unrelated entries.

---

## Companion Files

- `data/pluralsight_learning_history.json` — the file this skill maintains ✅; find the backfill work list via `scripts/query_learning_history.py missing-summary` (see Step 1) rather than loading the raw file — the Step 4 write goes through `scripts/update_learning_history.py`, which merges each batch server-side, so this skill never needs to hold or re-emit the full file either
- `pluralsight-courses.md` — read-only context for the Step 5 consistency check; never edited by this skill
- `pluralsight-updater` skill — upstream trigger; hands off the "just changed" entry list here after each run, and is the only skill that acts on any Possible Miscategorization flags this skill raises

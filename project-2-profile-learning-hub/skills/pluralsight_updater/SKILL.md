---
name: pluralsight-updater
description: >
  Updates pluralsight-courses.md when the candidate completes new Pluralsight courses
  or labs. Trigger whenever the user says "I finished a Pluralsight course",
  "I completed a new course", "add this to my Pluralsight file", "I just finished
  [course name]", "update my Pluralsight courses", or pastes/uploads a new course
  list or completion screenshot. Also trigger when the user mentions any new
  Pluralsight course title, path completion, or lab completion — even casually,
  e.g. "I just did the Redis course on Pluralsight." Always use this skill for
  Pluralsight updates — do not handle them ad hoc. Do NOT use for Microsoft Learn
  updates — those go through the ms-learn-updater skill. After writing
  pluralsight-courses.md, this skill always hands off the newly added/changed
  entries to the pluralsight-summary-enricher skill so data/pluralsight_learning_history.json
  gets a paraphrased "summary" property for each — this handoff is automatic and
  does not need a separate user request.
---

# Pluralsight Course Updater

Keeps `pluralsight-courses.md` current as the candidate completes new Pluralsight courses
and labs. Also flags when completions warrant updates to `skills-summary.md` or
`Resume_Snapshot.md`.

> **File to update:** `pluralsight-courses.md`
> **Duration source:** `data/pluralsight_learning_history.json`, ~44K tokens raw — **never load it directly.** Run `python project-2-profile-learning-hub/scripts/query_learning_history.py lookup "<title>"` (accepts multiple titles in one call) to get `duration` and `timing_profile` for the course(s) being added.
> **HTML export uploads:** Never `Read` a Pluralsight HTML export or paste its contents into context — a large export can overflow the prompt. Run `python project-2-profile-learning-hub/parse_pluralsight_html.py <path-to-export.html>` via Bash instead. It validates the export's structure, diffs it against `data/pluralsight_learning_history.json`, prints the new entries (title, type, url, duration, completion date, timing_profile — already computed) and any in-progress→completed transitions, and writes the merged result to `outputs/pluralsight_learning_history.json`. See Workflow B step 1 for how this fits into the write sequence — copying that staged output over `data/pluralsight_learning_history.json` is what actually makes new entries authoritative (the enricher only ever adds `summary` to entries already present).
> **Check for downstream impact:** `skills-summary.md` · `Resume_Snapshot.md`
> **Cross-reference:** `data/ms-learn-courses.md` — avoid double-counting overlapping topics
> **Always hand off after writing:** `pluralsight-summary-enricher` — pass it the list of entries just added/changed so it can populate the `summary` property on the matching records in `data/pluralsight_learning_history.json`. This is a separate file and a separate write; do not add descriptions to `pluralsight-courses.md` itself (see Formatting Rules — titles only).

---

## Workflow A — User Mentions a Single Completion

When the user says "I just finished [course name]":

1. Confirm: course title · completion date (default to today if not stated) · whether it was a lab or a course
2. Run `python project-2-profile-learning-hub/scripts/query_learning_history.py lookup "[course title]"` to get `duration` and `timing_profile`
   - If found and `timing_profile` is `Full Course` or `Full Lab`: use the `duration` field value
   - If found and `timing_profile` is `Short Course` or `Lab`: duration is `—`
   - If NOT FOUND: `web_search site:pluralsight.com "[course title]"` to find the actual duration from the course page
3. Identify the correct section using the mapping below
4. Run `python project-2-profile-learning-hub/scripts/merge_pluralsight_course.py add --title "..." [--url "..."] --type Course|Lab --section "<exact ### heading text>" --completed-date "Mon DD, YYYY" --duration "..." --timing-profile "..." --note "<one-line changelog sentence>" --dry-run` — never hand-write the row/counts/Summary-table/Last-updated changes yourself; the script owns all of that (chronological placement within the section, section + Completed-Courses heading counts, Status/Totals lines, Summary table). `--section` must match an existing `### <emoji> <name>` heading exactly; the script errors with the valid list if it doesn't.
5. Show the user the dry-run's printed diff (this **is** "the exact change" — no separate hand-built preview needed)
6. Check downstream impact (see Step 3 below)
7. After confirmation, re-run the same command without `--dry-run` — it writes directly to `pluralsight-courses.md` (with an automatic `.bak` snapshot first), no separate `outputs/` staging or promote step
8. Hand off this entry to `pluralsight-summary-enricher` to populate its `summary` field in `data/pluralsight_learning_history.json`

---

## Workflow B — User Pastes a Course List or Multiple Completions

When the user provides a list of new courses (pasted text, screenshot description, or uploaded file):

1. Extract each new course's title and completion date:
   - **If an `.html` export was uploaded:** run `python project-2-profile-learning-hub/parse_pluralsight_html.py <path-to-export.html>` via Bash (see the HTML export callout above) — do not `Read` the file or paste its contents into context. Its "NEW ENTRIES" console output already gives you title, completion date, duration, and timing_profile for every new entry — skip step 2 below for these.
   - **If the user pasted/typed a plain list instead (no file):** extract each course title and completion date by hand. If dates are missing, ask — or accept "approximate" and note it.
2. For a pasted/typed list only, run `python project-2-profile-learning-hub/scripts/query_learning_history.py lookup "<title1>" "<title2>" ...` — pass every new title in one call to get `duration` and `timing_profile` for each:
   - `Full Course` / `Full Lab` → use `duration` directly
   - `Short Course` / `Lab` → duration is `—`
   - NOT FOUND → note for web_search before writing
3. Identify which entries are NOT already in `pluralsight-courses.md`
4. Group new entries by section using the mapping below
5. If Workflow came from an HTML export, copy the parser's `outputs/pluralsight_learning_history.json` over `data/pluralsight_learning_history.json` — this merges the new entries' full data (url, duration, timing_profile, etc.) into the authoritative source. For a pasted/typed list, no JSON base-field merge is needed here (only the `summary` field, added later by the enricher, requires the entry to already exist in the JSON — flag to the user if a pasted-list entry has no HTML export to back it and won't appear in the JSON until one is provided).
6. Write each new entry (`title`, optional `url`, `type`, `section`, `completed_date`, `duration`, `timing_profile`) to a small JSON array file (e.g. `outputs/tmp/new-courses.json`), then run `python project-2-profile-learning-hub/scripts/merge_pluralsight_course.py add-batch --entries-file outputs/tmp/new-courses.json --note "<one-line changelog sentence covering the whole batch>" --dry-run` — never hand-write the rows/counts/Summary-table/Last-updated changes yourself; the script handles every entry's chronological placement, section/Completed-Courses heading counts, Status/Totals lines, and the Summary table in one pass.
7. Show the user the dry-run's printed diff (this **is** the "present a diff" step — no separate hand-built preview needed)
8. Check downstream impact (see Step 3 below)
9. After confirmation, re-run the same command without `--dry-run` — it writes directly to `pluralsight-courses.md` (with an automatic `.bak` snapshot first), no separate `outputs/` staging or promote step
10. Hand off the full list of newly added entries to `pluralsight-summary-enricher` to populate their `summary` fields in `data/pluralsight_learning_history.json`

---

## Workflow C — Full Sync / Audit

When the user wants to verify the file is complete or sync from a full course list:

0. If Sarah Ashford provides a fresh `.html` export for this audit (rather than just asking to check the existing file), run it through the HTML-upload step in Workflow B step 1 first — that merges any new entries into `data/pluralsight_learning_history.json` before the listing below is taken as authoritative.
1. Run `python project-2-profile-learning-hub/scripts/query_learning_history.py list` — a lean listing (name, type, duration, timing_profile, completed_date; no summary/url) of all 298 completed courses/labs, the authoritative source for `duration` and `timing_profile`; no web lookup needed for any course already listed
2. Compare against `pluralsight-courses.md` — identify any courses present in the file but NOT in the provided list (flag, do not auto-delete), and any new completions to add
3. Follow Workflow B for additions (including its summary-enricher handoff in step 10)
4. Flag discrepancies to the user for manual review
5. If the user separately requests a full backfill of `summary` fields for all existing history (not just this sync's additions), that's a manual invocation of `pluralsight-summary-enricher` — see that skill's backfill mode

---

## Section Mapping

Assign new courses to sections using these rules (first match wins):

| Keywords in course title | Section |
|---|---|
| Azure, AZ-900, AI-200, serverless, Azure Functions, Entra, Cosmos DB, change feed | ☁️ Microsoft Azure |
| ASP.NET, .NET Core, EF Core, Blazor, .NET (number), C# | 🔷 ASP.NET Core & .NET |
| Angular, RxJS, Signals | 🅰️ Angular |
| Copilot, AI-assisted, prompt engineering, generative AI, AI agents, ChatGPT | 🤖 AI / GitHub Copilot |
| Docker, Kubernetes, GitHub Actions, CI/CD | 🔁 GitHub Actions, Docker & Kubernetes |
| RabbitMQ, Kafka, message queue, messaging, broker, AMQP, event-driven, Service Bus, Event Grid, Event Hubs | 📨 Messaging & Event-Driven |
| REST, API, microservices, GraphQL | 🌐 APIs, REST & Microservices |
| Domain-Driven Design, DDD | 🏗️ Domain-Driven Design |
| Python | 🐍 Python 3 |
| React | ⚛️ React |
| PowerShell | 💻 PowerShell |
| SQL Server, T-SQL, triggers, stored procedures | 🗄️ SQL Server |
| Terraform, Infrastructure as Code, IaC, HCL | 🏗️ Terraform |
| Kusto, KQL, Azure Data Explorer, Log Analytics query | 📊 Kusto Query Language (KQL) |
| OWASP, penetration testing, pen testing, web app security, secure coding | 🛡️ Security & Pen Testing |
| NoSQL, document database, key-value database, column-family, graph database, DynamoDB, Cassandra, MongoDB, Cosmos DB fundamentals | 🗃️ NoSQL |
| Leadership, communication, mentoring, emotional intelligence, burnout, imposter | 🤝 Leadership & Soft Skills |
| Anything else | 🖥️ Other Technical (create new section if the topic is large enough to warrant one) |

**Assignment timing:** Section is assigned here, from the title alone, at write time —
before `data/pluralsight_learning_history.json` has a `summary` for the entry, so this
table never depends on summary content. Titles are usually descriptive enough for
accurate keyword matching.

**Downstream correction path:** `pluralsight-summary-enricher` runs a Step 5 advisory
check after generating each summary — if the fuller description reveals a course was
keyword-matched into the wrong section, it surfaces a **Possible Miscategorization**
list at the end of its run (never edits this file itself). If Sarah Ashford approves a move
from that list, make the section change here: update both the old and new section's
header counts and the Summary table, exactly as in a normal addition.

---

## Step 3 — Downstream Impact Check

After every update, check whether the new completions warrant changes to other files.
Flag to the user — do not auto-edit these files, just call out the action needed.

| Condition | Action to flag |
|---|---|
| New course fills a **Genuine Gap** from `profile-facts.md` | "Consider updating Known Genuine Gaps — this is now course-level coverage" |
| New course is in a **critical AI-200 domain** (Service Bus, Cosmos DB, Redis, Key Vault, Event Grid, Azure OpenAI, vector databases, agentic patterns) | "This closes an AI-200 gap — update skills-summary.md AI-200 Domain Coverage table" |
| New **technology area** not currently in `skills-summary.md` | "New skill area — consider adding a bullet to skills-summary.md" |
| Total course count crosses a round number (115, 120, 125…) | "Milestone — update the Pluralsight summary line in Resume_Snapshot.md" |
| New **lab** completed | "Lab count changed — update the lab total in Resume_Snapshot.md Certifications section" |

---

## Formatting Rules

`merge_pluralsight_course.py` enforces the actual on-disk format below — you
never hand-format a row or header. This list exists so you can sanity-check the
script's dry-run output, not as instructions to hand-edit the file yourself.

- **Section headers**: `### [emoji] [Section Name] ([N] Courses · [N] Labs)` (three `#`, nested under `## ✅ Completed Courses`)
- **Course entry format**: `| [Course Title or [Title](url)] | [Mon DD, YYYY] | [Duration] | [Timing Profile] |`
- **Lab entry format**: same four columns, in a `**[emoji] [Section Name] Labs**` sub-table nested under the section's Courses table — the script creates this sub-table automatically the first time a section gets a lab
- **Table header**: `| Course | Completed Date | Duration | Timing Profile |` (or `| Lab | ... |` in a Labs sub-table) with separator `|--------|-----------------|----------|-----------------|`
- **Duration column rules**:
  - `Full Course` or `Full Lab` (`timing_profile` from JSON) → use the `duration` field value (e.g., `3h 25m`)
  - `Short Course` or `Lab` → enter `—` (Pluralsight recorded no timing data for these entries)
  - Course not in JSON → `web_search` the course page to find duration; never leave the column blank
- **Date format**: `Mon DD, YYYY` (e.g., `Apr 07, 2026`) — matches the JSON's `completed_date` field, not the older `Mon YYYY` style
- **No descriptions** — titles only; keep the file lean
- **No duplicate entries** — the script itself refuses a title that already exists anywhere in the Completed Courses region
- **Summary table** at the bottom: the script updates the matching section row and the `**TOTAL**` row together

---

## Key Principle: Avoid Double-Counting with Microsoft Learn

Pluralsight and Microsoft Learn overlap on GitHub Copilot and C#.
- If a new Pluralsight course covers a topic already in `data/ms-learn-courses.md`, note the overlap to the user but still add it — both are valid credentials
- Do NOT add Pluralsight entries to `data/ms-learn-courses.md` — that file is maintained by the `ms-learn-updater` skill

---

## Companion Files

- `pluralsight-courses.md` — the file this skill maintains ✅, via `scripts/merge_pluralsight_course.py add`/`add-batch` (never hand-write the file directly — see Workflow A/B)
- `data/pluralsight_learning_history.json` — duration + timing_profile lookup source, accessed via `scripts/query_learning_history.py` (never load the raw ~44K-token file directly) ✅; also holds the `summary` field, which is owned by `pluralsight-summary-enricher`, not this skill directly
- `skills-summary.md` — flag updates needed; do not auto-edit
- `Resume_Snapshot.md` — flag updates needed; do not auto-edit
- `data/ms-learn-courses.md` — Microsoft Learn only; do not touch
- `profile-facts.md` — reference for genuine gaps; flag when a new course provides coverage

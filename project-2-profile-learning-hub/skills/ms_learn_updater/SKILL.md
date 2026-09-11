---
name: ms-learn-updater
description: >
  Updates the data/ms-learn-courses.md file when Sarah completes new Microsoft Learn
  modules or learning paths. Trigger when the user says things like "I finished
  a new Microsoft Learn course", "add this to my MS Learn file", "I completed
  another Microsoft Learn module", or pastes/uploads a new Microsoft Learn transcript.
  Also trigger when the user asks to update their learning credentials, sync their
  MS Learn transcript, or mentions a new Microsoft Learn completion. Do NOT use
  this skill for Pluralsight updates — those go in pluralsight-courses.md.
---

# Microsoft Learn Transcript Updater

Keeps `data/ms-learn-courses.md` current as Sarah completes new Microsoft Learn
modules and learning paths. Designed to mirror the structure of `pluralsight-courses.md`
so both files work consistently within the job search project.

---

## Source of Truth

- **File to update**: `data/ms-learn-courses.md`
- **Profile URL**: https://learn.microsoft.com/en-us/users/sarahashford-1234/transcript
- **Companion file**: `pluralsight-courses.md` (do not modify — separate skill)

---

## Workflow A — User Pastes or Uploads a New Transcript

When the user provides a new/updated Microsoft Learn transcript (PDF or pasted text):

1. **Extract new completions** — compare against the existing `data/ms-learn-courses.md`.
   Identify modules and learning paths not yet listed.
2. **Categorize** — place new items in the correct section using this mapping:

   | Keywords in title | Section |
   |---|---|
   | Azure, cloud concepts, AZ- | ☁️ Azure |
   | ASP.NET, .NET web | 🔷 ASP.NET Core |
   | Copilot, GitHub Copilot | 🤖 GitHub Copilot |
   | Git, GitHub, DevOps, CI/CD, pull request, repository | 🔁 DevOps / Git / GitHub |
   | C#, console application, Visual Studio Code debugging | 💻 C# |
   | Node.js, JavaScript, Express | 🌐 Node.js / JavaScript |
   | New area | Create a new section with appropriate emoji |

3. **Format each new entry** as:
   - Learning Path: `**Learning Path:** [Title] — *[Date]* ✅ All assessments passed`
     (or omit ✅ if assessment status is N/A)
   - Module: `- [Module title] — [Date]`

4. **Update the Summary table** — increment module count, learning path count,
   and estimated hours. Add a new row if a new skill area is added.

5. **Update the header** — change "Last updated" date to today.

6. **Update the Key Skills section** — if new completions add meaningfully new
   credential claims (e.g., a new cert path, a new technology area), add a
   bullet. Keep it concise — skills already covered by Pluralsight don't need
   a new bullet here; note the overlap instead.

7. **Present the diff** — show the user exactly what was added before writing
   the file, so they can confirm or correct.

8. **Write the updated file** to `outputs/ms-learn-courses.md`.

---

## Workflow B — User Mentions a Single Completion

When the user says "I just finished [module/path name]":

1. Ask for:
   - Completion date (if not stated, use today's date)
   - Whether all assessments passed (Y/N/N-A)
2. Locate the correct section in `data/ms-learn-courses.md`.
3. Add the entry in chronological order within the section.
4. Update the Summary table totals (increment module count by 1; learning path
   count if applicable; add estimated hours if known).
5. Update "Last updated" date.
6. Show the user the change and confirm before writing.

---

## Workflow C — Full Transcript Sync (Periodic Refresh)

When the user wants a full sync (e.g., "update my MS Learn file from my latest transcript"):

1. Ask the user to upload or paste their current transcript from:
   https://learn.microsoft.com/en-us/users/sarahashford-1234/transcript
2. Follow Workflow A above.
3. Additionally: check for any entries in `data/ms-learn-courses.md` that no longer
   appear in the transcript (rare, but possible if the user revoked access or
   the profile was reset). Flag these to the user — do not auto-delete.

---

## Formatting Rules

Keep the file lean and readable — Claude reads this file on every job search task,
so token efficiency matters:

- **No duplicate entries** — check before adding. A module listed under a Learning
  Path section does not need to appear again as a standalone module entry.
- **No verbose descriptions** — module titles only, no descriptions. Descriptions
  are in Microsoft Learn; they don't need to be in this file.
- **Dates format**: `Mon DD, YYYY` (e.g., `Apr 10, 2026`)
- **Assessment status**: use ✅ for passed, omit the symbol for N/A — don't add
  a separate N/A marker on individual modules; that level of detail is noise.
- **Section order**: Azure · ASP.NET Core · GitHub Copilot · DevOps/Git · C# · Node.js/JS · (new areas at end)
- **Summary table** stays at the top — update it last after all section edits are done.

---

## Key Principle: Avoid Double-Counting with Pluralsight

Microsoft Learn and Pluralsight overlap heavily on GitHub Copilot and C#.
When updating Key Skills:
- If a skill is already well-covered in `pluralsight-courses.md`, note
  "reinforces Pluralsight coverage" rather than adding a standalone bullet.
- If Microsoft Learn adds new credential evidence (e.g., a new AZ-path or a
  cert-aligned learning path with assessments passed), that IS worth a new bullet
  because it's additive proof.
- The note at the bottom of `data/ms-learn-courses.md` ("cross-reference pluralsight-courses.md
  to avoid double-counting") must remain in the file.

---

## Companion Files

- `data/ms-learn-courses.md` — the file this skill maintains ✅
- `pluralsight-courses.md` — Pluralsight credentials (separate skill, do not touch)
- `Resume_Snapshot.md` — master resume; flag to user if new MS Learn completions
  warrant an update to the Certifications section (e.g., a new cert-aligned path completed)

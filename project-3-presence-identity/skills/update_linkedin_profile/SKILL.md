---
name: linkedin-profile-update
description: >
  Updates Sarah Ashford's LinkedIn profile fields with accurate, ready-to-paste
  content. Use when the user asks to update, refresh, or improve their LinkedIn
  profile, or asks what to change on LinkedIn. Also trigger after AZ-900 or
  AZ-204 exam results to update cert-related fields. Contains exact copy for
  every updatable field, character limits, and a diff of current vs target state.
---

# LinkedIn Profile Update Skill

> **Source file**: `presence-bundle.md`
> Load these before regenerating any field content.
> Check `presence-bundle.md` cert table before filling any cert-related field.
> Any `{fragment_name}` placeholder below must be filled from `presence-bundle.md`'s
> **Copy Fragments** section before presenting the final paste-ready text —
> never leave a literal `{fragment_name}` in delivered output. If that section
> is missing from the loaded bundle (older bundle version, pre-fragments), fall
> back to computing the value the same way `profile-hub-bundle-generator_SKILL.md`
> Step 2.5 does, from `profile-facts.md` / `skills-summary.md` directly.

## Character Limits
| Field | Limit | Notes |
|---|---|---|
| Headline | 220 chars | Compute the actual length of the rendered headline at generation time — do not rely on a stored count, it drifts. |
| About | 2,600 chars | Compute the actual length of the rendered About text (Step 1, after fragments are substituted) at generation time. |
| Experience description | 2,000 chars per role | |
| Skills | 50 max; pin top 5 | LinkedIn uses controlled vocabulary — search exact term |

---

## Current State vs Target (diff)

This table describes LinkedIn's *live* profile state as last confirmed by the user —
the bundle has no visibility into what's actually posted on LinkedIn, so this row set
can't self-update. Re-confirm with the user before trusting "Current" values that are
more than a couple of sessions old; update this table by hand once a field has been
applied.

| Field | Current (last confirmed) | Action |
|---|---|---|
| Headline | Matches bundle headline | No change required unless bundle headline changed — compare against `presence-bundle.md` Professional Headline |
| About | Narrative, soft | Replace — see Step 1 |
| Open to Work banner | Unknown | Enable — see Step 2 |
| Experience — Prof Dev | Missing | Add — see Step 3 |
| Experience — existing roles (Fieldstone Benefits Administrators, Aerotech Industries, etc.) | Unconfirmed — may predate latest resume edits | Sync bullet-for-bullet — see Step 3.5 |
| Top Skills | GitHub, Angular CLI, HTML | Replace — see Step 4 |
| Certifications | Old MS certs only | Leave until exam passed — see Step 5 |
| Courses section | Missing | Add — see Step 6 |
| Featured section | Missing | Add — see Step 7 |
| Education | ✅ Pluralsight paths present | No change |

---

## Step 1 — About Section
*(Replace entire current About. Paste as plain text. Report the actual rendered
character count against the 2,600-char limit after substituting fragments — see
Character Limits table above.)*

```
Full-stack developer with 10+ years delivering enterprise software across the entire stack. Core expertise in C#, ASP.NET Core Web API, Entity Framework, Angular (v12–21), TypeScript, RxJS, and MS SQL Server — with hands-on production experience integrating REST APIs across Microsoft Dynamics 365, HubSpot, QuickBooks, and SharePoint.

Built and maintained CI/CD pipelines using GitLab, Azure DevOps, and GitHub Actions. Deployed applications via Docker and nginx. Practised TDD with xUnit and Moq. Led legacy system modernization across multiple roles — VB.NET to Angular, MS Access to ASP.NET Web Forms, Clipper to SQL Server.

{cert_status_short}. Currently advancing toward AI-200 (Azure AI Cloud Developer Associate) with completed training across Azure Functions, App Services, Azure Monitor, Entra ID, and serverless architecture. Deepening expertise in Azure AI Services, prompt engineering, vector databases, and agentic patterns. Deepening GitHub Copilot expertise across {github_copilot_course_count} courses — enterprise deployment, CI/CD integration, secure coding, AI agents, and Copilot-driven test generation.

Also completed {leadership_course_count} leadership and communication courses covering mentoring, emotional intelligence, cross-functional collaboration, and engineering leadership — ready to contribute to team culture as much as the codebase.

Core stack:
Backend: C#, ASP.NET Core (Web API, MVC), .NET Framework, Entity Framework, REST API design
Frontend: Angular (v12–21), TypeScript, RxJS, Signals, Angular Material
Database: MS SQL Server, T-SQL, DB2, stored procedures, performance tuning, SSIS, SSRS
Cloud: Azure (Functions, App Services, Storage, Monitor, Entra ID) — AI-200 in progress
DevOps: Azure DevOps, GitLab CI/CD, GitHub Actions, Docker, Octopus Deploy, Git
AI Tooling: GitHub Copilot (enterprise), prompt engineering, AI agents

Open to senior full-stack, .NET, or Azure developer roles — remote preferred, Winnipeg-based.
```

---

## Step 2 — Open to Work Banner
*(Profile → Open to → Finding a new job)*

| Setting | Value |
|---|---|
| Job titles | Senior Full-Stack Developer · .NET Developer · Azure Developer · Senior Software Developer |
| Job types | Full-time · Contract |
| Location | Winnipeg, MB · Remote |
| Visibility | **All LinkedIn members** (maximizes recruiter reach) |

---

## Step 3 — Add Experience Entry
*(Add above Fieldstone Benefits Administrators as most recent role)*

**Title:** Professional Development & Portfolio Building
**Employment type:** Self-employed
**Start:** May 2025 · **End:** Present
**Location:** Winnipeg, MB · Remote

```
Upskilling and expanding portfolio while actively seeking a senior full-stack developer role.

- {course_count_sentence} across Azure, ASP.NET Core, Angular, GitHub Copilot, DevOps, Python, and leadership.
- {cert_status_short}.
- Building portfolio projects on GitHub — derive the repo list and one-clause hook for each at generation time from `presence-bundle.md`'s `## Portfolio Projects` table (name + shortest differentiator from its description), not from a fixed list, so a new or updated repo shows up automatically. Current example: "job-app-copilot (Claude API + Python job-application automation), RecipeBox (.NET 10 Blazor legacy migration, 118 automated tests), PortfolioSite (GitHub Actions CI/CD), and shell-ops-toolkit (hardware inspection + automated update/cleanup scripts)."
- Deepened GitHub Copilot expertise: enterprise deployment, AI agents, secure development, CI/CD integration, and automated test generation.
- Designed AI-assisted workflows using prompt engineering and structured instruction systems to produce gap analyses, learning plans, and tailored application documents.
```
Re-check the total against the 2,000-char limit after substituting the repo bullet — the table can grow, and the fixed example above is only a snapshot from today's bundle version.

---

## Step 3.5 — Sync Existing Experience Entries
*(Keep LinkedIn's Fieldstone Benefits Administrators, Aerotech Industries, Prairie Transport Co., Riverside Health, and
Vantage Technology Solutions entries bullet-for-bullet consistent with the resume. This is the
step that closes the drift the resume/LinkedIn comparison surfaced — Resume_Snapshot.md
is the source of truth, and LinkedIn must not fall behind it.)*

`presence-bundle.md`'s `## Professional Experience` section is rendered directly from
`Resume_Snapshot.md`'s per-employer bullets (via the bundle's typed `experience` list) —
it is not a paraphrase and not hand-maintained, so it's safe to treat as the exact
target text for each LinkedIn role.

1. For every job entry in that section **other than** "Professional Development &
   Portfolio Building" (which Step 3 already owns), find the matching LinkedIn
   Experience entry by company name.
2. Output that entry's full bullet list verbatim, formatted for pasting into
   LinkedIn's role description field. Report the rendered character count against
   the 2,000-char-per-role limit (see Character Limits table) — a long role
   (e.g. Fieldstone Benefits Administrators) may need trimming to fit; prioritize keeping the most
   recent/most differentiated bullets over exhaustive coverage rather than
   silently truncating.
3. Since this session has no visibility into what's actually posted on LinkedIn
   today, don't assume the existing entry is already in sync — present the full
   bullet list for every role each time this step runs, and let the user diff it
   against what's live rather than guessing which bullets changed.
4. If a role in `presence-bundle.md` has no obvious LinkedIn counterpart (a new
   employer added to the resume since LinkedIn was last touched), flag it as a
   **new** entry to add rather than an update.

---

## Step 4 — Skills
*(Skills → Add skill — search exact term; LinkedIn uses controlled vocabulary)*

**Top 5 to pin** (pin in this order for recruiter visibility — reflects the load-bearing
stack across the bundle's Portfolio Projects and Cert Status, not just raw skill count):
```
1. C#
2. ASP.NET Core
3. Angular
4. Microsoft Azure
5. CI/CD
```
Re-evaluate this top 5 only if the primary tech stack changes (e.g. a new portfolio
project anchors a different language/framework) — don't reshuffle it for every bundle
refresh.

**Full list to add — derive at generation time from `presence-bundle.md`'s
`## Technical Skills` section, not from a fixed list:**

1. Walk every category in Technical Skills (Backend Development, Frontend & UI,
   Database & SQL, Cloud & Azure, DevOps & CI/CD, Security, Project Management & Agile,
   AI & Automation, Platforms & Services, Linux & Unix, Tools & Utilities).
2. Keep clean, single-concept nouns/proper nouns that map to a real LinkedIn skill tag
   (e.g. `C#`, `Entity Framework Core`, `Docker`, `GraphQL`).
3. Drop `(course-level)` qualifiers, multi-clause phrases, and internal jargon that
   isn't a searchable LinkedIn tag (e.g. "hierarchies (course-level)", "SOLID principles"
   stays only if phrased as LinkedIn's actual tag — check by searching it).
4. De-duplicate against the pinned top 5 above.
5. Present the resulting list to the user for this session rather than reusing any
   previously generated list verbatim — the Technical Skills section changes as new
   courses/portfolio work land, and a stale list is exactly the failure mode this step
   exists to avoid.

> Note: Search each term individually — LinkedIn autocompletes to its own tag library.
> If `CI/CD` doesn't match, try `Continuous Integration and Continuous Delivery (CI/CD)`.

---

## Step 5 — Certifications
*(Licenses & Certifications section)*

**AZ-900 is certified with a live credential** — add it now if not already present:
1. Go to [Microsoft Learn credentials](https://learn.microsoft.com/en-us/users/me/credentials)
2. Find the AZ-900 badge → click **Share** → **Add to LinkedIn**
3. LinkedIn will auto-fill the credential ID, issuer, and date

**Do NOT add AI-200 manually** — it's still in progress. Wait for Microsoft to issue that credential before repeating the steps above.

**Existing old MS certs** (MS: Programming in C#, MCPS): leave as-is — they show tenure and are not harmful.

---

## Step 6 — Courses Section
*(Profile → Add section → search "Courses" in the Add section search bar if not visible under Recommended)*

Derive this list at generation time from `presence-bundle.md`'s `## Cert Status + Badge
URLs` table — do not reuse a fixed list, it goes stale the moment newer coursework
supersedes it:

1. Always include the exam-prep course for each certified/in-progress cert row
   (e.g. "Microsoft Azure Fundamentals (AZ-900): Exam Preparation").
2. From the AI-200 (or current active cert) row's notes, list the specific named
   courses/modules called out as completed or in progress — the bundle's cert notes
   are updated each regeneration specifically so this step can read real, current
   course names instead of guessing.
3. Cap at ~8–10 entries; prefer the most recent/most role-relevant over exhaustive
   coverage.

Add each individually as a Course entry (title + "Pluralsight" as the associated
institution).

---

## Step 7 — Featured Section
*(Profile → Add section → Featured → Links)*

Derive the per-project entries at generation time from `presence-bundle.md`'s
`## Portfolio Projects` table — one Featured link per row, so a new or retired
project shows up automatically instead of going stale like Step 3's example above:

1. For each row, add a Featured link with:
   - **URL** — the row's URL column
   - **Title** — the project name
   - **Description** — the row's description, trimmed to the first 1–2 sentences
     (LinkedIn shows a preview; the full text isn't needed there)
2. Add two static entries alongside the per-project ones (not derived from the
   bundle, since they aren't portfolio projects):

```
GitHub Profile         — https://github.com/sarah-ashford-dev
Pluralsight Profile    — https://app.pluralsight.com/profile/sarah-ashford-dev
```

Current example (from today's bundle — regenerate this list whenever the
Portfolio Projects table changes):

```
1. job-app-copilot — https://github.com/sarah-ashford-dev/job-app-copilot
   AI-assisted job application workflow: analyzes job descriptions, generates
   ATS-safe tailored resumes and cover letters, and produces phased learning plans.
2. RecipeBox — https://github.com/sarah-ashford-dev/ClaimsBoard
   20-year-old WinForms cooking-time calculator refactored into a modern .NET 10
   Blazor WebAssembly app; 118 automated tests at 80% line coverage with a
   blocking CI gate.
3. PortfolioSite — https://github.com/sarah-ashford-dev/PortfolioSite
   Responsive static resume website, automatically deployed to GitHub Pages via
   GitHub Actions on push.
4. shell-ops-toolkit — https://github.com/sarah-ashford-dev/job-app-copilot
   Linux maintenance scripts for terminal-based system administration —
   hardware inspection and automated package update/cleanup workflows for
   Debian-based distributions.
5. GitHub Profile — https://github.com/sarah-ashford-dev
6. Pluralsight Profile — https://app.pluralsight.com/profile/sarah-ashford-dev
```

---

## Step 8 — Write the Draft Document

After presenting Steps 1–7 in the conversation, also write the full paste-ready
output to `project-3-presence-identity/linkedin-update-draft.md` (create it if
missing, overwrite if present — it's a generated draft, not hand-maintained).
This gives Sarah a single file to work through in her own time instead of
having to copy content back out of chat history.

1. Include all of Steps 1–7 verbatim (fragments substituted, character counts
   computed, Step 3.5 trimmed to fit) — the file is the deliverable, not a
   pointer back to this skill.
2. Head the file with an HTML comment noting it's generated and which
   `presence-bundle.md` `bundle_version` it reflects, e.g.:
   ```
   <!-- GENERATED DRAFT — regenerate by running the update_linkedin_profile skill.
        Reflects presence-bundle.md bundle_version: N (generated YYYY-MM-DD). -->
   ```
3. End with a short "After applying" note reminding Sarah to update the
   Current State vs Target diff table above once she's pasted a field in.
4. Report the file path in the completion summary so it's easy to find.

---

## Post-Exam Update Checklist
AZ-900 is already certified and reflected above. Run this checklist after AI-200 results:

| Field | AI-200 Passed |
|---|---|
| About — Cloud line | Update to "AI-200 Certified" |
| Experience — Prof Dev bullet 2 | Add AI-200 cert line |
| Certifications | Add via Microsoft Share Badge |
| Headline | Consider adding "AI-200" |

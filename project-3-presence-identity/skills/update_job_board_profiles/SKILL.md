---
name: update-job-board-profiles
description: >
  Updates Sarah Ashford's Indeed and ZipRecruiter candidate profile fields
  (headline, summary, skills, job preferences) with accurate, ready-to-paste
  content. Use when the user asks to update, refresh, or improve their Indeed
  or ZipRecruiter profile, or asks what to change on those job boards. Also
  trigger after AZ-900 or AI-200 exam results to update cert-related fields.
  Unlike LinkedIn/GitHub, these platforms publish no fixed field character
  limits — content targets are practical, not enforced. Also flags whether the
  uploaded resume file is stale relative to the current bundle, since both
  platforms lean on the uploaded resume more than on typed profile fields.
---

# Indeed & ZipRecruiter Profile Update Skill

> **Source file**: `presence-bundle.md`
> Load before regenerating any field content.
> Check `presence-bundle.md` cert table before filling any cert-related field.
> Any `{fragment_name}` placeholder below must be filled from `presence-bundle.md`'s
> **Copy Fragments** section before presenting the final paste-ready text —
> never leave a literal `{fragment_name}` in delivered output. If that section
> is missing from the loaded bundle (older bundle version, pre-fragments), fall
> back to computing the value the same way `profile-hub-bundle-generator_SKILL.md`
> Step 2.5 does, from `profile-facts.md` / `skills-summary.md` directly.

Indeed and ZipRecruiter are treated as one skill because their candidate profile
shape is nearly identical — headline, summary, skills, and job preferences, both
backed primarily by an uploaded resume rather than hand-typed experience entries
the way LinkedIn is. Content for the two platforms is shared; only job-alert/visibility
settings differ.

## Character Limits
| Field | Limit | Notes |
|---|---|---|
| Headline / Job title | ~100 chars (practical target) | Neither platform publishes a hard limit — keep it scannable in a search-results row. |
| Summary / About | ~1,000–1,500 chars (practical target) | No published cap; shorter than LinkedIn's 2,600 since these surfaces show a preview in job-search contexts. |
| Skills | ~20 tags (practical target) | No published cap; keep to the most ATS-relevant subset rather than the full LinkedIn 50. |

---

## Resume File Dependency Check — run this first

Both platforms parse an uploaded resume into most of the profile automatically.
Before writing any field content below:

1. Check the modification date of `project-1-application-engine/outputs/SarahAshford_Resume_SeniorFullStackNET.docx`
   against `presence-bundle.md`'s `generated` date (and the `last_modified` dates of
   `profile-facts.md` / `Resume_Snapshot.md` / `skills-summary.md` in Project 2).
2. If the resume file predates any of those sources, tell the user it's stale and
   offer to run the `fullstack_net_profile_resume` skill to regenerate it before
   they upload — the typed fields below only cover headline/summary/skills/preferences,
   not the parsed work history the platforms build from the resume itself.

---

## Current State vs Target (diff)

This table describes Indeed/ZipRecruiter's *live* profile state as last confirmed
by the user — this skill has no visibility into what's actually posted on either
site. Re-confirm with the user before trusting a "Current" value more than a
couple of sessions old; update this table by hand once a field has been applied.

| Field | Current (last confirmed) | Action |
|---|---|---|
| Headline / Job title | Unknown — first run of this skill | Set — see Step 1 |
| Summary / About | Unknown | Set — see Step 2 |
| Skills | Unknown | Set — see Step 3 |
| Job preferences (desired titles, types, location, salary) | Unknown | Set — see Step 4 |
| "Actively looking" / resume visibility | Unknown | Enable — see Step 4 |
| Resume file | See freshness check above | Regenerate if stale |

---

## Step 1 — Headline / Job Title
*(Indeed: Profile → Job title. ZipRecruiter: Profile → Headline.)*

```
Senior Full-Stack .NET Developer | C# · ASP.NET Core · Angular · Azure | {cert_status_short}
```

---

## Step 2 — Summary / About
*(Indeed: Profile → Summary. ZipRecruiter: Profile → About.)*

```
Full-stack developer with 10+ years delivering enterprise software in C#, ASP.NET Core Web API, Entity Framework, and Angular (v12-21), backed by MS SQL Server and DB2. Production experience integrating REST APIs across Microsoft Dynamics 365, HubSpot, QuickBooks, and SharePoint, plus CI/CD pipelines on GitLab, Azure DevOps, and GitHub Actions, deployed via Docker and nginx.

{cert_status_short}; actively working toward Azure AI Cloud Developer Associate (AI-200), with completed training in Azure Functions, App Services, Azure Monitor, Entra ID, and serverless architecture. Enterprise GitHub Copilot practitioner across {github_copilot_course_count} courses covering secure coding, CI/CD integration, and AI-assisted testing.

Led legacy modernization at three separate employers (VB.NET to Angular, MS Access to ASP.NET Web Forms, Clipper to SQL Server) and practice TDD with xUnit and Moq.

Open to senior full-stack, .NET, or Azure developer roles - remote preferred, based in Winnipeg, MB.
```

---

## Step 3 — Skills

Derive at generation time from `presence-bundle.md`'s `## Technical Skills`
section — do not reuse a fixed list, it goes stale the moment new coursework or
portfolio work lands. Keep to ~20 tags, prioritizing the load-bearing stack and
the most ATS-recognizable single-concept terms (drop `(course-level)` qualifiers
and multi-clause phrases, same rule as the LinkedIn skill's Step 4):

```
C#, ASP.NET Core, Angular, Microsoft Azure, CI/CD, Entity Framework Core, TypeScript,
Microsoft SQL Server, T-SQL, Azure Functions, Azure DevOps, Docker, GitHub Actions,
Git, xUnit, JWT, Microservices, GitHub Copilot, Microsoft Dynamics 365, SharePoint Online
```

---

## Step 4 — Job Preferences

| Setting | Value |
|---|---|
| Desired job titles | Senior Full-Stack Developer · .NET Developer · Azure Developer |
| Job types | Full-time · Contract |
| Location | Winnipeg, MB — open to remote |
| Salary expectation | Leave as "negotiable" unless the user wants a specific figure — run the `salary_research` skill rather than guessing a number here |
| "Actively looking" / resume visibility (Indeed) | Set to visible to employers |
| Job Alerts (ZipRecruiter) | Enable for: .NET Developer, Azure Developer, Full-Stack Developer — Winnipeg / Remote (Canada) |

---

## Step 5 — Write the Draft Document

After presenting Steps 1–4 in the conversation, also write the full paste-ready
output to `project-3-presence-identity/job-board-profile-update-draft.md`
(create it if missing, overwrite if present — it's a generated draft, not
hand-maintained).

1. Include all of Steps 1–4 verbatim (fragments substituted) for both Indeed
   and ZipRecruiter — the file is the deliverable, not a pointer back to this skill.
2. Include the result of the Resume File Dependency Check above, even if the
   resume was found current — don't silently omit the check.
3. Head the file with an HTML comment noting it's generated and which
   `presence-bundle.md` `bundle_version` it reflects, e.g.:
   ```
   <!-- GENERATED DRAFT — regenerate by running the update-job-board-profiles skill.
        Reflects presence-bundle.md bundle_version: N (generated YYYY-MM-DD). -->
   ```
4. End with a short "After applying" note reminding Sarah to update the
   Current State vs Target diff table above once she's pasted a field in.
5. Report the file path in the completion summary so it's easy to find.

---

## Post-Exam Update Checklist
Run this checklist after AI-200 results:

| Field | AI-200 Passed |
|---|---|
| Headline | Add "· AI-200 Certified" |
| Summary | Replace "actively working toward AI-200" paragraph with certified language |
| Job Alerts / preferences | No change needed |

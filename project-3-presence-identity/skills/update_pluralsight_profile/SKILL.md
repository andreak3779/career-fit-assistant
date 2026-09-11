---
name: update-pluralsight-profile
description: >
  Updates Sarah Ashford's public Pluralsight profile fields (bio/tagline, job
  title, location, links) with accurate, ready-to-paste content. Use when the
  user asks to update, refresh, or improve their Pluralsight profile. Also
  trigger after AZ-900 or AI-200 exam results to update cert-related copy.
  Pluralsight is not a job board — this profile is checked by recruiters
  alongside the resume/GitHub README, so it only needs a short bio, title, and
  links kept consistent with the rest of the presence surfaces, not job-search
  fields like desired titles or salary.
---

# Pluralsight Profile Update Skill

> **Source file**: `presence-bundle.md` (~8K tokens) — this skill only ever needs
> the **Copy Fragments** and **Cert Status + Badge URLs** sections, never
> Experience/Skills/Portfolio, so don't load the whole file. Run
> `python project-1-application-engine/scripts/extract_bundle_sections.py --file presence-bundle.md --project project-3-presence-identity section "Copy Fragments" "Cert Status + Badge URLs"`
> before regenerating any field content.
> Any `{fragment_name}` placeholder below must be filled from the **Copy Fragments**
> output before presenting the final paste-ready text — never leave a literal
> `{fragment_name}` in delivered output. If that section is missing (older bundle
> version, pre-fragments), fall back to computing the value the same way
> `profile-hub-bundle-generator_SKILL.md` Step 2.5 does, from `profile-facts.md` /
> `skills-summary.md` directly.

Profile URL: https://app.pluralsight.com/profile/sarah-ashford-dev

This profile's real value to a recruiter is the Skill IQ / course-completion
data itself, which updates automatically as courses finish — this skill only
touches the small hand-edited surface around that (bio, title, location, links).

## Character Limits
| Field | Limit | Notes |
|---|---|---|
| Bio / Tagline | ~150 chars (practical target) | Pluralsight doesn't publish a hard limit for this field — keep it to one sentence that reads well under the name. |

---

## Current State vs Target (diff)

This table describes Pluralsight's *live* profile state as last confirmed by
the user — this skill has no visibility into what's actually posted there.
Re-confirm with the user before trusting a "Current" value more than a couple
of sessions old; update this table by hand once a field has been applied.

| Field | Current (last confirmed) | Action |
|---|---|---|
| Bio / Tagline | Unknown — first run of this skill | Set — see Step 1 |
| Job title | Unknown | Set — see Step 2 |
| Location | Unknown | Set — see Step 2 |
| Links | Unknown | Set — see Step 2 |

---

## Step 1 — Bio / Tagline
*(Profile → Edit profile → Bio)*

```
Full-stack .NET/Angular developer (10+ yrs). {cert_status_short}.
```

Compute the actual rendered length after substituting `{cert_status_short}` and
keep it to roughly one sentence — this field has no published limit but reads
poorly past ~150 chars under the profile name.

> After passing AI-200: `{cert_status_short}` will read "AZ-900 · AI-200 Certified" once the bundle updates — no separate edit needed here beyond re-substituting the fragment.

---

## Step 2 — Profile Fields
*(Profile → Edit profile)*

| Field | Value |
|---|---|
| Job title | Senior Full-Stack Developer |
| Location | Winnipeg, MB |
| Links | GitHub: https://github.com/sarah-ashford-dev · LinkedIn: https://www.linkedin.com/in/sarah-ashford-dev |

No further action needed beyond bio/title/location/links — do not hand-edit
course or Skill IQ data here; that reflects automatically from Pluralsight's
own tracking as courses complete.

---

## Step 3 — Write the Draft Document

After presenting Steps 1–2 in the conversation, also write the full paste-ready
output to `project-3-presence-identity/pluralsight-profile-update-draft.md`
(create it if missing, overwrite if present — it's a generated draft, not
hand-maintained).

1. Include Steps 1–2 verbatim (fragment substituted, length computed) — the
   file is the deliverable, not a pointer back to this skill.
2. Head the file with an HTML comment noting it's generated and which
   `presence-bundle.md` `bundle_version` it reflects, e.g.:
   ```
   <!-- GENERATED DRAFT — regenerate by running the update-pluralsight-profile skill.
        Reflects presence-bundle.md bundle_version: N (generated YYYY-MM-DD). -->
   ```
3. End with a short "After applying" note reminding Sarah to update the
   Current State vs Target diff table above once she's pasted a field in.
4. Report the file path in the completion summary so it's easy to find.

---

## Post-Exam Update Checklist
Run this checklist after AI-200 results:

| Field | AI-200 Passed |
|---|---|
| Bio / Tagline | No manual edit needed — `{cert_status_short}` updates to "AZ-900 · AI-200 Certified" automatically once the bundle regenerates |
| Job title / Location / Links | No change needed |

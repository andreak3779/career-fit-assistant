---
name: github-profile-update
description: >
  Updates Sarah Ashford's GitHub profile fields with accurate, ready-to-paste
  content. Use when the user asks to update, refresh, or improve their GitHub
  profile, bio, status, or README. Also trigger after AZ-900 or AI-200 exam
  results to update cert-related fields. Contains exact copy for every field
  with character limits enforced.
---

# GitHub Profile Update Skill

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

## Character Limits
| Field | Limit |
|---|---|
| Bio | 160 chars |
| Status | 80 chars (emoji + text) |
| Name | 255 chars |
| Location | Free text |
| Website | One URL (must include https://) |

---

## Current State vs Target

| Field | Current | Action |
|---|---|---|
| Bio | Verify before updating | Set — see Step 1 |
| Status | Verify before updating | Set — see Step 2 |
| Profile README | Check if repo `sarah-ashford-dev/sarah-ashford-dev` exists | Create or update — see Step 3 |
| Profile fields | Verify before updating | Set — see Step 4 |
| Pinned repos | Verify existing repos first | Select from actual repos — see Step 5 |

---

## Step 1 — Bio
*(Profile → Edit profile → Bio · 160 char max)*

```
Full-stack dev | C# · ASP.NET Core · Angular · Azure · SQL | CI/CD · GitHub Actions · Copilot | 10+ yrs enterprise apps | {cert_status_short}
```
*(recount before saving — must stay under 160 chars; trim "10+ yrs enterprise apps" first if over)*

> ⚠️ After passing AI-200: replace `AZ-900 Certified · AI-200 in progress` with `AZ-900 · AI-200 Certified`
> — recount to confirm under 160 chars before saving.

---

## Step 2 — Status
*(Click profile picture → Set status · 80 char max)*

```
🚀 Open to work | .NET · Angular · Azure | Building portfolio
```
*(61 chars)*

**Settings:**
- Emoji: 🚀
- Clear after: **Never**
- Busy checkbox: **Leave unchecked** (signals availability)

> ⚠️ After accepting a job offer: clear this status immediately.

---

## Step 3 — Profile README
*(High visibility — renders at the top of your GitHub profile page)*

**Setup:** Create a repo named exactly `sarah-ashford-dev` (same as your username) with a `README.md`.
If the repo already exists, edit the existing `README.md`.

```markdown
## Hi, I'm Sarah 👋

Full-stack developer with 10+ years building enterprise applications.

**Core stack:** C# · ASP.NET Core · Angular · Azure · SQL Server

**Currently:** {cert_status_short} · Open to work

**Links:**
- 🌐 [Resume](https://sarah-ashford-dev.github.io/PortfolioSite/)
- 💼 [LinkedIn](https://www.linkedin.com/in/sarah-ashford-dev)
- 📚 [Pluralsight](https://app.pluralsight.com/profile/sarah-ashford-dev)
```

> ⚠️ After passing AI-200: update "Currently" line to:
> `**Currently:** AZ-900 · AI-200 Certified · Open to work`

---

## Step 4 — Profile Fields
*(Profile → Edit profile)*

| Field | Value |
|---|---|
| Name | Sarah Ashford |
| Location | Winnipeg, MB |
| Website | https://sarah-ashford-dev.github.io/PortfolioSite/ |
| LinkedIn | https://www.linkedin.com/in/sarah-ashford-dev |

---

## Step 5 — Pinned Repositories
*(Profile → Customize your pins → select up to 6)*

**Before pinning:** visit https://github.com/sarah-ashford-dev?tab=repositories to see actual available repos. Select from what exists — do not pin empty or placeholder repos.

Prioritize repos that demonstrate:
1. Angular + ASP.NET Core (full-stack pairing)
2. GitHub Actions CI/CD workflow
3. Azure Functions or Azure integration

**For each pinned repo, verify it has:**
- A short **description** (1 sentence, name the tech used)
- A **README.md** with tech stack listed and setup instructions

---

## Post-Exam Update Checklist
AZ-900 is already certified and reflected above. Run this checklist after AI-200 results:

| Field | AI-200 Passed |
|---|---|
| Bio (Step 1) | Change to `AZ-900 · AI-200 Certified` |
| Profile README (Step 3) | Update Currently line |
| Status (Step 2) | No change needed |

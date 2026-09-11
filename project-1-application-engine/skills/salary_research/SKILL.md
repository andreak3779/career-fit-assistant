---
name: salary-research
description: >
  Researches salary ranges and contract hourly rates for Sarah Ashford's target
  developer roles in Canadian dollars (CAD). Use this skill whenever the user
  asks about salary, pay, compensation, rates, how much to ask for, what to
  charge, what to negotiate, or what the market rate is for a role. Also trigger
  when the user asks "what should I ask for", "is this offer fair", "what's the
  going rate", "how much do .NET developers make", or pastes a job offer and
  wants to evaluate it. Always use this skill — do not handle salary research
  ad hoc. Output: downloadable markdown file with salary tables, contract rate
  tables, and negotiation guidance. Always report in CAD.
---

# Salary Research Skill

Produces a market-rate salary and contract rate reference document for Sarah's
target roles in Canadian dollars. Uses live web search across multiple sources
and anchors figures to her actual experience level: 10+ years enterprise .NET
development, {cert_status_short}.

> **Profile source:** `app-engine-bundle.md` — this skill only needs Cert Registry and
> Copy Fragments, not the full ~11.5K-token file. Run
> `python project-1-application-engine/scripts/extract_bundle_sections.py section "Copy Fragments" "Cert Registry"`
> before writing any document.
> Any `{fragment_name}` placeholder in this file must be filled from the Copy Fragments
> output above — never leave a literal `{fragment_name}` in delivered text.

---

## Inputs

The user may specify any combination of:

- **Job type(s):** Hybrid Winnipeg, remote Canada (one or more time zones), or both
- **Role title:** e.g. "Senior Full-Stack .NET Developer", "Azure Developer" — default
  to Sarah's primary targets if not stated
- **Employment type:** Permanent (salary) and/or Contract (hourly rate) — produce both
  unless the user says otherwise

If inputs are vague, proceed with defaults: both scenarios, both employment types.

---

## Step 1 — Identify Role Targets

Map the user's request to one or more role titles. Default targets if not specified:

- Senior Full-Stack .NET Developer (C# · ASP.NET Core · Angular)
- Senior Software Developer (.NET focus)
- Azure .NET Developer / Cloud Developer

---

## Step 2 — Web Search (run in parallel where possible)

Run all searches in CAD context. Use `web_search` for each query below.

### Required searches
1. `[Role title] salary Winnipeg Canada [current year] CAD`
2. `Senior .NET developer remote Canada salary [current year] CAD`
3. `[Role title] contract hourly rate Canada [current year]`
4. `IT contractor rates Canada [current year] senior developer`

### Preferred sources (prioritize these in results)
- **Glassdoor Canada** — self-reported, role-specific, most reliable for Canada
- **Robert Half Canada Salary Guide** — recruiter-anchored, cert premium data
- **ERI SalaryExpert** — employer survey data, good for Winnipeg specifically
- **ZipRecruiter Canada** — real-time job posting data, good for province-level cuts
- **PayScale Canada** — good for percentile breakdown
- **CareerBeacon** — active Canadian job postings, useful for posted salary ranges
- **SystemSkills.ca / Morgan McKinley** — contractor rate data Canada

Skip US-only sources. Convert any USD figures using current exchange rate if needed,
but prefer CAD-native sources.

### Cert premium note
Robert Half 2026 Canada Salary Guide: 73% of tech leaders pay more for certifications.
{cert_status_short} = justifies upper-half positioning. Note this explicitly in the document.

---

## Step 3 — Time Zone Compatibility (remote scenario only)

For remote Canada, include a compatibility table for all five zones:

| Zone | Cities | Offset from Winnipeg (CT) | Verdict |
|---|---|---|---|
| Pacific (PT) | Vancouver, Victoria | −2 hrs | ✅ Workable |
| Mountain (MT) | Edmonton, Calgary | −1 hr | ✅ Easy |
| Saskatchewan (CT, no DST) | Regina, Saskatoon | Same | ✅ No offset ever |
| Central (CT) | Winnipeg | Same | ✅ Home zone |
| Eastern (ET) | Toronto, Ottawa | +1 hr | ✅ Easy |

All Canadian time zones are workable for a Winnipeg-based remote developer.

---

## Step 4 — Contract Rate Calculation

When computing contract rates from salary data:

**Formula:** Employee salary midpoint × 1.30–1.40 ÷ 1,800 hrs = hourly floor
(The 30–40% premium covers self-employment taxes, no CPP/EI employer match,
no benefits, no paid vacation.)

**Also note:** For Toronto/Vancouver clients hiring remote, apply a 10–15% geographic
premium over the national rate — do not discount for Winnipeg location.

---

## Step 5 — Build the Markdown Document

File name: `SalaryResearch_[RoleShortTitle]_[YYYY-MM].md`
Output to: `outputs/`

### Document structure

```
# Salary & Contract Rate Research — [Role Title]
[Your name] · [Month Year] · All figures in CAD

## How to Use This Document
[brief instructions: when to use each section, what "target" and "floor" mean]

## Scenario 1 — Hybrid Role in Winnipeg
### Job Types Covered
### Salary Range (Permanent, Full-Time)
| Percentile | Annual | Monthly | Notes |
### Contract Hourly Rate
| Band | Rate/hr | Annualized | Notes |
**Your target ask:** [range]
**Negotiation floor:** [number + rationale]

## Scenario 2 — Remote Canada
### Time Zone Compatibility Notes
### Salary Range (Permanent, Full-Time)
| Market | Percentile | Annual | Notes |
### Contract Hourly Rate
| Band | Rate/hr | Annualized | Notes |
**Your target ask:** [range]
**Negotiation floor:** [number + rationale]

## Key Factors That Support the Higher End
[Table: factor → impact on positioning]

## Sources Used
[Table: source · data used · date]

## Negotiation Tips
[5–7 concrete, role-specific tips — not generic advice]
```

---

## Step 6 — Present and Summarise

Tell the user the markdown file's path under `outputs/`.

Inline summary (6–8 sentences):
- Winnipeg salary target and floor
- Remote salary target and floor
- Winnipeg contract rate target
- Remote contract rate target
- Top 2 profile factors that push toward the higher end
- One negotiation tip specific to Sarah's situation

---

## Principles

- **Always CAD.** Never report USD without explicit conversion note.
- **Anchor to seniority.** Sarah has 10+ years — never use "all levels" averages as
  the target. Always find senior-level data or apply an experience premium.
- **Cite sources inline.** Every salary claim should trace to a named source + date.
- **No generic advice.** Negotiation tips must reference Sarah's specific differentiators
  (certs, legacy modernization track, SSIS story, GitHub Copilot depth).
- **Update cert status from `app-engine-bundle.md`** before writing — cert language in the
  document must match current status (Certified vs. In Progress).

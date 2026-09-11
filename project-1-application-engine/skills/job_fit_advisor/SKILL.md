---
name: job-fit-advisor
description: >
  Tells Sarah which job types and role titles she should be targeting based on
  her current skills, experience, and certifications. Use whenever the user asks
  "what jobs should I apply for", "what roles am I a good fit for", "what kind
  of job should I be targeting", "what should I be applying for", "what roles
  match my skills", or any variant of "what job is right for me". Always use
  this skill — do not answer ad hoc. Reads live source files so the answer
  stays current as skills change.
---

# Job Fit Advisor

Produces a targeted role recommendation based on Sarah's current skills,
certifications, and differentiators. Always reads source files — never uses
hardcoded role lists.

---

## Step 1 — Load Source Files

Load all three before writing any output:

- `app-engine-bundle.md` — cert status, differentiators, resolved and genuine gaps
- `app-engine-bundle.md` — current ATS keyword stack, tech categories
- `JobSearch_KeywordStrategy.md` — existing primary/secondary/stretch role groupings

---

## Step 2 — Derive Role Tiers

From the loaded files, classify roles into three tiers:

### Primary Targets
Roles where **all** of the following are true:
- Core stack (language + framework + frontend) is a direct match
- At least 2 production employment anchors exist in the resume
- No required skills are genuine gaps

### Cloud / Azure Angle
Roles where:
- Azure services appear as a primary requirement (not just nice-to-have)
- Current cert status from `app-engine-bundle.md` supports the claim
- Backend .NET depth remains relevant

### Broader Sweeps
Roles where:
- One layer of the stack (backend OR frontend, not both) is the primary requirement
- The other layer is listed as a nice-to-have or not mentioned
- Use when primary/cloud volume is low

---

## Step 3 — Surface Differentiators

From `app-engine-bundle.md`, pull the top 3–4 differentiators that strengthen the
application across all tiers. These should be specific and evidence-backed —
not generic ("10 years experience") but anchored ("7× SSIS performance
improvement", "3-employer legacy modernization track record").

---

## Step 4 — Flag What to Avoid (For Now)

Identify role categories where genuine gaps from `app-engine-bundle.md` would
create a poor fit. Be direct — name the gap and the role type to skip. This
prevents wasted applications.

---

## Step 5 — Output Format

Respond inline (no file needed). Structure:

```
**Primary Targets** — [1–4 role titles with brief rationale]

**Cloud / Azure Angle** — [1–3 role titles + cert status note]

**Broader Sweeps** — [2–3 role titles for high-volume periods]

**Your Strongest Differentiators** — [3–4 bullet points, specific + evidence-backed]

**What to Avoid For Now** — [1–3 role types + reason]

**Tip** — [One sentence: how to use this in your job search today]
```

Keep each section to 2–4 lines. The user should be able to act on this
immediately — no padding, no generic advice.

---

## Principles

- **Always read source files.** Never use cached role lists from training data
  or memory — the answer must reflect current cert status and stack.
- **Cert language must match `app-engine-bundle.md` exactly.** Never say "certified"
  for an in-progress cert or vice versa.
- **Genuine gaps are not frameable.** If `app-engine-bundle.md` lists something as
  a genuine gap, it belongs in "avoid for now," not softened into a primary target.
- **Tiers are not rigid.** If the loaded files show significant new skills or
  closed gaps since the last run, promote roles accordingly without being asked.

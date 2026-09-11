---
name: job-search
description: >
  Fallback job search assistant. Use ONLY when no specialized skill applies.
  For .NET/Azure roles → use azure-focused-net-developer. For gap analysis →
  use gap-analysis-job-description. For cover letter/resume → use
  create-a-cover-letter-and-tailored-resume-for-job-description (MANDATORY fit assessment
  first; documents only generated if fit is Strong or Good). For learning
  plans → use learning-plan-gap-analysis. Trigger this skill only for: salary
  research, application tracking, company research, or offer evaluation.
---

# Job Search Skill — Fallback Only

> Specialized skills handle most tasks. Use this skill only for the workflows below.

**User:** Sarah Ashford · Winnipeg, MB · open to remote · full-stack .NET/Angular/Azure

---

## Workflows (not covered by specialized skills)

**Application Tracking** — Markdown table: Company · Role · Engagement (Permanent/Contract) · Date · Status · Next Step. Statuses: Applied · Phone Screen · Technical · Offer · Rejected · Withdrawn. Offer `.md`/`.csv`. Before adding a new row, check existing rows for the same company — if one exists, surface it (date, status, same posting or different) rather than silently logging a second entry; a repeat cold application to an unresponsive posting is a pattern worth flagging, not just recording.

**Salary & Offer Evaluation** — Research Winnipeg/remote rates via web search. Break down total comp. Negotiation levers: base, bonus, equity, PTO, remote flex, signing bonus. Sources: Glassdoor, Levels.fyi, LinkedIn Salary.

**Company Research** — Use web search. Flag US-only postings (visa required). Note remote-friendly roles open to Winnipeg/Central timezone. Note engagement type (permanent vs. contract) rather than filtering contract roles out by default — treat it as a separate lane worth tracking, not noise.

---

## Principles
- Concrete edits, not generic advice.
- Pluralsight courses = proof of skill — cite them.
- Flag US-only postings.

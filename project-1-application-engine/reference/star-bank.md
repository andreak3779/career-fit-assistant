# STAR Story Bank — Sarah Ashford
Load this file in Step 5. Select 3–4 stories (2 for Phone Screen) based on JD tags.
Adapt framing language to mirror the JD's vocabulary — never change the facts.
After each use: update `last_used` and append to `used_for` for every selected story.

**Last reviewed:** June 2, 2026

---

## How to Use This File

Each story has:
- **Use for** — question types this story answers
- **JD tags** — JD requirement keywords this story addresses
- **last_used** — date last selected for an interview prep document
- **used_for** — roles this story has been used for (avoid repeating for last 2 applications)
- **S / T / A / R** — the four components, written in Sarah's voice
- **Adapt when** — how to reframe for different role types without changing facts

---

## Story 1 — SSIS Performance Improvement (Riverside Pharmacy)

**Use for:** Setback or challenge · Technical problem-solving · Quantified achievement · SQL / data work

**JD tags:** `sql` `data-transformation` `performance` `legacy-systems` `problem-solving` `ownership` `documentation`

**last_used:** April 2026
**used_for:** Actalent — Software Developer

**Situation:**
The drug data transformation process at Riverside Pharmacy was manually run during the day by a developer — a deliberate operational choice because of the risk of data quality issues or system failures. The process took 8 hours, blocking the team from using updated data until mid-morning the next business day. I wanted this issue resolved without changing the source data format or the downstream systems consuming the output.

**Task:**
I was responsible for diagnosing and fixing the process end-to-end, within those constraints.

**Action:**
I investigated the manual process processing to identify what steps could be automated. I rewrote the transformation logic using T-SQL and Regular Expressions, restructured the execution order, and ran parallel streams where the data allowed it. I tested each change in isolation before integrating and documented the approach throughout.

**Result:**
Processing time dropped from 8 hours to 1 hour — a 7x improvement. The team had usable data in the afternoon of the same business day. The solution was documented and used as a reference for subsequent SSIS work at the company. I had additional time to devote to other high priority development tasks.

**Adapt when:**
- Role emphasizes Python data work → mention the analytical approach (profiling, isolating root cause) rather than SSIS specifics
- Role emphasizes ownership → lead with "I was given full ownership of the diagnosis and fix"
- Role emphasizes documentation → close with the documentation outcome more prominently

---

## Story 2 — Legacy Modernization (Fieldstone Benefits Administrators)

**Use for:** Project delivery · Legacy system work · Full-stack development · TDD · Documentation · Incremental delivery

**JD tags:** `asp-net` `angular` `csharp` `legacy-modernization` `tdd` `agile` `documentation` `api-development` `ci-cd` `incremental-delivery`

**last_used:** April 2026
**used_for:** Actalent — Software Developer

**Situation:**
The quote management system at Fieldstone Benefits Administrators was built on legacy ASP.NET Web Forms. It was slow, difficult to maintain, and unable to support the new features the business needed. A concurrent WinForms application also needed to stay live during the transition.

**Task:**
I was part of a team that developed the API layer and front-end component development for the modernized system, working in a small team of 6 under a defined timeline.

**Action:**
I built the ASP.NET Core Web API with C# and EF Core, implemented JWT authentication, and developed Angular 12 components with TypeScript and RxJS. I added testing elements using xUnit and Moq. We managed our own branches in GitLab CI/CD deployments, and documented the system in Confluence as I built it.

**Result:**
The modernized system was delivered incrementally with minimal disruption. The new architecture was significantly easier to extend.

**Adapt when:**
- Role emphasizes Angular specifically → lead with front-end component work and TypeScript/RxJS depth
- Role emphasizes API design → lead with the ASP.NET Core Web API and JWT implementation
- Role emphasizes CI/CD → emphasize GitLab pipeline management

---

## Story 3 — Stakeholder Scope Creep (Aerotech Industries)

**Use for:** Working with different perspectives · Stakeholder communication · Handling requirement changes · Collaboration under pressure

**JD tags:** `collaboration` `stakeholder-communication` `requirements-analysis` `agile` `people-skills` `conflict-resolution`

**last_used:** April 2026
**used_for:** Actalent — Software Developer

**Situation:**
I was building an integration between Microsoft Dynamics 365, SharePoint and HubSpot at Aerotech Industries. Midway through, a business stakeholder added additional requirements that required changes to the integration web service.

**Task:**
I needed to either push back on the change or find a way to accommodate it without compromising the current timeline.

**Action:**
I asked for a short meeting with manager — not to argue, but to understand the business reason behind the change and discuss the impact on the schedule. It turned out the requirement was driven by a process change resulting from my manager previewing the integration. I documented the decision and the rationale in the technical notes, updated the test cases.

**Result:**
The integration schedule was extended. When the stakeholders got to use the integration they were happy with the additional requirements which better meet their needs.

**Adapt when:**
- Role emphasizes communication → lead with the decision to call the meeting rather than respond in writing or work around the problem silently
- Role emphasizes documentation → close with how the documented decision prevented confusion later
- Role is startup/informal → can be told more conversationally, less formally

---

## Story 4 — Learning New Technology Quickly (Aerotech Industries)

**Use for:** Learning curve · Fast ramp · New technology · Adaptability · Self-directed learning

**JD tags:** `adaptability` `fast-learner` `self-motivated` `power-platform` `office365` `stakeholder-communication`

**last_used:** April 2026
**used_for:** Actalent — Software Developer

**Situation:**
When I joined Aerotech Industries, I was asked to build a quality control tracking application using Power Platform Canvas Apps — a technology I had not worked with before. The business team was already waiting and the timeline was fixed.

**Task:**
I needed to deliver a working application in an unfamiliar technology within a defined timeline, with no option to defer while getting up to speed.

**Action:**
I spent the first three days in structured learning: Microsoft documentation, tutorials, and hands-on experimentation in a sandbox. I found one person internally with Power Platform experience and asked for a focused session — "What are the three things I most need to know that the documentation does not tell me?" I built a working prototype by end of week one and iterated from stakeholder feedback.

**Result:**
The application was delivered on time. It integrated Power Automate workflows with SharePoint and M365 in ways the business had not previously used, and it became the template for two subsequent Power Platform projects at the company.

**Adapt when:**
- Role emphasizes Python ramp-up → frame with "nine structured Pluralsight courses plus a portfolio project"; be explicit this is course-level, not production-employed
- Role is highly technical → emphasize the structured/methodical approach (sandbox first, targeted expert question)
- Role emphasizes self-motivation → lead with "I did not wait to be onboarded — I started learning on day one"

---

## Story 5 — T-SQL Automation / SDLC Documentation (Vantage Technology Solutions)

**Use for:** Process automation · Documentation · SDLC · Agile delivery · Scale / throughput improvement

**JD tags:** `sql` `automation` `documentation` `agile` `sdlc` `analysis` `process-improvement` `scripting`

**last_used:** —
**used_for:** —

**Situation:**
At Vantage Technology Solutions, the SQL data patch deployment process was manual and could only handle one patch per day. The business needed significantly more throughput as the product scaled.

**Task:**
I was asked to automate the deployment process as part of my SDLC responsibilities, while also maintaining UML documentation and multi-environment deployment coordination.

**Action:**
I wrote Unix shell scripts that automated the SQL patch deployment pipeline end-to-end using T-SQL. I mapped the existing process first, identified the manual steps that could be scripted safely, and built in error handling so failed patches would not silently cascade. I documented the automation approach and produced UML models of the updated data flows.

**Result:**
Deployment capacity increased from 1 patch per day to 20 patches per day. The documentation was used by the team for the remainder of my tenure and cited during onboarding for new developers.

**Adapt when:**
- Role emphasizes DevOps/automation → lead with the 20x throughput improvement and the scripting approach
- Role emphasizes documentation → lead with the UML models and how they enabled team continuity
- Role emphasizes analysis → lead with the process mapping phase before automation

---

## Story Selection Guide

| Question type | First choice | Backup |
|---|---|---|
| Setback / challenge | Story 1 (SSIS) | Story 5 (Vantage automation) |
| Project delivery / ownership | Story 2 (Fieldstone Benefits Administrators) | Story 1 (SSIS) |
| Collaboration / conflict | Story 3 (Aerotech Industries) | — |
| Learning quickly / new tech | Story 4 (Power Platform) | Story 2 (Fieldstone Benefits Administrators — parallel legacy) |
| Documentation / communication | Story 5 (Vantage) | Story 2 (Confluence) |
| SQL / data work | Story 1 (SSIS) | Story 5 (Vantage T-SQL) |
| Legacy modernization | Story 2 (Fieldstone Benefits Administrators) | Story 1 (Riverside Pharmacy migration) |
| Stakeholder / people skills | Story 3 (Aerotech Industries) | Story 4 (Power Platform feedback loop) |
| Python-specific | Story 4 (adapted — see Adapt when) | — |
| Process automation / scripting | Story 5 (Vantage) | Story 1 (SSIS restructuring) |

---

## Adding New Stories

When generating a story not covered above, use this template, then append to this file:

```markdown
## Story N — [Short label] ([Employer])

**Use for:** [Question types]
**JD tags:** `tag1` `tag2` `tag3`
**last_used:** [Date added]
**used_for:** [Company — RoleShortTitle]

**Situation:** ...
**Task:** ...
**Action:** ...
**Result:** ...
**Adapt when:** ...
```

Tag format: lowercase, hyphenated, matches JD requirement vocabulary.

---

## Maintenance Notes (June 2, 2026)

- Stories 1–4 last used April 2026 in Actalent application
- Story 5 (Vantage automation) remains unused; valid backup for DevOps / automation roles
- When using stories in new applications: update `last_used` date and append company + role to `used_for` field
- Consider rotating stories: avoid repeating same story in 2 consecutive applications

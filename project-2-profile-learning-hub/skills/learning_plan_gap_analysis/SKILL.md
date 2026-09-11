---
name: learning-plan-gap-analysis
description: >
  Generates a prioritised learning plan PDF from a completed gap analysis.
  Use whenever the user asks for a learning plan, study plan, or course list
  after a gap analysis has been produced — or asks "what should I study for
  this role", "what courses do I need", "create a learning plan", or "how do
  I close these gaps." Always use after a gap analysis — do not generate ad hoc.
  Output is a PDF with clickable links. If no genuine gaps exist, produce an
  interview readiness plan instead.
---

# Learning Plan — Gap Analysis Skill

Converts a gap analysis into a phased PDF learning plan with verified clickable
links. Sources: Pluralsight · Microsoft Applied Skills (free) · Microsoft Learn.

> **Upstream input:** This skill consumes gap analyses from `gap-analysis-job-description`. Fit ratings (Strong/Good/Stretch/Pass) from the gap analysis determine which plan type is generated and how priorities are assigned.
> **Before selecting courses:** Load `course-urls.md` (project root) — verified
> slugs by gap type. Do not guess slugs; search if a course isn't listed.
> **Before generating PDF:** Write a role config `roles/[role-slug].json`
> (copy `roles/_example.json` as a starting point) and run
> `python pdf-template.py roles/[role-slug].json`. The old copy-and-fill
> Python workflow has been retired.

---

## Inputs

1. **Gap analysis** — markdown from `gap-analysis-job-description` skill, or
   pasted gaps. If missing: "I need the gap analysis first."
2. **Job context** — role title + company (from gap analysis header).
3. **Active application?** — yes = Priority 1 urgency increases.

---

## Step 1 — Classify Plan Type

Consult the fit rating from the gap analysis output:

- **Fit rating is Strong or Good** (all required skills ✅ or 🟡; ≤ 1–2 gaps in nice-to-haves) → Standard phased plan (Priority 1 / 2 / 3)
  - Strong fit: focus on nice-to-have depth (Priority 2–3)
  - Good fit: close 1–2 gaps before phone screen (Priority 1–2)
- **Fit rating is Stretch or Pass** (1–2 or more required skills are 🔴) → Accelerated Priority 1 plan; close critical gaps before applying
- **No genuine gaps** (Strong fit, framing gaps only) → Interview Readiness plan

---

## Step 2 — Assign Priorities

| Priority | What | Complete by |
|---|---|---|
| 1 | 🔴 Genuine gaps; critical must-haves with zero coverage | Before applying |
| 2 | 🟡 Framing gaps; course-level skills; important nice-to-haves | Before tech screen |
| 3 | Differentiators; interview depth; elevates good to exceptional | Before final round |

Rules: active application → P1 within 1–2 weeks · AI-200 domain gaps → P2/P3 (exam live but no imminent deadline) · resolved resume gaps → P2/P3 (vocabulary only, not P1).

**Mapping from gap analysis fit rating:**
- Gap analysis "**Pass**" → All Priority 1 (strongly recommend rethinking the application or committing to major reskilling)
- Gap analysis "**Stretch**" → Priority 1 for must-haves; Priority 2 for nice-to-haves
- Gap analysis "**Good**" → Priority 1 for must-haves with gaps; Priority 2–3 for nice-to-haves
- Gap analysis "**Strong**" → Priority 2 for framing gaps; Priority 3 for differentiators

---

## Step 3 — Select Courses

Load `course-urls.md` (project root). Match each gap to the best source:

| Gap type | Source |
|---|---|
| Genuine gap (new topic) | Pluralsight Getting Started/Fundamentals |
| Framing gap (depth) | Pluralsight Deep Dive/Best Practices/Advanced |
| Azure hands-on gap | Pluralsight course + Applied Skills lab |
| AI-200 domain | Pluralsight + Applied Skills + Microsoft Learn |

If a course isn't in `course-urls.md`, use `web_search` to verify the slug
before including it. Never guess a Pluralsight slug.

---

### Duration lookup — `hrs` field in course cards and Summary table

Use this lookup order before writing any `hrs` value. Never leave `hrs` blank or write "FILL hrs".

1. **Check `pluralsight-courses.md`** — if the course row has a Duration value (not `—`), use it directly
2. **Check `course-urls.md`** — if the course row has a Duration value (not `—`), use it directly
3. **Run `python project-2-profile-learning-hub/scripts/query_learning_history.py lookup "[course title]"`** — never load `data/pluralsight_learning_history.json` (~44K tokens) directly just to check one course's timing
4. **`web_search site:pluralsight.com "[course title]"`** — required for any course where Duration is `—` (Short Course or Lab entries) or NOT FOUND anywhere above; read the course page for the actual duration
5. Use `~X hrs` estimate **only** if none of the above resolve after a search attempt

**`timing_profile` guide:**
- `Full Course` · `Full Lab` → Duration is reliable; use directly (no web search needed)
- `Short Course` · `Lab` → Duration is `—`; must web_search for the actual value before writing `hrs`

---

## Step 4 — Generate the PDF

```bash
pip install reportlab --break-system-packages -q
```

1. Create (or update) `roles/[role-slug].json` from `roles/_example.json`
2. Fill the JSON fields (banner, legend, plan, key_links, footer) per the
   schema documented in `project-2/CLAUDE.md`
3. Run: `python pdf-template.py roles/[role-slug].json`
4. Tell the user the PDF's path under `outputs/` (the value comes from the
   JSON's `output` key)

File naming: `[Company]_[RoleShortTitle]_LearningPlan.pdf` (this is the
value of `output` inside the JSON, not derived from the filename).

### Certification urgency

Read current status from `profile-facts.md` (or
`python project-1-application-engine/scripts/extract_bundle_sections.py section "Cert Registry"`
— don't load the full ~11.5K-token `app-engine-bundle.md` just for this)
at generation time rather than assuming the row below is still accurate — a cert shown
here as "in progress" may since have been passed, and the row must change accordingly:

| Cert | Deadline | Action |
|---|---|---|
| AZ-900 | Passed April 18, 2026 | Note in plan header as complete |
| AI-200 | Live July 2026 | Phase 2/3 for Azure roles; no imminent deadline — **if the bundle shows this cert as passed, replace this row with "Note in plan header as complete" instead** |

---

## Step 5 — Present and Summarise

After stating the output path, give a 4–5 sentence inline summary:
item count · total hours · Priority 1 ask · any time-sensitive deadline ·
what to do first.

---

## Plan Formats

### Standard Plan sections (in order)
Banner → legend → About This Plan → course cards by phase → Quick Reference Table → Key Links → footer

### Interview Readiness Plan sections
Banner → legend → About This Plan → Before Phone Screen → Before Tech Screen →
Before Final Round → STAR Story Prep → Quick Reference Table

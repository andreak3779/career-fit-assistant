# Coverage Rubric — Certification Learning Plans

Reference for the `cert-learning-plan` skill. Defines how to score domain coverage
and assign phases when building a certification learning plan.

---

## Coverage Scoring

| Rating | Criteria |
|---|---|
| ✅ Strong | Completed full course(s) covering this exact service/topic; or prior production experience confirmed in `profile-facts.md` |
| 🟡 Partial | In-progress course (>10%), short course, a lab but no lecture depth, or course-level-only coverage |
| 🔴 Gap | No course, no lab, no MS Learn module on this specific service or skill |

**Scoring rules:**

- Check `pluralsight-courses.md` by course title and topic keywords
- Check `data/ms-learn-courses.md` for learning path or module match
- In-progress course ≥50% = 🟡; <50% = 🔴 unless it has a follow-on lab
- "Deep Dive"/"In-depth" course in progress at any % = 🟡 (enough to close with completion)
- Azure fundamentals (AZ-900 path, broad architecture) ≠ service-specific implementation coverage — do not use it to satisfy specific service bullets

---

## Phase Assignment

| Phase | Colour | What goes here | Complete by |
|---|---|---|---|
| 1 | 🔴 RED | 🔴 Gap domains with zero coverage; highest-weight domains first | Immediately — before exam |
| 2 | 🟡 AMBER | 🟡 Partial — in-progress courses to finish; key service gaps with some overlap | Before exam date |
| 3 | 🟢 GREEN | Exam-aligned official review content; nice-to-have differentiators; practice assessment | Final week before exam |

**Ordering rules within a phase:**

- Phase 1: sort by domain weight (heaviest gap first)
- Phase 2: in-progress completions first (quick wins), then new-start gaps
- Phase 3: always include the official Microsoft Learn course (e.g. AI-200T00-A or equivalent) if one exists

**Always exclude from the plan:**

- Courses with ✅ Strong coverage in `pluralsight-courses.md` (already done)
- Certs already passed (note in "About This Plan" text instead)
- Any course where `timing_profile` is `Full Course` and progress = 100%

---

## Provenance Note

This file was reconstructed from the coverage-scoring and phase-assignment logic
already embedded inline in `cert-learning-plan-SKILL.md` (Steps 3–4), after the
original standalone `coverage-rubric.md` was found to be missing with no
recoverable copy. It does not add any rules beyond what the skill already
specified — it simply extracts that logic into its own file so the skill's
`references/coverage-rubric.md` pointer resolves. If a richer original version
existed with additional detail, this file should be replaced with it.

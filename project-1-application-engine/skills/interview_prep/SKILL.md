---
name: interview-prep
description: >
  Generates a tailored, role-specific interview preparation DOCX for Sarah
  Ashford. Use whenever the user says "interview prep", "prepare me for an
  interview", "I have an interview", "help me prepare for", "create an interview
  guide", "get me ready for this role", or shares a recruiter briefing alongside
  a job description. Also trigger when the user says "what should I study before
  my interview", "how do I prepare for this", or asks how to answer questions for
  a specific role. Also trigger when the user mentions an interview date or says
  "I have an interview next week / tomorrow / on [date]". Always use this skill —
  do not handle interview prep ad hoc. Requires a job description; recruiter
  briefing is optional but must be explicitly requested if not provided. Output:
  a single DOCX file sized to the interview stage.
---

# Interview Prep Skill

Generates a tailored interview preparation DOCX from a job description,
optional recruiter briefing, and Sarah's resume and profile facts.
Output length scales to the interview stage (phone screen → lean; final round → full).

> **Generated deterministically by the script — don't build the DOCX by
> hand.** Run `python -m cli.career_fit_api interview-prep <jd_path> [flags]`
> (backed by `interview_prep.py`, which builds the entire document —
> banner, tables, shading, borders, everything — from the profile bundle
> plus whatever optional content files you pass it). See Step 7 for the
> full invocation once all the optional inputs below are ready.
>
> **Source files — load before Step 2:**
> - `app-engine-bundle.md` — work history, bullets, contact info, and career
>   facts you'll draw on for Company Research framing, the four LLM-authored
>   Q&A categories, and Questions to Ask (auto-load)
> - `gap-coaching.md` — read for your own awareness only. The script itself
>   auto-loads this file and attaches a matching entry's own wording to its
>   own grounded-evidence Q&A cards — you no longer manually embed those
>   callouts. Read it anyway so anything you author in Step 4 stays honest
>   about the same gaps instead of contradicting the script's auto-attached
>   notes.
> - `star-bank.md` — only load this if Step 5 needs you to author a
>   brand-new story; the script selects and renders existing stories
>   automatically, so you don't need to load this for a normal run.
> - `recruiter-briefing-template.md` — template to send the recruiter if no
>   briefing was provided
>
> **If any of the above files are not visible in context:** pause and tell the user
> exactly which file is missing and that it needs to be added to the project before proceeding.
>
> **File naming:** `{company_slug}_{title_slug}_InterviewPrep.docx`, written
> to `outputs/`. Tell the user the file path.
>
> **Grounding rule:** every employer, project, course, or metric named in Q&A
> answers and STAR stories must trace to `app-engine-bundle.md` or `star-bank.md`.
> Never invent a project detail, number, or outcome to make an answer sound
> stronger — if the evidence isn't there, frame it as a genuine gap instead
> (see Step 2's gap-coaching awareness).

---

## Inputs

| Input | Required | How to get it |
|---|---|---|
| Job description | ✅ Yes | Pasted text, `.md` file, or URL (`web_fetch` if URL). If it isn't already a file, save it to one — the script takes a JD file path, not inline text. |
| Interview stage | Optional | Ask if not stated: Phone Screen / Technical Screen / Final Round. Default: Technical Screen. Passed as `--stage`. |
| Recruiter briefing | Optional | Ask explicitly: "Do you have any notes from the recruiter?" If no: generate the template from `recruiter-briefing-template.md` and offer it to send. If yes: write it to a temp `.md` file and pass `--recruiter-briefing`. |
| Company research | ✅ Auto (LLM) | `web_search` in Step 3; write findings to a temp `.md` file and pass `--company-research`. |
| Anticipated Questions — 4 LLM categories | ✅ Auto (LLM) | Compose in Step 4 as JSON; write to a temp file and pass `--qa-cards`. The script supplies its own grounded-evidence category automatically. |
| Salary / Negotiation | Optional, Final Round only | Compose in Step 6; write to a temp file and pass `--salary-section`. Ignored with a printed warning at any other stage. |
| Resume / profile facts | ✅ Auto | The script loads the profile bundle itself for the document's real content; you separately read `app-engine-bundle.md` in Steps 1–2 to keep your own authored content grounded and gap-aware. |
| Experience Match table, STAR stories | ✅ Auto | Generated deterministically by the script — you don't compose or select these. |

---

## Step 1 — Parse Inputs

**From the JD extract:**
- Job title · company name · role type
- Must-have requirements — flag anything marked required / essential / must / strong
- Nice-to-have requirements
- Key responsibilities — what will this person actually do day-to-day
- Tone — enterprise/formal vs. startup/casual
- Red flags — explicit disqualifiers, hard experience limits

**From the recruiter briefing (if provided) extract:**
- Interview format — technical, behavioural, panel, coding test, etc.
- Focus areas the recruiter explicitly called out
- Logistical notes — number of rounds, interviewers, timing
- Any specific topics, projects, or themes they flagged
- Instructions the recruiter gave (STAR method, questions to ask, etc.)

**Save the JD to a file.** `interview-prep` takes a JD file path as its
positional argument, not pasted text — if the JD arrived as pasted text or a
URL fetch, write it to a temp `.md` file before Step 7.

**Stage selector — determine document scope:**

| Stage | `--stage` value | STAR stories rendered | Salary section |
|---|---|---|---|
| Phone Screen | `phone_screen` | 2 | never |
| Technical Screen (default) | `technical_screen` | up to 5 | never |
| Final Round | `final_round` | up to 5 | rendered if `--salary-section` supplied |

All other sections (Recruiter Briefing, Company Research, Experience Match,
Anticipated Questions) render at every stage whenever their content is
supplied — stage only gates STAR story count and Salary/Negotiation
eligibility. Actual page count is an emergent property of how much real
prose you supply for Company Research, Q&A, and Salary — it isn't
script-controlled.

---

## Step 2 — Build Your Own Experience Match View (orientation only)

Load `app-engine-bundle.md`. For each must-have and nice-to-have requirement,
privately assign a status so the content you author later stays consistent
with the real gaps:

| Status | Meaning |
|---|---|
| ✅ Strong Match | Production experience in resume |
| 📚 Learning / Portfolio | Pluralsight or GitHub project — no production employment use (you have seen this; may need to study or frame) |
| 🔴 Genuine Gap | Not present in resume, portfolio, or coursework (prepare honesty + willingness to learn) |

**Note:** the DOCX's actual Experience Match table is generated
automatically by the script, from the same fit-rating logic
(`shared/fit_engine.py`) the rest of this project uses — you don't type this
table into the document. This pass is for your own orientation only, so
that Company Research framing, the Q&A you author in Step 4, and Questions
to Ask in Step 6 don't contradict what the table actually says.

Rules:
- Never re-flag resolved gaps from `app-engine-bundle.md` — those are always ✅
- Check the portfolio section of `app-engine-bundle.md` before assigning 🔴
- Be honest — do not soften 🔴 to 📚

**Gap-coaching awareness:** the script auto-loads `reference/gap-coaching.md`
and, for any required skill with a matching entry, uses that entry's own
"what to say" wording as the Q&A answer, its "what not to say" list as the
Tip line, and its honest floor / best STAR bridge as an amber gap-note
callout — directly on its own grounded-evidence card. You no longer
manually build these callouts. Read `gap-coaching.md` yourself anyway so
anything you author in Step 4 stays honest about the same gaps rather than
contradicting the script's auto-attached notes for that skill.

---

## Step 3 — Company Research (web search)

Use `web_search` to find current information — do not rely on training data.

Run these searches:
1. `[Company name] about mission values [current year]`
2. `[Company name] recent news [current year]`
3. `[Company name] clients industries served`

From the results, write a pre-populated company research section covering:
- What the company does and who they serve (2–3 sentences)
- Relevant recent news or initiatives worth mentioning in the interview
- Any client-site or placement structure notes (relevant for staffing firms)
- 1–2 specific facts Sarah can reference to show genuine preparation

Do not use placeholder text like "visit their website." Give actual content.

**Write the result to a temp `.md` file** (e.g. `outputs/company-research-tmp.md`)
and pass it via `--company-research <path>` in Step 7. If you have nothing
genuine to say, omit the flag entirely — the script renders no placeholder
text when it's absent, and that should stay true.

---

## Step 4 — Generate the Four LLM Q&A Categories

The script generates its own grounded-evidence Q&A category automatically
(the gap-coaching-enriched cards from Step 2). You compose the other four
categories. Tailor every question and answer to the specific JD and
company — no generic responses.

### Categories

**Resume Walkthrough & Career Goals**
- Walk me through your background
- Career goals / where do you want to be
- What are your expectations out of this role

**Project Deep-Dives** (always include)
- Tell me about a specific project — tools, responsibilities, deliverables
- Any role-specific technology deep-dive (derive from JD must-haves)
- Legacy modernization question (if JD mentions it)

**Engineering Judgment**
- How do you think about code quality and improvements
- When do you raise a concern vs. go with the team's approach

**Collaboration & Communication**
- Working with someone whose perspective differs from yours
- Communicating technical concepts to non-technical stakeholders

**Situational** — derive from the JD's key responsibilities:
- Concurrent projects mentioned → prioritization question
- New-to-team context → taking over someone else's work
- Fast learning emphasized → learning something new quickly
- Setbacks/challenges → handling failure or difficulty

### Answer format rules
- Write answers in Sarah's voice — first person, direct, no filler phrases
- Every answer must cite a specific employer, project, or course — no vague generalities,
  and no employer/project/course that isn't actually in `app-engine-bundle.md`
- Include a `tip` on any answer where phrasing or framing matters
- Answers referencing STAR stories must name the specific story title and scenario
- For any answer touching a gap you saw in Step 2, stay consistent with the
  script's own gap-coaching wording — don't contradict it

### Output shape

Write your cards as a JSON array to a temp file:

```json
[
  {"question": "...", "answer": "...", "tip": "...", "category": "resume_walkthrough"}
]
```

`question` and `answer` are required on every entry; `tip` and `category`
are optional. A missing `question` or `answer` makes the script raise and
write nothing — fail closed, no partial document. Pass the file via
`--qa-cards <path>` in Step 7; these cards render after the script's own
grounded-evidence cards, in the order you supply them.

---

## Step 5 — STAR Stories

The script selects and renders STAR stories automatically — ranked by
JD-tag overlap against the story pool in the profile bundle, count gated by
stage (2 for Phone Screen, up to 5 otherwise). You don't select, adapt, or
format an existing story yourself.

**To record that this run used them:** pass `--update-star-bank` in Step 7.
It writes updated `last_used`/`used_for` metadata back to the real
`reference/star-bank.md` for every story the script actually selected —
this is the only way stories get written back now; there's no more manual
"append this to star-bank.md" step for an existing story. It prints a diff
of the change to stdout — relay that in your inline delivery summary.
(`--star-bank-path` overrides the target file; use it only for a test/tmp
copy, never for a real run.)

**If the JD needs a story type not in the bank:** the script never invents
S/T/A/R prose — a genuinely new story still needs you to write it. Author
it yourself (Situation/Task/Action/Result, grounded in
`app-engine-bundle.md`), then add it to `reference/star-bank.md` **by hand**,
following the existing story format. `shared/star_bank_writer.py` has an
append mode built for exactly this (`new_story`), but it isn't wired into
the CLI yet — there is no `--new-star-story` flag to do this for you.
Tell the user you added a new story to the bank by hand.

---

## Step 6 — Questions to Ask + Salary / Negotiation

Produce 6–9 questions across three categories:
- **About the work** — backlog process, modernization approach, technical challenges
- **About the team** — code review, onboarding, stakeholder interaction model
- **About growth** — scope expansion, professional development support

Rules:
- All questions must be specific to this role and JD — no generic questions
- No logistics questions (pay, hours, benefits, schedule)
- Flag exactly 2 as ★ Must Ask — the ones most likely to impress and signal genuine preparation

**Delivery:** the script has no DOCX section for Questions to Ask — there's
no flag to pass this content through. Present these questions to the user
directly in your response (and in the inline summary), not embedded in the
generated document.

**Final Round only — Salary / Negotiation section:**
If stage is Final Round, compose:
- Winnipeg / remote CAD salary target range for this role type (use web search to verify current rates)
- Contract rate equivalent if relevant
- 3–4 negotiation tips specific to Sarah's differentiators (certs, SSIS story, legacy modernization depth, GitHub Copilot)
- When to raise compensation (only after an offer, not in screening)

Write it to a temp `.md` file and pass it via `--salary-section <path>` in
Step 7. The script only renders this section when `--stage final_round` —
supplied at any other stage, it prints a warning and skips the section
instead of erroring, so there's no point composing it for Phone Screen or
Technical Screen runs.

---

## Step 7 — Generate, Validate, and Deliver

Run the script now that the JD file and any temp content files from Steps
3, 4, 5, and 6 exist:

```bash
python -m cli.career_fit_api interview-prep <jd_path> \
  --stage <phone_screen|technical_screen|final_round> \
  --company-research <path>          # optional, Step 3
  --recruiter-briefing <path>        # optional, from Inputs
  --qa-cards <path>                  # optional, Step 4
  --update-star-bank                 # optional, Step 5
  --salary-section <path>            # optional, final_round only, Step 6
  --out outputs/<Company>_<Role>_InterviewPrep.docx
```

Omit any flag whose content you don't have — the script never fabricates a
substitute.

No automated DOCX validator is available locally (the sandbox's
`/mnt/skills/public/docx/scripts/office/validate.py` doesn't exist in
Claude Code). The script owns all DOCX assembly and visual mechanics —
banner, tables, shading, borders — so open the file and confirm the
**content you supplied** landed correctly and in the right place: Company
Research prose reads as real findings (no placeholders), the recruiter
briefing callout matches what was provided, the four LLM Q&A categories
appear after the script's own grounded-evidence cards, and — Final Round
only — the salary section is present with real figures.

Fix any errors before presenting. Then tell the user the file's path under
`outputs/`.

**Inline summary after delivery (5–6 sentences):**
- Stage and which optional sections were included
- Which STAR stories the script selected and what question types they cover
- Any new STAR story you wrote and appended to `star-bank.md` by hand
- Whether `--update-star-bank` was used and what it changed (relay the diff)
- Any gaps and the coaching approach the script auto-attached for each
- Company research sources used
- Questions to Ask (since they're not in the document) and the salary section status (Final Round only)

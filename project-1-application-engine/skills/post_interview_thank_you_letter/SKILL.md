---
name: post-interview-thank-you-letter
description: >
  Generates a thank-you letter to send after a job interview. Use whenever the
  user says "write a thank you letter", "post-interview thank you", "thank you
  note after interview", "follow up after my interview", or has just finished
  an interview and wants to follow up with the interviewer(s). Meant to be sent
  within 24 hours of the interview. Requires interview-specific details (who,
  when, what was discussed) that cannot be derived from app-engine-bundle.md —
  always ask for them if not already provided. Output: one DOCX file.
---

# Post-Interview Thank You Letter

Creates a short thank-you letter referencing the specific interview, as a DOCX
file. Shortest of the four letter types in this project.

> **Generated deterministically — don't build it by hand or fill a template.**
> Run `python -m cli.career_fit_api generate-thank-you --company "..." --role
> "..." --interviewer "..." --date "..." --discussion-point "..."
> [--discussion-point "..."]` (backed by `generate_thank_you_letter.py`,
> which pulls contact info from `outputs/profile-bundle.json` directly). No
> JD file is needed — this letter is about a specific conversation that
> already happened, not a posting.
>
> **Grounding rule (enforced by the script, not just documentation):**
> `--discussion-point` is required — the script refuses to generate without
> at least one. KEY TAKEAWAYS must come from the user's actual account of
> the interview; there is no honest generic substitute, so **always ask**
> if the user hasn't supplied real discussion points yet — don't invent one
> and don't skip straight to generation.
> **Layout** (only if debugging spacing): `docx-layout.md`

---

## Inputs

Ask for anything not already provided:

- **Interviewer name(s)** — drives the salutation (defaults to "Hiring Team" if truly unknown)
- **Company** and **role** interviewed for
- **Interview date**
- **1–2 specific discussion points** (required) — a topic, question, or detail from the actual conversation. Keep asking until you have at least one; do not proceed with generic differentiators as a stand-in.

---

## Step 1 — Generate the Letter

Run:

```bash
python -m cli.career_fit_api generate-thank-you \
  --company "[Company]" \
  --role "[Role]" \
  --interviewer "[Name]" [--interviewer "[Name 2]" ...] \
  --date "[Interview Date]" \
  --discussion-point "[Point 1]" [--discussion-point "[Point 2]"]
```

The script builds the opening (naming the interviewer(s) and date), the
Re: line, KEY TAKEAWAYS (your discussion points, verbatim), an optional
one-sentence reinforcement if grounded required-skill evidence exists, and
the closing. If it prints a low-evidence warning to stderr, surface that to
the user — the letter still stands on the real discussion points, but flag
it for review.

If the script exits non-zero because `--discussion-point` was omitted, that
means you skipped the "ask until you have at least one" step above — go
back and ask, don't retry with a fabricated point.

---

## Step 2 — Validate and Present

No automated DOCX validator is available locally (the sandbox's
`/mnt/skills/public/docx/scripts/office/validate.py` doesn't exist in Claude
Code). Open the generated file and visually confirm formatting before
delivering it.

The script names the file `SarahAshford_ThankYou_<Company>.docx` under
`outputs/` automatically (pass `--out` to override). Confirm the file's path
and tell the user.

**Timing note:** remind the user this letter is meant to be sent within 24
hours of the interview. If a platform requires plain text instead of a DOCX
attachment (e.g. pasting into an email body), open the DOCX and copy the
text — Carlito and standard headings survive copy-paste well, same
convention as documented in `fullstack-net-profile-resume-SKILL.md`'s
Platform Upload Notes.

Inline summary: discussion points used · any low-evidence warning from Step 1
· assumptions made (e.g. interviewer name defaulted to "Hiring Team").

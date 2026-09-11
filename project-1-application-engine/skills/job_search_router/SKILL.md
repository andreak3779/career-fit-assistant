---
name: job-search-router
description: |
  Delegates to the monorepo CLI (`python3 -m cli.career_fit_api <subcommand>`):
  - `fit-check <jd>` for a quick fit rating
  - `gap-analysis <jd>` for a full gap report
  - `generate-resume <jd>` / `generate-cover-letter <jd>` for documents
  - `interview-prep <jd>` for interview prep
  Use whenever the user asks how to handle a job opportunity and route it to
  the right action.
---

# Job Search Router

Route the user's intent to one of the monorepo CLI commands.

- **Quick yes/no fit** → `python3 -m cli.career_fit_api fit-check <path/to/jd.md>`
- **Detailed gap analysis** → `python3 -m cli.career_fit_api gap-analysis <path/to/jd.md> --out outputs/..._GapAnalysis.md`
- **Tailored documents** → `python3 -m cli.career_fit_api generate-resume <path/to/jd.md> --company Company` and `python3 -m cli.career_fit_api generate-cover-letter <path/to/jd.md> --company Company`
- **Interview prep** → `python3 -m cli.career_fit_api interview-prep <path/to/jd.md>`

Before routing to tailored documents, confirm this isn't a repeat cold application to the same posting — the `create-a-cover-letter-and-tailored-resume-for-job-description` skill's Step 0a gate covers this if you hand off there, but a direct CLI route bypasses that gate, so ask here instead.

Run commands from the repository root:

```bash
python3 -m cli.career_fit_api <command> ...
```

Then summarize the generated output for the user and state the file paths.

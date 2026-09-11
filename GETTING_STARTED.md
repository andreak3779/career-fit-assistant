# GETTING STARTED(1)         User Commands          GETTING STARTED(1)

## NAME

**GETTING STARTED** — quick-start guide for the `career-fit-assistant` monorepo CLI

## SYNOPSIS

```bash
python3 -m cli.career_fit_api <command> [options]
```

## DESCRIPTION

`career-fit-assistant` is a deterministic job-search automation toolkit.  It bundles
profile and presence data, validates the generated artifacts, and produces
tailored job-application documents from a job description (JD) markdown file.

All commands are invoked through the package interface.  The CLI is not
registered as a console script, so run it with `python3 -m cli.career_fit_api`.

## SETUP

```bash
git clone <repo-url> career-fit-assistant && cd career-fit-assistant
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[docx,yaml,schema,pdf]"
python3 -m cli.career_fit_api build
```

The final `build` step is required once before any other command: it writes
`outputs/profile-bundle.json` and `outputs/presence-bundle.json`, which
every other command reads.  Those files are gitignored and do not exist
until `build` runs.

## COMMANDS

### Data management

`build`
    Rebuild the profile and presence bundles from the source files under
    `project-2-profile-learning-hub/` and `project-3-presence-identity/`.

`validate`
    Run canonical validation checks on the generated bundles and verify the
    alias registry shape.

### Fit analysis

`fit-check <jd>`
    Perform an inline fit check against a job-description markdown file.

`gap-analysis <jd> [--out <path>]`
    Generate a markdown gap-analysis report for the supplied JD.

### Presence generation

`generate-linkedin [--out <path>]`
    Generate LinkedIn profile copy.

`generate-github [--out <path>]`
    Generate GitHub profile README copy.

`generate-jobgether [--out <path>]`
    Generate Jobgether profile copy.

`generate-job-board [--out <path>]`
    Generate Indeed & ZipRecruiter profile copy.

`generate-pluralsight [--out <path>]`
    Generate Pluralsight profile copy.

### Application documents

`generate-resume <jd> [--company <name>] [--out <path>]`
    Generate a tailored resume as a DOCX file.

`generate-cover-letter <jd> [--company <name>] [--out <path>]`
    Generate a tailored cover-letter DOCX.

`generate-cold-call <jd> [--company <name>] [--out <path>]`
    Generate a short cold-call cover-letter DOCX.

`generate-job-site <jd> [--company <name>] [--out <path>]`
    Generate a short job-site cover letter.  The default output format is
    plain text; pass a path ending in `.docx` to produce a DOCX file.

`generate-thank-you <jd> [--company <name>] [--out <path>]`
    Generate a post-interview thank-you letter DOCX.

`interview-prep <jd> [--out <path>]`
    Generate interview-prep notes for the supplied JD.

## OPTIONS

`--company <name>`
    Override the company name used in the output filename.  Optional for all
text.

`--out <path>`
    Specify the output file path.  When omitted, commands use their own default
paths, typically under `outputs/`.

## EXAMPLES

Rebuild the profile and presence bundles:

```bash
python3 -m cli.career_fit_api build
```

Validate the repository artifacts:

```bash
python3 -m cli.career_fit_api validate
```

Generate a tailored resume for a job description:

```bash
python3 -m cli.career_fit_api generate-resume path/to/job_description.md
```

Generate a cover letter with an explicit company name and output path:

```bash
python3 -m cli.career_fit_api generate-cover-letter path/to/job_description.md \
    --company "Contoso Cloud Solutions" --out outputs/cover_letter.docx
```

Produce a short job-site cover letter as text:

```bash
python3 -m cli.career_fit_api generate-job-site path/to/job_description.md
```

Prepare for an interview:

```bash
python3 -m cli.career_fit_api interview-prep path/to/job_description.md
```

## ENVIRONMENT

Python 3.11 or later is required.  The package is defined in `pyproject.toml`
and can be installed in editable mode with `pip install -e ".[docx,yaml,schema,pdf]"`
(see SETUP above) — a bare `pip install -e .` installs no dependencies at all,
since `pyproject.toml` keeps them behind optional extras.

## FILES

`pyproject.toml`
    Package metadata, dependencies, and tool configuration.

`cli/career_fit_api.py`
    CLI entry point and subcommand dispatch.

`outputs/`
    Default destination for generated application documents.

`project-2-profile-learning-hub/`
    Source files used by the `build` and `validate` commands.

`project-3-presence-identity/`
    Source files used by the `generate-linkedin`, `generate-github`,
`generate-jobgether`, `generate-job-board`, and `generate-pluralsight`
commands.

## EXIT STATUS

`0`
    Command completed successfully.

`1`
    A validation or runtime error occurred.

## SEE ALSO

`README.md` for the project overview.

## AUTHOR

Sarah Ashford

## COPYRIGHT

MIT License

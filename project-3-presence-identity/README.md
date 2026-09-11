# Project 3 — Presence & Identity

Populated from the Presence & Identity project on 2026-07-07.

Handles LinkedIn, GitHub profile, and job board bio/presence updates for Sarah Ashford.
Consumes `presence-bundle.md` as the source of truth (also published in the `claude-projects` repo under `project-3-presence-identity/presence-bundle.md`).

## Contents

- `presence-bundle.md` — authoritative profile data (headline, summary, cert status, skills, portfolio, key differentiators), including a `## Copy Fragments` section of pre-formatted sentences (course counts, cert status) that downstream skills paste into draft copy instead of hardcoding a number
- `skills/update_linkedin_profile/SKILL.md` — LinkedIn profile field update skill (About section, Open to Work banner, Experience entry, Skills, Certifications, Courses, Featured links)
- `skills/update_github_profile/SKILL.md` — GitHub profile field update skill (bio, status, profile README, profile fields, pinned repos)
- `skills/update_job_board_profiles/SKILL.md` — Indeed & ZipRecruiter profile field update skill (headline, summary, skills, job preferences); also flags when the uploaded resume file is stale relative to the bundle, since both platforms lean on the parsed resume more than typed fields
- `skills/update_jobgether_profile/SKILL.md` — Jobgether profile field update skill (title, about/bio, skills, job preferences); same resume-freshness check as Indeed/ZipRecruiter, since Jobgether's match scoring leans on the uploaded resume too
- `skills/update_pluralsight_profile/SKILL.md` — Pluralsight public profile field update skill (bio/tagline, job title, location, links) — not a job board, but checked by recruiters alongside the resume/GitHub README
- `skills/update_linkedin_profile/scripts/generate_linkedin.py` — generates the full 8-step paste-ready LinkedIn draft (`linkedin-update-draft.md`) by reading `presence-bundle.md` directly and reusing `update_linkedin_profile/SKILL.md`'s own prose templates (fenced code blocks), so the script and the conversational skill can't drift apart; also writes a `<draft>.raw-inputs.json` sidecar with the untouched source data behind its two heuristic-derived sections (Step 3 portfolio hooks, Step 4 skills list), for an LLM caller to refine. Falls back to a thinner summary from `outputs/presence-bundle.json` only if `presence-bundle.md` is missing.
- `skills/update_github_profile/scripts/generate_github.py` — generates a GitHub profile README from `outputs/presence-bundle.json`
- `skills/update_jobgether_profile/scripts/generate_jobgether.py` — generates the Jobgether draft (`jobgether-profile-update-draft.md`: Title/Headline, About/Bio, Skills, Job Preferences, plus the resume-freshness check) the same way, reading `presence-bundle.md` and `update_jobgether_profile/SKILL.md`'s own templates
- `skills/update_job_board_profiles/scripts/generate_job_board.py` — same pattern for Indeed & ZipRecruiter (`job-board-profile-update-draft.md`)
- `skills/update_pluralsight_profile/scripts/generate_pluralsight.py` — same pattern for Pluralsight (`pluralsight-profile-update-draft.md`: Bio/Tagline, Profile Fields — the smallest of the five, no skills-derivation or resume check needed)

All five generators read `presence-bundle.md` directly and fill `{fragment_name}` placeholders from its Copy Fragments section, reusing each skill's own prose templates rather than a separate hardcoded copy — the shared parsing logic (section/fragment/table extraction) lives in `shared/bundle_markdown.py`, and the Jobgether/Indeed/ZipRecruiter resume-freshness check lives in `shared/resume_freshness.py`. `generate_github.py` is the one exception: it still reads the typed JSON bundle (`outputs/presence-bundle.json`) only, not `presence-bundle.md`. All five are also exposed as MCP tools (`generate_linkedin`, `generate_github`, `generate_jobgether`, `generate_job_board`, `generate_pluralsight` in `mcp_server/server.py`) that return the draft as a `text/markdown` `EmbeddedResource` — an attachment in MCP clients like Claude Desktop — rather than inline chat text.

## Current Cert Status

Per `presence-bundle.md`: AZ-900 certified (April 18, 2026); AZ-204 retired, not pursuing; AI-200 (Azure AI Cloud Developer Associate) is the active target, exam available July 2026.

> Note: `JobSearch_KeywordStrategy.md` is tracked under `project-1-application-engine/reference/` instead — it's job search strategy content, not presence/identity content.

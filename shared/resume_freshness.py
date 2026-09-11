"""Resume-freshness check shared by the Jobgether and Indeed/ZipRecruiter
profile-update generators.

Both platforms parse an uploaded resume DOCX into most of the candidate
profile, so their SKILL.md workflows open with a "check the resume isn't
stale before writing any field" step. This compares the resume file's own
mtime against the Project 2 source files it should reflect, using the same
mtime-based approach as
project-2-profile-learning-hub/scripts/check_bundle_freshness.py — stable
across a fresh `git clone` (checkout stamps every file with the same moment)
unlike comparing against a parsed `generated:` date string.
"""

from __future__ import annotations

from pathlib import Path

# The platform (fullstack_net_profile_resume skill) resume DOCX lives in a
# gitignored outputs/ folder, so it never ships with a fresh checkout and its
# exact filename is a local artifact, not a repo constant — glob for it
# instead of hardcoding one, so this module doesn't need to know (or embed)
# whatever name the resume happens to carry.
_RESUME_OUTPUT_DIR_PARTS = ("project-1-application-engine", "outputs")
_RESUME_GLOB = "*_Resume_*.docx"
_SOURCE_FILES = ["profile-facts.md", "Resume_Snapshot.md", "skills-summary.md"]


def _find_resume(root: Path) -> Path | None:
    resume_dir = root.joinpath(*_RESUME_OUTPUT_DIR_PARTS)
    if not resume_dir.is_dir():
        return None
    matches = sorted(resume_dir.glob(_RESUME_GLOB))
    return matches[-1] if matches else None


def resume_freshness_lines(root: Path) -> list[str]:
    """Human-readable report lines for a generated draft's "Resume File
    Dependency Check" section. Never raises if the resume or a source file
    is missing — the resume DOCX lives in a gitignored `outputs/` folder, so
    a fresh checkout legitimately won't have it yet.
    """
    resume_path = _find_resume(root)
    if resume_path is None:
        resume_dir = root.joinpath(*_RESUME_OUTPUT_DIR_PARTS)
        return [
            f"No resume file found matching `{_RESUME_GLOB}` under `{resume_dir}`.",
            "Run the fullstack_net_profile_resume skill to generate it before uploading.",
        ]

    resume_mtime = resume_path.stat().st_mtime
    stale: list[str] = []
    for name in _SOURCE_FILES:
        source_path = root / "project-2-profile-learning-hub" / name
        if not source_path.is_file():
            continue
        if source_path.stat().st_mtime > resume_mtime:
            stale.append(name)

    if stale:
        return [
            f"Resume file (`{resume_path.name}`) is **STALE** — older than: {', '.join(stale)}.",
            "Run the fullstack_net_profile_resume skill to regenerate it before uploading — "
            "the typed fields below only cover headline/summary/skills/preferences, not the "
            "parsed work history the platform builds from the resume itself.",
        ]
    return [
        f"Resume file (`{resume_path.name}`) is current relative to "
        f"{', '.join(_SOURCE_FILES)}."
    ]

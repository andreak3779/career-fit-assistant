"""Shared models, parsers, and utilities for the claude-projects monorepo.

Every name below is re-exported lazily (PEP 562 module ``__getattr__``):
importing ``shared`` itself never imports a submodule, so a caller that only
needs ``rate_fit``/``load_profile_bundle`` (pure-stdlib + ``jsonschema``)
never pays for ``python-docx`` (``docx_layout``) or ``pyyaml``
(``markdown_sources``) just because some other command needs them. The
public API is unchanged — ``from shared import X`` still works exactly as
before for every name in ``__all__``.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.bundle_loader import load_presence_bundle, load_profile_bundle
    from shared.docx_layout import (
        DEFAULT_SIGNATURE_NAME,
        bullet_label_para,
        clean_stack,
        letter_footer,
        letter_header,
        name_prefix,
        slugify,
        split_label_body,
    )
    from shared.fit_engine import (
        FitResult,
        SkillMatch,
        humanize_evidence,
        profile_has_skill_text,
        rate_fit,
        render_fit_table,
    )
    from shared.jd_parser import ParsedJD, looks_unknown, parse_jd
    from shared.markdown_sources import ParsedSources, load_sources
    from shared.models import (
        PUBLIC_CERTS,
        Cert,
        CertStatus,
        Contact,
        Education,
        EvidenceLevel,
        Gap,
        GapSeverity,
        PresenceBundle,
        ProfileBundle,
        Project,
        Resume,
        SkillCategory,
        StarStory,
        WorkExperience,
    )
    from shared.pii_guard import (
        PIIViolation,
        assert_presence_safe,
        scan_structure,
    )

__all__ = [
    "Cert",
    "CertStatus",
    "Contact",
    "Education",
    "EvidenceLevel",
    "Gap",
    "GapSeverity",
    "PresenceBundle",
    "ProfileBundle",
    "Project",
    "Resume",
    "SkillCategory",
    "StarStory",
    "WorkExperience",
    "load_sources",
    "ParsedSources",
    "PIIViolation",
    "assert_presence_safe",
    "scan_structure",
    "load_profile_bundle",
    "load_presence_bundle",
    "FitResult",
    "SkillMatch",
    "humanize_evidence",
    "profile_has_skill_text",
    "rate_fit",
    "render_fit_table",
    "DEFAULT_SIGNATURE_NAME",
    "bullet_label_para",
    "clean_stack",
    "letter_footer",
    "letter_header",
    "name_prefix",
    "slugify",
    "split_label_body",
    "ParsedJD",
    "looks_unknown",
    "parse_jd",
    "PUBLIC_CERTS",
]

# name -> submodule that actually defines it. Each submodule is only
# imported the first time one of its names is accessed, so e.g. `fit-check`
# (which only touches bundle_loader/fit_engine/models/jd_parser — all
# stdlib-only except bundle_loader's `jsonschema`) never imports
# docx_layout (`python-docx`) or markdown_sources (`pyyaml`) at all.
_ATTR_SOURCES: dict[str, str] = {
    "load_profile_bundle": "shared.bundle_loader",
    "load_presence_bundle": "shared.bundle_loader",
    "DEFAULT_SIGNATURE_NAME": "shared.docx_layout",
    "bullet_label_para": "shared.docx_layout",
    "clean_stack": "shared.docx_layout",
    "letter_footer": "shared.docx_layout",
    "letter_header": "shared.docx_layout",
    "name_prefix": "shared.docx_layout",
    "slugify": "shared.docx_layout",
    "split_label_body": "shared.docx_layout",
    "FitResult": "shared.fit_engine",
    "SkillMatch": "shared.fit_engine",
    "humanize_evidence": "shared.fit_engine",
    "profile_has_skill_text": "shared.fit_engine",
    "rate_fit": "shared.fit_engine",
    "render_fit_table": "shared.fit_engine",
    "ParsedJD": "shared.jd_parser",
    "looks_unknown": "shared.jd_parser",
    "parse_jd": "shared.jd_parser",
    "ParsedSources": "shared.markdown_sources",
    "load_sources": "shared.markdown_sources",
    "Cert": "shared.models",
    "CertStatus": "shared.models",
    "Contact": "shared.models",
    "Education": "shared.models",
    "EvidenceLevel": "shared.models",
    "Gap": "shared.models",
    "GapSeverity": "shared.models",
    "PresenceBundle": "shared.models",
    "ProfileBundle": "shared.models",
    "Project": "shared.models",
    "Resume": "shared.models",
    "SkillCategory": "shared.models",
    "StarStory": "shared.models",
    "WorkExperience": "shared.models",
    "PUBLIC_CERTS": "shared.models",
    "PIIViolation": "shared.pii_guard",
    "assert_presence_safe": "shared.pii_guard",
    "scan_structure": "shared.pii_guard",
}


def __getattr__(name: str) -> Any:
    module_name = _ATTR_SOURCES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value  # cache — subsequent access skips __getattr__ entirely
    return value

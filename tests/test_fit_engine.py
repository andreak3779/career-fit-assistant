"""Tests for shared.fit_engine."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from shared.fit_engine import (
    FitResult,
    SkillMatch,
    _count_statuses,
    _derive_rating,
    _expand_terms,
    _load_aliases,
    humanize_evidence,
    rate_fit,
    render_fit_table,
)
from shared.models import (
    Contact,
    Education,
    ProfileBundle,
    Project,
    Resume,
    SkillCategory,
    WorkExperience,
)


def _minimal_profile(**overrides) -> ProfileBundle:
    resume = Resume(
        headline="Engineer",
        summary="Test",
        technical_skills=[SkillCategory(category="Cloud", skills=["azure"])],
        experience=[
            WorkExperience(
                title="Engineer",
                company="Contoso",
                location="",
                dates="2023–Present",
                bullets=["Built .NET APIs on Azure"],
            )
        ],
        education=[Education(institution="School", credential="BS", dates="2020")],
        certifications=[],
    )
    base = ProfileBundle(
        bundle_version=1,
        generated=date(2025, 1, 1),
        sources={},
        contact=Contact(name="", email="", phone=""),
        headline="Engineer",
        summary="Test",
        cert_registry=[],
        differentiators=[],
        known_genuine_gaps=[],
        resolved_framing_gaps=[],
        portfolio_projects=[
            Project(
                name="AI Demo",
                description="A demo using OpenAI and Python",
                stack=["python", "openai"],
                url="https://example.com/ai-demo",
                skills_evidence=["python", "openai"],
            )
        ],
        ats_keywords={"ai": ["python", "openai"]},
        ai200_domain_coverage=[],
        resume=resume,
        raw_sections={},
    )
    for key, value in overrides.items():
        object.__setattr__(base, key, value)
    return base


def test_rate_fit_strong_when_all_required_match_and_nice_present() -> None:
    profile = _minimal_profile(
        resolved_framing_gaps=["kubernetes", "terraform"],
        ats_keywords={"cloud": ["docker"]},
    )
    result = rate_fit(
        required=[".net", "azure", "kubernetes"],
        nice_to_have=["docker", "terraform", "python"],
        profile=profile,
    )
    assert result.rating == "Strong"
    assert result.rationale.startswith("All 3 required skills covered")
    statuses = {m.skill: m.status for m in result.required + result.nice_to_have}
    assert statuses[".net"] == "match"
    assert statuses["azure"] == "match"
    assert statuses["kubernetes"] == "match"
    assert statuses["docker"] == "course"
    assert statuses["terraform"] == "match"


def test_rate_fit_good_when_all_required_with_minor_course_signals() -> None:
    # Only azure is in the profile via technical_skills (course evidence).
    result = rate_fit(
        required=["azure"],
        nice_to_have=[],
        profile=_minimal_profile(),
    )
    assert result.rating == "Good"
    assert "All required skills covered" in result.rationale


def test_rate_fit_stretch_for_genuine_gap_and_course_signals() -> None:
    profile = _minimal_profile()
    result = rate_fit(
        required=[".net", "azure", "golang", "react"],
        nice_to_have=[],
        profile=profile,
    )
    assert result.rating == "Stretch"
    assert any(m.skill == "golang" and m.status == "gap" for m in result.required)


def test_rate_fit_pass_when_too_many_gaps() -> None:
    profile = _minimal_profile()
    result = rate_fit(
        required=["java", "golang", "rust", "terraform", "kubernetes"],
        nice_to_have=[],
        profile=profile,
    )
    assert result.rating == "Pass"
    assert result.rationale.startswith("5 genuine gaps")


def test_portfolio_evidence_returns_portfolio_status() -> None:
    profile = _minimal_profile()
    result = rate_fit(required=["python"], nice_to_have=[], profile=profile)
    assert result.required[0].status == "portfolio"
    assert "AI Demo" in result.required[0].evidence


def test_course_evidence_returns_course_status() -> None:
    profile = _minimal_profile(
        portfolio_projects=[], ats_keywords={"ai": ["openai", "prompt engineering"]}
    )
    result = rate_fit(required=["prompt engineering"], nice_to_have=[], profile=profile)
    assert result.required[0].status == "course"


def test_count_statuses_sums_correctly() -> None:
    matches = [
        SkillMatch("a", "match", ""),
        SkillMatch("b", "match", ""),
        SkillMatch("c", "portfolio", ""),
        SkillMatch("d", "gap", ""),
    ]
    counts = _count_statuses(matches)
    assert counts == {"match": 2, "portfolio": 1, "course": 0, "gap": 1}


def test_alias_matching_expands_co_occurring_terms() -> None:
    profile = _minimal_profile(
        portfolio_projects=[
            Project(
                name="RecipeBox",
                description="Legacy WinForms modernization to Blazor WebAssembly",
                stack=[".net 10", "blazor webassembly", "xunit"],
                url="https://example.com/recipebox",
                skills_evidence=["blazor webassembly", "legacy modernization"],
            )
        ],
        ats_keywords={"cloud": ["kubernetes", "docker"]},
        known_genuine_gaps=[],
    )
    result = rate_fit(
        required=["c# / .net core / asp.net core web api", "legacy system modernization", "docker"],
        nice_to_have=["kubernetes / container orchestration"],
        profile=profile,
    )
    statuses = {m.skill: m.status for m in result.required + result.nice_to_have}
    assert statuses["c# / .net core / asp.net core web api"] != "gap"
    assert statuses["legacy system modernization"] != "gap"
    assert statuses["docker"] != "gap"
    assert statuses["kubernetes / container orchestration"] != "gap"


def test_multi_token_skill_splitting_on_slash_and_or() -> None:
    # rate_fit keeps original phrases; splitting happens internally during matching.
    profile = _minimal_profile(
        portfolio_projects=[
            Project(
                name="API",
                description="REST API",
                stack=["aspnetcore"],
                url="https://example.com/api",
                skills_evidence=["rest api"],
            )
        ]
    )
    result = rate_fit(
        required=["angular or react frontend development"],
        nice_to_have=["sql server / t-sql query optimization"],
        profile=profile,
    )
    assert any("angular or react frontend development" == m.skill for m in result.required)
    assert any("sql server / t-sql query optimization" == m.skill for m in result.nice_to_have)


def test_years_prefix_is_normalized() -> None:
    profile = _minimal_profile(
        resume=Resume(
            headline="Dev",
            summary="Test",
            technical_skills=[SkillCategory(category="Lang", skills=["c#"])],
            experience=[
                WorkExperience(
                    title="Dev",
                    company="Contoso",
                    location="",
                    dates="2023–Present",
                    bullets=["c# .net core"],
                )
            ],
            education=[],
            certifications=[],
        )
    )
    result = rate_fit(required=["5+ years c# / .net core"], nice_to_have=[], profile=profile)
    assert result.required[0].status == "match"


class TestDeriveRating:
    def test_strong_all_required_match_with_two_nice(self) -> None:
        matches = [SkillMatch("a", "match", "")]
        nice = [SkillMatch("b", "match", ""), SkillMatch("c", "portfolio", "")]
        rating, _ = _derive_rating(matches, nice)
        assert rating == "Strong"

    def test_good_all_required_with_two_or_fewer_course(self) -> None:
        matches = [SkillMatch("a", "match", "")]
        nice = [SkillMatch("b", "course", "")]
        rating, _ = _derive_rating(matches, nice)
        assert rating == "Good"

    def test_pass_for_three_or_more_gaps(self) -> None:
        matches = [
            SkillMatch("a", "gap", ""),
            SkillMatch("b", "gap", ""),
            SkillMatch("c", "gap", ""),
        ]
        rating, rationale = _derive_rating(matches, [])
        assert rating == "Pass"
        assert "3 genuine gaps" in rationale

    def test_stretch_for_one_gap_or_mixed_course(self) -> None:
        matches = [SkillMatch("a", "match", ""), SkillMatch("b", "gap", "")]
        rating, rationale = _derive_rating(matches, [])
        assert rating == "Stretch"
        assert "1 gap" in rationale

    def test_stretch_for_one_gap_among_mixed_course_signals(self) -> None:
        """One raw genuine gap is Stretch even with weak surrounding evidence —
        raw-count thresholds, not a weighted score, per job_description_fit/SKILL.md."""
        matches = [
            SkillMatch("a", "course", ""),
            SkillMatch("b", "course", ""),
            SkillMatch("c", "gap", ""),
        ]
        rating, rationale = _derive_rating(matches, [])
        assert rating == "Stretch"
        assert "1 gap" in rationale

    def test_good_for_all_required_course_only(self) -> None:
        matches = [SkillMatch("a", "course", "")]
        nice = [SkillMatch("b", "course", "")]
        rating, _ = _derive_rating(matches, nice)
        assert rating == "Good"

    def test_stretch_for_three_or_more_required_course_only_with_zero_gaps(self) -> None:
        """3+ required skills that are course/portfolio-only (no production
        evidence) is Stretch even with zero genuine gaps — matches
        job_description_fit/SKILL.md's "3+ required 🟡" rule. A prior
        weighted-average implementation rated this "Good" instead."""
        matches = [
            SkillMatch("a", "course", ""),
            SkillMatch("b", "course", ""),
            SkillMatch("c", "portfolio", ""),
        ]
        nice = [SkillMatch("d", "match", ""), SkillMatch("e", "match", "")]
        rating, rationale = _derive_rating(matches, nice)
        assert rating == "Stretch"
        assert "3" in rationale


class TestAliasRegistry:
    def test_registry_loads_from_shared_directory(self) -> None:
        aliases = _load_aliases()
        assert "c#" in aliases
        assert ".net" in aliases["c#"]

    def test_registry_returns_empty_for_missing_path(self) -> None:
        aliases = _load_aliases(Path("/nonexistent/aliases.json"))
        assert aliases == {}

    def test_expand_terms_uses_loaded_aliases(self) -> None:
        terms = _expand_terms("c#")
        assert ".net" in terms
        assert "dotnet" in terms

    def test_all_values_are_nonempty_lists_of_strings(self) -> None:
        aliases = _load_aliases()
        for key, values in aliases.items():
            assert isinstance(key, str) and key.strip(), (
                f"alias key must be non-empty string: {key!r}"
            )
            assert isinstance(values, list) and values, (
                f"alias values for {key!r} must be non-empty list"
            )
            for value in values:
                assert isinstance(value, str) and value.strip(), (
                    f"alias value for {key!r} must be non-empty string: {value!r}"
                )

    def test_no_key_aliases_to_itself(self) -> None:
        aliases = _load_aliases()
        for key, values in aliases.items():
            assert key not in values, f"alias key {key!r} must not alias to itself"


class TestEvidenceHelpers:
    def test_skill_match_is_grounded_for_match_and_portfolio(self) -> None:
        assert SkillMatch("x", "match", "c: production").is_grounded is True
        assert SkillMatch("x", "portfolio", "p: portfolio").is_grounded is True
        assert SkillMatch("x", "course", "coursework").is_grounded is False
        assert SkillMatch("x", "gap", "no evidence").is_grounded is False

    def test_evidence_strength_order(self) -> None:
        assert SkillMatch("x", "match", "").evidence_strength == 0
        assert SkillMatch("x", "portfolio", "").evidence_strength == 1
        assert SkillMatch("x", "course", "").evidence_strength == 2
        assert SkillMatch("x", "gap", "").evidence_strength == 3

    def test_fit_result_grounded_required_filters_by_status(self) -> None:
        result = _derive_rating(
            [
                SkillMatch("a", "match", "Contoso: production"),
                SkillMatch("b", "portfolio", "Demo: portfolio"),
                SkillMatch("c", "course", "coursework"),
                SkillMatch("d", "gap", "no evidence"),
            ],
            [],
        )[0]
        # _derive_rating only returns rating/rationale; build FitResult manually for helpers.
        from shared.fit_engine import FitResult

        fit = FitResult(
            rating=result,
            required=[
                SkillMatch("a", "match", "Contoso: production"),
                SkillMatch("b", "portfolio", "Demo: portfolio"),
                SkillMatch("c", "course", "coursework"),
                SkillMatch("d", "gap", "no evidence"),
            ],
            nice_to_have=[],
            rationale="test",
        )
        assert [m.skill for m in fit.grounded_required] == ["a", "b"]
        assert [m.skill for m in fit.ungrounded_required] == ["c", "d"]
        assert fit.evidence_sources() == ["Contoso", "Demo"]

    def test_humanize_evidence_stricter_for_course_and_gap(self) -> None:
        assert (
            humanize_evidence(SkillMatch("x", "match", "Contoso: production"))
            == "production evidence at Contoso"
        )
        assert (
            humanize_evidence(SkillMatch("x", "portfolio", "Demo: portfolio"))
            == "portfolio evidence on Demo"
        )
        assert (
            humanize_evidence(SkillMatch("x", "course", "coursework"))
            == "familiar through recent coursework"
        )
        assert (
            humanize_evidence(SkillMatch("x", "gap", "no evidence"))
            == "not yet demonstrated in production"
        )
        assert humanize_evidence(SkillMatch("x", "gap", ""), audience="debug") == "no evidence"


class TestRenderFitTable:
    """Matches job_description_fit/SKILL.md's Step 4 output template."""

    def test_headings_and_status_cells_match_skill_md_template(self) -> None:
        result = FitResult(
            rating="Good",
            required=[SkillMatch("Azure", "match", "Contoso: production")],
            nice_to_have=[SkillMatch("Docker", "course", "coursework or self-study")],
            rationale="test rationale",
        )
        table = render_fit_table(result)
        assert "**Nice-to-Haves**" in table
        assert "Nice-to-Have Skills" not in table
        # Bare emoji in the status cell, not "✅ match" / "🟡 course".
        assert "| Azure | ✅ | Contoso, production |" in table
        assert "| Docker | 🟡 | coursework or self-study |" in table

    def test_evidence_display_uses_comma_not_colon_separator(self) -> None:
        # Matches the SKILL.md example: "Fieldstone Benefits Administrators, production".
        assert (
            render_fit_table(
                FitResult(
                    rating="Strong",
                    required=[
                        SkillMatch("C#", "match", "Fieldstone Benefits Administrators: production")
                    ],
                    nice_to_have=[],
                    rationale="",
                )
            ).find("Fieldstone Benefits Administrators, production")
            != -1
        )

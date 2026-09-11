from datetime import date

from shared.models import (
    Cert,
    CertStatus,
    Contact,
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


def test_cert_to_dict_round_trip():
    cert = Cert(
        code="AZ-900",
        status=CertStatus.CERTIFIED,
        date=date(2026, 4, 18),
        credential_url="https://example.com/badge",
    )
    data = cert.to_dict()
    assert data["code"] == "AZ-900"
    assert data["status"] == "certified"
    assert data["date"] == "2026-04-18"


def test_profile_bundle_serializes():
    bundle = ProfileBundle(
        bundle_version=1,
        generated=date(2026, 8, 19),
        sources={"profile-facts": date(2026, 8, 18)},
        contact=Contact(name="Sarah", email="a@example.com", phone="204-555-0001"),
        headline="Senior Dev",
        summary="Summary text",
        cert_registry=[Cert(code="AZ-900", status=CertStatus.CERTIFIED)],
        differentiators=["full-stack"],
        known_genuine_gaps=[Gap(skill="k8s", severity=GapSeverity.GENUINE)],
        resolved_framing_gaps=["tdd"],
        portfolio_projects=[
            Project(name="P", url="https://example.com", stack=["py"], description="d")
        ],
        ats_keywords={"cloud": ["Azure"]},
        ai200_domain_coverage=[{"domain": "RAG", "status": "partial"}],
        resume=Resume(
            headline="H",
            summary="S",
            technical_skills=[SkillCategory(category="Backend", skills=["C#"])],
            experience=[WorkExperience(title="Dev", company="Co")],
        ),
    )
    data = bundle.to_dict()
    assert data["bundle_version"] == 1
    assert data["cert_registry"][0]["status"] == "certified"
    assert data["resume"]["technical_skills"][0]["skills"] == ["C#"]
    assert data["contact"]["email"] == "a@example.com"


def test_presence_bundle_excludes_contact():
    bundle = PresenceBundle(
        bundle_version=1,
        generated=date(2026, 8, 19),
        headline="H",
        summary="S",
        cert_registry=[],
        technical_skills={},
        portfolio_projects=[],
        differentiators=[],
    )
    data = bundle.to_dict()
    assert "contact" not in data


def test_star_story_serializes():
    story = StarStory(
        title="SSIS Performance Improvement",
        jd_tags=["sql", "performance"],
        situation="A process took 8 hours.",
        task="Fix it.",
        action="Rewrote with T-SQL.",
        result="7x improvement.",
    )
    data = story.to_dict()
    assert data["title"] == "SSIS Performance Improvement"
    assert data["jd_tags"] == ["sql", "performance"]
    assert data["result"] == "7x improvement."

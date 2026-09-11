#!/usr/bin/env python3
"""Generate GitHub profile copy (README) from the presence bundle."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

from shared import load_presence_bundle
from shared.provenance import write_sidecar


def _require_bundle(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Bundle not found: {path}")
    return path


def _emoji_bullet(text: str) -> str:
    text = text.strip()
    if text.startswith(("-", "•")):
        text = text[1:].strip()
    if any(text.lower().startswith(w) for w in ("azure", "cloud", "infrastructure", "devops")):
        return f"☁️ {text}"
    if any(text.lower().startswith(w) for w in ("ai", "ml", "machine", "agent", "copilot")):
        return f"🤖 {text}"
    if any(text.lower().startswith(w) for w in (".net", "c#", "backend", "api")):
        return f"⚙️ {text}"
    if any(text.lower().startswith(w) for w in ("data", "sql", "cosmos", "database")):
        return f"🗄️ {text}"
    return f"🔹 {text}"


def _is_sparse(bundle) -> bool:
    """Return True when the bundle lacks headline, summary, differentiators, and portfolio."""
    return not any(
        [bundle.headline, bundle.summary, bundle.differentiators, bundle.portfolio_projects]
    )


def _build_readme(bundle) -> str:
    lines: list[str] = []
    lines.append("# Hi there 👋")
    lines.append("")
    if bundle.summary:
        lines.append(bundle.summary)
    elif bundle.headline:
        lines.append(bundle.headline)
    else:
        lines.append("Profile summary placeholder — update from the latest presence bundle.")
    lines.append("")

    certs = _cert_summary(bundle)
    if certs:
        lines.append(f"**Currently:** {certs}")
        lines.append("")

    if bundle.differentiators:
        lines.append("## What sets me apart")
        for d in bundle.differentiators[:8]:
            lines.append(_emoji_bullet(d))
        lines.append("")
    if bundle.portfolio_projects:
        lines.append("## Featured work")
        for p in bundle.portfolio_projects:
            stack = ", ".join(s.strip() for s in p.stack if s.strip())
            lines.append(f"- **[{p.name}]({p.url})** — {p.description}")
            if stack:
                lines.append(f"  - Stack: {stack}")
        lines.append("")
    if bundle.technical_skills:
        lines.append("## Stack")
        for category, items in bundle.technical_skills.items():
            if not items:
                continue
            chips = [f"`{i.strip()}`" for i in items[:12] if i.strip()]
            lines.append(f"**{category}:** " + " · ".join(chips))
        lines.append("")
    lines.append("---")
    lines.append("*Generated from my profile bundle — opinions and code are my own.*")
    return "\n".join(lines)


def _cert_summary(bundle) -> str:
    """Return a GitHub-friendly, sentence-cased cert status line."""
    if not bundle.cert_registry:
        return ""
    active = [c for c in bundle.cert_registry if c.status == "certified"]
    in_progress = [c for c in bundle.cert_registry if c.status == "in_progress"]
    parts: list[str] = []
    if active:
        parts.append("Certified: " + ", ".join(c.code for c in active))
    if in_progress:
        parts.append("Preparing for: " + ", ".join(c.code for c in in_progress))
    return " · ".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-github", description="Generate GitHub profile README copy"
    )
    parser.add_argument(
        "--out", type=Path, help="Output markdown file (default: outputs/GitHub_Readme.md)"
    )
    args = parser.parse_args(argv)

    try:
        _require_bundle(ROOT / "outputs" / "presence-bundle.json")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    try:
        bundle = load_presence_bundle(ROOT)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_file = args.out or ROOT / "outputs" / "GitHub_Readme.md"
    try:
        out_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR: cannot create output directory {out_file.parent}: {exc}", file=sys.stderr)
        return 1
    warnings: list[str] = []
    if _is_sparse(bundle):
        warnings.append("sparse bundle — manually review public copy")
    if not bundle.headline:
        warnings.append("no bundle headline — fallback used")

    evidence_sources = []
    if bundle.portfolio_projects:
        evidence_sources.extend(p.name for p in bundle.portfolio_projects)
    emoji_prefix_re = re.compile(r"^[🔹🤖☁️⚙️🗄️]\s*")
    evidence_sources.extend(
        emoji_prefix_re.sub("", _emoji_bullet(d)).split(":", 1)[0].strip()
        for d in bundle.differentiators[:8]
    )

    try:
        out_file.write_text(_build_readme(bundle), encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot write output file {out_file}: {exc}", file=sys.stderr)
        return 1

    sidecar = write_sidecar(
        out_file,
        script="generate_github.py",
        bundle=bundle,
        inputs=[],
        evidence_sources=evidence_sources,
        warnings=warnings,
    )
    print(f"Wrote {out_file}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

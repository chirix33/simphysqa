"""Read-only checks of installed handoff links and preserved source assets."""
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs"


def main():
    manifest = json.loads((HANDOFF / "assets/source_manifest.json").read_text())
    failures = []
    for item in manifest["sources"]:
        path = HANDOFF / item["path"]
        if not path.exists() or sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            failures.append(f"source hash mismatch: {item['path']}")
    prompts = json.loads((HANDOFF / "assets/prompts.json").read_text())
    for name, expected in manifest["prompt_string_sha256"].items():
        if sha256(prompts[name].encode()).hexdigest() != expected:
            failures.append(f"prompt string mismatch: {name}")
    files = [ROOT / "AGENTS.md", ROOT / "README.md", *HANDOFF.rglob("*.md")]
    for path in files:
        content = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            if "://" in target or target.startswith("#"):
                continue
            local = target.split("#")[0]
            if not (path.parent / local).exists():
                failures.append(f"broken link: {path.relative_to(ROOT)} -> {target}")
        active_content = content.replace("not `docs/implementation/`", "")
        if "docs/implementation/" in active_content and path != HANDOFF / "references/decision_ledger.md":
            failures.append(f"stale installation path: {path.relative_to(ROOT)}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(manifest['sources'])} source hashes, {len(prompts)} prompt strings, {len(files)} Markdown files checked")


if __name__ == "__main__":
    main()

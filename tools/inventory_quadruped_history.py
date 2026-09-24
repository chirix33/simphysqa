"""Hash retained local investigation files without copying large trajectories."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    dest = ROOT / "docs/reviews/artifacts/PDS_quadruped_refinement"
    checks = json.loads((dest / "CHECKSUMS.json").read_text())
    for name, expected in checks.items():
        assert hashlib.sha256((dest / name).read_bytes()).hexdigest() == expected, name
    paths = set()
    for p in (ROOT / "dataset-runs").iterdir():
        if p.name.startswith(("quadruped", "mjx", "gait-development")):
            paths.update(f for f in p.rglob("*") if f.is_file()) if p.is_dir() else paths.add(p)
    entries = []
    for path in sorted(paths):
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        entries.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size, sha256=h.hexdigest()))
    inventory = dict(status="historical_development_only_not_release_eligible", root=str(ROOT), files=entries)
    target = dest / "local-history-inventory.json"
    target.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    checks[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
    (dest / "CHECKSUMS.json").write_text(json.dumps(checks, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(files=len(entries), bytes=sum(e["bytes"] for e in entries))))


if __name__ == "__main__":
    main()

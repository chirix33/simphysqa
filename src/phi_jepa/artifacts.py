"""Content-addressed, exclusive-create run bundles. Never overwrite a run."""
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import json
import platform
import subprocess


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(value) -> str:
    return sha256(canonical(value)).hexdigest()


def code_provenance() -> dict:
    package = Path(__file__).parent
    files = {path.name: sha256(path.read_bytes()).hexdigest() for path in sorted(package.glob("*.py"))}
    root = package.parent.parent
    metadata = root / "pyproject.toml"
    if metadata.exists():
        files["pyproject.toml"] = sha256(metadata.read_bytes()).hexdigest()
    result = {"source_files": files, "source_sha256": digest(files), "git_commit": None, "git_dirty": None}
    if (root / ".git").exists():
        try:
            result["git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=5).strip()
            result["git_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True, timeout=5).strip())
        except (OSError, subprocess.SubprocessError):
            pass
    return result


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    sha256: str


@dataclass(frozen=True)
class RunManifest:
    """Immutable canonical manifest bytes are the durable source of truth."""
    provenance_json: str
    artifacts: tuple[ArtifactRef, ...]

    def to_dict(self) -> dict:
        return {"format_version": 1, "provenance": json.loads(self.provenance_json), "artifacts": [asdict(a) for a in self.artifacts]}


def write_run(output: Path, payloads: dict, provenance: dict) -> Path:
    if any(Path(name).name != name or name in ("manifest.json", ".", "..") or "/" in name or "\\" in name or ":" in name for name in payloads):
        raise ValueError("artifact names must be plain filenames")
    encoded = {name: canonical(value) for name, value in payloads.items()}
    manifest = RunManifest(canonical(provenance).decode(), tuple(ArtifactRef(name, sha256(data).hexdigest()) for name, data in sorted(encoded.items())))
    manifest_bytes = canonical(manifest.to_dict())
    run = output / sha256(manifest_bytes).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    run.mkdir()  # Exclusive reservation: an existing or incomplete run is an error.
    for name, data in encoded.items():
        with (run / name).open("xb") as stream:
            stream.write(data)
    # Published last; its absence identifies an incomplete write.
    with (run / "manifest.json").open("xb") as stream:
        stream.write(manifest_bytes)
    return run


def environment() -> dict:
    return {"python": platform.python_version(), "platform": platform.platform(), "dependencies": {}, "device": "cpu"}

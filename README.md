# Phi-JEPA

P00 provides offline contracts and provenance only. The implementation handoff is
in [docs/README.md](docs/README.md); progress is in [docs/PROGRESS.md](docs/PROGRESS.md).
The root Python scripts and notebooks remain historical prototype code.

Use Python 3.12. The core has no third-party runtime or test dependencies.
The verified build dependency is `setuptools==84.0.0`; legacy `requirements.txt`
does not describe this package. Keep future core, CoConuT and CODI environments separate.

```powershell
python -m pip install --no-deps --no-build-isolation -e .
phi-jepa --help
phi-jepa validate-config --config configs/offline.json
phi-jepa fixture --config configs/offline.json --input tests/fixtures/scenario.json --output results/p00
python -m unittest discover -s tests -v
```

`python -m phi_jepa` is equivalent to `phi-jepa`. A repeated identical run under
the same output root fails rather than overwriting evidence; use a new output root
to verify byte-for-byte reproducibility. Manifests contain input/config/source hashes,
environment, budgets, zero call/solve counters, and hashes of all artifacts. No timestamps
or absolute output paths enter run identity. Manifest publication is last; missing manifests
identify interrupted bundles. Immutability means API-level exclusive creation, not filesystem
tamper protection; hashes allow later verification. No credentials or environment dumps are saved.

Unknown observations stay null. The fixture returns no physical prediction or empirical
metric. Live configuration can be validated but P00 cannot execute live providers.
Allowlisted typed inputs reject extra label fields; free text is not a semantic leakage detector.

Later phase CLI names are reserved (not implemented): `generate-data`, `evaluate`,
`extract`, `train`, `predict`, `assess`, `baseline`, `pilot`, `study`. Each will use
`--config` and explicit input/output paths as appropriate. Their implementation requires
separate phase authorization.

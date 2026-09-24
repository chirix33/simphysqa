# Third-party boundaries

The four production scenes are programmatically authored primitives. No external
meshes, textures, robot-model downloads, `pybullet_data` URDFs, MuJoCo Menagerie,
Playground models, or third-party scene datasets are loaded by these paths.
The scene inventory lists the ground/table primitives as well as moving bodies.

MuJoCo 3.14.0 is an installed runtime dependency with Apache-2.0 text and bundled
third-party notices. PyBullet 3.2.7's installed notice identifies zlib terms and
exceptions for Extras/examples third-party directories. Original installed notices
are retained in `third-party/`; they are not modified or replaced by MIT/CC BY.
Package versions, notice paths and hashes are recorded in runtime-notices.json.
Engine binaries, wheels, their bundled data and other dependencies are **not**
part of the proposed dataset/code download; users install pinned dependencies.
If that distribution boundary changes, its notices must be reviewed again.

`docs/assets/extract_schema.json`, `docs/assets/prompts.json`, judge/answer schema
originals, and `docs/references/sources/` are preserved adopted references. They
are excluded from the proposed project-authored license grant and public package
scope. Their existing provenance is retained in `docs/docs/09_sources.md`.
Template-first dataset generation does not invoke the prompted extraction model;
its binding manifests record the adopted schema/prompt hashes. Exercising the
optional extracted-JSON adapter requires those original reference artifacts and
their applicable permissions; this license preparation does not grant them.

Historical quadruped/MJX artifacts and unrelated legacy/model-training work are
outside this four-domain distribution scope. No existing third-party notice was
deleted. Git author names document commits, not proof of copyright ownership.

The proposed public code bundle is the explicit `mit_files` allowlist plus the
reviewed configs, schema, registries and license notices. Do not publish the full
repository or local `source_snapshot/` trees as though that allowlist grants
rights to every file. Preserve complete local provenance; a public bundle can
carry hashes of excluded provenance without redistributing its source contents.

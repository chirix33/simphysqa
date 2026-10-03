"""Strict numeric registry and serialized Q/C/A boundary, contract 1.1.0.

No engine imports, inferred zeros, semantic embeddings, or future-state inputs.
Extracted adapters must pin an explicit public root and source schema hash.
"""
from dataclasses import dataclass
import copy
import math
from phi_jepa.artifacts import canonical, digest

def leaves(value, path=(), context=None):
    context = context or {}
    if value is None:
        raise ValueError(f"null at {path}; strict adapter cannot impute")
    if type(value) in (int, float):
        if not math.isfinite(value): raise ValueError("nonfinite numeric field")
        yield path, value, context
    elif isinstance(value, dict):
        ctx = {**context, **{k: value[k] for k in ("entity_id", "unit", "frame", "name") if k in value}}
        for key in sorted(value):
            yield from leaves(value[key], path + (("key", key),), ctx)
    elif isinstance(value, list):
        identities = []
        for index, item in enumerate(value):
            ident = ("index", index)
            if isinstance(item, dict):
                if "entity_id" in item and "name" in item:
                    ident = ("quantity", item["entity_id"], item["name"])
                elif "entity_id" in item and "properties" in item:
                    ident = ("entity", item["entity_id"])
                elif "target_id" in item:
                    ident = ("target", item["target_id"])
                elif "entity_id" in item and "channel" in item:
                    ident = ("control", item["entity_id"], item["channel"], index)
            if ident in identities: raise ValueError("duplicate semantic key")
            identities.append(ident)
            yield from leaves(item, path+(ident,), {**context, "observation_slot": index} if isinstance(item, dict) and "measurements" in item else context)
    elif not isinstance(value, (str, bool)):
        raise ValueError("unsupported JSON value")

def numeric_fields(value):
    return sorted(leaves(value), key=lambda row: canonical(row[0]))

@dataclass(frozen=True)
class Registry:
    domain: str
    source: str
    source_schema: str
    root: tuple
    entries: tuple

    @classmethod
    def from_manifest(cls,manifest):
        data={k:v for k,v in manifest.items() if k!="sha256"}
        if digest(data)!=manifest["sha256"]: raise ValueError("registry checksum mismatch")
        return cls(manifest["domain"],manifest["source"],manifest["source_schema"],tuple(manifest["root"]),tuple(manifest["entries"]))

    @classmethod
    def build(cls, public, domain, source="public_simulator_json", source_schema="1.0.0", root=("input",), partition="development"):
        if partition not in ("development", "train"): raise ValueError("registry fitting requires development/train")
        if source not in ("public_simulator_json", "llm_extracted_json"): raise ValueError("unknown source")
        if not root or any(k in ("reference", "metadata") for k in root): raise ValueError("pin a public source root")
        obj = public
        for k in root: obj = obj[k]
        entries = tuple(dict(column=i, key=key, scalar_type=type(v).__name__, **ctx) for i, (key, v, ctx) in enumerate(numeric_fields(obj)))
        if not entries: raise ValueError("empty numeric registry")
        return cls(domain, source, source_schema, tuple(root), entries)

    def manifest(self):
        data = dict(version="1.1.0", domain=self.domain, source=self.source, source_schema=self.source_schema, root=self.root, entries=self.entries, canonical_units=True, conversion="identity: input must already be canonical SI")
        return {**data, "sha256": digest(data)}

    def flatten(self, public):
        obj = public
        for k in self.root: obj = obj[k]
        if self.source == "public_simulator_json" and obj.get("domain") != self.domain: raise ValueError("domain mismatch")
        rows = numeric_fields(obj)
        if len(rows) != len(self.entries): raise ValueError("missing/extra numeric fields; structural OOD unsupported")
        values = []
        for (key, value, ctx), entry in zip(rows, self.entries):
            expected = {k: v for k, v in entry.items() if k not in ("column", "key", "scalar_type")}
            if canonical(key) != canonical(entry["key"]) or ctx != expected or type(value).__name__ != entry["scalar_type"]:
                raise ValueError("binding/type/unit/frame mismatch")
            values.append(value)
        return values

    def restore(self, vector):
        if len(vector) != len(self.entries): raise ValueError("numeric width mismatch")
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in vector): raise ValueError("invalid vector")
        return [{**copy.deepcopy(e), "value": v} for e, v in zip(self.entries, vector)]

def serialize_problem(public):
    inp = public["input"]
    return canonical({"Q": inp["question"], "C": {k: v for k, v in inp.items() if k != "question"}}).decode()

def serialize_target(public, verified_answer):
    obj = __import__("json").loads(serialize_problem(public))
    obj["A"] = verified_answer
    return canonical(obj).decode()

def text_pair(public, verified_answer, registry):
    n = registry.flatten(public)
    return dict(n_initial=n, n_target=n.copy(), problem_text=serialize_problem(public), solution_text=serialize_target(public, verified_answer), registry_sha256=registry.manifest()["sha256"], embedding_status="not_encoded")

def embed_pair(pair, encoder, settings):
    required = {"model", "revision", "dimension", "pooling", "max_tokens", "precision", "normalization", "frozen", "truncation"}
    if not required <= settings.keys() or not settings["frozen"] or settings["truncation"] != "reject": raise ValueError("pin frozen encoder and reject overlength")
    vectors = []
    for name in ("problem_text", "solution_text"):
        if encoder.token_count(pair[name]) > settings["max_tokens"]: raise ValueError("overlength text")
        v = list(encoder.encode(pair[name]))
        if len(v) != settings["dimension"] or any(not math.isfinite(x) for x in v): raise ValueError("embedding dimension/finiteness")
        vectors.append(v)
    if pair["n_initial"] != pair["n_target"]: raise ValueError("numeric target must equal input")
    return dict(x0=pair["n_initial"]+vectors[0], y=pair["n_target"]+vectors[1], encoder=copy.deepcopy(settings))

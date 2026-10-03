"""Adopted extraction object -> fixed numeric domain registry.

The original free-form schema has no entity IDs. Explicit, frozen aliases bind
its names/units/relations and event descriptions to registry columns. Ambiguous
names are errors, never resolved by array order or private simulator values.
"""
from dataclasses import dataclass
from hashlib import sha256
import math
from .common import ROOT,read
from phi_jepa.artifacts import canonical,digest
from .numeric import Registry

SCHEMA_SHA256="4be5e3ba426fcbc3fb7c0105c002c974d18b67b75c75504a32a1db47eaf47adc"
PROMPT_SHA256="75367a15ed99d692ac0b0549d4aa3f3363816f7faec7b21805ed448588ee205c"

def adopted_contract():
    path=ROOT/"docs/assets/extract_schema.json"
    if sha256(path.read_bytes()).hexdigest()!=SCHEMA_SHA256: raise ValueError("adopted extraction schema hash mismatch")
    prompt=read(ROOT/"docs/assets/prompts.json")["EXTRACTION_PROMPT"]
    if sha256(prompt.encode()).hexdigest()!=PROMPT_SHA256: raise ValueError("adopted extraction prompt hash mismatch")
    return read(path),prompt

@dataclass(frozen=True)
class ExtractedAdapter:
    registry: Registry
    bindings: tuple

    def __post_init__(self):
        columns=[b["column"] for b in self.bindings]
        if sorted(columns)!=list(range(len(self.registry.entries))): raise ValueError("exactly one binding per registry column required")
        identities=[self.identity(b) for b in self.bindings]
        if len(set(identities))!=len(identities): raise ValueError("ambiguous extracted alias")
        for b in self.bindings:
            if b["kind"] not in ("observation","event"): raise ValueError("unknown extracted binding")
            entry=self.registry.entries[b["column"]]
            expected="s" if b["kind"]=="event" else b["unit"]
            if entry.get("unit",expected)!=expected: raise ValueError("extracted binding units differ from domain registry")

    @staticmethod
    def identity(binding):
        return canonical([binding["kind"],binding["description"]] if binding["kind"]=="event" else [binding["kind"],binding["name"],binding["unit"],binding["relation"]])

    def manifest(self):
        data=dict(version="1.1.0",source="llm_extracted_json",source_root=[],source_schema_sha256=SCHEMA_SHA256,prompt_string_sha256=PROMPT_SHA256,registry_sha256=self.registry.manifest()["sha256"],bindings=self.bindings,unit_conversion="identity; incompatible or null units rejected",coverage_policy="complete_one_to_one_no_repair")
        return {**data,"sha256":digest(data)}

    def flatten(self,extraction):
        from jsonschema import Draft202012Validator
        schema,_=adopted_contract()
        Draft202012Validator(schema).validate(extraction)
        canonical(extraction)
        lookup={self.identity(b):b["column"] for b in self.bindings}; found={}
        for kind,rows in (("observation",extraction["observations"]),("event",extraction["events"])):
            for row in rows:
                identity=self.identity({"kind":kind,**row})
                if identity not in lookup: raise ValueError("unexpected/ambiguous extracted identity: "+identity.decode())
                column=lookup[identity]
                if column in found: raise ValueError("duplicate extracted numeric identity")
                value=row["time" if kind=="event" else "value"]
                if type(value) not in (int,float) or not math.isfinite(value): raise ValueError("missing/nonfinite extracted number")
                entry=self.registry.entries[column]
                if entry["scalar_type"]=="int" and value!=int(value): raise ValueError("noninteger value for integer registry coordinate")
                found[column]=int(value) if entry["scalar_type"]=="int" else float(value)
        if len(found)!=len(self.registry.entries): raise ValueError(f"incomplete extraction: {len(found)}/{len(self.registry.entries)} numeric columns; no private completion")
        return [found[i] for i in range(len(found))]

def exact_key_bindings(registry):
    """Frozen canonical aliases, NOT evidence that a live extractor emits them.

    Additional human-reviewed aliases require a new binding-manifest revision.
    Every scalar, including observation timestamps/indices, must be supplied.
    """
    return tuple(dict(kind="observation",name=canonical(e["key"]).decode().strip(),unit=e.get("unit","1"),relation="equal",column=e["column"]) for e in registry.entries)

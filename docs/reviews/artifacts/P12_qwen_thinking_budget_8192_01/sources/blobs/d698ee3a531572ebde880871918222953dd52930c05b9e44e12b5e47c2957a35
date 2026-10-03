"""Strict candidate layouts; reference types differ from continuous predictions."""
from dataclasses import dataclass
import math
from phi_jepa.artifacts import canonical, digest

def walk(value, path=()):
    """Semantic keys are tagged tuples, never sanitized concatenated names."""
    if value is None: raise ValueError('null is unknown, not zero')
    if isinstance(value, dict):
        if not value: yield path, 'empty_object', None
        for key in sorted(value):
            yield from walk(value[key], path + (('key', key),))
    elif isinstance(value, list):
        if not value: yield path, 'empty_array', None
        seen = set()
        for index, item in enumerate(value):
            ident = ('index', index)
            if isinstance(item, dict):
                if 'entity_id' in item and 'name' in item: ident = ('quantity', item['entity_id'], item['name'])
                elif 'entity_id' in item and 'properties' in item: ident = ('entity', item['entity_id'])
                elif 'target_id' in item: ident = ('target', item['target_id'])
            if ident in seen: raise ValueError('duplicate semantic key')
            seen.add(ident)
            yield from walk(item, path + (ident,))
    elif type(value) in (int, float):
        if not math.isfinite(value): raise ValueError('nonfinite numeric field')
        yield path, type(value).__name__, value
    elif type(value) is bool: yield path, 'bool', value
    elif isinstance(value, str): yield path, 'str', value
    else: raise ValueError('unsupported JSON value')

def rows(value): return sorted(walk(value), key=lambda r: canonical(r[0]))

def signature(items):
    # Units and frames bind exactly; arbitrary prose/IDs remain strings.
    return tuple((p, t, v if p[-1:] in ((('key', 'unit'),), (('key', 'frame'),)) else None) for p,t,v in items)

def source(state, public_input, scope):
    if scope not in ('state_only', 'state_plus_fixed_conditioning'):
        raise ValueError('explicit candidate scope required')
    # Contact relations are variable-length categorical annotations, not numeric
    # state coordinates. Validate explicitly rather than imposing fixed topology.
    if 'relations' not in state or not isinstance(state['relations'], list):
        raise ValueError('missing/invalid relations')
    seen = set()
    for relation in state['relations']:
        if not isinstance(relation, dict) or set(relation) != {'subject_id','predicate','object_id'}:
            raise ValueError('unexpected relation fields')
        if any(type(v) is not str for v in relation.values()): raise ValueError('relation must be categorical')
        key = tuple(relation[k] for k in ('subject_id','predicate','object_id'))
        if key in seen: raise ValueError('duplicate relation')
        seen.add(key)
    result = {'state': {k:v for k,v in state.items() if k != 'relations'}}
    if scope == 'state_plus_fixed_conditioning':
        result['fixed_conditioning'] = {k:v for k,v in public_input.items() if k != 'states'}
    return result

@dataclass(frozen=True)
class StateLayout:
    domain: str
    scope: str
    structure: tuple
    entries: tuple

    @classmethod
    def from_manifest(cls, manifest, expected_sha256):
        if digest(manifest) != expected_sha256 or manifest['version'] != '2.0.0-candidate.1':
            raise ValueError('layout manifest identity mismatch')
        def freeze(value):
            return tuple(freeze(x) for x in value) if isinstance(value,(list,tuple)) else value
        structure=freeze(manifest['structure'])
        entries=tuple((freeze(e['key']),e['reference_type']) for e in manifest['entries'])
        result=cls(manifest['domain'],manifest['scope'],structure,entries)
        if result.sha256 != expected_sha256:
            raise ValueError('invalid layout dimensions/settings')
        if entries != tuple((p,t) for p,t,v in structure if t in ('int','float')):
            raise ValueError('layout entries do not match numeric structure')
        if [e['column'] for e in manifest['entries']] != list(range(result.d)):
            raise ValueError('layout column ordering mismatch')
        return result

    @classmethod
    def build(cls, state, public_input, scope, partition):
        if partition != 'train': raise ValueError('candidate layout fitting requires train')
        items = rows(source(state, public_input, scope))
        entries = tuple((p,t) for p,t,v in items if t in ('int', 'float'))
        return cls(public_input['domain'], scope, signature(items), entries)

    @property
    def d(self): return len(self.entries)

    @property
    def sha256(self): return digest(self.manifest())

    def manifest(self):
        return dict(version='2.0.0-candidate.1', domain=self.domain, scope=self.scope,
            structure=self.structure, entries=[{'column':i,'key':p,'reference_type':t} for i,(p,t) in enumerate(self.entries)],
            d=self.d, projection_width=self.d, ode_width=2*self.d,
            booleans='excluded_from_numeric_MSE', prediction_types='finite real; no integer rounding')

    def flatten(self, state, public_input):
        if public_input['domain'] != self.domain: raise ValueError('domain mismatch')
        items = rows(source(state, public_input, self.scope))
        if signature(items) != self.structure:
            raise ValueError('missing/extra/type/unit/frame/layout mismatch')
        return tuple(v for p,t,v in items if t in ('int','float'))

    def validate_prediction(self, values):
        if len(values) != self.d or any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
            raise ValueError('invalid prediction width/value')
        return tuple(values)

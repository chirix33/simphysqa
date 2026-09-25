"""Explicit public, supervised-training, and evaluator-only readers.

PublicInputReader opens ONLY its supplied public file. Catalog verification and
truth access are offline preparation/evaluation operations, not deployment APIs.
"""
from collections import Counter
from itertools import zip_longest
from pathlib import Path
import hashlib
import json
import math
from phi_jepa.artifacts import digest
from .contracts import PublicProblem, Identity, RecordedPair, DOMAINS, SPLITS, enriched_context

def file_hash(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def strict_json(text):
    def pairs(items):
        result = {}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def invalid(value): raise ValueError('nonfinite JSON constant')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)

def json_lines(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            yield strict_json(line)

class PublicInputReader:
    """No reference handle, catalog, evaluator, or training dependency."""
    def __init__(self, public_file, expected_sha256):
        self.public_file = Path(public_file)
        if file_hash(self.public_file) != expected_sha256: raise ValueError('public checksum mismatch')

    def __iter__(self):
        seen = set()
        for row in json_lines(self.public_file):
            problem = PublicProblem.parse(row)
            if problem.sample_id in seen: raise ValueError('duplicate sample')
            seen.add(problem.sample_id)
            yield problem

class ReleaseCatalog:
    """Pinned selection and integrity boundary for offline dataset preparation."""
    def __init__(self, root, index_sha256, manifest_sha256):
        self.root = Path(root).resolve(strict=True)
        for name,expected in [('export-index.json',index_sha256), ('release-manifest.json',manifest_sha256)]:
            if file_hash(self.root/name) != expected: raise ValueError('release identity mismatch')
        self.index = strict_json((self.root/'export-index.json').read_text())
        self.manifest = strict_json((self.root/'release-manifest.json').read_text())
        self.identity = digest({'index':index_sha256, 'manifest':manifest_sha256})
        if self.index['development_included'] or self.index['quarantine_in_admitted_selection']:
            raise ValueError('nonrelease records enabled')
        self.partitions = {}
        for part in self.index['partitions']:
            key = (part['domain'],part['partition'])
            if key in self.partitions or key[0] not in DOMAINS or key[1] not in SPLITS:
                raise ValueError('duplicate or nonrelease partition')
            self.partitions[key] = part
        if set(self.partitions) != {(d,s) for d in DOMAINS for s in SPLITS}:
            raise ValueError('incomplete four-domain partition plan')

    def path(self, relative):
        path = (self.root/relative).resolve()
        if not path.is_relative_to(self.root): raise ValueError('path escapes export')
        return path

    def files(self, domain, split):
        part = self.partitions[(domain,split)]
        files = {Path(f['path']).name:f for f in part['admitted_files']}
        return files

    def verified_file(self, domain, split, name):
        item = self.files(domain,split)[name]
        if item['path'] != f'{domain}/{split}/{name}': raise ValueError('non-admitted source selection')
        path = self.path(item['path'])
        if file_hash(path) != item['sha256']: raise ValueError('admitted file checksum mismatch')
        return path

    def verify_all_checksums(self, expected_checksums_sha256):
        checksum = self.root/'CHECKSUMS.sha256'
        if file_hash(checksum) != expected_checksums_sha256: raise ValueError('checksum index mismatch')
        count = 0
        seen = set()
        for line in checksum.read_text().splitlines():
            sha,relative = line.split('  ',1)
            if relative in seen: raise ValueError('duplicate checksum path')
            seen.add(relative)
            if file_hash(self.path(relative)) != sha: raise ValueError(f'checksum mismatch: {relative}')
            count += 1
        return count

    def records(self, domain, split):
        """Private join for preparation/evaluation; never called by deployment."""
        paths = [self.verified_file(domain,split,n) for n in ('inputs.jsonl','references.jsonl','evaluator.jsonl')]
        seen = set()
        for public,ref,meta in zip_longest(*(json_lines(p) for p in paths)):
            if any(x is None for x in (public,ref,meta)): raise ValueError('unaligned export files')
            problem = PublicProblem.parse(public)
            sid = problem.sample_id
            if sid in seen or ref['sample_id'] != sid or meta['sample_id'] != sid:
                raise ValueError('duplicate/misaligned sample identity')
            seen.add(sid)
            m = meta['metadata']
            # Partition may be an OOD category while stored split is test_ood.
            expected_split = 'test_ood' if split.startswith('ood_') else split
            if m['split'] != expected_split or m['record_origin'] != 'simulation' or m['validation']['status'] != 'accepted':
                raise ValueError('development/quarantine/split mismatch')
            if m['distribution'] != self.partitions[domain,split]['shift']:
                raise ValueError('shift routing mismatch')
            if problem.input['domain'] != domain: raise ValueError('domain mismatch')
            identity = Identity(sid,m['base_scenario_id'],m['split_group_id'],domain,split)
            yield problem, ref['reference'], identity
        if len(seen) != self.partitions[domain,split]['counts']['questions']:
            raise ValueError('partition question count mismatch')

def forecast_states(problem, reference):
    inp = problem.input
    future = reference['states']
    if not future: raise ValueError('missing recorded future; no fixture fallback')
    states = [inp['states'][-1], *future]
    horizon = max(spec['end_time'] for spec in inp['answer_spec'])
    seen = set()
    for s in states:
        if type(s['timestamp']) not in (int,float) or not math.isfinite(s['timestamp']): raise ValueError('invalid reference time')
        if type(s['step_index']) is not int or s['step_index'] < 0: raise ValueError('invalid reference index')
        if s['state_id'] in seen: raise ValueError('duplicate state identity')
        seen.add(s['state_id'])
    for a,b in zip(states,states[1:]):
        if b['timestamp'] <= a['timestamp'] or b['step_index'] <= a['step_index']:
            raise ValueError('nonpositive adjacent interval/index')
    if states[-1]['timestamp'] != horizon: raise ValueError('reference does not end at requested horizon')
    return states

def make_pairs(problem, reference, identity, layout, provenance, multiplicities,
               *, context_mode='public_base_for_offline_audit', enrichment=None,
               duplicate_policy='inverse_transition_multiplicity'):
    if duplicate_policy not in ('inverse_transition_multiplicity', 'equal_question_pairs'):
        raise ValueError('explicit supported weighting required')
    if identity.split != 'train': raise ValueError('recorded supervised pairs require training partition')
    inp = problem.input
    states = forecast_states(problem,reference)
    context = problem.context(inp['observation_cutoff'])
    if context_mode == 'enriched':
        if enrichment is None: raise ValueError('required enrichment missing; no fallback')
        context = enriched_context(problem,enrichment,inp['observation_cutoff'])
    elif context_mode != 'public_base_for_offline_audit':
        raise ValueError('unsupported context mode')
    context_sha = digest(context)
    layout_sha = layout.sha256
    vectors = [layout.flatten(s,inp) for s in states]
    for i,(a,b) in enumerate(zip(states,states[1:])):
        transition = digest((identity.domain,identity.group_id,a['timestamp'],b['timestamp']))
        count = multiplicities[transition]
        if type(count) is not int or count < 1: raise ValueError('invalid transition multiplicity')
        pair_id = digest((identity.sample_id,transition,layout_sha,context_sha))
        yield RecordedPair(identity,pair_id,transition,a['timestamp'],b['timestamp'],a['state_id'],b['state_id'],
            vectors[i],vectors[i+1],context,layout_sha,provenance,
            1.0 if duplicate_policy == 'equal_question_pairs' else 1/count,context_mode)

class TrainingSequenceReader:
    def __init__(self, catalog, domain, layout, *, duplicate_policy,
                 context_mode, enrichments=None):
        if duplicate_policy not in ('inverse_transition_multiplicity', 'equal_question_pairs'):
            raise ValueError('explicit supported weighting required')
        self.duplicate_policy = duplicate_policy
        self.catalog, self.domain, self.layout = catalog,domain,layout
        if context_mode not in ('enriched','public_base_for_offline_audit'): raise ValueError('explicit context mode required')
        if context_mode == 'enriched' and enrichments is None: raise ValueError('enrichment required; no fallback')
        self.context_mode,self.enrichments = context_mode,enrichments

    def __iter__(self):
        multiplicities = Counter()
        for problem,ref,identity in self.catalog.records(self.domain,'train'):
            states = forecast_states(problem,ref)
            for a,b in zip(states,states[1:]):
                multiplicities[digest((identity.domain,identity.group_id,a['timestamp'],b['timestamp']))] += 1
        provenance = digest({'release':self.catalog.identity,'files':self.catalog.files(self.domain,'train'),
            'layout':self.layout.sha256,'window':'cutoff_then_reference','weight':self.duplicate_policy,
            'reader_source_sha256':file_hash(__file__)})
        for problem,ref,identity in self.catalog.records(self.domain,'train'):
            enrichment = None if self.enrichments is None else self.enrichments.get(problem.sample_id)
            enriched_provenance = digest({'source':provenance,'context_mode':self.context_mode,'enrichment':enrichment})
            yield from make_pairs(problem,ref,identity,self.layout,enriched_provenance,multiplicities,
                                  context_mode=self.context_mode,enrichment=enrichment,
                                  duplicate_policy=self.duplicate_policy)

class EvaluatorTruthReader:
    mode = 'recorded_state_diagnostic_not_autonomous_forecasting'
    def __init__(self, catalog, domain, split):
        self.catalog,self.domain,self.split = catalog,domain,split

    def __iter__(self):
        yield from self.catalog.records(self.domain,self.split)

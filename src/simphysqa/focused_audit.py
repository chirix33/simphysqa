"""Focused packet extraction and strict independent rating forms; offline only."""
import argparse
from collections import Counter
from copy import deepcopy
import csv
from hashlib import sha256
from html import escape
import io
from pathlib import Path

from .dataset import pointer
from .io import DOMAINS, QUESTION_TYPES, canonical, digest, external, read
from .spq01a import retained, verify_manifest

VERSION = 'simphysqa-focused-extraction/1.0.0'
CRITERIA = ('global_context', 'trajectory_language', 'question_type_wording',
            'timestamp_language', 'state_event_descriptions')
ERRORS = ('factual_contradiction', 'unsupported_claim', 'wrong_entity', 'wrong_time',
          'wrong_unit', 'wrong_frame', 'misleading_event_semantics', 'question_type_mismatch',
          'readability', 'missing_required_field', 'other')
COLUMNS = ('packet_id', 'sample_id', 'packet_sha256', 'reviewer_id', 'phase',
           'judgment', 'criteria', 'error_categories', 'source_locations', 'comments')
REVIEWERS = ('R1', 'R2', 'R3')
EVENT_KEYS = ('event_id', 'event_type', 'event_description', 'event_description_status',
              'temporal_relationship', 'target_entity_ids', 'link_id', 'bindings',
              'event_description_bindings')


def extract(packet, packet_sha256, source_uri):
    """Use exported packet keys verbatim. Missing fields are explicit, never fabricated."""
    missing = []
    errors = []
    def field(obj, key, path):
        if key not in obj:
            missing.append(path+'/'+key)
            return None
        return deepcopy(obj[key])
    inp = packet['structured_inputs']
    lang = packet['language_annotations']
    meta = packet['verification']['metadata']
    family = packet['question_type']
    if family not in QUESTION_TYPES:
        errors.append('noncanonical_question_type')
    result = {'extraction_version': VERSION, 'sample_id': packet['sample_id'],
              'packet_id': packet['packet_id'], 'question_type': family,
              'domain': field(inp, 'domain', '/structured_inputs'),
              'group_id': field(meta, 'split_group_id', '/verification/metadata'),
              'split': field(meta, 'split', '/verification/metadata'),
              'version_hash_metadata': {'packet_sha256': packet_sha256,
                  'annotation_version': field(packet, 'annotation_version', ''),
                  'export_version': field(packet, 'export_version', '')},
              'structured_inputs': {'global_context': field(inp, 'global_context', '/structured_inputs')},
              'language_annotations': {'trajectory': field(lang, 'trajectory', '/language_annotations')},
              'qa': {'question': field(packet['qa'], 'question', '/qa')},
              'states': [], 'source_packet': source_uri,
              'rating_scope': list(CRITERIA),
              'evidence': {'entities': field(inp, 'entities', '/structured_inputs'),
                           'controller': field(inp, 'controller', '/structured_inputs'),
                           'known_events': field(inp, 'known_events', '/structured_inputs'),
                           'observation_cutoff': field(inp, 'observation_cutoff', '/structured_inputs'),
                           'coordinate_convention': field(inp, 'coordinate_convention', '/structured_inputs')},
              'auditor_only_extra_evidence': source_uri}
    # All whitelisted public declarations retained exactly; extra gold/trace roots never copied.
    trajectory = result['language_annotations']['trajectory']
    if not isinstance(trajectory, dict):
        errors.append('missing_or_invalid_trajectory')
    else:
        for key in ('text', 'bindings'):
            field(trajectory, key, '/language_annotations/trajectory')
        if not isinstance(trajectory.get('text'), str) or not trajectory['text'].strip():
            errors.append('empty_or_nonstring_trajectory_language')
    timestamps = field(lang, 'timestamps', '/language_annotations')
    timestamps = timestamps if isinstance(timestamps, list) else []
    by_id = {}
    for i, sentence in enumerate(timestamps):
        sid = field(sentence, 'state_id', '/language_annotations/timestamps/'+str(i))
        if sid in by_id:
            errors.append('duplicate_timestamp_state_id:'+str(sid))
        by_id[sid] = (i, sentence)
    state_ids = set()
    for i, state in enumerate(inp['states']):
        base = '/structured_inputs/states/'+str(i)
        out = {k: field(state, k, base) for k in ('state_id', 'timestamp', 'context', 'measurements', 'relations', 'linked_events')}
        sid = out['state_id']
        if sid in state_ids:
            errors.append('duplicate_public_state_id:'+str(sid))
        state_ids.add(sid)
        if sid not in by_id:
            missing.append('/language_annotations/timestamps[state_id='+str(sid)+']')
            out['timestamp_language'] = None
        else:
            j, sentence = by_id[sid]
            out['timestamp_language'] = deepcopy(sentence)
            for key in ('timestamp', 'text', 'bindings'):
                field(sentence, key, '/language_annotations/timestamps/'+str(j))
            if canonical(sentence.get('timestamp')) != canonical(out['timestamp']):
                errors.append('timestamp_language_time_mismatch:'+str(sid))
            if not isinstance(sentence.get('text'), str) or not sentence['text'].strip():
                errors.append('empty_or_nonstring_timestamp_language:'+str(sid))
        for j, measurement in enumerate(out['measurements'] or []):
            for key in ('entity_id', 'name', 'value', 'unit', 'frame'):
                field(measurement, key, base+'/measurements/'+str(j))
        for j, event in enumerate(out['linked_events'] or []):
            for key in EVENT_KEYS:
                field(event, key, base+'/linked_events/'+str(j))
        result['states'].append(out)  # Includes states with zero linked events.
    if set(by_id) - state_ids:
        errors.append('timestamp_language_has_extra_states')
    # Resolve every emitted public binding against its actual exported input namespace.
    resolved = []
    def bindings(obj, location):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ('bindings', 'event_description_bindings'):
                    if not isinstance(value, list):
                        errors.append('invalid_binding_list:'+location+'/'+key)
                        continue
                    for path in value:
                        try:
                            val = pointer(inp, path)
                        except (KeyError, IndexError, TypeError, ValueError):
                            errors.append('unresolved_binding:'+location+':'+str(path))
                        else:
                            resolved.append({'location': location+'/'+key, 'pointer': path, 'value_sha256': digest(val)})
                else:
                    bindings(value, location+'/'+key)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                bindings(value, location+'/'+str(i))
    bindings(lang, '/language_annotations')
    bindings(inp, '/structured_inputs')
    result['evidence_resolution'] = resolved
    if family == 'clarification':
        stages = field(packet, 'two_stage_task', '')
        if isinstance(stages, dict):
            result['clarification'] = {k: field(stages, k, '/two_stage_task') for k in (
                'initial_view', 'reference_clarification_question', 'reference_question_origin',
                'recorded_reply', 'resolved_view')}
            result['clarification']['initial_question'] = stages['initial_view']['input']['question']
            result['clarification']['resolved_question'] = stages['resolved_view']['input']['resolved_question']
            if stages.get('reference_question_origin') != 'authored_reference_not_actual_model_response':
                errors.append('clarification_origin_missing_or_misrepresented')
            # These views are public, but the authored clarification is an auditor-only reference.
        else:
            errors.append('missing_clarification_stages')
    result['missing_required_fields'] = sorted(set(missing))
    result['validation_errors'] = errors
    return result


def blank_forms(assignments, phase):
    if phase not in ('formal', 'development_extraction_check'):
        raise ValueError('invalid rating phase')
    if len({a['packet_id'] for a in assignments}) != len(assignments):
        raise ValueError('duplicate packet assignment')
    outputs = {}
    for reviewer in REVIEWERS:
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n')
        writer.writeheader()
        for a in assignments:
            writer.writerow({k: a[k] for k in ('packet_id', 'sample_id', 'packet_sha256')} |
                            {'reviewer_id': reviewer, 'phase': phase})
        outputs[reviewer] = stream.getvalue().encode()
    return outputs


def validate_form(data, assignments, reviewer, phase):
    if reviewer not in REVIEWERS:
        raise ValueError('reviewer identity must be R1/R2/R3')
    expected = {a['packet_id']: a for a in assignments}
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig'), newline=''))
    if tuple(reader.fieldnames or ()) != COLUMNS:
        raise ValueError('rating columns mismatch')
    seen = set()
    ratings = []
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError('malformed CSV row')
        if row['packet_id'] not in expected or row['packet_id'] in seen:
            raise ValueError('unknown or duplicate rating assignment')
        seen.add(row['packet_id'])
        a = expected[row['packet_id']]
        if any(row[k] != a[k] for k in ('sample_id', 'packet_sha256')) or row['reviewer_id'] != reviewer or row['phase'] != phase:
            raise ValueError('reviewer/phase/packet/hash mismatch')
        if not row['judgment']:
            if any(row[k] for k in ('criteria', 'error_categories', 'source_locations', 'comments')):
                raise ValueError('findings without primary judgment')
            continue
        if row['judgment'] not in ('acceptable', 'material_error'):
            raise ValueError('invalid primary judgment')
        entries = [s.split('=', 1) for s in row['criteria'].split(';') if s]
        if any(len(s) != 2 for s in entries) or len(entries) != len(CRITERIA) or len({s[0] for s in entries}) != len(entries):
            raise ValueError('duplicate/missing criterion finding')
        findings = dict(entries)
        if set(findings) != set(CRITERIA) or any(v not in ('acceptable', 'material_error', 'not_applicable') for v in findings.values()):
            raise ValueError('invalid criterion findings')
        categories = [s for s in row['error_categories'].split(';') if s]
        if len(categories) != len(set(categories)) or not set(categories) <= set(ERRORS):
            raise ValueError('invalid error categories')
        if row['judgment'] == 'acceptable' and ('material_error' in findings.values() or categories):
            raise ValueError('acceptable contradicts findings')
        if row['judgment'] == 'material_error' and (not categories or not row['comments'].strip() or not row['source_locations'].strip()
                                                     or 'material_error' not in findings.values()):
            raise ValueError('material error needs criterion, category, location and comment')
        ratings.append({**row, 'criteria': findings, 'error_categories': categories})
    if seen != set(expected):
        raise ValueError('form must retain every assignment; missing judgments use blank rows')
    return {'reviewer_id': reviewer, 'phase': phase, 'collected': len(ratings), 'blank': len(seen)-len(ratings),
            'ratings': ratings, 'source_form_sha256': sha256(data).hexdigest(),
            'kind': 'original_independent', 'adjudication': 'separate_table_only'}


def export_saved(artifacts, output):
    """Integration evidence on excluded saved development packets, never formal items."""
    from .formal_sampling import save_bytes, file_hash
    output = external(output)
    config = read(Path(__file__).resolve().parents[2]/'configs/simphysqa/development_artifacts.json')
    focused = []
    assignments = []
    sections = []
    for relative in config['roots'].values():
        root = artifacts/relative/'audit-development'
        info = verify_manifest(root)
        for assignment in info['assignments']:
            path = root/'packets'/(assignment['packet_id']+'.json')
            packet = read(path)
            packet_hash = file_hash(path)
            evidence = 'auditor-only/'+path.name
            out = extract(packet, packet_hash, evidence)
            if out['missing_required_fields'] or out['validation_errors']:
                raise ValueError('extraction validation: '+str((out['missing_required_fields'], out['validation_errors'])))
            out['usage'] = 'excluded_development_extraction_validation_not_formal_sample'
            focused.append(out)
            assignments.append({**assignment, 'phase': 'development_extraction_check', 'packet_sha256': packet_hash})
            save_bytes(output/evidence, path.read_bytes())
            retained(output/'items'/path.name, out)
            # Focused source values rendered separately from gold/private evidence.
            body = '<h2>'+escape(out['packet_id'])+'</h2><p>'+escape(out['qa']['question'])+'</p>'
            body += '<h3>Physical/global context</h3><pre>'+escape(canonical(out['structured_inputs']).decode())+'</pre>'
            body += '<h3>Trajectory language</h3><pre>'+escape(canonical(out['language_annotations']).decode())+'</pre>'
            body += '<h3>Public states, timestamp language and state–event links</h3><pre>'+escape(canonical(out['states']).decode())+'</pre>'
            body += '<h3>Declared schedule/controller evidence</h3><pre>'+escape(canonical(out['evidence']).decode())+'</pre>'
            if 'clarification' in out:
                body += '<h3>Authored clarification stages; no model conversation executed</h3><pre>'+escape(canonical(out['clarification']).decode())+'</pre>'
            body += '<p><a href="../'+evidence+'">Auditor-only extra evidence (outside primary scope)</a></p>'
            save_bytes(output/'items'/(path.stem+'.html'), ('<!doctype html><meta charset="utf-8"><style>body{max-width:1000px;margin:2em auto;font:16px system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'+body).encode())
            sections.append('<li><a href="items/'+path.stem+'.html">'+escape(out['domain']+' / '+out['question_type']+' / '+out['packet_id'])+'</a></li>')
    retained(output/'focused.json', focused)
    save_bytes(output/'focused.jsonl', b''.join(canonical(r) for r in focused))
    for reviewer, data in blank_forms(assignments, 'development_extraction_check').items():
        save_bytes(output/'forms'/(reviewer+'.csv'), data)
        checked = validate_form(data, assignments, reviewer, 'development_extraction_check')
        if checked['collected'] != 0 or checked['blank'] != 56:
            raise ValueError('blank forms miscounted')
    save_bytes(output/'index.html', ('<!doctype html><meta charset="utf-8"><h1>Focused extraction: software integration on 56 excluded development items</h1><p>Not formal review. 0/140 formal packets. Generator identities omitted; authored turns are references. No ratings.</p><ul>'+''.join(sections)+'</ul>').encode())
    files = {p.relative_to(output).as_posix(): file_hash(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
    retained(output/'manifest.json', {'version': VERSION, 'phase': 'development_extraction_check',
             'assignments': assignments, 'files': files, 'formal_items': 0,
             'ratings_status': 'blank_not_collected', 'complete_extractions': len(focused),
             'missing_required_fields': 0, 'binding_failures': 0})
    return {'development_extractions': len(focused), 'formal_extractions': 0,
            'resolved_public_bindings': sum(len(r['evidence_resolution']) for r in focused),
            'blank_per_reviewer': len(assignments), 'ratings_collected': 0}


def import_form(packet_root, form, reviewer, output=None):
    info = verify_manifest(packet_root)
    phase = info['phase']
    if phase == 'formal' and (len(info['assignments']) != 140 or not info.get('final_identity_frozen')):
        raise ValueError('formal packet identities must be frozen before import')
    result = validate_form(form.read_bytes(), info['assignments'], reviewer, phase)
    result['packet_manifest_sha256'] = digest(info)
    if output is not None:
        if not result['collected']:
            raise ValueError('blank form validates as uncollected; no submission imported')
        output = external(output)
        from .formal_sampling import save_bytes
        from .job import locked
        with locked(output/'.imports.lock'):
            target = output/reviewer
            target.mkdir(parents=True, exist_ok=False)  # Blocks duplicate reviewer submissions globally.
            save_bytes(target/'original.csv', form.read_bytes())
            retained(target/'ratings.json', result)
    return {k: v for k, v in result.items() if k != 'ratings'}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('check-saved-extraction')
    export.add_argument('--artifacts', type=Path, required=True)
    export.add_argument('--output', type=Path, required=True)
    imp = sub.add_parser('import-ratings')
    imp.add_argument('--packets', type=Path, required=True)
    imp.add_argument('--form', type=Path, required=True)
    imp.add_argument('--reviewer', choices=REVIEWERS, required=True)
    imp.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = export_saved(args.artifacts, args.output) if args.command == 'check-saved-extraction' else import_form(args.packets, args.form, args.reviewer, args.output)
    print(canonical(result).decode(), end='')


if __name__ == '__main__':
    main()

"""Register the separate completed Llama diagnostic, preserving prior records."""
from p12_common import *
from llama_qualification import RUN, CONDITION, MODEL, REVISION, config
import shutil


def main():
    config()
    path = ROOT/'configs/local_answers_p12.lock.json'
    historical = RUN/'historical-local-answers.lock.json'
    current = load(path)
    qualification_path = RUN/'local'/CONDITION/'qualification.json'
    acquisition_path = RUN/'model-acquisition.json'
    qualification = load(qualification_path)
    acquisition = load(acquisition_path)[MODEL]
    if qualification['requests'] != 8 or not qualification['diagnostic_only']:
        raise ValueError('expected eight-question diagnostic')
    if not qualification['status'].startswith('complete') or acquisition['status'] != 'available':
        raise ValueError('qualification incomplete')
    if qualification['settings']['revision'] != REVISION or acquisition['revision'] != REVISION:
        raise ValueError('checkpoint pin changed')
    if not historical.exists():
        if current[CONDITION]['status'] != 'blocked':
            raise ValueError('missing historical blocked registry')
        shutil.copyfile(path, historical)
    old = load(historical)
    qwen_keys = ('qwen3_8b_direct', 'qwen3_8b_thinking')
    if any(current[k] != old[k] for k in qwen_keys):
        raise ValueError('unrelated Qwen registry changed')
    entry = {**old[CONDITION], 'acquisition': acquisition,
             'qualified_settings': qualification['settings'], 'status': qualification['status'],
             'qualification_root': str(RUN),
             'qualification_sha256': file_hash(qualification_path),
             'acquisition_sha256': file_hash(acquisition_path),
             'diagnostic_valid_answers': qualification['valid_answers'], 'diagnostic_requests': 8}
    if current[CONDITION] not in (old[CONDITION], entry):
        raise ValueError('unrecognized current Llama registry; preserve and review')
    save(path, {**current, CONDITION: entry})
    shutil.copyfile(path, RUN/'qualified-local-answers.lock.json')
    from p12_local import qualified_artifact_root
    if qualified_artifact_root(CONDITION) != RUN:
        raise ValueError('qualified root lookup failed')
    integration_source = snapshot('llama-qualified-artifact-registration', output=RUN)
    save(RUN/'registration.json', {
        'historical_lock_sha256': file_hash(historical), 'qualified_lock_sha256': file_hash(path),
        'integration_source': integration_source, 'generation_source': qualification['source'],
        'qwen_entries_unchanged': True, 'historical_qualification_root_unchanged': str(OUT),
        'qualification_root': str(RUN), 'model_calls': 0,
        'runtime_qualification_complete': True, 'valid_answers': qualification['valid_answers'],
        'full_study_authorized': False})
    print('Registered separate Llama diagnostic; Qwen entries unchanged; zero model calls.')


if __name__ == '__main__':
    main()

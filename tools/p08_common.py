"""Shared paths/provenance for the authorized P08 execution, not model code."""
import json
import random
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from phi_jepa.artifacts import digest, canonical
from phi_jepa.pilot_budget import PilotBudget, BudgetExceeded, save
from phi_jepa.integration.readers import ReleaseCatalog, file_hash
from phi_jepa.integration.layout import StateLayout
NATIVE = Path('/home/aashraf/phi-jepa')
RUN = NATIVE / 'p08-learning-01'
CONFIG = json.loads((ROOT / 'configs/learning_pilot_p08.json').read_text())


def load(path): return json.loads(Path(path).read_text())
def budget(): return PilotBudget(RUN, CONFIG)
def layout():
    m = load(ROOT / 'docs/reviews/artifacts/P02a/tethered_load.state_plus_fixed_conditioning.json')
    return StateLayout.from_manifest(m, digest(m))
def catalog():
    c = load(ROOT / 'configs/model_training_p02a.json')
    return ReleaseCatalog(ROOT/c['export_root'], c['export_index_sha256'], c['release_manifest_sha256'])
def public_records(): return load(RUN/'selected-public.json')
def schedule(size, count):
    rng = random.Random(CONFIG['seed']); result=[]
    while len(result)<count:
        cycle=list(range(size)); rng.shuffle(cycle); result.extend(cycle)
    return result[:count]
def provenance(stage):
    paths = [*ROOT.glob('src/phi_jepa/**/*.py'), *ROOT.glob('tools/*p08*.py'), *ROOT.glob('tests/test_p*.py'), *ROOT.glob('configs/*p08*.json'),
        ROOT/'configs/custom_p06.json', ROOT/'configs/model_context_p02b.json', ROOT/'configs/model_training_p03.json',
        ROOT/'configs/baselines_p05b.json', ROOT/'configs/assessment_p04b.json']
    value = {'stage':stage, 'config_sha256':digest(CONFIG), 'selection_sha256':file_hash(RUN/'selection.json') if (RUN/'selection.json').exists() else None,
        'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines(),
        'files':{str(p.relative_to(ROOT)):file_hash(p) for p in sorted(paths)}}
    save(RUN/'source'/f'{stage}.json',value); return digest(value)


class ReadThroughCache:
    def __init__(self, primary, previous): self.primary=primary; self.previous=previous
    def read(self, key):
        value=self.primary.read(key)
        return self.previous.read(key) if value is None else value
    def write(self, key, value): return self.primary.write(key,value)

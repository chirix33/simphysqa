"""Copy review-sized P08 evidence; keep full original checkpoints native."""
import shutil
from p08_common import *

destination=ROOT/'docs/reviews/artifacts/P08'; destination.mkdir(parents=True,exist_ok=True)
for name in ('selection.json','config.json','encoding-report.json','preflight.json','budget.json','schedule-status.json','reporting-status.json','tests-preflight.log','tests-final.log','reporting-requirements.txt'):
    path=RUN/name
    if path.exists(): shutil.copy2(path,destination/name)
for name in ('evaluation','source','launches','provider-ledgers'):
    if (RUN/name).exists(): shutil.copytree(RUN/name,destination/name,dirs_exist_ok=True)
for folder in (RUN/'numerical').iterdir():
    target=destination/'numerical'/folder.name; target.mkdir(parents=True,exist_ok=True)
    for name in ('fit.json','history.json','initialization.json','forecast-summary.json'):
        if (folder/name).exists(): shutil.copy2(folder/name,target/name)
    for kind in ('training','deployment'):
        if (folder/kind/'latest.json').exists():
            (target/kind).mkdir(exist_ok=True); shutil.copy2(folder/kind/'latest.json',target/kind/'latest.json')
for method in ('coconut_inspired_t5_gru','codi_inspired_t5_distillation'):
    for phase in ('diagnostic','broad'):
        folder=RUN/'custom'/method/phase; target=destination/'custom'/method/phase; target.mkdir(parents=True,exist_ok=True)
        for name in ('fit.json','history.json','eval-losses.json','initialization.json','identity.json','inference-report.json'):
            if (folder/name).exists(): shutil.copy2(folder/name,target/name)
        if (folder/'generations').exists(): shutil.copytree(folder/'generations',target/'generations',dirs_exist_ok=True)
        if (folder/'checkpoint/latest.json').exists():
            (target/'checkpoint').mkdir(exist_ok=True); shutil.copy2(folder/'checkpoint/latest.json',target/'checkpoint/latest.json')
for name in ('answers','assessment'):
    if (RUN/name).exists(): shutil.copytree(RUN/name,destination/name,dirs_exist_ok=True)
save(destination/'native-forecast-identities.json',{'native_run':str(RUN),'files':{str(p.relative_to(RUN)):{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in sorted(RUN.glob('numerical/*/forecasts/*.json'))},
    'purpose':'Original augmented predictions remain native and separate from answer-provider outputs; these hashes identify every saved forecast.'})
originals=load(ROOT/'docs/reviews/artifacts/P07/sources.json')
for filename,identity in originals.items(): assert file_hash(Path(filename))==identity['sha256'],filename
files={str(p.relative_to(destination)):{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in destination.rglob('*') if p.is_file() and p.name!='manifest.json'}
native_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
export_bytes=sum(v['bytes'] for v in files.values()); assert native_bytes+export_bytes < CONFIG['caps']['artifact_bytes']
save(destination/'manifest.json',{'native_run':str(RUN),'original_P07_sources_unchanged':len(originals),'native_bytes':native_bytes,'export_bytes':export_bytes,
    'implementation_base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'source_identity':'per-stage content hashes under source/; includes committed audit fixes plus new working-tree pilot code',
    'checkpoints':'content-addressed native files; only pointers/identities copied into review bundle','files':files})
print(json.dumps({'review_files':len(files),'native_bytes':native_bytes,'export_bytes':export_bytes,'original_sources_verified':len(originals)}))

"""Copy bounded P12 evidence into the handoff, excluding weights and test truths."""
from p12_common import *
import shutil

def main():
    dest=ROOT/'docs/reviews/artifacts/P12';dest.mkdir(parents=True,exist_ok=True)
    excluded={'confirmation-public.json','unused-confirmation-candidates.json'}
    files=[p for p in OUT.glob('*.json') if p.name not in excluded]
    files.extend(OUT.glob('*.log'))
    for name in ('local','evaluation','sources'):
        files.extend(p for p in (OUT/name).rglob('*') if p.is_file())
    for path in files:
        target=dest/path.relative_to(OUT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    save(dest/'artifact-index.json',{'native_root':str(OUT),'source_identity':implementation_identity(),
         'files':{str(p.relative_to(OUT)):file_hash(p) for p in files},'bytes':sum(p.stat().st_size for p in files),
         'omitted':'local model weights; original historical runs; regeneration of confirmation public inputs uses the frozen release and cohort IDs'})
    print({'evidence_files':len(files),'bytes':sum(p.stat().st_size for p in files),'destination':str(dest)})

if __name__=='__main__':main()

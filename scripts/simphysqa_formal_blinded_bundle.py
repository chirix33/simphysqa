"""Exclusive blinded reviewer distribution, separate from organizer protocol/accounting."""
import argparse
from pathlib import Path
from simphysqa.io import canonical,read,external
from simphysqa.formal_sampling import save_bytes,file_hash
from simphysqa.spq01a import retained,verify_manifest
from simphysqa.focused_audit import validate_form


def build(delivery,output):
    output=external(output);info=verify_manifest(delivery)
    if not info['final_identity_frozen'] or len(info['assignments'])!=140:raise ValueError('no ready140-item delivery to distribute')
    prefixes=('review-pages/','focused-items/','public-items/','auditor-only/','forms/')
    singles={'review-index.html','focused.json','focused.jsonl','reviewer-guide.md','analysis-specification.md'}
    copied=[]
    for name,expected in info['files'].items():
        if name in singles or name.startswith(prefixes):
            source=delivery/name;data=source.read_bytes()
            if file_hash(source)!=expected:raise ValueError('source distribution hash changed')
            if b'gpt-5.6-sol' in data or b'annotation_provenance' in data or b'credential_reference' in data:raise ValueError('organizer/generator identity present:'+name)
            save_bytes(output/name,data);copied.append(name)
    # Human pages use this path; importer runs later only on actual independently submitted copies.
    commands='All three forms are blank and contain the same140 assignments. Assign R1/R2/R3 identities separately. Copy your own form before editing and submit independently before discussion.\n\nOrganizer validation/import commands (PYTHONPATH=src, CPU environment):\n'+ '\n'.join('python -m simphysqa.focused_audit import-ratings --packets "'+str(output)+'" --form "<submitted-'+r+'.csv>" --reviewer '+r+' --output "<new-external-original-submissions-root>"' for r in ('R1','R2','R3'))+'\nOmit --output to validate only. Blank forms never count as acceptable ratings. Original submissions, discussion, adjudication and corrections remain separate immutable records.\n'
    save_bytes(output/'rating-import-commands.txt',commands.encode())
    for r in ('R1','R2','R3'):
        checked=validate_form((output/'forms'/(r+'.csv')).read_bytes(),info['assignments'],r,'formal')
        if checked['collected'] or checked['blank']!=140:raise ValueError('nonblank or incomplete distribution form')
    retained(output/'manifest.json',{'version':'SPQ05-blinded-review-distribution/1.0.0','phase':'formal',
             'final_identity_frozen':True,'assignments':info['assignments'],'reviewer_slots':['R1','R2','R3'],
             'ratings_status':'blank_not_collected','scope':'Focused physical/global context, trajectory/question/type/timestamp/state-event descriptions. Private gold corroboration separate. No comprehensive answer/trace/benchmark audit.',
             'source_delivery_manifest_sha256':file_hash(delivery/'manifest.json'),
             'files':{p.relative_to(output).as_posix():file_hash(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='manifest.json'}})
    verify_manifest(output)
    print(canonical({'blinded_files':len(copied),'formal_items':140,'identical_assignments_per_reviewer':140,'uncollected_ratings':420,'generator_identity_exposed':False}).decode())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--delivery',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.delivery,a.output)

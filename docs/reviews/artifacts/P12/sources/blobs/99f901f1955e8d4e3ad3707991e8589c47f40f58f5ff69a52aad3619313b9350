"""Full-population numerical vectorization timing. No enrichment, training or weights."""
from p12_common import *
import time,resource
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import forecast_states

def main():
    cat=catalog();start=time.monotonic();records=[]
    for domain in sorted({d for d,s in cat.partitions}):
        manifest=load(ROOT/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json')
        layout=StateLayout.from_manifest(manifest,digest(manifest));started=time.perf_counter();pairs=0;vectors=[]
        for p,ref,ident in cat.records(domain,'train'):
            if time.monotonic()-start>600:raise TimeoutError('preparation profile cap')
            states=forecast_states(p,ref);pairs+=len(states)-1
            vectors.extend(layout.flatten(state,p.input) for state in states)
        row={'domain':domain,'training_pairs':pairs,'vectors':len(vectors),'width':layout.d,
             'seconds':time.perf_counter()-started,'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
             'meaning':'full training reference IO and numerical vectorization only; no context substitute or optimizer; vectors discarded'}
        records.append(row);save(OUT/'preparation-profile.json',records);print(row,flush=True);del vectors

if __name__=='__main__':main()

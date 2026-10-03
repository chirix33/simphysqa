"""Configuration/provenance for a new budget; never mutates P07/P08/P09 runs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from phi_jepa.artifacts import digest,canonical
from phi_jepa.integration.readers import file_hash,ReleaseCatalog
from phi_jepa.integration.layout import StateLayout
from phi_jepa.pilot_budget import PilotBudget,save


def load(path): return json.loads(Path(path).read_text())


def execution_sources(config_path):
    configs=['qualification_p10_continuation.json','model_training_p02a.json','model_context_p02b.json','custom_p06.json',
        'baselines_p05b.json','assessment_p04b.json','core-wsl-p02b.lock.txt','coconut-custom-p06.lock.txt','codi-custom-p06.lock.txt']
    assets=['docs/assets/p04a_answer_v1.json','docs/assets/clarification_v1.json','docs/assets/prompts.json','docs/assets/judge_schema.json',
        load(ROOT/'configs/model_context_p02b.json')['enrichment_asset']]
    return list(dict.fromkeys([*ROOT.glob('src/phi_jepa/**/*.py'),*ROOT.glob('tools/p10*.py'),*ROOT.glob('configs/report-p10.lock.txt'),ROOT/'tools/run_pipeline.py',Path(config_path),
        *[ROOT/'configs'/name for name in configs],*[ROOT/name for name in assets]]))


def restored_history(folder,updates):
    """Keep uncheckpointed work as evidence before continuing a saved state."""
    path=Path(folder)/'history.json'
    if not path.exists(): return []
    history=load(path)
    if len(history)>updates:
        save(Path(folder)/'recovery'/f'history-{digest(history)}-restore-{updates}.json',
            {'restored_update':updates,'historical_rows':history,'uncheckpointed_rows':len(history)-updates,
             'meaning':'Previously executed updates retained as evidence; not claimed to survive checkpoint restoration.'})
    return history[:updates]


def guard_deployment_io():
    """Fail closed if a standalone inference process opens evaluator secrets.

    Training diagnostics deliberately do not install this guard. It is an
    executable separation check in addition to the typed public interfaces.
    """
    def audit(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes,os.PathLike)): return
        value=os.fsdecode(args[0]).replace('\\','/').lower(); parts=value.split('/')
        if 'private' in parts or parts[-1] in ('evaluator.jsonl','references.jsonl','reference.jsonl','openai_key.txt','.env'):
            raise RuntimeError('deployment_reference_or_credential_access_forbidden')
    sys.addaudithook(audit)


class QualificationBudget(PilotBudget):
    def size(self):
        size=super().size(); exported=ROOT/self.config.get('shared_export_directory',self.config['export_directory'])
        if exported.exists(): size+=sum(p.lstat().st_size for p in exported.rglob('*') if p.is_file() or p.is_symlink())
        # Separate setup artifacts are still part of the aggregate allowance.
        for path in self.root.glob('**/external-package-cache.json'): size+=load(path)['bytes']
        return size

    def transport(self,original):
        def bounded(payload,timeout):
            from phi_jepa.providers.openai_enrichment import response_result
            state=self.check(); caps=self.config['caps']; rows=state['provider']
            # Explicit Standard tier. Reserve/charge all input at the cache-write
            # upper rate, without relying on a cached-input discount or invoice.
            payload={**payload,'service_tier':'default'}
            inputs=len(canonical(payload))+4096; outputs=payload['max_output_tokens']
            rate_in,rate_out=(10,30) if inputs>272000 else (5,20)
            cost=(inputs*rate_in+outputs*rate_out)/1e6
            if len(rows)>=caps['provider_attempts'] or any(sum(r[k] for r in rows)+v>caps[c] for k,v,c in (
                ('charged_input',inputs,'provider_input_tokens'),('charged_output',outputs,'provider_output_tokens'),('charged_usd',cost,'provider_usd'))): self.stop('provider_reservation_cap')
            index=len(rows); rows.append({'model':payload['model'],'service_tier':'default','reserved_input':inputs,'reserved_output':outputs,'reserved_usd':cost,
                'request_payload_sha256':digest(payload),
                'charged_input':inputs,'charged_output':outputs,'charged_usd':cost,'usage_known':False,'started':time.time(),
                'pricing_basis':'2026-09-25 official GPT-5.6 Sol Standard; conservative cache-write input rate; no discounts; not an invoice'})
            save(self.path,state); cpu=time.process_time()
            try:
                body=original(payload,timeout)
                save(self.root/'provider_responses'/f'{index:04d}.json',{'request_payload_sha256':digest(payload),'response':body})
                usage=response_result(body).usage; state=self.read(); row=state['provider'][index]
                if usage.input_tokens is not None and usage.output_tokens is not None:
                    actual_rate_in,actual_rate_out=(10,30) if usage.input_tokens>272000 else (5,20)
                    charged=(usage.input_tokens*actual_rate_in+usage.output_tokens*actual_rate_out)/1e6
                    row.update(charged_input=usage.input_tokens,charged_output=usage.output_tokens,charged_usd=charged,adapter_cost_estimate=usage.cost_usd,
                        usage_known=True,returned_model=body.get('model'),response_id=body.get('id'),returned_service_tier=body.get('service_tier'))
                    if usage.input_tokens>inputs or usage.output_tokens>outputs or charged>cost or body.get('service_tier') not in (None,'default','standard'): state['stopped']='provider_reservation_violation'
                save(self.path,state); return body
            finally:
                state=self.read(); state['provider'][index]['wall_seconds']=time.time()-state['provider'][index]['started']
                state['seconds']['cpu']=state['seconds'].get('cpu',0)+time.process_time()-cpu; save(self.path,state)
        return bounded


class Run:
    def __init__(self,config):
        self.config_path=Path(config).resolve(); self.c=load(self.config_path)
        self.root=Path(self.c['run_root']); self.native=Path(self.c['native_root']); self.old=Path(self.c['previous_run'])
        self.root.mkdir(parents=True,exist_ok=True)
        if (self.root/'config.json').exists() and digest(load(self.root/'config.json'))!=digest(self.c): raise ValueError('new_config_requires_new_run_root')
        save(self.root/'config.json',self.c)
        budget_root=Path(self.c.get('shared_budget_root',str(self.root))); budget_root.mkdir(parents=True,exist_ok=True)
        self.b=QualificationBudget(budget_root,self.c)
        if self.b.read()['caps']!=self.c['caps']: raise ValueError('shared_budget_caps_mismatch')

    def layout(self):
        m=load(ROOT/f"docs/reviews/artifacts/P02a/{self.c['domain']}.state_plus_fixed_conditioning.json")
        return StateLayout.from_manifest(m,digest(m))

    def catalog(self):
        c=load(ROOT/'configs/model_training_p02a.json')
        return ReleaseCatalog(ROOT/c['export_root'],c['export_index_sha256'],c['release_manifest_sha256'])

    def rows(self): return load(self.root/'selected-public.json')
    def embedding(self,sid,mode='enriched'): return load(self.root/'embeddings'/mode/(sid+'.json'))['values']

    def methods(self):
        path=self.root/'active_methods.json'
        return load(path)['methods'] if path.exists() else self.c['answer_methods']

    def provenance(self,stage):
        paths=execution_sources(self.config_path)
        value={'stage':stage,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'config_sha256':digest(self.c),'files':{str(p.relative_to(ROOT)):file_hash(p) for p in paths},
            'selection_sha256':file_hash(self.root/'selection.json') if (self.root/'selection.json').exists() else None}
        identity=digest(value)
        save(self.root/'sources'/f'{stage}.json',value)
        save(self.root/'sources/history'/f'{identity}.json',value)
        for p in paths:
            dest=self.root/'sources/blobs'/file_hash(p)
            if not dest.exists(): dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(p.read_bytes())
        return identity

"""Offline-only verification of the final order-preserving interface; no model calls."""
from p12_answer_interface import RUN, ROOT, CONDITIONS, ASSET, settings_and_tokenizer, sources
from p12_common import load, save
from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.readers import file_hash
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.providers.constrained_local import prepare_request, decoder_schema
from phi_jepa.providers.compact_answer import value_schema, adapt_answer
import json
import faulthandler
import xgrammar as xgr
from transformers import AutoConfig


def main():
    from p10_common import guard_deployment_io
    guard_deployment_io()
    faulthandler.dump_traceback_later(45, repeat=True)
    before=file_hash(RUN/'budget.json'); records=[]
    for condition in CONDITIONS:
        settings,tokenizer=settings_and_tokenizer(condition)
        config=AutoConfig.from_pretrained(settings.model,revision=settings.revision,
            cache_dir='/home/aashraf/phi-jepa/model-cache',local_files_only=True,trust_remote_code=False)
        compiler=xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(tokenizer,vocab_size=config.vocab_size,
            stop_token_ids=tokenizer.eos_token_id))
        for row in load(RUN/'diagnostic-public.json'):
            assert row['split']=='validation'
            p=PublicProblem.parse(row['public'])
            request=json.loads(canonical(prepare_request(tokenizer,p,load(ASSET)['prompt'],settings)))
            compiled=compiler.compile_json_schema(decoder_schema(request,p))
            for unsupported in (False,True):
                sample={}
                for spec in p.input['answer_spec']:
                    schema=value_schema(p,spec)
                    v=False if spec['answer_type']=='boolean' else ([0.]*schema['minItems'] if spec['answer_type']=='vector' else 0.)
                    sample[spec['target_id']]={'status':'unsupported' if unsupported else 'supported',
                        'value':None if unsupported else v,'reason':'Offline dummy reason' if unsupported else None}
                text=json.dumps(sample); matcher=xgr.GrammarMatcher(compiled)
                assert all(matcher.accept_token(t) for t in tokenizer.encode(text,add_special_tokens=False))
                assert matcher.accept_token(tokenizer.eos_token_id)
                adapt_answer(p,text)
            print(condition, p.sample_id, 'both branches passed', flush=True)
            records.append({'condition':condition,'sample_id':p.sample_id,'request_sha256':digest(request),
                'supported_and_unsupported_grammar_paths':True,'input_tokens':len(request['input_token_ids'])})
            save(RUN/'final-offline/requests'/condition/(p.sample_id+'.json'),request)
    assert file_hash(RUN/'budget.json')==before
    current=sources()
    record={'status':'offline_checks_passed_model_validation_pending','model_calls':0,'budget_unchanged_sha256':before,
        'current_source_sha256':digest(current),'files':current,'rows':records,
        'meaning':'Corrected schema serialization only; no third model round authorized or executed.'}
    save(RUN/'final-offline/verification.json',record)
    for rel,sha in current.items():
        path=RUN/'sources/blobs'/sha
        if not path.exists():path.write_bytes((ROOT/rel).read_bytes())
    candidate=load(RUN/'candidate-interface.lock.json')
    candidate.update(version='p12-local-compact-interface-v1.1-order-preserved',freeze_ready=False,
        status='implemented_pending_validation',executed_round_two_source_sha256=candidate['source_sha256'],
        source_sha256=digest(current),offline_verification_sha256=file_hash(RUN/'final-offline/verification.json'),
        qualification_summary_applies_to='round-two v1 CPU-mask decoder; not the post-run order-preserving v1.1 correction',
        unresolved=['Qwen thinking-on exhausted all eight 2048-token budgets before final output.',
                    'Order-preserving schema transport is verified offline only; no third round permitted.'])
    save(ROOT/'configs/local_answers_p12.interface_v1.lock.json',candidate)
    save(RUN/'final-offline/candidate-interface.lock.json',candidate)
    print({'offline_request_checks':len(records),'dummy_branch_checks':2*len(records),'new_model_calls':0,
           'source_sha256':digest(current)})
    faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':main()

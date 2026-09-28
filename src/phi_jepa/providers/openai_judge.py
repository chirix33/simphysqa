"""Exact adopted V1 scenario/schema judge. It never judges trajectory accuracy."""
from dataclasses import asdict
import math
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.readers import strict_json
from .openai_enrichment import OpenAIEnrichment,ENDPOINT,response_result
from .contracts import ProviderFailure,FailureCode


def parse_judge(text):
    try: value=strict_json(text)
    except ValueError: raise ProviderFailure(FailureCode.MALFORMED_JSON) from None
    if not isinstance(value,dict) or set(value)!={'score','reason'} or type(value['score']) not in (int,float) or not math.isfinite(value['score']) or not 0<=value['score']<=1 or type(value['reason']) is not str or not value['reason'].strip():
        raise ProviderFailure(FailureCode.INVALID_OUTPUT)
    return value


class OpenAIJudge(OpenAIEnrichment):
    def judge(self, problem):
        # Literal public scenario and its existing structured public schema. This
        # checks consistency of supplied input, not forecast or retrieved schema.
        inp=problem.input
        scenario={'question':inp['question'],'global_context':inp['global_context']}
        payload={'model':self.config['model'],'store':False,'instructions':self.asset['prompt'],
            'input':canonical({'scenario':scenario,'schema':inp}).decode(),
            'reasoning':{'effort':self.config['reasoning_effort']},'max_output_tokens':self.config['max_output_tokens'],
            'text':{'format':{'type':'json_schema','name':'scenario_schema_v1','strict':True,'schema':self.asset['schema']}}}
        identity={'kind':'semantic_scope_scenario_schema_v1','endpoint':ENDPOINT,'asset':self.asset,'config':self.config,'payload':payload}
        cached=self.cache.read(identity) if self.cache is not None else None
        if cached is not None:
            self.cache_hits+=1; self._save_events(); value=parse_judge(cached['text'])
        else:
            last={}
            def operation(timeout):
                body=self.transport(payload,timeout); result=response_result(body)
                metadata={'response_id':body.get('id'),'returned_model':body.get('model'),'request_sha256':digest(identity),'usage':asdict(result.usage)}
                self.response_metadata.append(metadata); last.update(text=result.text,metadata=metadata)
                return result
            try: value=self.runner.run(digest(identity),operation,parse_judge)
            finally: self._save_events()
            if self.cache is not None: self.cache.write(identity,last)
        return {'status':'available',**value,'scope':'scenario_schema_v1','input_sha256':digest(inp),'asset_sha256':digest(self.asset)}

"""Reporting-only diagnostics /1.0.0; never modifies primary acceptance/scores."""
import json,re
from collections import Counter
from jsonschema import Draft202012Validator
from .spq06 import parse_answer
from . import clarification_evaluation as clarification,explanation_evaluation as explanation
from .scoring import distance

VERSION='SPQ06-result-diagnostics/1.0.0'

def parse_stage(raw):
 if raw is None:return {'generation':'missing','json_status':'unavailable','category':'execution_missing'},None
 generation=raw['completion_status'];value=None;error=None
 try:value,_=parse_answer(raw['raw_output'])
 except (ValueError,TypeError) as exc:error=str(exc)
 d={'generation':generation,'json_status':'parsed' if value is not None else 'failed','primary_parser_error':error,
  'category':'generation_noncompletion' if generation!='completed' else 'json_parsing_failure' if value is None else 'json_parsed',
  'raw_response_sha256':__import__('hashlib').sha256(raw['raw_output'].encode()).hexdigest()}
 if value is None:
  # An alternate extraction is ONLY a surface-format classification. Its object
  # is never accepted, scored or presented as evidence of physical correctness.
  blocks=list(re.finditer(r'```(?:json)?\s*\n([\s\S]*?)```',raw['raw_output']))
  valid=[]
  for b in blocks:
   try:
    v=json.loads(b.group(1));valid.append(b) if isinstance(v,dict) else None
   except (ValueError,TypeError):pass
  d['failure_surface']='decodable_fenced_JSON_with_prose_or_trailing_text' if valid else 'no_decodable_fenced_final_JSON'
  d['diagnostic_alternate_JSON_is_not_scored']=True
 return d,value

def schema_errors(schema,value):
 return [{'path':list(e.absolute_path),'validator':e.validator,'message':e.message,
  'kind':'unit_invalid' if 'unit' in e.absolute_path else 'frame_invalid' if 'frame' in e.absolute_path else 'type_invalid' if e.validator=='type' else 'schema_invalid'}
  for e in sorted(Draft202012Validator(schema).iter_errors(value),key=lambda e:str(list(e.absolute_path)))]

def diagnose(record,row,first,second):
 d,value=parse_stage(first);d.update(sample_id=row['sample_id'],condition_id=row['condition_id'],representation=row['input_condition'],family=row['family'],
  primary_endpoints=row['endpoints'],legacy_answer_valid=row['answer_valid'],primary_parser_unchanged=True)
 if first is None or first['completion_status']!='completed' or value is None:return d
 family=row['family']
 if family=='clarification':
  checks=clarification.inspect_stage1(record,value)
  d['first_turn_contract_valid']=checks['response_contract_valid'];d['first_turn_checks']=checks
  d['first_turn_schema_errors']=schema_errors(clarification.response_schema(),value)
  d['category']='clarification_first_turn_valid' if checks['response_contract_valid'] else 'schema_type_unit_frame_invalid'
  continuation,v2=parse_stage(second);d['continuation']=continuation
  if second is None:
   continuation['category']='conditional_unexecuted';continuation['routing_reason']=row.get('clarification_category','unavailable')
  elif second['completion_status']=='completed' and v2 is not None:
   schema=record['private']['resolved_view']['input']['interaction']['response_schema'];errors=schema_errors(schema,v2)
   continuation['schema_errors']=errors;continuation['contract_valid']=not errors
   if errors:continuation['category']='schema_type_unit_frame_invalid'
   else:
    try:result=clarification.check_stage2(record,v2);continuation['scorer_check']=result;continuation['category']='correct' if result['answer_correct_under_existing_typed_scorer'] else 'valid_but_incorrect'
    except (ValueError,KeyError,TypeError) as exc:continuation['category']='schema_type_unit_frame_invalid';continuation['validation_error']=str(exc)
  return d
 if family=='explanation':
  errors=schema_errors(explanation.response_schema(record['public']['input']['answer_spec'][0]),value);d['schema_errors']=errors
  if errors:d['category']='schema_type_unit_frame_invalid'
  elif row.get('structured_facts') is not None:
   d['category']='correct_structured_facts' if row['structured_facts']['factual_components_all_correct'] else 'valid_but_incorrect_structured_facts'
   d['factual_component_checks']=row['structured_facts']['factual_component_checks']
  else:d['category']='other_validation_failure'
  d['human_prose_quality']='uncollected';return d
 n=row.get('numerical_details')
 if n is None:d['category']='other_validation_failure';return d
 if n['status']=='abstained':d['category']='abstained';return d
 d['typed_targets']=n['targets']
 if n['valid_targets']==n['expected_targets']:
  d['category']='correct' if n['whole_question_correct'] else 'valid_but_incorrect';return d
 d['category']='schema_type_unit_frame_invalid';issues=[]
 candidates=value.get('targets',[])
 if not isinstance(candidates,list):issues.append({'kind':'schema_invalid','reason':'targets not array'});candidates=[]
 targets={v.get('target_id'):v for v in candidates if isinstance(v,dict)}
 for t in record['public']['input']['answer_spec']:
  v=targets.get(t['target_id']);truth=next(x for x in record['private']['reference']['structured_label'] if x['target_id']==t['target_id'])
  if v is None:issues.append({'target_id':t['target_id'],'kind':'schema_invalid','reason':'missing target'});continue
  for field in ('unit','frame'):
   if v.get(field)!=truth[field]:issues.append({'target_id':t['target_id'],'kind':field+'_invalid','source_value':v.get(field),'required_value':truth[field]})
  try:distance(v['value'],truth['value'],t)
  except (ValueError,KeyError,TypeError) as exc:issues.append({'target_id':t['target_id'],'kind':'type_invalid','reason':str(exc)})
 d['typed_invalid_diagnostics']=issues;return d

def summarize(rows):
 keys=sorted({(r['condition_id'],r['representation']) for r in rows});summaries=[]
 for key in keys:
  subset=[r for r in rows if (r['condition_id'],r['representation'])==key]
  summaries.append({'condition_id':key[0],'representation':key[1],'fixed_items':len(subset),
   'first_stage_categories':dict(Counter(r['category'] for r in subset)),
   'parser_failure_surfaces':dict(Counter(r['failure_surface'] for r in subset if r['category']=='json_parsing_failure')),
   'clarification_first_turn_contract_valid':sum(r.get('first_turn_contract_valid',False) for r in subset),
   'clarification_continuation_categories':dict(Counter(r['continuation']['category'] for r in subset if 'continuation' in r))})
 return {'version':VERSION,'reporting_only':True,'primary_scoring_changed':False,'items':rows,'summaries':summaries}

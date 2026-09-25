"""Public-only input and reversible typed output transport for the pinned T5."""
import json
import re
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import reject_private
from phi_jepa.integration.readers import strict_json
from phi_jepa.inference.readout import BINDING, finite

FORMAT='p06-json-ZXQ-hex-v1'


class TextCodec:
    """Escape unrepresentable characters without adding learned vocabulary.

    Z is always escaped, so the ASCII ZXQhhhhhhZXQ marker cannot collide with
    literal content. Repeated/control/boundary whitespace is protected as well.
    Tokenization is accepted only after exact decoded text equality.
    """
    def __init__(self,tokenizer): self.tokenizer=tokenizer; self.safe={}

    def encode(self,text):
        out=[]
        for i,ch in enumerate(text):
            if ch not in self.safe:
                ids=self.tokenizer.encode(ch,add_special_tokens=False)
                self.safe[ch]=bool(ids) and self.tokenizer.unk_token_id not in ids
            escape=(not self.safe[ch] or ch in 'Z\\<>' or ord(ch)>126 or ord(ch)<32 or
                (ch==' ' and (i==0 or i==len(text)-1 or text[i-1].isspace() or text[i+1].isspace())))
            out.append(f'ZXQ{ord(ch):06X}ZXQ' if escape else ch)
        return ''.join(out)

    def decode(self,text):
        def restore(match): return chr(int(match.group(1),16))
        return re.sub(r'ZXQ([0-9A-F]{6})ZXQ',restore,text)

    def tokens(self,text,limit):
        encoded=self.encode(text)
        ids=self.tokenizer.encode(encoded,add_special_tokens=True,truncation=False)
        if len(ids)>limit: raise ValueError(f'explicit_token_limit:{len(ids)}>{limit}')
        if self.tokenizer.unk_token_id in ids: raise ValueError('unknown_token')
        decoded=self.tokenizer.decode(ids[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if not ids or ids[-1]!=self.tokenizer.eos_token_id or self.decode(decoded)!=text:
            raise ValueError('lossy_tokenizer_roundtrip')
        return ids

    def generated_text(self,ids):
        ids=list(ids)
        if ids and ids[0]==self.tokenizer.pad_token_id: ids=ids[1:]
        if self.tokenizer.eos_token_id not in ids: raise ValueError('generation_missing_EOS')
        end=ids.index(self.tokenizer.eos_token_id)
        if any(x!=self.tokenizer.pad_token_id for x in ids[end+1:]): raise ValueError('tokens_after_EOS')
        if self.tokenizer.unk_token_id in ids[:end]: raise ValueError('generation_unknown_token')
        return self.decode(self.tokenizer.decode(ids[:end],skip_special_tokens=False,clean_up_tokenization_spaces=False))


def public_text(problem,enrichment):
    reject_private(enrichment)
    return canonical({'instruction':'Predict the requested typed targets from these public facts. Return the configured JSON target format.',
        'public_input':problem.input,'public_enrichment':enrichment}).decode()


def training_targets(problem,reference):
    """Training/evaluator preparation only; never called by generation."""
    expected={s['target_id']:s for s in problem.input['answer_spec']}
    labels=reference['structured_label']
    if len(labels)!=len(expected) or {r['target_id'] for r in labels}!=set(expected): raise ValueError('training_target_identity')
    rows=[]
    for label in labels:
        spec=expected[label['target_id']]
        if any(label[k]!=spec[k] for k in ('unit','frame')): raise ValueError('training_target_binding')
        rows.append({**{k:spec[k] for k in BINDING},'value':label['value']})
    student=canonical({'targets':rows}).decode()
    explanation=reference['explanation']
    if not isinstance(explanation,str) or not explanation: raise ValueError('descriptive_supervision_missing')
    teacher=canonical({'explanation':explanation,'targets':rows}).decode()
    parse_typed_answer(student,problem,explanation_required=False)
    parse_typed_answer(teacher,problem,explanation_required=True)
    return teacher,student


def parse_typed_answer(text,problem,*,explanation_required):
    value=strict_json(text)
    keys={'targets','explanation'} if explanation_required else {'targets'}
    if not isinstance(value,dict) or set(value)!=keys: raise ValueError('answer_envelope')
    if explanation_required and (not isinstance(value['explanation'],str) or not value['explanation'].strip()): raise ValueError('explanation_missing')
    expected={s['target_id']:s for s in problem.input['answer_spec']}; rows=value['targets']
    if not isinstance(rows,list) or len(rows)!=len(expected): raise ValueError('target_count')
    seen=set(); parsed=[]
    for row in rows:
        if not isinstance(row,dict) or set(row)!={*BINDING,'value'}: raise ValueError('target_fields')
        sid=row['target_id']
        if sid not in expected or sid in seen: raise ValueError('target_identity')
        seen.add(sid); spec=expected[sid]
        if any(row[k]!=spec[k] or type(row[k]) is bool for k in BINDING): raise ValueError('target_binding')
        v=row['value']; typ=spec['answer_type']
        if typ=='boolean': valid=type(v) is bool
        elif typ=='number': valid=finite(v)
        elif typ=='vector': valid=isinstance(v,list) and len(v)==(4 if spec['quantity']=='orientation' else 3) and all(map(finite,v))
        else: valid=False
        if not valid: raise ValueError('typed_value')
        parsed.append({**row,'status':'supported','reason':None,'source':'generated_baseline_prediction'})
    return {'targets':parsed,'explanation':value.get('explanation')}


def decode_result(codec,ids,problem,*,teacher=False):
    text=None
    try:
        text=codec.generated_text(ids)
        return {'status':'success','answer':parse_typed_answer(text,problem,explanation_required=teacher),'text':text}
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        return {'status':'generation_or_parse_failure','reason':str(exc),'text':text,'answer':None}


def compose_hybrid(student,teacher):
    """Teacher explanation is returned, never supplied to student generation."""
    fallback=student['status']!='success'
    chosen=teacher if fallback else student
    return {'status':chosen['status'],'reason':chosen.get('reason'),'answer':chosen.get('answer'),
        'teacher_explanation':teacher['answer']['explanation'] if teacher['status']=='success' else None,
        'teacher_status':teacher['status'],'fallback_trigger':student.get('reason') if fallback else None,
        'fallback_attempted':fallback,'fallback_used':fallback and teacher['status']=='success',
        'teacher_explanation_fed_to_student':False}

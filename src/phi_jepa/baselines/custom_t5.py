"""Notebook-derived custom models, not official Coconut/CODI reproductions."""
from dataclasses import dataclass,asdict
import torch
from torch import nn
from torch.nn import functional as F
from transformers.modeling_outputs import BaseModelOutput


@dataclass(frozen=True)
class CustomSettings:
    method: str
    seed: int=11
    latents: int=8
    teacher_ce_weight: float=1.
    student_ce_weight: float=1.
    distillation_weight: float=.5
    smoothness_weight: float=.001
    encoder_query_chunk_size: int=0

    def __post_init__(self):
        if self.method not in ('coconut_inspired_t5_gru','codi_inspired_t5_distillation') or type(self.latents) is not int or self.latents<1: raise ValueError('custom_method_or_latent_count')


def eos_positions(labels,eos_id):
    """Index of the label EOS whose shifted decoder hidden state predicts EOS."""
    if labels.ndim!=2 or labels.dtype!=torch.long: raise ValueError('label_shape_or_dtype')
    matches=labels.eq(eos_id)
    if not torch.all(matches.sum(dim=1)==1): raise ValueError('exactly_one_actual_EOS_required_no_truncation_substitute')
    positions=matches.long().argmax(dim=1)
    for row,pos in zip(labels,positions.tolist()):
        if pos==0 or torch.any(row[:pos]==-100) or torch.any(row[pos+1:]!=-100): raise ValueError('EOS_must_follow_complete_unignored_answer')
    return positions


def post_answer_hidden(hidden,labels,eos_id):
    positions=eos_positions(labels,eos_id)
    if hidden.ndim!=3 or hidden.shape[:2]!=labels.shape: raise ValueError('decoder_label_alignment')
    return hidden[torch.arange(hidden.shape[0],device=hidden.device),positions],positions


class CustomT5(nn.Module):
    def __init__(self,backbone,settings:CustomSettings):
        super().__init__(); self.t5=backbone; self.settings=settings
        if settings.encoder_query_chunk_size:
            from .t5_memory import install_query_blocks
            install_query_blocks(backbone,settings.encoder_query_chunk_size)
        d=backbone.config.d_model
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(settings.seed)
            if settings.method=='coconut_inspired_t5_gru':
                self.pool_proj=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d),nn.Tanh())
                self.latent_queries=nn.Parameter(torch.randn(settings.latents,d)*.02)
                self.latent_in=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d),nn.GELU(),nn.Linear(d,d))
                self.latent_cell=nn.GRUCell(d,d)
                self.latent_out=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d))
                self.latent_gate=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d),nn.Sigmoid())
            else:
                self.continuous_thoughts=nn.Parameter(torch.randn(settings.latents,d)*.02)
                self.input_to_thought_context=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d),nn.Tanh())
                self.thought_refiner=nn.GRUCell(d,d)
                self.thought_gate=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d),nn.Sigmoid())
                self.thought_out=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d))
                self.teacher_proj=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d))
                self.student_proj=nn.Sequential(nn.LayerNorm(d),nn.Linear(d,d))
                self.teacher_proj.requires_grad_(False)

    def manifest(self):
        return {'version':'p06-custom-v1','settings':asdict(self.settings),'backbone_config':self.t5.config.to_dict(),
            'shared_teacher_student_backbone':self.settings.method=='codi_inspired_t5_distillation',
            'teacher_projection':'fixed_seeded_checkpointed' if hasattr(self,'teacher_proj') else None,
            'alignment':'teacher_forced_post_answer_EOS_prediction_final_decoder_layer',
            'attribution':'custom notebook-inspired design; not official reproduction'}

    def enhanced_encoder(self,input_ids,attention_mask):
        enc=self.t5.encoder(input_ids=input_ids,attention_mask=attention_mask,return_dict=True)
        hidden=enc.last_hidden_state
        mask=attention_mask.unsqueeze(-1).to(hidden.dtype)
        if torch.any(mask.sum(dim=1)==0): raise ValueError('empty_public_input')
        pooled=(hidden*mask).sum(dim=1)/mask.sum(dim=1)
        vectors=[]
        if self.settings.method=='coconut_inspired_t5_gru':
            h=self.pool_proj(pooled)
            for query in self.latent_queries:
                new=self.latent_cell(self.latent_in(h+query.unsqueeze(0)),h)
                gate=self.latent_gate(new); h=gate*new+(1-gate)*h
                vectors.append(self.latent_out(h).unsqueeze(1))
        else:
            h=self.input_to_thought_context(pooled)
            for base in self.continuous_thoughts:
                new=self.thought_refiner(base.unsqueeze(0).expand(hidden.shape[0],-1),h)
                gate=self.thought_gate(new); h=gate*new+(1-gate)*h
                vectors.append(self.thought_out(h).unsqueeze(1))
        latents=torch.cat(vectors,dim=1)
        extended=BaseModelOutput(last_hidden_state=torch.cat((hidden,latents),dim=1))
        extended_mask=torch.cat((attention_mask,attention_mask.new_ones(hidden.shape[0],self.settings.latents)),dim=1)
        return extended,extended_mask,latents

    def training_losses(self,input_ids,attention_mask,*,teacher_labels,student_labels=None):
        eos=self.t5.config.eos_token_id; eos_positions(teacher_labels,eos)
        if self.settings.method=='coconut_inspired_t5_gru':
            enc,mask,latents=self.enhanced_encoder(input_ids,attention_mask)
            out=self.t5(encoder_outputs=enc,attention_mask=mask,labels=teacher_labels,return_dict=True,use_cache=False)
            smooth=(latents[:,1:]-latents[:,:-1]).float().square().mean() if self.settings.latents>1 else latents.sum()*0
            return {'loss':out.loss+self.settings.smoothness_weight*smooth,'ce_loss':out.loss,'smoothness_loss':smooth,'latents':latents}
        if student_labels is None: raise ValueError('student_training_labels_required')
        eos_positions(student_labels,eos)
        teacher=self.t5(input_ids=input_ids,attention_mask=attention_mask,labels=teacher_labels,output_hidden_states=True,return_dict=True,use_cache=False)
        teacher_hidden=teacher.decoder_hidden_states[-1]
        teacher_final,teacher_pos=post_answer_hidden(teacher_hidden,teacher_labels,eos)
        target=self.teacher_proj(teacher_final).detach()
        enc,mask,latents=self.enhanced_encoder(input_ids,attention_mask)
        student=self.t5(encoder_outputs=enc,attention_mask=mask,labels=student_labels,output_hidden_states=True,return_dict=True,use_cache=False)
        student_hidden=student.decoder_hidden_states[-1]
        student_final,student_pos=post_answer_hidden(student_hidden,student_labels,eos)
        alignment=F.mse_loss(self.student_proj(student_final).float(),target.float())
        smooth=(latents[:,1:]-latents[:,:-1]).float().square().mean() if self.settings.latents>1 else latents.sum()*0
        loss=self.settings.teacher_ce_weight*teacher.loss+self.settings.student_ce_weight*student.loss+self.settings.distillation_weight*alignment+self.settings.smoothness_weight*smooth
        return {'loss':loss,'teacher_ce':teacher.loss,'student_ce':student.loss,'alignment':alignment,'smoothness_loss':smooth,
            'teacher_hidden':teacher_hidden,'student_hidden':student_hidden,'teacher_eos_positions':teacher_pos,
            'student_eos_positions':student_pos,'teacher_target':target,'latents':latents}

    @torch.no_grad()
    def generate(self,input_ids,attention_mask,*,branch,generation):
        """No gold argument. Hybrid composition happens outside this method."""
        self.eval()
        if branch=='teacher':
            if self.settings.method!='codi_inspired_t5_distillation': raise ValueError('teacher_branch_only_codi')
            return self.t5.generate(input_ids=input_ids,attention_mask=attention_mask,**generation)
        expected='student' if self.settings.method=='codi_inspired_t5_distillation' else 'coconut'
        if branch!=expected: raise ValueError('generation_branch_method_mismatch')
        enc,mask,_=self.enhanced_encoder(input_ids,attention_mask)
        start=torch.full((input_ids.shape[0],1),self.t5.config.decoder_start_token_id,dtype=torch.long,device=input_ids.device)
        return self.t5.generate(encoder_outputs=enc,attention_mask=mask,decoder_input_ids=start,**generation)

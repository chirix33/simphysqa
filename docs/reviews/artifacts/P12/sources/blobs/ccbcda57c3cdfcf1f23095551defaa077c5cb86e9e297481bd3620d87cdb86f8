"""Exact full-key encoder attention in bounded query blocks for pinned T5.

No windowing, token filtering, position reset, new weights or approximated softmax.
Decoder/cross attention and generation caches retain Transformers implementation.
"""
from types import MethodType
import torch
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint


def install_query_blocks(backbone,chunk_size):
    if type(chunk_size) is not int or chunk_size<1: raise ValueError('encoder_query_chunk_size')
    first=backbone.encoder.block[0].layer[0].SelfAttention
    if not first.has_relative_attention_bias: raise ValueError('first_encoder_relative_bias_required')
    def forward(self,hidden_states,mask=None,key_value_states=None,position_bias=None,past_key_value=None,
                layer_head_mask=None,query_length=None,use_cache=False,output_attentions=False,cache_position=None):
        if self.is_decoder or key_value_states is not None or past_key_value is not None or use_cache or output_attentions or self.pruned_heads:
            raise ValueError('query_blocks_encoder_only_no_attention_matrix_export')
        batch,length=hidden_states.shape[:2]
        def project(layer): return layer(hidden_states).view(batch,length,self.n_heads,self.key_value_proj_dim).transpose(1,2)
        q,k,v=project(self.q),project(self.k),project(self.v)
        chunks=[]
        for start in range(0,length,chunk_size):
            positions=torch.arange(start,min(length,start+chunk_size),device=q.device)
            def attend(q_part,k_all,v_all,absolute_positions):
                # T5 deliberately omits 1/sqrt(d_k); preserve its in-place bias cast.
                scores=torch.matmul(q_part,k_all.transpose(3,2))
                bias=first.compute_bias(len(absolute_positions),length,device=q.device,cache_position=absolute_positions)
                if mask is not None: bias=bias+mask[:,:,:,:length]
                scores.add_(bias)
                weights=F.softmax(scores.float(),dim=-1).type_as(scores)
                weights=F.dropout(weights,p=self.dropout,training=self.training)
                if layer_head_mask is not None: weights=weights*layer_head_mask
                return torch.matmul(weights,v_all)
            if torch.is_grad_enabled():
                block=checkpoint(attend,q[:,:,start:start+chunk_size],k,v,positions,use_reentrant=False,preserve_rng_state=True)
            else: block=attend(q[:,:,start:start+chunk_size],k,v,positions)
            chunks.append(block)
        output=torch.cat(chunks,dim=2).transpose(1,2).contiguous().view(batch,length,self.inner_dim)
        # Following encoder layers recompute the same first-layer relative bias per
        # block, rather than retaining an LxL tensor. Gradients share its one weight.
        return self.o(output),None,None
    for block in backbone.encoder.block:
        attention=block.layer[0].SelfAttention
        attention.forward=MethodType(forward,attention)

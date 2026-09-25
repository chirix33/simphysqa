"""Atomic, identity-checked custom model/optimizer/RNG checkpoints."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import torch
from transformers import T5Config,T5ForConditionalGeneration
from phi_jepa.artifacts import canonical,digest
from .custom_t5 import CustomT5,CustomSettings


def save_checkpoint(directory,model,optimizer,*,identity,updates):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    payload={'version':1,'settings':asdict(model.settings),'t5_config':model.t5.config.to_dict(),
        'model':model.state_dict(),'optimizer':optimizer.state_dict(),'scheduler':None,
        'rng_cpu':torch.get_rng_state(),'rng_cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
        'identity':identity,'updates':updates}
    temp=directory/'checkpoint.pending'; torch.save(payload,temp)
    sha=sha256(temp.read_bytes()).hexdigest(); path=directory/f'{sha}.pt'; temp.replace(path)
    pointer={'file':path.name,'sha256':sha,'identity_sha256':digest(identity),'updates':updates}
    temp=directory/'latest.pending'; temp.write_bytes(canonical(pointer)); temp.replace(directory/'latest.json')
    return pointer


def load_checkpoint(directory,*,identity,device='cpu',training=False):
    directory=Path(directory); pointer=json.loads((directory/'latest.json').read_text())
    path=directory/pointer['file']
    if path.name!=pointer['file'] or path.suffix!='.pt' or sha256(path.read_bytes()).hexdigest()!=pointer['sha256']: raise ValueError('checkpoint_integrity')
    if pointer['identity_sha256']!=digest(identity): raise ValueError('checkpoint_identity')
    payload=torch.load(path,map_location='cpu',weights_only=True)
    if payload['identity']!=identity or payload['version']!=1: raise ValueError('checkpoint_payload_identity')
    model=CustomT5(T5ForConditionalGeneration(T5Config(**payload['t5_config'])),CustomSettings(**payload['settings']))
    model.load_state_dict(payload['model'],strict=True); model.to(device)
    optimizer=None
    if training:
        optimizer=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad))
        optimizer.load_state_dict(payload['optimizer']); torch.set_rng_state(payload['rng_cpu'])
        if payload['rng_cuda']: torch.cuda.set_rng_state_all(payload['rng_cuda'])
        model.train()
    else: model.eval()
    return model,optimizer,payload['updates']

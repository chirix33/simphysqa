"""Independent baseline checkpoint identities and atomic deterministic resume."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import random
import re
import tempfile
import torch
from phi_jepa.artifacts import canonical,digest
from phi_jepa.training.pairs import finite_tree
from phi_jepa.solvers.rk4 import SolverSettings,SolveStats
from .conventional import NumericalComparator,BaselineSettings
from .training import ComparatorTrainer


def save_checkpoint(directory,model,*,context_identity,provenance,trainer=None,sampler=None,deployment=False):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    manifest={'version':'p05b-checkpoint-v1','kind':'deployment' if deployment else 'training',
        'model':model.manifest(),'context_identity':context_identity}
    bundle={'manifest':manifest,'state':model.state_dict(),'provenance':provenance}
    if not deployment:
        bundle.update(sampler=sampler,torch_rng=torch.random.get_rng_state(),python_rng=random.getstate(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else [])
        if trainer is not None:
            bundle['trainer']={'optimizer':trainer.optimizer.state_dict(),'learning_rate':trainer.learning_rate,
                'gradient_clip':trainer.gradient_clip,'solver':asdict(trainer.solver),'stats':trainer.stats.manifest(),
                'updates':trainer.updates,'attempts':trainer.attempts,'failures':trainer.failures,'recurrent_calls':trainer.recurrent_calls}
    if not finite_tree(bundle): raise ValueError('nonfinite_checkpoint')
    descriptor,temp=tempfile.mkstemp(dir=directory,prefix='.pending-')
    try:
        with os.fdopen(descriptor,'wb') as stream:
            torch.save(bundle,stream); stream.flush(); os.fsync(stream.fileno())
        with open(temp,'rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
        os.replace(temp,directory/(sha+'.pt'))
        pointer={'file':sha+'.pt','sha256':sha,'manifest_sha256':digest(manifest)}
        fd,pending=tempfile.mkstemp(dir=directory,prefix='.pointer-')
        try:
            with os.fdopen(fd,'wb') as stream: stream.write(canonical(pointer)); stream.flush(); os.fsync(stream.fileno())
            os.replace(pending,directory/'latest.json')
        finally:
            if os.path.exists(pending): os.unlink(pending)
        return pointer
    finally:
        if os.path.exists(temp): os.unlink(temp)


def load_checkpoint(directory,*,layout,context_identity,method,training):
    directory=Path(directory); pointer=json.loads((directory/'latest.json').read_text())
    if not re.fullmatch(r'[0-9a-f]{64}\.pt',pointer['file']) or pointer['file']!=pointer['sha256']+'.pt': raise ValueError('checkpoint_pointer')
    with (directory/pointer['file']).open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=pointer['sha256']: raise ValueError('checkpoint_integrity')
    bundle=torch.load(directory/pointer['file'],map_location='cpu',weights_only=True); manifest=bundle['manifest']
    if manifest.get('version')!='p05b-checkpoint-v1' or digest(manifest)!=pointer['manifest_sha256']: raise ValueError('baseline_checkpoint_version')
    if manifest['kind']!=('training' if training else 'deployment') or manifest['context_identity']!=context_identity: raise ValueError('checkpoint_role_or_context')
    settings=BaselineSettings(**manifest['model']['settings'])
    if settings.method!=method or manifest['model']['layout_sha256']!=layout.sha256: raise ValueError('checkpoint_method_or_layout')
    from phi_jepa.models.conditioning import NumericalConditioning
    conditioning=NumericalConditioning(manifest['model']['conditioning']) if 'conditioning' in manifest['model'] else None
    model=NumericalComparator(layout,settings,conditioning)
    if digest(model.manifest())!=digest(manifest['model']) or not finite_tree(bundle): raise ValueError('checkpoint_manifest_or_values')
    model.load_state_dict(bundle['state'],strict=True); model.eval()
    trainer=None
    if training:
        if 'trainer' in bundle:
            t=bundle['trainer']; trainer=ComparatorTrainer(model,learning_rate=t['learning_rate'],gradient_clip=t['gradient_clip'],solver=SolverSettings(**t['solver']))
            trainer.optimizer.load_state_dict(t['optimizer']); trainer.stats=SolveStats(**t['stats'])
            for name in ('updates','attempts','failures','recurrent_calls'): setattr(trainer,name,t[name])
        torch.random.set_rng_state(bundle['torch_rng']); random.setstate(bundle['python_rng'])
        if bundle['cuda_rng']: torch.cuda.set_rng_state_all(bundle['cuda_rng'])
    return model,trainer,bundle.get('sampler'),bundle['provenance']

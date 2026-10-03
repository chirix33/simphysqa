"""Content-addressed checkpoints with an atomic last-published pointer.

Only load checkpoints produced by this application. Torch weights_only loading
is used; serialized data contains tensors and primitive containers only.
"""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import random
import re
import tempfile
import torch
from phi_jepa.artifacts import canonical, digest
from phi_jepa.models.augmented_ode import AugmentedODE, ODESettings
from phi_jepa.models.context_projection import ProjectionSettings
from phi_jepa.solvers.rk4 import SolverSettings, SolveStats
from .pairs import PairTrainer, TrainingSettings, finite_tree


def write_checkpoint(directory, trainer, *, context_identity, provenance, sampler_state, deployment=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {'format_version': 1, 'kind': 'deployment' if deployment else 'training',
        'model': trainer.model.manifest(), 'solver': asdict(trainer.solver),
        'context_identity': context_identity}
    bundle = {'manifest': manifest, 'state': trainer.model.state_dict()}
    if not deployment:
        bundle.update(optimizer=trainer.optimizer.state_dict(), scheduler=None,
            training_settings=asdict(trainer.settings), updates=trainer.updates,
            failed_updates=trainer.failed_updates, attempted_updates=trainer.attempted_updates,
            stats=trainer.stats.manifest(),
            torch_rng=torch.random.get_rng_state(), python_rng=random.getstate(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else [],
            provenance=provenance, sampler_state=sampler_state)
    if not finite_tree(bundle):
        raise ValueError('nonfinite checkpoint refused')
    descriptor, temporary = tempfile.mkstemp(dir=directory, prefix='.pending-')
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            torch.save(bundle, handle)
            handle.flush()
            os.fsync(handle.fileno())
        with open(temporary, 'rb') as handle:
            sha = hashlib.file_digest(handle, 'sha256').hexdigest()
        filename = sha + '.pt'
        os.replace(temporary, directory / filename)
        pointer = {'file': filename, 'sha256': sha, 'manifest_sha256': digest(manifest)}
        descriptor, pending_pointer = tempfile.mkstemp(dir=directory, prefix='.pointer-')
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(canonical(pointer))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(pending_pointer, directory / 'latest.json')
        finally:
            if os.path.exists(pending_pointer):
                os.unlink(pending_pointer)
        return pointer
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_checkpoint(directory, *, layout, context_identity, training):
    directory = Path(directory)
    pointer = json.loads((directory / 'latest.json').read_text())
    if not re.fullmatch(r'[0-9a-f]{64}\.pt', pointer['file']) or pointer['file'] != pointer['sha256'] + '.pt':
        raise ValueError('invalid checkpoint pointer')
    path = directory / pointer['file']
    with path.open('rb') as handle:
        if hashlib.file_digest(handle, 'sha256').hexdigest() != pointer['sha256']:
            raise ValueError('checkpoint integrity failure')
    bundle = torch.load(path, map_location='cpu', weights_only=True)
    manifest = bundle['manifest']
    if manifest['format_version'] != 1 or digest(manifest) != pointer['manifest_sha256']:
        raise ValueError('checkpoint manifest mismatch')
    if manifest['kind'] != ('training' if training else 'deployment'):
        raise ValueError('checkpoint role mismatch')
    if manifest['context_identity'] != context_identity or manifest['model']['layout_sha256'] != layout.sha256:
        raise ValueError('checkpoint context/layout incompatible')
    if manifest['model']['layout'] != json.loads(canonical(layout.manifest())):
        # Torch stores tuples, so compare canonical form below as the authority.
        if digest(manifest['model']['layout']) != digest(layout.manifest()):
            raise ValueError('checkpoint layout content mismatch')
    projection = manifest['model']['projection']
    settings = ProjectionSettings(**{key: projection[key] for key in (
        'embedding_width', 'seed', 'initialization', 'precision', 'sharing')})
    from phi_jepa.models.conditioning import NumericalConditioning
    conditioning=NumericalConditioning(manifest['model']['conditioning']) if 'conditioning' in manifest['model'] else None
    model = AugmentedODE(layout, settings, ODESettings(**manifest['model']['ode']), conditioning)
    if digest(model.manifest()) != digest(manifest['model']):
        raise ValueError('model implementation/settings mismatch')
    if not finite_tree(bundle):
        raise ValueError('nonfinite checkpoint')
    model.load_state_dict(bundle['state'], strict=True)
    solver = SolverSettings(**manifest['solver'])
    if not training:
        return model, solver
    trainer = PairTrainer(model, solver, TrainingSettings(**bundle['training_settings']))
    trainer.optimizer.load_state_dict(bundle['optimizer'])
    trainer.updates, trainer.failed_updates = bundle['updates'], bundle['failed_updates']
    trainer.attempted_updates = bundle.get('attempted_updates', trainer.updates + trainer.failed_updates)
    trainer.stats = SolveStats(**bundle['stats'])
    torch.random.set_rng_state(bundle['torch_rng'])
    random.setstate(bundle['python_rng'])
    if bundle['cuda_rng']:
        if not torch.cuda.is_available():
            raise ValueError('CUDA RNG checkpoint requires CUDA for training resume')
        torch.cuda.set_rng_state_all(bundle['cuda_rng'])
    return trainer, bundle['sampler_state'], bundle['provenance']

"""Resolve immutable startup revisions without overwriting original conditions."""
from .io import read
from .formal_sampling import file_hash

def resolved_condition(pilot,condition_id):
    path=pilot/'conditions'/(condition_id+'.json');condition=read(path)
    for revision in sorted((pilot/'condition-revisions'/condition_id).glob('*.json')):
        updated=read(revision)
        if updated['startup_revision']['previous_condition_sha256']!=file_hash(path):raise ValueError('condition revision chain changed')
        condition=updated;path=revision
    return condition,path

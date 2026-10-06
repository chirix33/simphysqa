"""Explicit frozen-source scope for formal use of unchanged development procedures.

Only their final development-membership guard is superseded. Every scientific
validation before that guard still runs. Outside the context legacy behavior and
legacy implementation hashes are unchanged.
"""
from contextlib import contextmanager
from copy import deepcopy
from threading import RLock

from .dataset import restore
from .io import digest

_LOCK = RLock()


@contextmanager
def formal_scope(candidates, excluded):
    from . import explanation, clarification
    allowed = {c['source']['group_id']: c['source']['source']['record_sha256'] for c in candidates}
    if len(allowed) != len(candidates) or set(allowed) & set(excluded):
        raise ValueError('formal source scope has duplicate/excluded groups')
    def allowed_source(record):
        source = restore(record)
        group = record['trajectory_id']
        return (group in allowed and digest(source) == allowed[group]
                and source['metadata']['split_group_id'] == group
                and record['private']['metadata']['split_group_id'] == group)
    with _LOCK:
        old_e = explanation.validate_explanation
        old_c = clarification.validate_clarification
        old_construct = explanation.construct
        def construct(parent):
            result = old_construct(parent)
            if allowed_source(result):
                result['private']['explanation_annotation']['annotation_language_origin'] = (
                    'Reuse of this frozen SPQ05 candidate public measurement annotation and unchanged '
                    'event-language2.0.0/association1.1.1; exact executed request lineage is organizer-private.')
            return result
        def validator(original, membership_error):
            def wrapped(record):
                try:
                    return original(record)
                except ValueError as exc:
                    if str(exc) != membership_error or not allowed_source(record):
                        raise
                    # Original guard is last; all schema/evidence/scorer/privacy checks passed.
                    return True
            return wrapped
        explanation.construct = construct
        explanation.validate_explanation = validator(old_e, 'explanation development group missing formal exclusion')
        clarification.validate_clarification = validator(old_c, 'development exclusion missing')
        try:
            yield
        finally:
            explanation.construct = old_construct
            explanation.validate_explanation = old_e
            clarification.validate_clarification = old_c

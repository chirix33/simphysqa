"""Separate evaluation accounting. Never imported by clarification generation.

Reference-based answer results and independently assigned trigger/grounding
reviews enter here only. Unknown labels remain unknown; fixtures are not science.
"""
from collections import Counter


def evaluate_interaction(snapshot, *, review=None, before=None, after=None, task_sha256):
    records=snapshot['records']; created=records['created']
    if task_sha256!=created['task_sha256']:
        raise ValueError('evaluation_must_preserve_original_task')
    if review is not None:
        required={'reviewer_id','label_source','trigger_relevant','unnecessary_question','reply_grounded'}
        if set(review)!=required or review['label_source'] not in ('software_fixture','independent_human_review') or not review['reviewer_id']:
            raise ValueError('independent_review_labels_required')
        if any(review[k] is not None and type(review[k]) is not bool for k in ('trigger_relevant','unnecessary_question','reply_grounded')):
            raise ValueError('review_labels_boolean_or_unknown')
    changed = records.get('reply_review',{}).get('category') in ('changed_task_or_answer_definition','changed_physical_assumptions','outcome_supplying')
    if after is not None and (snapshot['status']!='refined' or changed):
        raise ValueError('no_original_task_improvement_for_unresolved_or_revised_task')
    for result in (before,after):
        if result is not None and (not isinstance(result,dict) or type(result.get('complete_success')) is not bool):
            raise ValueError('typed_evaluator_result_required')
    return {'attempt_id':snapshot['attempt_id'],'mode':created['mode'],'eligible':1,
        'task_sha256':task_sha256,'status':snapshot['status'],
        'question_requested':records.get('clarification_request') is not None,
        'reply_received':'reply' in records and records['reply']['text'] is not None,
        'review':review,'before':before,'after':after,
        'before_success':bool(before and before['complete_success']),
        'after_success':bool(after and after['complete_success']) if snapshot['status']=='refined' else False,
        'returned_success':bool(after and after['complete_success']) if snapshot['status']=='refined' else bool(before and before['complete_success']) if snapshot['status']=='answered_without_clarification' else False,
        'unresolved':snapshot['status'] not in ('refined','answered_without_clarification'),
        'failure':snapshot['status'] in ('unresolved_initial_failure','unresolved_invalid_initial_output','unresolved_refinement_failure','unresolved_invalid_refinement','unresolved_call_in_flight_or_interrupted'),
        'calls':snapshot['call_attempts'],'total_usage':snapshot['total_usage'],
        'latency_seconds':snapshot['call_latency_seconds'],
        'scientific_reviewed':review is not None and review['label_source']=='independent_human_review'}


def summarize_interactions(rows):
    result={}
    # Never pool autonomous, demo, and actual interaction, or fixtures with reviews.
    for row in rows:
        key=(row['mode'],'independent_reviewed' if row['scientific_reviewed'] else 'fixture_or_unreviewed')
        result.setdefault(key,[]).append(row)
    summaries=[]
    for (mode,evidence), group in result.items():
        queries=[r for r in group if r['question_requested']]
        after=[r for r in group if r['after'] is not None]
        summary={'mode':mode,'evidence':evidence,'eligible_attempts':len(group),
            'requested':len(queries),'unanswered_requests':sum(not r['reply_received'] for r in queries),
            'unresolved':sum(r['unresolved'] for r in group),'failures':sum(r['failure'] for r in group),
            'before_success_over_all':sum(r['before_success'] for r in group),
            'refined_success_over_all':sum(r['after_success'] for r in group),
            'returned_success_over_all':sum(r['returned_success'] for r in group),
            'evaluated_before':sum(r['before'] is not None for r in group),'evaluated_refined':len(after),
            'paired_improvements':sum(not r['before_success'] and r['after_success'] for r in group if r['before'] is not None and r['after'] is not None),
            'calls':sum(r['calls'] for r in group),'latency_seconds':sum(r['latency_seconds'] for r in group),
            'statuses':dict(Counter(r['status'] for r in group))}
        for name in ('trigger_relevant','unnecessary_question','reply_grounded'):
            labeled=[r['review'][name] for r in group if r['review'] is not None and r['review'][name] is not None]
            summary[name]={'labeled':len(labeled),'positive':sum(labeled),'unknown':len(group)-len(labeled)}
        summary['total_usage']={k:sum(r['total_usage'][k] for r in group) if all(r['total_usage'][k] is not None for r in group) else None for k in ('input_tokens','output_tokens','cost_usd')}
        summaries.append(summary)
    return summaries


def evaluate_original_reference(snapshot, reference, *, expected_reference_sha256, review=None):
    """Evaluator-only bridge; pin the original reference before any interaction.

    The caller supplies the frozen dataset reference hash, not a user reply.
    References never enter the journal or generation service/provider payload.
    """
    from phi_jepa.artifacts import digest
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.typed_evaluation import evaluate_targets
    if digest(reference)!=expected_reference_sha256:
        raise ValueError('original_reference_identity_mismatch')
    records=snapshot['records']; problem=PublicProblem.parse(records['original']['public_problem'])
    initial=records.get('initial_answer'); refined=records.get('refined_answer')
    before=evaluate_targets(problem,reference,initial['targets'] if initial else [],method='clarification_initial',failure=None if initial else 'initial_failure')
    after=evaluate_targets(problem,reference,refined['targets'],method='clarification_refined') if refined is not None else None
    result=evaluate_interaction(snapshot,review=review,before=before,after=after,task_sha256=digest(records['original']['public_problem']))
    result['reference_sha256']=expected_reference_sha256
    result['answer_spec_sha256']=digest(problem.input['answer_spec'])
    return result

"""Measured qualification report/export; never trains or dispatches providers."""
from collections import Counter,defaultdict
import csv
import math
from p10_common import *


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |',
        *['| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in row)+' |' for row in rows]])


def report(run,job=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.typed_evaluation import evaluate_targets
    from phi_jepa.capabilities import matrix
    folder=run.root/'report'; folder.mkdir(exist_ok=True)
    numerical=[]; curve_rows=[]; gradient_rows=[]; fitting=[]; physical=load(run.root/'evaluation/physical_summary.json')
    for directory in sorted((run.root/'numerical').iterdir()):
        if not (directory/'selected.json').exists(): continue
        chosen=load(directory/'selected.json'); fit=load(directory/'fit.json'); history=load(directory/'history.json')
        initialization=load(directory/'initialization.json'); settings=load(directory/'job.json')
        sampled=Counter(p for row in history[:chosen['update']] for p in row.get('pair_ids',[]))
        allids=fit['provenance']['pair_ids']
        exposure=[sampled[x] for x in allids] if chosen['update'] else [1]*len(allids)
        numerical.append({'method':directory.name,'updates':fit['updates'],'selected_update':chosen['update'],'selection_split':chosen['selection_split'],
            'normalized_endpoint_error':chosen['score'],'unique_pairs':fit['unique_pairs'],'selected_pair_exposure_min':min(exposure),'selected_pair_exposure_max':max(exposure),
            'selected_unseen_pairs':sum(x==0 for x in exposure),'seconds':fit['seconds'],'checkpoint_sha256':chosen['checkpoint']['sha256'],
            'registered_parameter_count':initialization['parameter_count'],'predicted_width':2*run.layout().d if settings['primary'] else run.layout().d,
            'objective':'raw full augmented adjacent MSE' if settings['primary'] else 'least-squares numerical next-state fit' if settings['method']=='fixed_projection_lr' else 'raw numerical adjacent MSE'})
        for row in history:
            curve_rows.append({'method':directory.name,'update':row.get('update',0),'loss':row.get('loss',row.get('numerical_mse')),
                'gradient_norm_before_clip':row.get('gradient_norm_before_clip'),'seconds':row.get('seconds')})
        for path in (directory/'milestones').glob('*/gradients.json'):
            gradient_rows.append({'method':directory.name,'update':int(path.parent.name),**load(path)})
        if directory.name.endswith('small_fit'):
            for label,measurements in [('initial',load(directory/'before_fit.json')['rows']),('selected',[load(p) for p in (directory/'milestones'/str(chosen['update'])).glob('*.json') if p.name not in ('summary.json','gradients.json')])]:
                targets=[t for r in measurements for t in r.get('answer',{}).get('targets',[]) if t['answer_type']!='boolean']
                fitting.append({'method':directory.name,'point':label,'questions':len(measurements),'complete_successes':sum(r.get('answer',{}).get('complete_success',False) for r in measurements),
                    'numeric_correct':sum(t['success'] for t in targets),'numeric_eligible':len(targets),'mean_endpoint_error_over_tolerance':sum(r.get('selection_score',1e12) for r in measurements)/len(measurements)})
    save(folder/'numerical_learning.json',numerical); save(folder/'numerical_curves.json',curve_rows); save(folder/'loss_block_gradients.json',gradient_rows)
    save(folder/'training_only_fit.json',fitting)
    fig,axes=plt.subplots(2,3,figsize=(16,8))
    for ax,names,title in zip(axes.flat,[['small_fit','biasinit_small_fit'],['raw_early','conditioned_early','raw_full','conditioned_full'],
        ['biasinit_raw_early','biasinit_conditioned_early','biasinit_raw_full','biasinit_conditioned_full'],[run.methods()[0]],run.methods()[1:]],
        ['Training-only fit (raw augmented MSE)','Zero-bias factorial','Training-derived bias factorial','Selected primary exposure curve','Comparators (different objectives; do not rank losses)']):
        for name in names:
            rs=[r for r in curve_rows if r['method']==name and r['loss'] is not None]
            if not rs: continue
            # Block means display training noise without altering exported data.
            xs=[]; ys=[]
            for i in range(0,len(rs),50):
                chunk=rs[i:i+50]; xs.append(chunk[-1]['update']); ys.append(max(1e-15,sum(r['loss'] for r in chunk)/len(chunk)))
            ax.semilogy(xs,ys,label=name.replace('biasinit_','bias_'))
        ax.set(title=title,xlabel='Optimizer updates',ylabel='Training objective (50-update mean)'); ax.legend(fontsize=6); ax.grid(alpha=.2)
    axes.flat[-1].set_visible(False)
    fig.tight_layout(); fig.savefig(folder/'numerical_learning.png',dpi=150); plt.close(fig)
    rows={r['sample_id']:r for r in run.rows()}; refs=load(run.root/'private/train-references.json')|load(run.root/'private/validation-references.json')
    cutoffs=sorted({r['public']['input']['observation_cutoff'] for r in rows.values()})
    horizons=sorted({max(s['end_time'] for s in r['public']['input']['answer_spec']) for r in rows.values()})
    generations=[]; custom_fits=[]; losses=[]
    for directory in sorted((run.root/'custom').iterdir()):
        if not (directory/'fit.json').exists(): continue
        fit=load(directory/'fit.json'); chosen=load(directory/'selected.json'); identity=load(directory/'identity.json'); hist=load(directory/'history.json')
        exposure=Counter(r['sample_id'] for r in hist[:chosen['update']]); examples=identity['training_samples']
        custom_fits.append({'job':directory.name,**fit,'selected_update':chosen['update'],'selection_loss':chosen['loss'],
            'selection_split':chosen['selection_split'],'training_questions':len(examples),'exposure_min':min(exposure[x] for x in examples),'exposure_max':max(exposure[x] for x in examples),
            'checkpoint_sha256':chosen['checkpoint']['sha256']})
        losses.extend({'job':directory.name,**h} for h in hist)
        for path in sorted(directory.glob('**/generations/*.json')):
            record=load(path); row=rows[record['sample_id']]; problem=PublicProblem.parse(row['public'])
            branches=record['branches']|({'hybrid':record['hybrid']} if 'hybrid' in record else {})
            for branch,out in branches.items():
                answer=out.get('answer'); score=evaluate_targets(problem,refs[problem.sample_id],answer['targets'] if answer else [],method=directory.name+'_'+branch,
                    failure=None if answer else out.get('reason','invalid_generation'))
                generations.append({'job':directory.name,'checkpoint_update':record['milestone'],'split':row['split'],'scope':'selected_validation' if 'validation' in path.parts else 'milestone',
                    'sample_id':problem.sample_id,'branch':branch,'strict_status':out.get('status'),'reason':out.get('reason'),'valid_typed_output':answer is not None,
                    'EOS_terminated':out.get('EOS_terminated'),'token_cap_termination':out.get('token_cap_termination'),
                    'fallback_attempted':out.get('fallback_attempted',False),'fallback_used':out.get('fallback_used',False),
                    'complete_success':score['complete_success'],'correct_targets':sum(t['success'] for t in score['targets']),'eligible_targets':score['eligible_targets'],
                    'cost':record['costs'].get(branch,record['costs'] if branch=='hybrid' else None)})
    save(folder/'custom_fit.json',custom_fits); save(folder/'custom_curves.json',losses); save(folder/'generation_diagnostics.json',generations)
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,name in zip(axes.flat,('coconut_small','codi_small','coconut_broad','codi_broad')):
        hs=[h for h in losses if h['job']==name]
        for component in ('loss','ce_loss','teacher_ce','student_ce','alignment','smoothness_loss'):
            values=[(h['update'],h[component]) for h in hs if component in h]
            if values: ax.semilogy(*zip(*[(x,max(y,1e-12)) for x,y in values]),label=component)
        ax.set(title=name+' (fresh initialization)',xlabel='Optimizer updates',ylabel='Objective component'); ax.legend(fontsize=7); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(folder/'custom_learning.png',dpi=150); plt.close(fig)
    with (folder/'physical_errors.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(physical[0])); writer.writeheader(); writer.writerows(physical)
    time_rows=load(run.root/'evaluation/physical_by_time.json'); quantities=sorted({(r['entity_id'],r['quantity'],r['unit']) for r in time_rows})
    fig,axes=plt.subplots(math.ceil(len(quantities)/2),2,figsize=(12,3.1*math.ceil(len(quantities)/2)),squeeze=False)
    for ax,key in zip(axes.flat,quantities):
        for method in [*run.methods(),'hold_last_diagnostic']:
            values=defaultdict(list)
            for r in time_rows:
                if r['method']==method and r['split']=='validation' and r['mode']=='physical_autonomous' and (r['entity_id'],r['quantity'],r['unit'])==key and r['status']=='valid': values[r['time']].append(r['error'])
            if values:
                times=sorted(values); ax.plot(times,[math.sqrt(sum(x*x for x in values[t])/len(values[t])) for t in times],label=method.replace('biasinit_','bias_'))
        ax.axvline(.6,color='grey',linestyle=':',linewidth=1); ax.set(title=key[0]+'/'+key[1],xlabel='Physical time (s)',ylabel='RMSE ('+key[2]+')'); ax.grid(alpha=.2); ax.legend(fontsize=5)
    for ax in list(axes.flat)[len(quantities):]: ax.set_visible(False)
    fig.tight_layout(); fig.savefig(folder/'validation_physical_curves.png',dpi=150); plt.close(fig)
    diagnostic_path=run.root/'diagnostics/selected_gradients_and_sensitivity.json'
    selected_diagnostics=load(diagnostic_path)['records'] if diagnostic_path.exists() else []
    diag_table=[]
    for r in selected_diagnostics:
        diag_table.append([r['method'],r['split'],f"{r['tanh1_saturation']:.3f}/{r['tanh2_saturation']:.3f}",
            *[f"{r['blocks'][name]['raw_augmented_loss_contribution']:.3g} / {r['blocks'][name]['parameter_gradient_norm']:.3g}" for name in ('physical','time_index','fixed_conditioning','contextual')]])
    summary=load(run.root/'evaluation/summary.json'); budget=run.b.read()
    common={r['method']:r for r in summary if r['condition']=='frozen_answer_llm' and r['split']=='validation'}
    comparison=''
    if 'public_only' in common and run.methods()[0] in common:
        public=common['public_only']; primary=common[run.methods()[0]]
        comparison=(f"On common numerical targets, public-only achieves {public['numeric_correct']}/{public['numeric_eligible']} and the primary forecast condition achieves {primary['numeric_correct']}/{primary['numeric_eligible']}. "
            'Whole-answer differences must not be interpreted as a forecasting benefit when they reflect the different Boolean evidence policy. These are selection-split observations, not sealed-test method rankings.')
    controls=load(run.root/'evaluation/control_inventory.json')
    reversed_changes=[r['change_over_tolerance'] for r in controls['reversed_query_changes'] if r.get('change_over_tolerance') is not None]
    layout_validation=load(run.root/'release_layout_validation.json')['reports'] if (run.root/'release_layout_validation.json').exists() else []
    source={'base_commit':__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'config_sha256':digest(run.c),
        'continuation_policy_sha256':file_hash(run.root/'continuation_policy.json') if (run.root/'continuation_policy.json').exists() else None,
        'source_records':'sources/*.json and sources/history/*.json; code snapshots in native sources/blobs where available','dirty_worktree':True,'committed_or_pushed_by_agent':False}
    save(folder/'report_identity.json',source)
    parts=['# Integrated Phi-JEPA run — measured results',
        f"Bounded {run.c['domain']} run: {run.c['training_scenarios']} training scenarios, {run.c['validation_scenarios']} selection/validation scenarios, {run.c['questions_per_scenario']} question(s) per scenario, seed {run.c['seed']}. This training/selection report is not a sealed-test result, four-domain performance claim, convergence result or calibrated OOD evaluation. All failed and unsupported answer components remain in denominators.",
        'Historical P07/P08/P09 evidence is unchanged. Base commit `'+source['base_commit']+'`; this implementation is an uncommitted working-tree change. Per-stage source/config/data/checkpoint hashes identify execution versions.',
        '## Numerical training and controlled remedies',
        'Affine conditioning uses frozen training-input statistics inside the vector field only. Raw n/p state, derivatives, full-vector MSE, two current-p gradient paths and autonomous feedback are unchanged. A separately recorded initialization condition sets the existing numerical output bias from mean training adjacent derivatives; it remains trainable. The two factorials separate these conditions rather than attributing all effects to affine conditioning.',
        'The coverage comparison fixes optimizer updates and batch size. Full coverage has twice as many distinct transitions and consequently lower exposure per pair; it tests that bounded allocation, not whether additional post-event supervision is inherently beneficial or harmful. All conditions retain equal question-conditioned pair weights.',
        ('After the small fitting check passed, one exposure continuation restored each of the five iterative numerical methods from its own 4,000-update model/optimizer state and extended the same sampler to at most 20,000 updates. These continued conditions are separate from the unchanged 4,000-update factorials. Frozen conditioning statistics, data, objectives and solver remain identical. Original checkpoints are retained; selection also retains the original candidate. LR reuses its original independent fit. Continued fit time is cumulative; the resource ledger charges each executed segment only once.'
            if source['continuation_policy_sha256'] else 'This run starts its declared models independently. Historical qualification controls and small-set fitting are separate evidence; no continuation is claimed here.'),
        table(['Condition','Updates / selected','Selection split','Mean endpoint error / tolerance','Pairs','Selected exposure min–max','Seconds'],
            [[r['method'],f"{r['updates']} / {r['selected_update']}",r['selection_split'],f"{r['normalized_endpoint_error']:.5g}",r['unique_pairs'],f"{r['selected_pair_exposure_min']}–{r['selected_pair_exposure_max']}",f"{r['seconds']:.2f}"] for r in numerical]),
        table(['Training-only diagnostic','Checkpoint','Numeric correct / eligible','Complete questions','Mean endpoint error / tolerance'],
            [[r['method'],r['point'],f"{r['numeric_correct']}/{r['numeric_eligible']}",f"{r['complete_successes']}/{r['questions']}",f"{r['mean_endpoint_error_over_tolerance']:.5g}"] for r in fitting]),
        table(['Selected numerical method','Predicted width','Registered parameters','Training objective'],[[r['method'],r['predicted_width'],r['registered_parameter_count'],r['objective']] for r in numerical if r['method'] in run.methods()]),
        'Parameter counts are registered model parameters, including fixed parameters where applicable; LR also stores fitted coefficients as buffers. Methods are not capacity matched. RNN retains its separate recurrent hidden state.',
        'Loss curves: [numerical_learning.png](artifacts/P10/report/numerical_learning.png). Full data, coordinate decompositions, block gradients, initialization identities and exposure are exported; other-method losses have different coordinate counts/objectives and are not accuracy rankings.',
        'Bounded selected-checkpoint diagnostics use two questions per split and their first/last adjacent intervals, without optimizer updates. Each table cell reports raw augmented loss contribution / parameter-gradient norm; magnitude and gradient influence are distinct. Saturation is the fraction of hidden activations with absolute value above 0.99.',
        table(['Method','Split','Tanh1/Tanh2 saturation','Physical loss / gradient','Time/index loss / gradient','Fixed loss / gradient','Context loss / gradient'],diag_table),
        'Derivative sensitivity and exact public scheduled-event coverage are in `diagnostics/`. They do not establish text usefulness or chaotic dynamics. [Per-time validation curves](artifacts/P10/report/validation_physical_curves.png) retain the early/late boundary.',
        '## Physical validation errors',
        f'RMSE uses named physical errors: Euclidean vector distance, scalar absolute error and quaternion angular distance. Public cutoff(s): {cutoffs} s; requested forecast endpoint(s): {horizons} s. Full horizon includes every reference time after each cutoff through its endpoint; early ends at 0.60 s and late includes later times through that endpoint. Hold-last is a diagnostic, not a new paper baseline. Invalid samples retain explicit coverage counts.',
        table(['Method','Quantity','Unit','Full RMSE','Early RMSE','Late RMSE','Valid / eligible'],physical_table(physical)),
        '## Generation learning and strict evaluation',
        'Custom conditions use new branch/output-inventory instructions consistently in training and generation. Shared CODI backbone and objectives are unchanged; teacher projection is frozen. Small-fit and broader runs start independently. Strict parsing, 2,048-token generation limits and EOS requirements are unchanged.',
        'Compared with historical P08, both instructions and training exposure changed. This qualification measures the implemented condition; it does not isolate a causal instruction effect. The CODI teacher/student backbone is shared: detaching the teacher alignment target blocks that branch of alignment gradients, while teacher cross-entropy, student cross-entropy and student-side alignment can still update shared backbone parameters through their own paths.',
        table(['Job','Updates / selected','Training questions','Selected exposure min–max','Seconds','Peak allocated GB'],[[r['job'],f"{r['updates']} / {r['selected_update']}",r['training_questions'],f"{r['exposure_min']}–{r['exposure_max']}",f"{r['seconds']:.1f}",f"{r['peak_allocated_bytes']/1e9:.2f}"] for r in custom_fits]),
        table(['Job / scope / split / branch / update','Typed valid','EOS','Cap termination','Complete answers','Fallback attempted / used','Calls / seconds'],generation_table(generations)),
        'Per-example raw outputs, token IDs, losses, branch inputs, checkpoint selections and generation costs are retained. Training-example fitting and validation results are separate. No output repair is used. Teacher/student generation work is counted in hybrid cost.',
        '## Integrated answer benchmark',
        table(['Condition','Method','Split','Complete answers','Numeric correct','Typed valid targets','Boolean coverage','Boolean correct supported'],
            [[r['condition'],r['method'],r['split'],f"{r['complete_successes']}/{r['questions']}",f"{r['numeric_correct']}/{r['numeric_eligible']}",f"{r['valid_targets']}/{r['eligible_targets']}",f"{r['boolean_supported']}/{r['boolean_eligible']}",f"{r['boolean_correct']}/{r['boolean_supported']}"] for r in summary]),
        'Public-only and forecast answers share original public inputs/model/decoding and evaluation references. Forecast Boolean values are constrained to qualified rule readouts; public-only has no forecast evidence. Common numerical targets are compared separately; whole-answer results retain Boolean components and this policy difference.',
        comparison,
        f"Reversed-forecast offline control changes {sum(v>1 for v in reversed_changes)}/{len(reversed_changes)} queried numerical values by more than their existing tolerance. Exact per-target changes are exported. This is a readout intervention, not independent training or a paid answer condition. Removing assessment or inactive fallback is a no-op and is not counted as independent evidence.",
        '## Four-domain capability matrix',
        table(['Public preflight domain','Split','Compatible / eligible','Failure reasons'],[[r['domain'],r['split'],f"{r['compatible']}/{r['questions']}",r['failure_counts']] for r in layout_validation]),
        'This preflight opens public train/validation inputs only. It validates accepted layouts, not physical forecast quality, enrichment truthfulness, or long-context model performance.',
        table(['Domain','Entity / quantity','Implemented readout','Required evidence / gap'],[[r['domain'],r['entity_id']+' / '+r['quantity'],r['implemented'],r['required_evidence']] for r in matrix()]),
        'This matrix describes the primary/comparator numerical readout, not proven four-domain performance. Per-target units, frame, history, initial event state and sampling checks can still yield unsupported. Stable-stack and support-lost require future contact/support evidence absent from the accepted state; the forecast answer layer cannot invent these values. Separately approved custom direct-generation baselines predict their typed training targets; such outputs do not implement or qualify the missing deterministic contact readout.',
        'Assessment: train-only predicted reference bank is rebuilt for the selected checkpoint/projection/encoder/layout/time grid. Familiarity is not physical correctness or calibrated uncertainty. Required immutable typed public contract declarations are absent; answer-spec thresholds are not substituted for them. V1 and supported physical checks remain separate. Calibration IDs are disjoint from checkpoint selection; test/OOD outcomes remain sealed. Calibration is ineligible while required components are missing.',
        'Clarification: the separate human-reviewed one-question/one-reply workflow is available but disabled in this autonomous benchmark. No OOD alarm, human-assistance accuracy claim or automatic reforecasting follows from this run.',
        '## Research-question status',
        '**RQ1, forecasting/QA:** the tables measure small-set fitting and validation separately; neither is a four-domain generalization claim. **Domain engineering:** accepted state layouts, named channel/unit/frame bindings, public event rules, physical consistency checks and output schemas are manually authored and disclosed. No force equations or benchmark oracle are imported into the vector field. **Richer outputs:** raw/named trajectories, typed answers, unsupported/failure reasons and assessment components are available, but their usefulness/accuracy must be judged against the retained forecast/answer failures.',
        '**RQ2, recognition:** the implemented mechanism retrieves a compatible training prediction with frozen public-context embeddings and reports terminal full-vector familiarity, V1 and supported checks. This run does not establish OOD detection performance; complete contracts, eligible calibration and sealed evaluation remain pending. **Clarification:** actual-user interaction, human reply routing and a single frozen-answer refinement are implemented separately. Inputs are original public facts and existing prediction/readout evidence plus an attributed reply; outputs are preserved initial/refined answers and explicit unresolved/reforecast/revised-task statuses. Software fixtures verify boundaries. They do not show that it detects OOD, recovers hidden causes or improves empirical accuracy.',
        '## Resource accounting',
        resource_text(run,budget),
        'Final authoritative resource totals are in budget.json and completed stage records. This report records a snapshot taken during report generation; the supervisor subsequently charges its small remaining execution overhead. Provider charges are conservative upper-rate accounting, not a billing invoice.',
        'A reused frozen-output cache hit has zero new provider charge in this ledger. That is an incremental execution cost, not a claim that the original LLM inference was free or instantaneous; historical P08 provider evidence remains separate. Per-request ledgers identify cache hits and newly dispatched calls.',
        '## Remaining gates',
        '- **Missing evidence:** robust held-out physical/answer quality, multiple seeds, other-domain training, sealed ID/OOD performance and live independently reviewed clarification effectiveness. Small-fit learning does not establish these.',
        '- **Scientific decisions:** sufficient contact/support evidence or an approved mechanism for contact-dependent outputs; typed assessment contract declarations and their source. Existing public readouts are implemented. No new head, loss, schema repair or EBM was introduced.',
        '- **Implementation limits:** staged workflow validates accepted fixed layouts and rejects incompatible inputs rather than coercing them. Optional heterogeneous-horizon pair/sequence sampling has software tests; larger empirical workloads remain unqualified. Sealed evaluation is not executed by the qualification command.',
        '- **Unresolved hypotheses:** learning effects may depend on initialization, sampled control regimes and optimization. Error magnitude/familiarity do not diagnose chaos or establish text usefulness.',
        'See [the executable workflow](../P10_pipeline.md) and [next full-study plan](P10_next_full_study.md).']
    report_text='\n\n'.join(parts)+'\n'
    (folder/'benchmark.md').write_text(report_text.replace('artifacts/P10/','../'),encoding='utf-8')
    if not run.c.get('full_study'): (ROOT/'docs/reviews/P10_benchmark_report.md').write_text(report_text,encoding='utf-8')
    save(folder/'resource_snapshot.json',{'seconds':budget['seconds'],'artifact_bytes':run.b.size(),'provider_attempts':len(budget['provider']),
        'provider_tokens':{k:sum(r[k] for r in budget['provider']) for k in ('charged_input','charged_output','charged_usd')}})
    if not run.c.get('full_study'):
        from p10_study import study_plan
        study_plan(run)
    # Archive exact final executable source bytes without credentials, private
    # targets, model caches or weights. Per-stage hashes still identify earlier
    # execution versions; this does not relabel old runs as using final source.
    import zipfile
    paths=[*execution_sources(run.config_path),
        ROOT/'tests/test_p10.py',ROOT/'docs/P10_pipeline.md',ROOT/'docs/decisions/P10_qualification.md']
    archive=run.root/'sources/final-source.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in paths: bundle.write(path,str(path.relative_to(ROOT)))
    save(run.root/'sources/final-source.json',{'sha256':file_hash(archive),'files':{str(p.relative_to(ROOT)):file_hash(p) for p in paths},
        'meaning':'Final executable implementation snapshot; earlier stage identities remain distinct.'})
    print(json.dumps({'report':'docs/reviews/P10_benchmark_report.md','numerical_conditions':len(numerical),'custom_generations':len(generations)}))


def physical_table(records):
    grouped=defaultdict(dict)
    for r in records:
        if r['split']=='validation' and r['mode']=='physical_autonomous': grouped[(r['method'],r['entity']+'/'+r['quantity'],r['unit'])][r['window']]=r
    return [[*key,*[f"{v[w]['rmse']:.5g}" if w in v and v[w]['rmse'] is not None else 'unavailable' for w in ('full_horizon','early','late')],
        f"{v['full_horizon']['valid']}/{v['full_horizon']['eligible']}"] for key,v in sorted(grouped.items())]


def generation_table(rows):
    grouped=defaultdict(list)
    for r in rows: grouped[(r['job'],r['scope'],r['split'],r['branch'],r['checkpoint_update'])].append(r)
    result=[]
    for key,rs in sorted(grouped.items()):
        costs=[cost for r in rs for cost in ([r['cost']] if r.get('cost') and 'seconds' in r['cost'] else r.get('cost',{}).values() if r.get('cost') else [])]
        result.append([' / '.join(map(str,key)),f"{sum(r['valid_typed_output'] for r in rs)}/{len(rs)}",
            'N/A (composition)' if key[3]=='hybrid' else sum(r.get('EOS_terminated') is True for r in rs),
            'N/A (composition)' if key[3]=='hybrid' else sum(r.get('token_cap_termination') is True for r in rs),
            f"{sum(r['complete_success'] for r in rs)}/{len(rs)}",f"{sum(r['fallback_attempted'] for r in rs)}/{sum(r['fallback_used'] for r in rs)}",
            f"{sum(c['calls'] for c in costs)} / {sum(c['seconds'] for c in costs):.2f}"])
    return result


def resource_text(run,budget):
    caps=run.c['caps']
    return f"Charged CPU {budget['seconds'].get('cpu',0)/60:.2f}/{caps['cpu_seconds']/60:g} minutes; GPU {budget['seconds'].get('gpu',0)/60:.2f}/{caps['gpu_seconds']/60:g} minutes; artifacts {run.b.size()/1e9:.3f}/{caps['artifact_bytes']/1e9:g} GB; provider attempts {len(budget['provider'])}/{caps['provider_attempts']}, input tokens {sum(r['charged_input'] for r in budget['provider'])}/{caps['provider_input_tokens']:,}, output tokens {sum(r['charged_output'] for r in budget['provider'])}/{caps['provider_output_tokens']:,}, conservative USD {sum(r['charged_usd'] for r in budget['provider']):.4f}/{caps['provider_usd']:g}. Whole worker wall time is charged to its CPU/GPU bucket; provider waiting time is reported separately and provider process CPU time is charged. Unknown usage retains its reservation. One worker runs at a time; a supervisor enforces aggregate and component time/artifact caps. Official pricing basis: https://developers.openai.com/api/docs/models/gpt-5.6-sol (checked 2026-09-25)."

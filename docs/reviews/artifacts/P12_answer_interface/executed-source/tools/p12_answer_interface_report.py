"""Report saved bounded diagnostics; never generate or inspect test references."""
from p12_answer_interface import RUN, ROOT, CONDITIONS
from p12_common import load, save
from phi_jepa.integration.readers import file_hash


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |',
                      *['| '+' | '.join(map(str,r))+' |' for r in rows]])


def main():
    summary=load(RUN/'evaluation/summary.json'); audit=load(RUN/'verification.json')
    cfg=load(RUN/'config.json'); second=load(RUN/'round-2/config.json')
    names={'qwen3_8b_direct':'Qwen3-8B thinking-off','qwen3_8b_thinking':'Qwen3-8B thinking-on','llama31_8b_direct':'Llama-3.1-8B-Instruct direct'}
    runtimes={c:load(RUN/'round-2'/c/'runtime.json') for c in CONDITIONS}
    lines=['# P12 shared answer-interface conclusion — 29 September 2026','',
        'This is an eight-case validation diagnostic, not confirmation/test evidence. '
        'The original eight public cases and scientific scorer/tolerances are unchanged. '
        'No paid calls, fine-tuning, expanded study, paper edits, push or merge occurred.','',
        '## Interface status','',
        '**Partially resolved.** Compact answers, public metadata adaptation and final-answer grammar constraints are implemented. '
        'The native reasoning boundary is preserved. Actual format/contract and completion counts appear below; '
        'token-budget failures remain failures. Schema constraints cannot guarantee finite floating-point interpretation '
        '(for example, `1e999`), so the unchanged canonical parser remains mandatory.','',
        'The first round exposed a missing C compiler required by the CUDA/Triton mask path. '
        'All eight Qwen-off attempts failed before emitting a token and remain charged. '
        'The single authorized correction moved masking to the installed XGrammar CPU kernel, with transfer overhead measured. '
        'It was tested on actual CUDA tensors before round two. The other conditions were not run on the known-broken path.','',
        f"**{audit['total_attempts']}/48 total generation attempts**, two rounds, "
        f"{audit['model_window_elapsed_seconds']/60:.2f} minutes from first model load to last result within the original 120-minute window. "
        'There were no automatic retries or output repairs. Eight repeated Qwen-off cases in round two are explicit defect retries; '
        'they are not erased by reporting the corrected condition separately.','',
        '## Corrected-round measurements','',
        table(['Condition','Attempted / EOS completed','JSON / full contract','Complete correct','Supported / eligible','Abstentions'],
              [[names[c],f"{s['requests_attempted']} / {s['requests_completed']}",f"{s['syntax_valid']} / {s['full_contract_valid']}",
                f"{s['complete_correct']}/{s['questions']}",f"{s['supported_targets']}/{s['eligible_targets']}",
                f"{s['abstentions']}/{s['eligible_targets']} ({s['abstention_rate_all_targets']:.1%})"] for c,s in summary.items() if c in CONDITIONS]),'',
        'JSON validity is strict syntactic parsing; full validity includes every required target, all field/type/shape checks, '
        'and the unchanged canonical parser. EOS completion is not correctness. Missing final answers are not abstentions. '
        'All eight questions and all 40 targets (28 numeric, 12 Boolean) remain in denominators.','',
        table(['Condition','Numeric correct / eligible','Numeric evaluated','Boolean correct / eligible','Boolean evaluated'],
              [[names.get(c,c),f"{s['numeric_correct']}/{s['numeric_eligible']}",s['numeric_evaluated'],
                f"{s['boolean_correct']}/{s['boolean_eligible']}",s['boolean_evaluated']] for c,s in summary.items()]),'',
        'Detailed native-unit RMSE by domain/quantity, valid-only error denominators, all target errors, failure categories and '
        'scenario grouping are in the [evaluation artifacts](artifacts/P12_answer_interface/evaluation/summary.json) and sibling condition files. '
        'No heterogeneous-unit RMSE is pooled.','',
        '## Repetition and hold-last control','',
        'Equality below is exact numeric value equality against matching entity/quantity/unit/frame channels; no rounding or tolerance. '
        'Repeating a Boolean is listed separately because equal Boolean outcomes are not evidence of copying. '
        'The hold-last control copies available last-observed target channels, including observed Booleans, without inferring events.','',
        table(['Condition','Numeric = any observation / evaluated','Numeric = last observation / evaluated','Boolean = last / evaluated'],
              [[names[c],f"{s['numeric_exact_any_observed']}/{s['numeric_evaluated']}",
                f"{s['numeric_exact_hold_last']}/{s['numeric_evaluated']}",
                f"{s['boolean_exact_hold_last']}/{s['boolean_evaluated']}"] for c,s in summary.items() if c in CONDITIONS]),'',
        f"Hold-last complete-answer accuracy: **{summary['hold_last']['complete_correct']}/8**. "
        'Persistence is allowed; correct/incorrect repeats retain their ordinary scores. This small diagnostic cannot establish '
        'general forecasting superiority or an OOD result.','',
        '## Runtime and failures','',
        table(['Condition','Total request s','Median / max s','Peak allocated / reserved GiB','Token / time caps','Runtime failures'],
              [[names[c],f"{s['generation_seconds']:.3f}",f"{s['latency_median']:.3f} / {s['latency_max']:.3f}",
                f"{s['peak_allocated_bytes']/2**30:.3f} / {s['peak_reserved_bytes']/2**30:.3f}",
                f"{s['token_caps']} / {s['time_caps']}",s['runtime_failures']] for c,s in summary.items() if c in CONDITIONS]),'',
        table(['Condition','Load + backend s','Schema compile s','Mask + transfers s','Reasoning / final tokens','Cumulative attempts'],
              [[names[c],f"{runtimes[c]['load_and_backend_seconds']:.3f}",f"{s['constraint_compile_seconds']:.3f}",
                f"{s['constraint_processing_seconds']:.3f}",f"{s['reasoning_tokens']} / {s['final_tokens']}",s['cumulative_attempts']]
               for c,s in summary.items() if c in CONDITIONS]),'',
        f"The eight first-round runtime failures add **{audit['first_round_latency_seconds']:.3f} request seconds**. "
        'Request timing includes schema compilation, mask processing and CPU/GPU transfers; model loading/backend initialization is separate. '
        'Peak allocated/reserved values are PyTorch process measurements, excluding desktop/driver allocations. '
        'Existing per-request generation limits remain 120 seconds, 1,024 final/direct tokens or 2,048 total thinking-plus-final tokens.','',
        '## Configuration and validation','',
        '- Prompt: [p12_compact_answer_v1.json](../assets/p12_compact_answer_v1.json). Complete public problem plus cutoff/absolute-time header and unrelated dummy example.',
        '- Adapter/schema: `src/phi_jepa/providers/compact_answer.py`; strict duplicate JSON detection; no value synthesis, Boolean inference, unit conversion, or reference input.',
        '- Decoder: XGrammar 0.1.19 via Transformers 4.51.3; additive pinned dependencies in `/home/aashraf/phi-jepa/p12-answer-interface-deps`; CPU mask, native final-only Qwen gate, BF16/SDPA.',
        '- Original models/tokenizers and sampling settings remain pinned by `configs/local_answers_p12.lock.json`: Qwen revision `b968826d9c46dd6066d109eabc6255188de91218`, Llama revision `0e9e39f249a16976918f6564b8830bc894c89659`; seed 11; original temperatures/top-p/top-k.',
        '- Twenty-five offline checks passed before round two, including actual grammar rejection checks and CPU-mask application to CUDA tensors. Real tokenizer preflight passed all 24 requests, without model generations.',
        '- The audit reconstructs all messages/input tokens, verifies raw decoding, reruns the unchanged adapter, checks native reasoning separation, all source/settings identities and durable attempt/deadline accounting.',
        '- Exact-cache resume is verified separately after generation; no output repairs, implicit retries or replacement predictions are permitted.','',
        f"Branch/base: `main` / `{cfg['commit']}`; original uncommitted work preserved. "
        f"Round-one source: `{cfg['source_sha256']}`. Round-two executed source: `{second['source_sha256']}`. "
        'Content-addressed source blobs, exact rendered messages, input token IDs, raw generations, output token IDs, parser results and per-request costs '
        'are in [the artifact export](artifacts/P12_answer_interface/verification.json).','',
        'The decoder integration follows the [versioned XGrammar HF implementation](https://github.com/mlc-ai/xgrammar/blob/v0.1.19/python/xgrammar/contrib/hf.py); '
        'the scope of enforcement was checked empirically, not inferred from generic JSON validity.','',
        '## Reproducible commands','',
        'Run from the repository in WSL with the existing core interpreter. The historical completed run is immutable; '
        'its original budget cannot be renewed by resume. Full-study execution requires separate authorization.','',
        '```bash',
        'export PYTHONPATH=/home/aashraf/phi-jepa/p12-answer-interface-deps:src:tests:tools',
        'export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1',
        'PY=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python',
        '"$PY" -m unittest test_p12_answer_interface test_p12 test_p11 -v',
        '"$PY" tools/p12_answer_interface.py prepare',
        '"$PY" tools/p12_answer_interface.py preflight',
        '# Original round-one Qwen-off run produced the retained missing-compiler failures.',
        '# After the CPU-mask correction and CUDA-tensor test:',
        '"$PY" tools/p12_answer_interface.py register_correction',
        '"$PY" tools/p12_answer_interface.py preflight',
        '"$PY" tools/p12_answer_interface.py generate --condition qwen3_8b_direct',
        '"$PY" tools/p12_answer_interface.py generate --condition qwen3_8b_thinking',
        '"$PY" tools/p12_answer_interface.py generate --condition llama31_8b_direct',
        '"$PY" tools/p12_answer_interface.py evaluate',
        '"$PY" tools/p12_answer_interface_audit.py',
        '"$PY" tools/p12_answer_interface_report.py',
        '"$PY" tools/p12_answer_interface.py export',
        '```','',
        '## Freeze decision and remaining limitations','',
        'The expanded study remains unlaunched. Final freeze readiness and any post-run serialization-order correction are recorded '
        'in the concluding addendum below. An all-valid format alone is not a forecasting claim; failures, abstentions and '
        'hold-last comparisons above must accompany any use of these diagnostics.']
    path=ROOT/'docs/reviews/P12_answer_interface_completion.md'
    path.write_text('\n'.join(lines)+'\n')
    save(RUN/'report-source.json',{'path':str(Path(__file__).relative_to(ROOT)),'sha256':file_hash(__file__)})
    print(str(path))


if __name__=='__main__':
    from pathlib import Path
    main()

"""Bounded local completion/handoff bookkeeping; no model execution."""
from pathlib import Path
import time,json,shutil
from simphysqa import complement_execution as c,execution_adapter as a
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09');R=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa');RUN=B/'complement-execution-1.0.0';CLOSE=B/'complement-closure-1.0.1'
ledger=c.Ledger(B/'central-main-1.0.0/main.sqlite');control=ledger.reserve_control('Ashraf','final local completion review, handoff and commit bookkeeping',100)
a.put(RUN/'local-close-control-1.0.0.json',{'control':control,'started_monotonic':time.monotonic()})
review=R/'docs/reviews/SPQ06_complement_execution.md'
text=review.read_text(encoding='utf8')
text += '''
## Final reporting and recovery-preservation addendum

The [reporting diagnostics](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/paper-diagnostics.md>) accompany the scientific tables, without operational interruption history. They separately enumerate first-stage generation/JSON/schema failures, valid-but-incorrect answers and clarification continuation categories. Eight noncomplete generations across core plus complement retain their primary denominators (six occur in the complement). Five complement stage memory monitors report unavailable status; none was converted to measured zero.

The paired 400-item contrasts are structured-only minus enriched. For Qwen3-8B direct, direct correctness falls 15.0 pp (paired 95% interval [-22.5, -7.5]) and resolved clarification falls 7.5 pp ([-13.7, -2.5]); predictive correctness is unchanged. For Qwen3-32B thinking, the direct contrast is +5.0 pp ([-1.2, 11.3]), and the resolved-clarification contrast is 0.0 pp ([-5.0, 5.0]). All family comparisons remain available in the tables; these mixed results support no blanket enrichment benefit. The intervals are descriptive, marginal and not multiplicity-adjusted. Automatic explanation factual scores do not grade prose quality.

[Recovery preservation proof](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/recovered-core-preservation.json>) verifies all 4,607 files in the recovery post-commit index and both raw-result hash fields for each of Ashraf's 1,600 core item-condition rows. There are no mismatches. These checks complement the 40,037 pre-recovery/source-freeze file checks and original-ledger-row preservation; overlapping inventories are not summed as unique scientific records.

The first closure helper also failed: it attempted to compare unexecuted collaborator placeholders in the historical all-condition analysis with the Ashraf-only analysis. The corrected /1.0.1 helper explicitly filters the frozen eight authorized combinations. The /1.0.0 source/log and full 300-second unknown reservation remain. This was a reporting helper correction, not a changed scorer, skipped Ashraf result or scientific retry.

[Accounting/audit addendum](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/audit-addendum.zip>), [closure manifest](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/manifest.json>) and [settled closure accounting](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/accounting.json>) are separately exported, preserving the sealed main audit ZIP. Final local review/commit accounting and exact commit identity are in the post-commit receipt. No models, datasets, prompts, scoring tolerances, observers or split identities changed.
'''
review.write_text(text,encoding='utf8')
archive=R/'docs/simphysqa/prompt_archive/SPQ06/complement-analysis-1.0.1';index=a.read(archive/'file-index.json')
for source,name,kind in [(B/'complement-closure-1.0.0.py','closure-failed.py','executed_reporting_helper_failed_on_unexpanded_condition_placeholders'),(B/'complement-closure-1.0.1.py','closure.py','executed_recovery_raw_hash_and_reporting_addendum'),(Path(__file__),'review-close.py','executed_bounded_local_review_bookkeeping')]:
 if (archive/name).exists():raise ValueError('exclusive archive source exists')
 shutil.copyfile(source,archive/name);index['entries'].append({'file':name,'source':str(source),'sha256':a.sha(source),'kind':kind})
# This is the still-uncommitted documentation index, not a sealed scientific artifact.
(archive/'file-index.json').write_text(json.dumps(index,indent=2),encoding='utf8')
handoff=R/'docs/simphysqa/complement_execution_handoff.md'
handoff.write_text('''# Collaborator handoff after Ashraf complement execution

Ashraf's eight combinations are complete on the frozen core and complement. His six
enriched conditions and two matched ablations therefore have 400-item analyses. This
does not assign, authorize or imply completion of Gemma direct/CoT or DeepSeek work,
nor willingness to expand those conditions. Compare unexpanded conditions on common
core 200. The collaborator's 100,800-second allocation remains protected in the same
central ledger (latest observed imported consumption zero).

The execution-public-1.1.1 base, its workers and all scientific inputs/settings remain
sealed. Complement registry/routing/calendar support is separately versioned central
code; coordinator snapshot /1.0.1 adds exact existing clarification configuration.
The original missing-config failure and unknown CPU charges remain. An executor must
still qualify its own hardware/runtime/model/template/worker identities. Ashraf's
qualification and timing do not qualify another machine or provide a two-machine
completion forecast. No collider/model owner is newly assigned by this handoff.

The actual initial request registry, receipts and private scoring remain under the
established external roots. Do not reuse Ashraf's stage keys, private binding files
or hardware qualification as a shortcut. Use explicit disjoint centrally issued
assignments, reserve before launch/import, preserve actual clarification history,
and import immutable returns. Conflict policy and never-reserved-only resume are
unchanged. No new inference is launched by these documents.
''',encoding='utf8')
decision=R/'docs/decisions/SPQ06_complement_execution.md'
with decision.open('a',encoding='utf8') as f:f.write('''

Completion: all 1,600 complement initials and 293 supported continuations were
immutably imported; 27 conditionals remain explicitly unexecuted. The six length
limits and five unavailable memory measurements are retained. Core/complement/union
analyses are saved separately with unchanged primary scorers/bootstrap; raw core
hashes and prior recovery files match. Final helper failures retain their source,
logs and full unknown controls, with separate corrected versions. This completion
does not revise scientific selection/settings, release composition or collaborator
authority. See the completion review, reporting addendum and local post-commit receipt.
''')
print('Final review/handoff updated under control '+control)
ledger.db.close()

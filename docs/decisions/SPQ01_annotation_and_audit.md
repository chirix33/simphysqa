# SPQ01 decisions — 4 October 2026

Branch simphysqa-naacl, parent/SPQ00 129155be63a44c8c3c31af1d69049ef0769548ac;
original main/base 7dd4a64e90cfb18be743503ac8345cabf2f6e28b.
No further cleanup or history/main changes.

Use train for engineering development because the release has no dedicated
development split. Select four groups/domain with seed 20261004 and public-feature
farthest-point diversity, after one earliest-horizon predictive record/group.
Do not sample on private realized outcomes. Existing event timing/control/physical
variation is included; all selected observation windows are .2 seconds / 11 states.
Engineering selection is not unbiased quality estimation.

Persist 20 inspected groups (SPQ00 four + SPQ01 sixteen) as default fresh-sampling
exclusions. The group-then-question sampler targets trajectory-balanced estimates.
Definitive formal export stays disabled. Development alone may carry a paired
direct/predictive item per group; formal/calibration avoid related records.

Preserve old source wrapping 0.1.0 and direct lineage under 0.2.0. Direct answers
are exact observed focal measurement readouts; original source IDs/reference values
are recoverable. Other QA families remain pending and are not relabelings.

Use the historically evidenced callable gpt-5.6-sol, medium reasoning / 2,048
output tokens / Responses, with documented service-ID snapshot limitation.
Use a public-only compact physical projection, controlled prompt/schema hashes,
durable immutable attempts/items, two attempts/item and 16/32/$5 hard caps.
Human review remains a research activity, not a software gate.

The live job succeeded automatically on 16 first attempts. Raw responses exposed
implicit cache writes; preserve initial spend estimates and recompute ordinary,
cached-read, cache-write and output components from raw usage. Final estimate
$.522767 replaces $.491492 for reporting. Completed outputs are not overwritten.

Reproduce the supplied PowerBinary approximation, then explicitly implement its
fixed-prevalence one-parameter score statistic for finite-sample simulation.
Do not claim an estimated-prevalence Fleiss test is powered by this calculation.
The 140-record conditional simulated power is .87906 versus approximate .82374;
keep the settled allocation and report the discrepancy. Estimator/nuisance
prevalence/missingness/interval decisions still require scientific analysis freeze.

Primary generation proceeds independently of an unpinned alternative model.
The separate matched-input comparison interface records identical physical,
prompt and schema hashes; alternative requests remain pending. All generated
language is human-unreviewed; there is no annotation-quality or agreement result.

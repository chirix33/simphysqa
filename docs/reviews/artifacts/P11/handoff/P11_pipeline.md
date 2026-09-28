# Deadline study commands

Run from the repository in WSL2. Native artifacts and checkpoints live in
`/home/aashraf/phi-jepa/p11-tonight-01`; the frozen configuration is
`configs/study_p11_frozen.json`. The commands below reuse that frozen selection;
do not rerun `freeze` or change the population after held-out evaluation.

```bash
CORE=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
$CORE tools/p11_provider.py enrich
$CORE tools/p11_schedule.py gpu
$CORE tools/p11_provider.py wait_answers
```

The enrichment and waiting-answer commands must have only one active paid
request writer. The waiting command waits until all enrichment requests have
finished. The GPU supervisor waits for enrichment, prepares training/selection
references, encodes frozen Qwen inputs, and prepares custom tokens. It launches
one CPU numerical supervisor and serial custom GPU training/inference. Remote
answer work waits for the corresponding local main forecast. External commands
may run in separate terminals only in this documented arrangement.

Individual resumable stages:

```bash
$CORE tools/p11_data.py references
$CORE tools/p11_data.py encode
/home/aashraf/phi-jepa/.venvs/phi-coconut-custom/bin/python tools/p11_data.py custom_prepare
$CORE tools/p11_numerical.py train driving main
$CORE tools/p11_numerical.py inference driving main
/home/aashraf/phi-jepa/.venvs/phi-coconut-custom/bin/python tools/p11_custom.py train coconut
/home/aashraf/phi-jepa/.venvs/phi-coconut-custom/bin/python tools/p11_custom.py inference coconut
/home/aashraf/phi-jepa/.venvs/phi-codi-custom/bin/python tools/p11_custom.py train codi
/home/aashraf/phi-jepa/.venvs/phi-codi-custom/bin/python tools/p11_custom.py inference codi
$CORE tools/p11_evaluate.py
$CORE tools/p11_assessment.py
$CORE tools/p11_verify_artifacts.py
$CORE tools/p11_report.py
$CORE tools/p11_completion.py
```

Numerical arguments cover all four frozen domains and `main`/`appendix`.
Deployment installs a reference-open guard. Custom inference consumes only
public token records and checkpoint weights; held-out labels are first opened
by the evaluator. Historical checkpoint files are not modified. A crash may
resume from the last published checkpoint; histories retain executed work
that was not checkpointed. Failed requests are recorded and are not silently
retried or replaced with fixtures.

Assessment remains partial where required typed contracts or V1 components are
missing. Calibration is unavailable. Human-reviewed clarification is the
separately enabled P09/P10 interface, outside unattended P11 conditions.
Generation limits and strict parsers are unchanged. See the completion report
for actual completion statuses and costs, not the configuration's intended
workload.

P11 execution is now complete. Its final numerical/custom checkpoints are
preserved in the native run. Use the evaluation/report commands to inspect
existing evidence; do not restart a completed training stage to obtain a new
condition. The fixed deadline guards intentionally prevent late expensive
work. Any future study needs a new run identity, frozen plan and authorization.

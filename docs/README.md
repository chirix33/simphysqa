# SimPhysQA documentation

Read [agent instructions](../AGENTS.md), [current progress](PROGRESS.md) and the
[foundation](simphysqa/foundation.md) first. Current main includes the accepted
foundation and SPQ05 verified audit delivery. This SPQ06 review branch adds local
qualification and frozen held-out preparation; the main experiment is not launched.

| Topic | Entry |
| --- | --- |
| Purpose, setup, privacy and scope | [Foundation](simphysqa/foundation.md) |
| Accepted development evidence | [56-item index](simphysqa/development-index.md), [portable aliases/hashes](simphysqa/development-index.json) |
| Direct/predictive and public language | [Annotation](simphysqa/annotation.md) |
| Counterfactual | [Matched intervention contract](simphysqa/counterfactual.md) |
| Explanation | [Explanation contract](simphysqa/explanation_qa.md) |
| Clarification | [Query-gap contract](simphysqa/clarification_qa.md) |
| Event language and associations | [Event language](simphysqa/event_language.md), [associations](simphysqa/associations.md), [shared descriptions](simphysqa/event_descriptions.md) |
| Answer evidence | [Answer annotations](simphysqa/answer_annotations.md) |
| Current internal human audit | [SPQ05 protocol](simphysqa/formal_protocol.md), [guide](simphysqa/formal_reviewer_guide.md), [analysis](simphysqa/formal_analysis.md), [delivery receipt](reviews/SPQ05_completion.md) |
| SPQ06 qualification/preparation | [Completion](reviews/SPQ06_completion.md), [protocol](simphysqa/spq06_protocol.md), [main design](simphysqa/spq06_main_design.md), [commands](simphysqa/spq06_commands.md), [GGUF CUDA notes](simphysqa/gguf_cuda_setup.md) |
| Evaluation and remaining work | [Evaluation](simphysqa/evaluation.md), [pending research](simphysqa/pending.md) |
| Exact execution/procedure provenance | [Archive](simphysqa/prompt_archive/README.md), [SPQ05 supplement](simphysqa/prompt_archive/SPQ05/README.md) |
| Licenses/source generation | [License scope](../LICENSE.md), [original specification](../SPECIFICATION.md), [generation validation](../VALIDATION.md) |
| Workflow/recovery | [Cleanup decision](decisions/repo_cleanup.md), [historical note](history.md), [blocker template](prompts/BLOCKER_REPORT.md) |

SPQ prompts are authoring instructions; archived annotation requests are actual
generator payloads. Neither saved prompts nor proposed configs authorize a new run.
Completed SPQ reports and PDS source-generation evidence remain in reviews/ and
decisions/. Their dated execution restrictions and machine paths are historical
receipts, not current branch instructions. The current task/user authorization governs.

Original source-generation documents/configs retain obsolete downstream model fields
for provenance; learned-method sections are superseded. Source records, physical
definitions, tolerances and generation/admission semantics remain unchanged.
The two SHA256SUMS files describe original distribution snapshots, not today's tree;
use Git and the historical revisions to recover removed entries. Exact prompt/schema
assets and the archived per-file mappings are preserved.

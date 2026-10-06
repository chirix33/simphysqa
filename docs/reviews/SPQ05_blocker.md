# Closed historical budget blocker — 6 October 2026

The user authorized additional bounded resources and the exact external annotation payload/destination. Final 140-item package verified; shortfall 0. See [SPQ05 completion](SPQ05_completion.md). The original pre-authorization blocker below is retained as history, not current status. Human ratings remain uncollected.

# SPQ05 blocker — additional live-resource budget

- Phase/substep and status: SPQ05 family qualification/annotation/final packet freeze;
  implemented_pending_validation; complete formal packets0/140, shortfall140.
- Repository branch/commit and relevant paths: simphysqa-spq05, baseff2fe26,
  preparation producer0ff61ad; docs/simphysqa/formal_protocol.md,
  configs/simphysqa/formal_audit.json, external preparation-1.0.1/preflight.json.
- Expected behavior and source requirement: same140 fresh, balanced, fully qualified
  packets for each of three reviewers, excluding20 inspected groups; user explicitly
  forbids silently expanding old budgets and requests protocol/dry-run before asking.
- Exact command/minimal reproducer: `python -m simphysqa.formal_sampling --inventory
  <Prior>/spq01/inventory-final --artifacts <Prior> --output <Audit>/preparation-1.0.1`;
  exact machine paths/commands are in SPQ05_completion.md.
- Observed behavior and sanitized log: successful no-call prepare prints
  `remaining_initial_requests:0`, `remaining_simulation_executions:0`,
  `status:blocked_budget_not_ready_for_review`. New budgets=null. No transport called.
- Environment: Windows PowerShell, Python3.12.14, existing isolated CPU environment,
  jsonschema4.26.0; no GPU required. Replay requires original pinned WSL simulator
  runtime, separate from this CPU environment; not newly executed/qualified here.
- Attempts made/outcomes: refreshedmain/clean branch; read contracts/budgets; verified
  source6340 shards, prior62 manifests, original16-call accounting and32 saved solve
  reservations; froze280 disjoint candidates; exact payload/token dry-run; focused
  extraction56 excluded saved packets, blank form/import and actual resume checks.
- Confirmed root cause: old initial16-call and32-solve allowances already consumed.
  The only generated language is in excluded development groups. Generic source
  contexts cannot be substituted as completed timestamp language. New credentials
  have not been accessed; scope authorization does not invent new resource ceilings.
- Impact: live generation and final140 freeze blocked. Protocol, source/candidate
  ledgers, guide/analysis, extraction/import software, versioned provenance and
  preservation checks complete. No final manifest, formal forms or human ratings.
- Option A/tradeoff: authorize an explicit additional bounded run. Proposed maxima:
  280 initial annotation requests,560 total attempts,USD125,7M input/1,146,880 output
  tokens,2h annotation;672 simulations,180s/solve,1h total. Reserve spending only
  as needed, conditional per-attempt admission; historical full reservation56.15
  for all candidate initial payloads/112.30 before feedback for two attempts.
  Refresh pricing/provider/runtime and adapt runner first. Qualification shortfall
  remains possible; this is not a guaranteed140/quality result.
- Option B/tradeoff: retain existing ceilings and accept this preparation/shortfall
  handoff; no valid way to fill the required fresh five-family140 now.
- Recommended option: A if the intended audit is to begin; this preserves random
  ordering, exclusions, scorer-disjoint clarification and verified outcomes without
  expanding the full release or replacing scientific requirements.
- Smallest question: what explicit additional bounded annotation/simulation ceilings
  are authorized? The proposal above was asked in the coding session; no per-item
  human approval is required. Different ceilings can be supplied explicitly.
- Evidence to close: user authorization recorded, resource config pinned; refreshed
  non-secret provider/runtime preflight and qualified live runner; saved outcomes,
  call/failure/rejection/replacement ledgers and140 validated packet manifests.

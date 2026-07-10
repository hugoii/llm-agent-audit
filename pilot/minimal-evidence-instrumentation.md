# Minimal Evidence Instrumentation

This note defines the smallest event surface needed when an existing redacted
trace cannot support an Agent Authorization Review. It is a field target, not a
required SDK, collector, agent runtime, or observability product.

## Integration order

Use the least intrusive path that works:

1. export existing spans, logs, approval records, tool events, job events, and
   ledger or ERP audit rows;
2. map the existing fields into `normalized_trace.schema.json` or
   `evidence_event.schema.json`;
3. add only the missing event at the nearest authoritative boundary;
4. rerun one synthetic staging action and reassess readiness.

Do not refactor the agent runner merely to satisfy the review.

## Minimal action-boundary events

| Event | Emit at | Purpose |
|---|---|---|
| `workflow.phase.changed` | workflow state store or orchestrator | Bind execution to a phase and state-artifact version. |
| `authorization.decision_made` | policy or permission check | Record actor, action, canonical target, arguments hash, decision, and policy version. |
| `approval.bound` | approval service or transaction-authorization layer | Bind approval to the exact action, target, and arguments hash. |
| `harness.gate.evaluated` | deterministic workflow gate | Show whether the workflow allowed the next phase. |
| `tool.call_attempted` | tool gateway or action adapter | Record the actual actor, role, tool grant, action, target, and arguments hash. |
| `execution.revalidated` | action gateway immediately before execution | Reread authoritative state and bind the decision to the exact action, target, and arguments hash. |
| `action.executed` | business action service | Produce a receipt bound to the same action, target, and arguments hash. |
| `business.postcondition.observed` | ERP, ledger, audit table, or independent readback | Observe the resulting business state independently of the agent reply. |

`workflow.fork_join.observed` is optional unless the selected workflow performs
parallel branches, shared-resource mutation, or an atomic join.

## Correlation

Every event needs a stable `trace_id`, unique `event_id`, unique `span_id`, and
timestamp. Use `parent_span_id` to preserve causal order across agent,
orchestrator, gateway, job, and business-system boundaries. Asynchronous work
can start a new trace only if the export preserves a causal link to the original
request.

The readiness check rejects target or argument drift across authorization,
approval, tool attempt, revalidation, and execution. It also rejects a committed
execution after an authorization, workflow gate, or execution-time revalidation
returned `denied` or `route_to_review`.

Existing OpenTelemetry traces and correlated logs are acceptable. Preserve the
customer's original identifiers in the customer-controlled source; use
redacted, tokenized, or irreversible surrogate identifiers in the review
export.

## Optional harness context

When material to the scenario, map:

- `workflow_id`, `workflow_phase`, and `state_artifact_sha256`;
- `knowledge_version` and policy version;
- `parent_run_id`, `agent_role`, `delegated_by`, and `delegation_chain`;
- `tool_grant_id` and the exact granted tool names;
- `gate_id` and `gate_decision`;
- `fork_id`, `branch_id`, `join_id`, `join_status`, atomicity, and shared
  resource keys.

Do not mark these fields complete because they appeared in a prompt or agent
reply. They need an orchestrator, policy, gateway, state-store, or business
system evidence source.

## Data minimization

Do not emit or send raw prompts, unrestricted tool payloads, production secrets,
access tokens, bank-account values, payment-card data, PHI, PII, or raw customer
records. Prefer:

- canonical resource IDs or irreversible surrogates;
- SHA-256 of canonical action arguments and state artifacts;
- approval and policy identifiers without approval-body content;
- mutation IDs and state hashes instead of full before/after records;
- a separate redaction note and customer-owned unredacted source of record.

## Readiness command

Validate the event shape and generate the gap map:

```bash
python -m actionboundary validate \
  --evidence-events examples/minimal_evidence_events.redacted.json

python -m actionboundary readiness \
  --evidence-events examples/minimal_evidence_events.redacted.json \
  --out tmp/evidence-readiness.json
```

Missing events mean the workflow is not yet fully observable. They do not prove
that the authorization control failed. A strict scenario that requires missing
runtime evidence remains `INCONCLUSIVE`.

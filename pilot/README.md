# Audit your own agent (pilot kit)

Run an Agent Authorization Review against your own tool-using agent, fully
async, staging only. You get back an OWASP/NIST-mapped report with correlated
runtime evidence, strict verdicts, and concrete fixes. ActionBoundary does not
need access to your production systems, real customer data, or shared
credentials.

## The rule that makes trace results valid

An Agent Authorization Review is about what the agent does: which tools it calls,
with what arguments, and what authorization evidence existed at that moment.

The trace should show the action path: the caller request, the data the agent
read, the principal or role when relevant, the tool calls and results, the
authorization records or decisions the system used, and what actually changed.

Keep two things separate:

- `scenario_setup`: what the test fixture intended or seeded before execution;
- `runtime_evidence`: what the agent, tools, policy layer, approval system, or
  sandbox ledger actually observed during the run.

Scenario setup can explain the test. It does not prove that the system checked
the same facts at runtime.

Some scenarios test **indirect** prompt injection or other untrusted business
context. In those scenarios, the test content must go into
`data_the_agent_reads`, such as a ticket, invoice, email, document, or tool
response. It should not be pasted into the user's message unless the scenario
explicitly says it is testing a direct user request.

Other scenarios may test direct requests, benign controls, authorization-source
confusion, scope mismatch, or short multi-turn workflows. In every case, follow
the scenario instructions and preserve the runtime evidence: tool calls,
authorization decisions, tool results, and side-effect or ledger outcomes. The
normalized runtime evidence is what the verdict uses.

## Files

- `what-we-need.md`: the short first-contact checklist for sending three details before engineering setup.
- `client-handoff.md`: the technical handoff note for choosing a safe staging
  path, running one setup scenario, and sending back traces.
- `trace_schema.json`: flexible client trace submission schema for what you send
  back (a `runs` array). It accepts imperfect existing logs.
- `normalized_evidence_schema.json`: strict normalized runtime evidence schema
  used by the verdict protocol after ActionBoundary converts the client trace
  into action-level evidence.
- `sample_flexible_client_trace.json`: a worked example of the flexible client trace submission.
- `sample_normalized_evidence_v1_1.json`: the same scenario after
  ActionBoundary normalization into strict action-level runtime evidence.
- `adapter_template.py`: fill in two functions (`load_scenario_data`,
  `run_agent`) to run the scenarios you were sent against your staging agent and
  emit traces in the schema.
- `verdict_protocol.md`: how ActionBoundary decides `EXPLOITED`, `BLOCKED`,
  `BENIGN_PASS`, `BENIGN_REGRESSION`, `INCONCLUSIVE`,
  `INFRASTRUCTURE_ERROR`, or `NOT_TESTED`.
- `score_authorization_trace.py`: local scorer for fixed fixtures and setup
  checks; final client reports still include human review of the evidence.
- `ap_payment_boundary_scenarios.md`: a focused 8-scenario sketch for one
  staging payment action, including approval scope, cross-agent handoff, and
  retry/idempotency.
- `ap_payment_boundary_manifest.json`: machine-readable AP payment scenario
  oracle with invariant IDs, material fields, required runtime evidence, and
  allowed terminal states.

## Steps

1. Fill in `adapter_template.py` for your agent. Staging or sandbox only, with mocked or sandboxed tools.
2. Run it on the scenario set you were sent. It writes `trace_results.json`.
3. Optionally run the local scorer as a setup check:

   ```bash
   python pilot/score_authorization_trace.py trace_results.json \
     --manifest pilot/ap_payment_boundary_manifest.json \
     --out scored_trace_results.json
   ```

4. Send `trace_results.json` back. The trace should be correlated enough to
   identify the acting identity, target resource, authorization decision, tool
   result, and sandbox or business outcome. No production, no real customer
   data, no shared credentials.

Tip: before the full run, do one scenario first and send it back so the wiring
can be checked. The common mistakes are missing tool results, missing
authorization decisions, missing side-effect evidence, copying fixture fields
into runtime evidence, and, for indirect-injection scenarios, putting the test
instruction in the user prompt instead of in the data the agent reads.

Main project and writeup: https://github.com/hugoii/llm-agent-audit

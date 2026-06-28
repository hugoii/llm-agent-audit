# How the pilot works

A fixed-scope, lightweight check of whether your tool-using agent only takes high-impact actions with the right authorization evidence. Staging only. No production access, no real customer data, no shared credentials.

## The steps

1. We start with a 3-scenario sketch so you can judge fit before setup.
2. If it fits, we first inspect one existing redacted trace or exported log
   from the workflow, if you already have one. No new instrumentation or
   staging run is required for this scoreability diagnostic.
3. If no useful trace exists, or the trace is not representative, we run one
   synthetic staging trace as the Evidence Readiness Check.
4. If the trace is ready, we agree on 5 to 10 selected scenarios mapped to
   actions your agent can trigger. ActionBoundary identifies the risky
   authorization cases and chooses benign controls from a workflow-specific
   library when one applies, instead of asking your team to design normal-path
   test cases from scratch.
5. Your team runs them against a staging copy of your agent or shares a safe
   test endpoint, then exports the tool-call traces plus authorization
   decisions, tool results, and side-effect or ledger evidence.
6. I normalize and score the runtime evidence against the pilot verdict
   protocol, then send you an OWASP/NIST-mapped report with the action evidence
   and concrete fixes.
7. One included retest of the same scenario set after you apply fixes.

If the first trace is not scoreable yet, the output is an evidence gap map and
the smallest instrumentation plan needed before a full trace-backed pilot.

Founding design-partner reviews may use a narrower scope: identify 2 to 3
candidate high-impact action paths, then select one representative path for a
narrow but deep staging review. The selected path uses 5 to 10 selected
scenarios, including benign controls, strict verdicts, concrete fixes, and one
same-path retest. The limited early pricing applies to the first design
partners. Broader workflows, additional paths, expanded reports, or extra
retests are scoped separately.

## Minimal inputs

- One existing redacted trace or exported log if available: LangSmith,
  Langfuse, OpenTelemetry, Datadog, CloudWatch, internal JSON logs, tool
  invocation tables, audit tables, or job logs are all acceptable starting
  points.
- A staging or sandbox copy of the agent, with its tools mocked or sandboxed,
  or a safe test endpoint, when moving beyond the first diagnostic.
- A way to capture correlated runtime evidence: the agent's tool calls, acting identity, target resource, authorization decisions, tool results, and side-effect or ledger outcomes.
- A short written authorization for the test.

No production access, no real customer data, no shared credentials.

## Readiness engagement ladder

| Level | What is available | Appropriate engagement | Output |
|---|---|---|---|
| Level 0 | Product/workflow description only | Scenario design review | 3 scenarios plus the evidence map a buyer would expect |
| Level 1 | Existing redacted trace, but authorization or outcome evidence is incomplete | Existing trace diagnostic | Scoreability result, missing evidence, and smallest next instrumentation point |
| Level 2 | Tool calls and partial authorization evidence, but one synthetic run is needed | Synthetic readiness check | Go/no-go for the full pilot plus instrumentation plan |
| Level 3 | Actor, target, authorization, tool result, and outcome are visible | Full trace-backed pilot | Report, strict verdicts, fixes, and retest |
| Founding design-partner | Trace path is scoreable and the buyer wants a narrow first review | Representative-path review | 2 to 3 candidate paths identified; one path reviewed with 5 to 10 selected scenarios including benign controls, compact evidence memo, fixes, and one same-path retest |

Only Level 3 produces the full workflow trace-backed authorization verdict. A
founding design-partner review can start from Level 3 evidence but deliberately
limits the reviewed path, report depth, number of action paths, and retest
scope. Lower levels are still useful paid or design-partner engagements because
they show exactly what evidence is missing before a customer security reviewer
asks for it.

## What you get

An independent, evidence-backed report you can act on, and that you can show to a customer's security review or your own team.

For a customer-run trace, the report is explicit about the evidence boundary:
ActionBoundary independently designs and scores the scenarios using
client-provided staging traces. Execution happens in a client-controlled
environment, so the report does not pretend ActionBoundary independently
attested to the completeness of all client-side logs.

## What it is not

Not production testing. Not a full penetration test, compliance certification, SAST, IAM/MCP configuration audit, or secret scan. It is a focused look at one thing: whether high-impact agent actions are bound to trusted, current, scope-matching authorization evidence.

## Safety

Staging or sandbox only, never production. Written authorization before any test. A harmless canary value for any leak test, never real secrets.

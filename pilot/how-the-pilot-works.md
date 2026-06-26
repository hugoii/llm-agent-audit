# How the pilot works

A fixed-scope, lightweight check of whether your tool-using agent only takes high-impact actions with the right authorization evidence. Staging only. No production access, no real customer data, no shared credentials.

## The steps

1. We start with a 3-scenario sketch so you can judge fit before setup.
2. If it fits, we check one synthetic staging trace for scoreability. This is
   the Evidence Readiness Check.
3. If the trace is ready, we agree on 5 to 10 scenarios mapped to actions your
   agent can trigger. ActionBoundary identifies the risky authorization cases
   and writes scenarios for your tools, not a generic checklist.
4. Your team runs them against a staging copy of your agent or shares a safe
   test endpoint, then exports the tool-call traces plus authorization
   decisions, tool results, and side-effect or ledger evidence.
5. I normalize and score the runtime evidence against the pilot verdict
   protocol, then send you an OWASP/NIST-mapped report with the action evidence
   and concrete fixes.
6. One included retest of the same scenario set after you apply fixes.

If the readiness trace is not scoreable yet, the output is an evidence gap map
and the smallest instrumentation plan needed before a full trace-backed pilot.

## Minimal inputs

- A staging or sandbox copy of the agent, with its tools mocked or sandboxed, or a safe test endpoint.
- A way to capture correlated runtime evidence: the agent's tool calls, acting identity, target resource, authorization decisions, tool results, and side-effect or ledger outcomes.
- A short written authorization for the test.

No production access, no real customer data, no shared credentials.

## Readiness levels

| Level | What is available | What ActionBoundary can do |
|---|---|---|
| Level 0 | No staging path or no observable tool calls | Scenario sketch or design review only |
| Level 1 | Tool calls are visible, but authorization or outcome logs are missing | Evidence Readiness Check |
| Level 2 | Tool calls and authorization are visible, but final outcome is missing | Partial review plus instrumentation fixes |
| Level 3 | Actor, target, authorization, tool result, and outcome are visible | Full trace-backed pilot |

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

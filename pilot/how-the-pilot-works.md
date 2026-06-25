# How the pilot works

A fixed-scope, lightweight check of whether your tool-using agent only takes high-impact actions with the right authorization evidence. Staging only. No production access, no real customer data, no shared credentials.

## The steps

1. We start with a 3-scenario sketch so you can judge fit before setup.
2. If it fits, we agree on 5 to 10 scenarios mapped to actions your agent can trigger. ActionBoundary identifies the risky authorization cases and writes scenarios for your tools, not a generic checklist. Scenarios can cover a single high-impact action or a short workflow where an earlier approval might be reused or applied too broadly later in the workflow.
3. Your team runs them against a staging copy of your agent or shares a safe test endpoint, then exports the tool-call traces. There is a small adapter to make this easier, and we can do a quick one-scenario setup check first so the results separate scenario setup from runtime evidence.
4. I normalize and score the traces against the pilot verdict protocol, then send you an OWASP/NIST-mapped report with the tool-call evidence and concrete fixes.
5. One included retest of the same scenario set after you apply fixes.

## Minimal inputs

- A staging or sandbox copy of the agent, with its tools mocked or sandboxed, or a safe test endpoint.
- A way to capture the agent's tool calls (most teams already log these).
- A short written authorization for the test.

That is it. No production access, no real customer data, no shared credentials.

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

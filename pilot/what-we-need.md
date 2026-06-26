# What ActionBoundary needs first

Send three details. ActionBoundary can use them to draft the first scenario set before any engineering setup.

## The three details

1. **Product and buyer**

   What your agent does, who buys it, and why this review matters now.

2. **One workflow or action surface**

   Tell us where the agent can affect the business: refund, payment, access grant, export, record change, scheduling step, submission, or customer message. You do not need to choose the exact failure case. ActionBoundary identifies the risky authorization boundary and turns it into scenarios.

3. **Safe test path**

   Any safe way to observe the workflow: one existing redacted trace, staging
   traces, a sandbox endpoint, exported tool-call and authorization logs, or
   another non-production run path. LangSmith, Langfuse, OpenTelemetry,
   Datadog, CloudWatch, internal JSON logs, tool tables, audit tables, and job
   logs are all acceptable starting points.

That is enough for a first reply. The first response is not a full engagement request; it is a scenario-fit check.

## What happens next

If the workflow fits the review, ActionBoundary sends a small first scenario
set. Before a paid pilot, we first inspect one existing redacted trace or
exported log if you already have one. No new instrumentation or staging run is
required for that first scoreability diagnostic. If no useful trace exists, we
can use one synthetic staging trace instead. If the trace is not ready for a
strict verdict, the output is an evidence gap checklist and minimal
instrumentation plan.

For setup, the review usually needs:

- one staging or sandbox workflow;
- an existing redacted trace, exported logs, or a narrow safe test endpoint that can show tool calls, authorization decisions, tool results, and side-effect outcomes;
- where authority lives today, such as user role, permission, approval, tenant scope, policy, or system record;
- written authorization for the named staging or sandbox scope.

See [Evidence Readiness Check](evidence-readiness-check.md) for the
existing-trace-first gate that decides whether the full trace-backed pilot is
ready.

## What not to send

Do not send production credentials, real customer data, real secrets, PHI, PII, payment card data, financial account data, raw database dumps, or unrestricted admin accounts.

Use synthetic data, de-identified data, or harmless canary values. If sensitive data could appear in a trace, pause first so the data can be removed or the right agreement can be put in place.

Private traces should move through a customer-approved secure channel, not
public GitHub issues, public pull requests, or public chat. The default
retention rule is deletion within 30 days after final report delivery, or sooner
on written request. See [Trust & Data Handling](../TRUST.md).

## Engineering handoff

When the workflow is ready for setup, use the [technical handoff](client-handoff.md) for trace format, setup paths, adapter options, expected engineering time, and deliverables.

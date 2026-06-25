# What ActionBoundary needs first

Send three details. ActionBoundary can use them to draft the first scenario set before any engineering setup.

## The three details

1. **Product and buyer**

   What your agent does, who buys it, and why this review matters now.

2. **One workflow or action surface**

   Tell us where the agent can affect the business: refund, payment, access grant, export, record change, scheduling step, submission, or customer message. You do not need to choose the exact failure case. ActionBoundary identifies the risky authorization boundary and turns it into scenarios.

3. **Safe test path**

   Any safe way to observe the workflow: staging traces, a sandbox endpoint, exported tool-call and authorization logs, or another non-production run path.

That is enough for a first reply. The first response is not a full engagement request; it is a scenario-fit check.

## What happens next

If the workflow fits the review, ActionBoundary sends a small first scenario set. The paid pilot starts only after the safe test path and evidence boundary are clear.

For setup, the review usually needs:

- one staging or sandbox workflow;
- runtime traces, exported logs, or a narrow safe test endpoint that can show tool calls, authorization decisions, tool results, and side-effect outcomes;
- where authority lives today, such as user role, permission, approval, tenant scope, policy, or system record;
- written authorization for the named staging or sandbox scope.

## What not to send

Do not send production credentials, real customer data, real secrets, PHI, PII, payment card data, financial account data, raw database dumps, or unrestricted admin accounts.

Use synthetic data, de-identified data, or harmless canary values. If sensitive data could appear in a trace, pause first so the data can be removed or the right agreement can be put in place.

## Engineering handoff

When the workflow is ready for setup, use the [technical handoff](client-handoff.md) for trace format, setup paths, adapter options, expected engineering time, and deliverables.

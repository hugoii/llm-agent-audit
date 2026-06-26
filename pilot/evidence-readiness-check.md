# Evidence Readiness Check

Before a full Agent Authorization Review, ActionBoundary can check whether one
existing redacted trace or exported log is scoreable.

This is a small pre-pilot gate. It uses evidence the team already has whenever
possible: LangSmith, Langfuse, OpenTelemetry, Datadog, CloudWatch, internal
JSON logs, tool invocation tables, audit tables, or payment job logs. No new
instrumentation and no new staging run are required for the first diagnostic.

If there is no existing trace, or the trace is not representative, the same
check can use one synthetic staging run.

## Goal

Decide whether one high-impact agent action can support a trace-backed
authorization verdict.

The check does not decide that the system is safe. It decides whether the trace
can prove what happened well enough to run the full pilot.

## Input

Preferred input:

- one existing redacted trace, exported log, or structured table for a
  high-impact action.

Acceptable sources include LangSmith, Langfuse, OpenTelemetry/OTLP, Datadog,
Honeycomb, New Relic, CloudWatch, internal JSON logs, tool invocation tables,
approval audit tables, payment job logs, webhook logs, or sandbox ledger
events.

The trace can come from an ordinary development, staging, demo, or sandbox run.
It does not need to be a new test scenario for the first diagnostic.

If no useful existing trace is available, use one synthetic staging run for a
high-impact action, such as:

- schedule a payment;
- submit or release a payment batch;
- update vendor remittance details;
- issue a refund;
- grant access;
- export customer or vendor data;
- submit a regulated or customer-visible record.

Use synthetic, redacted, de-identified, or harmless canary data. Do not send
production credentials, real secrets, unrestricted admin accounts, raw customer
data, payment card data, financial account data, PHI, or PII.

## What ActionBoundary Checks

The readiness check looks for runtime evidence that can be correlated to the
same action:

- acting identity or service account;
- target resource, such as invoice, vendor, tenant, account, or record;
- authorization source, approval lookup, policy decision, or permission check;
- tool decision;
- tool result;
- business, ledger, sandbox, or audit-log outcome;
- trace ID, correlation ID, event IDs, or timestamps.

Scenario setup is useful context, but it does not count as runtime evidence.

## Output

The result is one of three readiness levels:

| Result | Meaning | Next step |
|---|---|---|
| `READY` | Actor, target, authorization, tool result, and outcome are observable. | Proceed to the trace-backed pilot. |
| `PARTIALLY_READY` | Some runtime evidence is visible, but a strict verdict would still be incomplete. | Add the smallest missing instrumentation, then rerun one trace. |
| `NOT_READY` | The workflow is not yet observable enough for trace-backed scoring. | Do a scenario sketch, tool-surface review, or staging evidence plan first. |

## Engagement Ladder

Readiness is a path, not a rejection. Different teams can start at different
levels:

| Level | What the team has | Appropriate engagement | Output |
|---|---|---|---|
| 0 | Product and workflow description only | Scenario design review | 3 scenarios plus the evidence map a buyer would expect |
| 1 | Existing redacted trace, but authorization or outcome evidence is incomplete | Existing trace diagnostic | Scoreability result, missing evidence, and smallest next instrumentation point |
| 2 | Tool calls and partial authorization evidence, but one synthetic run is needed | Synthetic readiness check | Go/no-go for the full pilot plus instrumentation plan |
| 3 | Actor, target, authorization source, tool result, and outcome are visible | Full trace-backed pilot | Scenario report, strict verdicts, fixes, and retest |

Only Level 3 supports a full trace-backed authorization verdict. Lower levels
still produce useful buyer-readiness work without pretending the system has
passed or failed.

## Example Finding

```text
PARTIALLY_READY

Observed:
- tool calls
- tool results
- target invoice ID

Missing:
- acting principal or service account
- approval lookup source
- final sandbox ledger outcome

Strict verdict today:
INCONCLUSIVE

Recommended instrumentation:
1. Emit actor_id and tenant_id at the tool gateway.
2. Log approval lookup source, approval_id, and decision reason.
3. Emit payment_intent_id or business_action_key for retries.
4. Record final sandbox ledger outcome.
```

## What This Is Not

The readiness check is not a full authorization review, penetration test,
compliance certification, SOC report, or production security assessment.

It is a buyer-readiness artifact: it tells the team whether they can produce the
runtime evidence an enterprise security reviewer will expect for one
high-impact agent action.

## When To Use It

Use this before the full pilot when:

- an existing trace or log may already show enough to diagnose scoreability;
- staging exists, but logging may be incomplete;
- tool calls are visible, but authorization decisions are not structured;
- side effects are created asynchronously through jobs, webhooks, or ledgers;
- the team is not sure whether current traces separate scenario setup from
  runtime evidence;
- a customer is likely to ask how the agent proves that money movement, data
  export, access grant, or record change was authorized.

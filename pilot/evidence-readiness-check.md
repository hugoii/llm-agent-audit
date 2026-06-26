# Evidence Readiness Check

Before a full Agent Authorization Review, ActionBoundary can check whether one
synthetic staging trace is scoreable.

This is a small pre-pilot gate. It protects the client from starting a full
trace-backed review when the current staging path cannot yet show enough
runtime evidence for a strict verdict.

## Goal

Decide whether one high-impact agent action can support a trace-backed
authorization verdict.

The check does not decide that the system is safe. It decides whether the trace
can prove what happened well enough to run the full pilot.

## Input

One synthetic staging run or exported trace for a high-impact action, such as:

- schedule a payment;
- submit or release a payment batch;
- update vendor remittance details;
- issue a refund;
- grant access;
- export customer or vendor data;
- submit a regulated or customer-visible record.

The run should use synthetic or de-identified data. No production access, real
customer data, real secrets, or shared credentials are needed.

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

- staging exists, but logging may be incomplete;
- tool calls are visible, but authorization decisions are not structured;
- side effects are created asynchronously through jobs, webhooks, or ledgers;
- the team is not sure whether current traces separate scenario setup from
  runtime evidence;
- a customer is likely to ask how the agent proves that money movement, data
  export, access grant, or record change was authorized.


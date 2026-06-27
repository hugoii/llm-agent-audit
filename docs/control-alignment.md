# ActionBoundary Control Alignment

This page maps ActionBoundary's trace-backed review fields to common security,
AI-agent, and AP/payment-control language.

It is not a compliance certification, audit opinion, SOC report, PCI
assessment, or legal conclusion. Trace evidence drives the verdict. The
references below support review language and control discussion only.

## Why This Exists

ActionBoundary scenarios are not arbitrary AI prompts. They test whether a
high-impact agent action is bound to trusted, current, scope-matching
authorization evidence.

For AP/payment workflows, that means the review asks familiar control questions:

- Who actually caused the payment action?
- Did the current actor have payment authority?
- Did the approval cover the vendor, amount, currency, destination, tenant, and
  timing?
- Did bank details come from a trusted vendor master or approved bank-change
  workflow?
- Did the tool or application layer enforce authorization outside the model?
- What business side effect actually happened?
- Can the trace prove the answer with audit-quality event IDs, timestamps, and
  source-of-truth evidence?

The model may propose work. The application or tool layer must authorize the
transaction.

## Control Map

| ActionBoundary check | Real-world control question | Common review language | Required trace evidence |
|---|---|---|---|
| Observed actor / principal | Who caused the high-impact action? | NIST SP 800-53 AC-3 Access Enforcement and AC-6 Least Privilege | `observed_actor`, principal or service account ID, role, tenant, permissions, timestamp, evidence source |
| Payment approval scope | Did the approval cover vendor, amount, currency, destination, entity, tenant, and timing? | OWASP Transaction Authorization; COSO internal control language | Approval lookup, policy version, source-of-truth approval record, scope match, parameter coverage |
| Invoice approval is not payment authority | Is execution authority separate from invoice approval? | NIST SP 800-53 AC-5 Separation of Duties; COSO control activities | Actor permission, approval evidence, payment-tool authorization decision, denial or approval reason |
| Vendor-bank source of truth | Did payment destination come from the vendor master or an approved bank-change workflow? | FBI Business Email Compromise guidance; GFOA Electronic Vendor Fraud guidance | Vendor master record, bank-change approval, requested account source, trusted account source, out-of-band verification when available |
| Tool-layer enforcement | Did the application or tool enforce authorization outside the model response? | OWASP AI Agent Security; OWASP Transaction Authorization; NIST AC-3 | Policy decision, allowed or denied status, tool result, reason, source system, event ID |
| Side effect / outcome | What actually changed? | NIST SP 800-53 AU-12 Audit Record Generation; payment-control audit evidence | Sandbox ledger event, job status, payment lifecycle status, production-side-effect flag, real-payment-rail flag, trace ID |
| Retry / duplicate payment | Did one business action create at most one payment side effect? | Idempotency, audit logging, fraud-monitoring review language | `business_action_key`, idempotency key, prior payment lookup, duplicate-denied status, existing-result-returned status |
| Benign controls | Does normal AP automation still work when authorization is valid? | COSO monitoring and control-effectiveness language | Authorized actor, matching approval, trusted destination, allowed tool result, expected terminal state |
| Missing or conflicting evidence | Can a reviewer tell whether the boundary held? | Auditability and evidence-readiness language | Missing-evidence list, unknown terminal state, conflicting policy/tool/outcome records, instrumentation gap |

## How To Use This Mapping

Use this page to explain why the review asks for actor, approval, destination,
tool result, and business-outcome evidence.

Do not use it to imply:

- COSO compliance;
- NIST compliance;
- PCI readiness;
- SOC 2 readiness;
- NACHA compliance;
- financial-grade certification;
- audit approval;
- legal conclusion.

Safer language:

- aligned to common review language;
- mapped for control discussion;
- fixed-scope authorization-boundary review;
- trace evidence drives the verdict;
- useful before customer security review, procurement review, or finance-control
  review.

## AP/Payment Examples

| Scenario | Control principle | What ActionBoundary verifies |
|---|---|---|
| Vendor email or invoice PDF requests a bank-account change | Email and PDF content are business context, not bank authority | Whether destination came from vendor master or an approved bank-change workflow |
| Invoice is approved, but actor lacks payment authority | Approval state and execution authority are separate controls | Whether the current user or service account had payment execution permission |
| Approval reference is stale, copied, or carried through a handoff | Transaction authorization must be current and source-of-truth backed | Whether the payment tool performed its own approval lookup at action time |
| Payment is scheduled, routed, released, or reversed | The terminal business effect matters more than the status label | Whether the trace maps raw lifecycle status to a strict terminal state |
| Retry or webhook replay repeats a payment action | One business action should not create duplicate payment effects | Whether idempotency or duplicate controls denied the replay or returned the existing result |
| Trace lacks side-effect evidence | Missing terminal evidence is not a pass | Whether the report should mark the action `INCONCLUSIVE` or return an evidence-readiness gap |

## Reference Layer

These references are used as review-language support. They do not replace the
customer's own control framework, auditor, assessor, legal counsel, or compliance
program.

- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
- [OWASP Transaction Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [COSO Internal Control - Integrated Framework](https://www.coso.org/guidance-on-ic)
- [FBI Business Email Compromise](https://www.fbi.gov/how-we-can-help-you/scams-and-safety/common-frauds-and-scams/business-email-compromise)
- [GFOA Electronic Vendor Fraud](https://www.gfoa.org/materials/electronic-vendor-fraud)

Where payment-card environments are specifically in scope, PCI DSS
access-control and logging concepts may be relevant, but ActionBoundary is not a
PCI assessment. Use the [PCI Security Standards Council document library](https://www.pcisecuritystandards.org/document_library/)
for current PCI materials.

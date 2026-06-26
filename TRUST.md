# Trust & Data Handling

ActionBoundary is designed for staging-only Agent Authorization Reviews. The
default engagement does not require production access, production credentials,
real customer data, or shared credentials.

This page is the short buyer-facing security posture. Engagement-specific terms
are confirmed in the statement of work, NDA, MSA, BAA, or DPA where applicable.

## Default posture

- **Staging or sandbox only.** Reviews use staging, sandbox, exported logs, or
  redacted traces. Production systems are out of scope by default.
- **Trace-based by default.** Your team can run scenarios and send back traces;
  ActionBoundary does not need access to your systems.
- **Synthetic or redacted data.** Test data should be synthetic, de-identified,
  or represented by harmless canary values.
- **No shared credentials.** Do not send passwords, API keys, session tokens,
  private keys, production credentials, or unrestricted admin accounts.
- **Written authorization first.** Any staging test path must be named and
  authorized in writing before a pilot run.

## What not to send

Do not send production credentials, real customer data, real secrets, PHI, PII,
payment card data, financial account data, raw database dumps, or unrestricted
admin accounts.

If sensitive data could appear in a trace, pause first. Either redact or
de-identify the trace before transfer, or put the right agreement in place
before anything is shared.

## Trace transfer

Private traces should be transferred through a customer-approved secure channel,
such as a client portal, encrypted file share, private repository, or agreed
secure link.

Do not send private traces through public GitHub issues, public pull requests,
public discussions, or public chat channels.

## Redaction requirements

Before sharing a trace, remove or replace:

- customer names, emails, phone numbers, addresses, account numbers, and other
  direct identifiers;
- secrets, tokens, credentials, signatures, authorization headers, and session
  cookies;
- production tenant IDs, production ledger IDs, production bank details, and raw
  payment instructions;
- PHI, PII, cardholder data, and regulated financial data unless a written
  agreement explicitly permits it.

Synthetic values and harmless canaries are preferred. A canary should prove
whether data moved without exposing a real secret.

## Access and storage

Client traces are kept on encrypted, access-controlled local storage after
receipt. Access is limited to the named reviewer for the engagement unless
otherwise agreed in writing.

Client traces are not used for model training, public examples, benchmark data,
marketing claims, or third-party disclosure without explicit written permission.

## Retention and deletion

Default retention is deletion within 30 days after final report delivery, or
sooner on written request.

Deletion confirmation is available on request. Engagement-specific retention
terms can replace this default when required by contract.

## Third-party LLMs and subprocessors

Client traces are not sent to third-party LLMs, model providers, or shared
analysis tools by default.

If your team requests or approves LLM-assisted analysis or another third-party
processing path, it requires written approval first and should use minimized,
redacted inputs.

Default trace-analysis subprocessors: none.

## Contracts

ActionBoundary can review and sign reasonable engagement paperwork when the
work requires it, including NDA, MSA, DPA, or BAA terms.

The review is not a compliance certification, SOC 2 audit, HIPAA assessment,
PCI assessment, penetration test, SAST, or full IAM/MCP configuration audit. It
is a focused authorization-boundary review for one or more high-impact agent
actions.

## Contact

Security and data-handling questions: jiahao@actionboundary.dev

Public security reporting guidance: [SECURITY.md](SECURITY.md)

# Technical Evidence Directory

This directory is the public evidence room for ActionBoundary. It is organized
for different readers: a buyer doing a first check, a CTO or security reviewer
digging into the method, and an engineer preparing a staging trace handoff.

The main website and root README stay intentionally short. Use this page when
you want the deeper artifacts.

## Start Here

- [Evidence flow](evidence-flow.md): how untrusted business content, tool calls,
  authorization evidence, findings, fixes, and retests connect.
- [Sample evidence report](sample-pilot-report-v0.8.md): the public synthetic
  report source.
- [Rendered PDF sample](sample-evidence-report-v0.8.pdf): the polished sample
  report generated from the public report source.
- [Customer trace handoff template](customer-trace-handoff-template.md): the
  smallest useful trace export shape for one redacted staging run.
- [Control alignment](control-alignment.md): how trace evidence maps to common
  AI-agent, security, and AP/payment-control review language.

## Customer Handoff

- [What we need first](../pilot/what-we-need.md): the short first-contact
  checklist before engineering setup.
- [Evidence readiness check](../pilot/evidence-readiness-check.md): how one
  existing redacted trace is inspected before a full run.
- [Technical handoff](../pilot/client-handoff.md): the engineering handoff for a
  staging or sandbox pilot.
- [Adapter template](../pilot/adapter_template.py): a small Python adapter shape
  for emitting trace results from a customer agent.
- [Pilot kit README](../pilot/README.md): the full pilot artifact map.

## Sample Deliverables

- [Sample evidence report source](sample-pilot-report-v0.8.md)
- [Sample evidence report PDF](sample-evidence-report-v0.8.pdf)
- [Legacy sample PDF](sample-evidence-report.pdf)
- [Offline demo report](offline-demo-report.md)

## AP And Payment Authorization

- [A payment approval is not user authorization](payment-approval-is-not-user-authorization.md)
- [Control alignment](control-alignment.md)
- [AP agent authorization methodology](ap-agent-authorization-methodology.md)
- [AP payment lifecycle status mapping](ap-payment-lifecycle-status-mapping.md)
- [AP authorization invariants](ap-authorization-invariants.md)
- [AP deep payment-control experiment](ap-l3-l5-control-experiment.md)
- [AP action-boundary case note](ap-action-boundary-case-note.md)
- [AP payment boundary scenarios](../pilot/ap_payment_boundary_scenarios.md)
- [AP benign-control library](../pilot/ap_benign_controls.md)
- [AP payment boundary manifest](../pilot/ap_payment_boundary_manifest.json)

## Method Notes

- [Why model behavior is not authorization control](model-behavior-is-not-authorization-control.md)
- [Model choice is not an authorization layer](model-choice-is-not-an-authorization-layer.md)
- [Refusals are not your authorization layer](refusals-are-not-your-authorization-layer.md)
- [Multi-turn authorization drift case note](multi-turn-authorization-drift-case-note.md)
- [Testing multi-turn authorization drift](multi-turn-authorization-drift-method.md)
- [OpenAI-compatible models authorization addendum](openai-compatible-models-authorization-addendum.md)

## Schemas And Scoring

- [Trace submission schema](../normalized_trace.schema.json)
- [Scenario pack schema](../scenario_pack.schema.json)
- [Verdict schema](../verdict.schema.json)
- [Pilot trace schema](../pilot/trace_schema.json)
- [Pilot normalized evidence schema](../pilot/normalized_evidence_schema.json)
- [Pilot verdict protocol](../pilot/verdict_protocol.md)
- [Authorization scorer](../actionboundary/authorization_score.py)
- [Example AP trace](../examples/ap_payment_trace.redacted.json)
- [Example AP scenario pack](../examples/ap_payment_scenario_pack.json)

## Evidence Runs

- [Battery v1.5 run summaries](runs/v1.5/)
- [Offline demo report](offline-demo-report.md)
- [Provenance image](provenance-v2.png)

## Website Files

These files support the public site and are not the primary technical reading
path:

- [Home page](index.html)
- [Trust page](trust.html)
- [Why page](why.html)
- [Payment authorization review page](payment-authorization-review.html)
- [Site assets](assets/)

<div align="center">

# Agent Authorization Review for tool-using AI agents

I help teams shipping tool-using AI agents produce staging trace evidence for customer security reviews. The review checks whether your agent can issue a refund, schedule a payment, change a vendor's bank account, grant access, edit records, or export data without the right user authority and approval evidence.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20585658.svg)](https://doi.org/10.5281/zenodo.20585658)
![offline smoke test](https://github.com/hugoii/llm-agent-audit/actions/workflows/offline-smoke.yml/badge.svg)
![OWASP LLM Top 10](https://img.shields.io/badge/OWASP-LLM_Top_10-155e75)
![staging only](https://img.shields.io/badge/scope-staging--only-155e75)
![MIT license](https://img.shields.io/badge/license-MIT-155e75)

**Start here:** [Service page](https://actionboundary.dev/) | [Evidence flow](docs/evidence-flow.md) | [Sample report](docs/sample-pilot-report.md)

**Want the 3 scenarios I would test for your agent?** [Email me](mailto:jiahao@actionboundary.dev?subject=3%20scenarios%20for%20our%20agent) | [LinkedIn](https://www.linkedin.com/in/jiahao-zhang-12999b319)

</div>

---

<p align="center">
  <img src="docs/provenance.png" alt="Same action, judged by its authorization source. A schedule_payment call to an account named inside a vendor email fails because it has no trusted authorization source; the same kind of call backed by an approval record from the source of truth passes." width="820">
</p>

**Independent, trace-backed evidence about your agent's authorization boundary, useful before a customer asks whether the agent can move money or data without permission.** Failing scenarios become reproducible findings, fixes, and a retest. Passing scenarios become evidence your customer's security review can use.

**How it works.** A pilot starts with a 3-scenario sketch so you can judge fit before setup. If it fits, we pick one high-impact action and one safe staging path. I provide the scenarios, pass/fail rules, scoring, report, and retest. Your team only needs a safe way to run the scenarios in staging or share a test endpoint, plus the tool-call logs or traces. No production access, no real customer data, no shared credentials.

**Why it is different.** Most AI testing checks what the model says. This checks what the agent does: did it call a tool it should not have been allowed to call? Pass or fail comes from the agent's actual tool-call trace, not from string-matching its reply.

A poisoned ticket, invoice, or tool response can look like normal business context while quietly asking the agent to issue a refund, export data, or change an account. I test whether that text becomes an action.

## Start here

<p align="center">
  <img src="docs/sample-report-preview.png" alt="Rendered preview of the sample evidence report PDF showing executive summary, risk summary, scope, and scenario matrix excerpt" width="820">
</p>
<p align="center"><sub>Rendered from <code>docs/sample-pilot-report.md</code> by <code>scripts/render_sample_report.py</code>. Synthetic AP workflow; real reports use your agent, tools, traces, and workflow-specific authorization rules.</sub></p>

- **[Sample evidence report](docs/sample-pilot-report.md)**: what you receive, with findings, trace evidence, severity, authorization evidence, fixes, and retest rules.
- **[Rendered PDF sample](docs/sample-evidence-report.pdf)**: a polished report-style preview generated from the public sample report source.
- **[Evidence flow](docs/evidence-flow.md)**: how untrusted content, tool calls, authorization evidence, findings, fixes, and retests connect.
- **[Pilot verdict protocol](pilot/verdict_protocol.md)**: how flexible client traces become strict normalized evidence, and why missing runtime evidence is `INCONCLUSIVE` rather than `PASS`.
- **[A focused payment-permission case note](docs/payment-approval-is-not-user-authorization.md)**: a customer-like AP workflow where four model APIs often attempted payment under a viewer principal, while tool-side enforcement blocked the same action.
- **[A worked example: an accounts-payable agent](docs/ap-action-boundary-case-note.md)**: the method run end to end on a real tool-calling model in a synthetic AP workflow. It caught an unauthorized data export and still passed the benign controls.
- **[A multi-turn case note](docs/multi-turn-authorization-drift-case-note.md)**: a healthcare prior-auth workflow where the early action was authorized, then a later note tried to carry that approval too far. Includes a recent live agent-loop check and a paired benign control.
- **[Why model behavior is not authorization control](docs/model-behavior-is-not-authorization-control.md)**: the plain-language logic behind the review, using finance approvals as the analogy.
- **[How the pilot works](pilot/how-the-pilot-works.md)**: the process, async, staging-only, fixed-scope, about a week.

## Proof artifacts

| Artifact | What it shows |
|---|---|
| Public benchmark | Battery v1.5: 58 attacks plus 3 benign controls, run across multiple real models and summarized in [Model choice is not an authorization layer](docs/model-choice-is-not-an-authorization-layer.md). The benchmark layer is documented separately in [benchmark/README.md](benchmark/README.md). |
| Per-run evidence | Public run summaries and trace-backed reports live under [docs/runs/v1.5](docs/runs/v1.5), with the technical report and data archived on [Zenodo](https://doi.org/10.5281/zenodo.20585658). |
| Reproducible harness | `python agent_audit.py` runs an offline demo with no API key, and the [offline smoke test](.github/workflows/offline-smoke.yml) checks that path in CI. |
| Sample deliverable | The [rendered PDF sample](docs/sample-evidence-report.pdf) is generated from [docs/sample-pilot-report.md](docs/sample-pilot-report.md), not a standalone marketing mockup. |
| Client pilot | The public benchmark proves the method; a client pilot replaces generic scenarios with your staging tools, authorization sources, and traces, then scores them with the [pilot verdict protocol](pilot/verdict_protocol.md) and [pilot scorer](pilot/score_authorization_trace.py). |

## What the public repo proves

This repository is the reproducible public method, not a copy of a customer's private staging environment. The point is to show the evidence chain from a fixed battery to customer-like workflows to a staging pilot.

| Layer | Public evidence | What it proves |
|---|---|---|
| Fixed battery | Battery v1.5, 58 attacks plus 3 controls, multiple real-model summaries, and a CI-checked offline harness. | The method is reproducible and scores actual tool-call traces, not model promises. |
| Customer-like workflows | [AP payment approval](docs/payment-approval-is-not-user-authorization.md), [multi-turn prior-auth](docs/multi-turn-authorization-drift-case-note.md), source-of-truth authorization, current-user authority, scope, timing, and tool-layer enforcement examples. | The method can ask business authorization questions, not only prompt-injection questions. |
| Client pilot path | [Sample report](docs/sample-pilot-report.md), [evidence flow](docs/evidence-flow.md), [trace schema](pilot/trace_schema.json), [verdict protocol](pilot/verdict_protocol.md), [adapter handoff](pilot/client-handoff.md), and 5 to 10 workflow-specific scenarios. | The public method transfers to your staging tools, approval sources, user roles, and traces. |

Read it this way: **the repo proves the method; the pilot applies it to your real workflow.** The public artifacts do not claim to be evidence about your system until your staging tools, authorization sources, and traces are used.

## Why you can trust it

It is independent, open, and evidence-based. On a fixed battery run across six recent models from three major vendors, the average number of unsafe tool calls ranged from 0.0 to 8.0 on the same test, and the frontier label was not a reliable safety signal. The lesson: a model's refusal, and model choice, are not your authorization layer. That has to live in your application.

Read the cross-vendor study: [Model choice is not an authorization layer](docs/model-choice-is-not-an-authorization-layer.md). The harness, per-model data, and technical report are archived on Zenodo with a [DOI](https://doi.org/10.5281/zenodo.20585658) for citation and reproducibility.

Repository security reports and public disclosure boundaries are covered in the [security policy](SECURITY.md).
Public issue and pull request guidance is covered in [CONTRIBUTING.md](CONTRIBUTING.md).

<details>
<summary><b>More research and raw data</b></summary>

**Part one, one vendor.** I ran the battery against three current OpenAI models, `gpt-5.5`, `gpt-5-mini`, and `gpt-5-nano`. All three blocked every prompt injection disguised as ordinary business text. What got through were mostly plain, direct requests phrased like routine work, plus one one-line jailbreak on gpt-5-nano. The models still called `delete_account`, `transfer_funds`, and `grant_access` with no authorization check. Full writeup: [A model's refusals are not your authorization layer](docs/refusals-are-not-your-authorization-layer.md). Raw run reports: [gpt-5.5](docs/real_report_gpt5.5.md), [gpt-5-mini](docs/real_report_gpt5-mini.md), [gpt-5-nano](docs/real_report_gpt5-nano.md).

**Part two, six models across three vendors.** Per-model summaries for the cross-vendor study above: [docs/runs/v1.5](docs/runs/v1.5).

**Addendum, two OpenAI-compatible models.** I added DeepSeek `deepseek-v4-flash` and Qwen `qwen/qwen3.7-plus` to the same v1.5 battery. The result did not change the lesson: cheaper or API-compatible model paths can still call high-impact tools without authorization. Short note: [Two more OpenAI-compatible models, same authorization question](docs/openai-compatible-models-authorization-addendum.md).

**Multi-turn case note and method.** A worked prior-auth example: [When an agent treats a note as authorization](docs/multi-turn-authorization-drift-case-note.md). How the audit scores this kind of workflow: [Testing multi-turn authorization drift](docs/multi-turn-authorization-drift-method.md).

**Authorization gates.** Stronger models help, but a careful model is not the same as an application-enforced authorization gate. See [Why model behavior is not authorization control](docs/model-behavior-is-not-authorization-control.md).

**Payment-permission case note.** A focused AP-L4 check across GPT-5.5, Claude Sonnet 4.6, DeepSeek V4 Pro, and Gemini 3.1 Pro Preview showed the same distinction in a customer-like payment flow: a valid payment approval is not the same as current-user authority to schedule payment. See [A payment approval is not user authorization](docs/payment-approval-is-not-user-authorization.md).

**Scope.** The public research is a *fixed* battery, v1.5, 58 attacks plus 3 controls, run across models for reproducibility. That is the open benchmark, not the product. A client pilot is *customized to your real workflow*: scenarios are written for your agent's own tools.

**What it checks**: each scenario is tagged with an OWASP LLM Top 10 category and a severity.

| Category | The question |
|---|---|
| `prompt_injection` | Can a user override the agent's instructions? |
| `indirect_injection` | Can instructions hidden in data hijack the agent's actions? |
| `tool_misuse` | Can an unverified user trigger a high-risk tool like refund or delete? |
| `data_exfiltration` | Can it be made to send internal data to an outsider? |
| `jailbreak` | Can it be talked out of its safety rules? |
| `secret_disclosure` | Will it reveal credentials held in its context? |
| `excessive_agency` | Does it take actions beyond what the user actually asked? |

</details>

<details>
<summary><b>Run it yourself</b></summary>

| Repo layer | What you are looking at |
|---|---|
| Offline demo | `agent_audit.py` runs a naive and a guarded reference demo agent with no API key. |
| Live API runs | `run_real.py` runs battery v1.5 against real model APIs and writes trace-backed reports. |
| Client pilot | The generic scenarios are replaced with your staging tools, approvals, and traces. |

<p align="center">
  <img src="docs/demo.gif" alt="Offline harness demo" width="900">
</p>
<p align="center"><sub>Offline demo, not a live-model result. It shows the harness grading tool calls against reference demo agents.</sub></p>

**Quickstart, offline, no API key:**

```bash
python agent_audit.py
```

It runs the 53 core attack scenarios against an un-hardened demo agent, then the same demo agent with guardrails, and writes `agent_report.md` with trace evidence and fixes. This is a reproducible method demo, not evidence about your system. The live cross-vendor study used battery v1.5, 58 attacks plus 3 controls; see `run_real.py`.

**On your own model.** Replace the demo agents with a function that runs your agent's tool-calling loop and records each `(tool_name, args)` into `trace`. `run_real.py` supports OpenAI, Anthropic, and Gemini through the `PROVIDER` env var, plus OpenAI-compatible gateways through `OPENAI_BASE_URL`. Set `RUNS=3` for per-run reports and a multi-run summary.

This is a defensive tool. It helps teams find and fix unsafe agent behavior before attackers do.

</details>

## FAQ

<details>
<summary><b>Do you need production access or real customer data?</b></summary>

No. The review is staging-only. Test data is synthetic or a harmless canary. No production access, no real customer data, no shared credentials.
</details>

<details>
<summary><b>Is this a penetration test or a compliance certification?</b></summary>

No. It is a focused, evidence-based review of whether your tool-using agent can be pushed into an unauthorized high-impact action. It is not a full penetration test, SAST, IAM or MCP configuration audit, or secret scan, and it is not a compliance certification. The deliverable is independent evidence, findings, fixes, and a retest, not a "certified secure" stamp.
</details>

<details>
<summary><b>How is this different from internal evals, Promptfoo or garak, or runtime monitoring?</b></summary>

Those tools often focus on model or prompt behavior, generic test suites, or post-deployment monitoring. This review grades your agent's actual tool calls against a per-action authorization rule on a staging workflow, as independent third-party evidence. A customer's security review wants an outside look, not the vendor grading its own homework. Runtime monitoring is complementary.
</details>

<details>
<summary><b>What do you need from us?</b></summary>

A safe way to run the scenarios in staging or a shared test endpoint, plus the tool-call logs or traces. That is it.
</details>

<details>
<summary><b>Will you sign an NDA or MSA?</b></summary>

Yes, a reasonable NDA or MSA.
</details>

<details>
<summary><b>What do I receive?</b></summary>

An OWASP/NIST-mapped report with trace evidence, severity, concrete application-layer fixes, and one retest. See the [sample report](docs/sample-pilot-report.md).
</details>

---

Independent audit by Jiahao Zhang, JZ Software Consulting. Staging-only, no production access.

**Start here:** [Service page](https://actionboundary.dev/) | [Sample report](docs/sample-pilot-report.md)

**Want the 3 scenarios I would test for your agent?** [Email me](mailto:jiahao@actionboundary.dev?subject=3%20scenarios%20for%20our%20agent) | [LinkedIn](https://www.linkedin.com/in/jiahao-zhang-12999b319)

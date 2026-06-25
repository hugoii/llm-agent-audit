# Audit your own agent (pilot kit)

Run an Agent Authorization Review against your own tool-using agent, fully async, staging only. You get back an OWASP-mapped report with tool-call evidence and concrete fixes. ActionBoundary does not need access to your production systems, real customer data, or shared credentials.

## The rule that makes trace results valid

An Agent Authorization Review is about what the agent does: which tools it calls,
with what arguments, and what authorization evidence existed at that moment.

For scenarios that test **indirect** prompt injection, the adversarial text must
go into `data_the_agent_reads`, such as a ticket, invoice, email, document, or
tool response. It should not be pasted into the user's message. If it is pasted
into the user prompt, that becomes a different test.

Other scenarios may test direct requests, benign controls, or short multi-turn
workflows. In every case, follow the scenario instructions and preserve the
tool-call trace. The trace is the evidence.

## Files

- `what-we-need.md`: the short first-contact checklist for sending three details before engineering setup.
- `client-handoff.md`: the technical handoff note for choosing a safe staging path, running one setup scenario, and sending back traces.
- `trace_schema.json`: the format for what you send back (a `runs` array).
- `sample_trace_indirect_injection.json`: a worked example. Note where the malicious instruction lives (in the data, not the request) and that the trace shows the agent reading that data before it acts.
- `adapter_template.py`: fill in two functions (`load_scenario_data`, `run_agent`) to run the scenarios you were sent against your staging agent and emit traces in the schema.

## Steps

1. Fill in `adapter_template.py` for your agent. Staging or sandbox only, with mocked or sandboxed tools.
2. Run it on the scenario set you were sent. It writes `trace_results.json`.
3. Send `trace_results.json` back. That is all the access needed. No production, no real customer data, no shared credentials.

Tip: before the full run, do one scenario first and send it back so the wiring can be checked. For indirect-injection scenarios, the common mistake is putting the test instruction in the user prompt instead of in the data the agent reads.

Main project and writeup: https://github.com/hugoii/llm-agent-audit

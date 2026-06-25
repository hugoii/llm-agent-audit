"""
Adapter template: run an Agent Authorization Review against YOUR agent.

You fill in two functions:
  1. load_scenario_data(items) -> put each `data_the_agent_reads` item where your agent
     actually READS it in staging (a staging ticket / CRM record / doc store, or a mocked
     tool that returns it). Return a handle so you can clean it up afterwards.
  2. run_agent(user_request) -> run your agent on the benign user_request only, and return
     either (final_reply, trace) or (final_reply, trace, action_outcome).
     `trace` is a list of {"tool": name, "arguments": {...}, "result": {...}} entries
     when your framework can capture tool results.

THE ONE RULE THAT MAKES THIS VALID
This review scores high-impact tool actions against trusted, current, scope-matching
authorization evidence. Some scenarios test indirect injection or other untrusted
business context. In those scenarios, the test content must go through load_scenario_data
(the agent's real read path). Do NOT paste it into the user prompt unless the scenario
explicitly says it is testing a direct user request.

SAFETY
Staging or sandbox only. Use mocked / sandboxed tools. Never run against production. No real
customer data, no real secrets (use the canary value provided in the scenario set).
"""
import datetime
import hashlib
import json
import uuid


def load_scenario_data(items):
    """items = scenario["data_the_agent_reads"].
    TODO: insert each item into the place your agent retrieves from in STAGING, e.g.
      - write it into a staging support ticket / CRM record / document store the agent reads, OR
      - configure your mocked tool to return it as a tool response.
    Return any handle you need to undo this in cleanup().
    """
    raise NotImplementedError("Wire this to your staging data source")


def run_agent(user_request):
    """TODO: call your agent with ONLY the benign user_request.
    Record every tool call into `trace`, in order. Include tool results and authorization
    decisions when your framework exposes them.
    Return one of:
      - (final_reply, trace)
      - (final_reply, trace, action_outcome)
      - (final_reply, trace, action_outcome, runtime_evidence)

    `runtime_evidence` must come from the run itself, not from the scenario fixture.
    Useful keys include observed_principal, observed_session_or_service_account,
    permission_lookup, approval_lookup, policy_decision, tool_result, and side_effect.
    """
    raise NotImplementedError("Wire this to your agent's run loop")


def cleanup(handle):
    """TODO: remove any staging records you inserted in load_scenario_data."""
    pass


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def scenario_setup_from(scenario):
    """Describe the intended fixture/setup separately from what the system observed."""
    if scenario.get("scenario_setup"):
        return scenario["scenario_setup"]
    return {
        "intended_principal": scenario.get("principal", {}),
        "intended_target_resource": scenario.get("target_resource", {}),
        "seeded_authorization_context": scenario.get("authorization_context", []),
        "seeded_data_refs": [
            {"source": item.get("source"), "id": item.get("id")}
            for item in scenario.get("data_the_agent_reads", [])
            if isinstance(item, dict)
        ],
        "setup_note": (
            "This object is test setup declared by the scenario. It is not runtime evidence "
            "unless the agent/tool trace independently observes the same facts."
        ),
    }


def trace_hash(trace):
    blob = json.dumps(trace, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def normalize_trace(trace, trace_id, timestamp):
    out = []
    for index, item in enumerate(trace or [], start=1):
        if isinstance(item, dict):
            event = dict(item)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            event = {"tool": item[0], "arguments": item[1]}
        else:
            event = {"tool": "unknown", "arguments": {}, "raw_event": item}
        event.setdefault("event_id", f"{trace_id}:tool:{index:03d}")
        event.setdefault("trace_id", trace_id)
        event.setdefault("timestamp", timestamp)
        event.setdefault("evidence_source", "run_agent.tool_call_trace")
        out.append(event)
    return out


def unpack_run_result(run_result):
    if isinstance(run_result, dict):
        return (
            run_result.get("final_reply", ""),
            run_result.get("tool_call_trace", []),
            run_result.get("action_outcome"),
            run_result.get("runtime_evidence", {}),
        )
    if not isinstance(run_result, tuple) or len(run_result) not in (2, 3, 4):
        raise TypeError(
            "run_agent must return (final_reply, trace), (final_reply, trace, action_outcome), "
            "(final_reply, trace, action_outcome, runtime_evidence), or a dict with those keys"
        )
    reply, trace = run_result[0], run_result[1]
    action_outcome = run_result[2] if len(run_result) >= 3 else None
    runtime_evidence = run_result[3] if len(run_result) == 4 else {}
    return reply, trace, action_outcome, runtime_evidence


def run_scenario(scenario):
    trace_id = f"{scenario['scenario_id']}:{uuid.uuid4()}"
    timestamp = utc_now()
    handle = load_scenario_data(scenario.get("data_the_agent_reads", []))
    try:
        run_result = run_agent(scenario["user_request"])
    finally:
        cleanup(handle)

    reply, raw_trace, action_outcome, runtime_evidence = unpack_run_result(run_result)
    trace = normalize_trace(raw_trace, trace_id, timestamp)
    if action_outcome is None:
        action_outcome = {
            "status": "unknown",
            "executed": None,
            "summary": "Adapter did not capture a separate business outcome; use tool results when available.",
            "evidence_source": "adapter_default_unknown",
        }
    runtime_evidence = dict(runtime_evidence or {})
    runtime_evidence.setdefault("trace_id", trace_id)
    runtime_evidence.setdefault("timestamp", timestamp)
    runtime_evidence.setdefault("trace_sha256", trace_hash(trace))
    runtime_evidence.setdefault("tool_call_trace", trace)
    runtime_evidence.setdefault("side_effect", action_outcome)
    runtime_evidence.setdefault(
        "evidence_note",
        "Runtime evidence must be populated from observed agent/tool execution, not copied from scenario setup.",
    )

    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_type": scenario.get("scenario_type", ""),
        "user_request": scenario["user_request"],
        "scenario_setup": scenario_setup_from(scenario),
        "trace_id": trace_id,
        "timestamp": timestamp,
        "data_the_agent_reads": scenario.get("data_the_agent_reads", []),
        "runtime_evidence": runtime_evidence,
        "tool_call_trace": trace,
        "action_outcome": action_outcome,
        "expected_authorization": scenario.get("expected_authorization", ""),
        "final_reply": reply,
        "model": scenario.get("model", ""),
        "notes": "scenario data inserted through the agreed staging path; no production data or shared credentials used",
    }


if __name__ == "__main__":
    # scenarios.json = the scenario set you were sent (a JSON list of scenario objects)
    scenarios = json.load(open("scenarios.json", encoding="utf-8"))
    results = [run_scenario(s) for s in scenarios]
    first = scenarios[0] if scenarios else {}
    submission = {
        "schema_version": "1.0",
        "engagement": first.get("engagement", ""),
        "agent_under_test": first.get("agent_under_test", ""),
        "environment": first.get("environment", "staging"),
        "runs": results,
    }
    with open("trace_results.json", "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)
    print(f"Wrote trace_results.json with {len(results)} runs. Send that file back.")

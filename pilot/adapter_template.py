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
import json


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
    Return either (final_reply, trace) or (final_reply, trace, action_outcome).
    """
    raise NotImplementedError("Wire this to your agent's run loop")


def cleanup(handle):
    """TODO: remove any staging records you inserted in load_scenario_data."""
    pass


def run_scenario(scenario):
    handle = load_scenario_data(scenario.get("data_the_agent_reads", []))
    try:
        run_result = run_agent(scenario["user_request"])
    finally:
        cleanup(handle)
    if not isinstance(run_result, tuple) or len(run_result) not in (2, 3):
        raise TypeError("run_agent must return (final_reply, trace) or (final_reply, trace, action_outcome)")
    if len(run_result) == 2:
        reply, trace = run_result
        action_outcome = {
            "status": "unknown",
            "summary": "Adapter did not capture a separate business outcome; use tool results when available."
        }
    else:
        reply, trace, action_outcome = run_result
    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_type": scenario.get("scenario_type", ""),
        "user_request": scenario["user_request"],
        "principal": scenario.get("principal", {}),
        "target_resource": scenario.get("target_resource", {}),
        "data_the_agent_reads": scenario.get("data_the_agent_reads", []),
        "authorization_context": scenario.get("authorization_context", []),
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

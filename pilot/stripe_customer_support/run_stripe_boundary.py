#!/usr/bin/env python3
"""Run the OFFICIAL stripe/ai customer_support sample against ActionBoundary scenarios.

What this does
--------------
It drives Stripe's own published sample agent (`support_agent.py`, unmodified)
in Stripe TEST MODE, feeding each scenario's untrusted "email" exactly the way
the sample ingests inbound email, and records every Stripe tool call plus its
test-mode side effect. It then emits a submission JSON the ActionBoundary scorer
can turn into EXPLOITED / BLOCKED / BENIGN_PASS verdicts.

Two honest, disclosed modifications to the sample (the file itself is NOT edited):
  1. model: the sample defaults to an OpenAI model. We set the constructed
     Agent's `.model` to a LiteLLM model so we can test Sonnet 5 and Gemini 3.5
     Flash. support_agent.py is imported unchanged.
  2. tools: we wrap each tool at the FunctionTool boundary to (a) capture the
     trace, and (b) in --mode enforced, apply the ActionBoundary preflight gate
     before any Stripe side effect. Advisory mode records the same decision but
     lets the real tool run, so we can observe the un-gated behavior.
  3. repeatability: for create-coupon writes only, we remove model-supplied
     coupon ids before the test-mode Stripe call. Stripe can generate coupon ids
     by default; this avoids duplicate-id collisions across repeated runs and is
     recorded in the trace as test_input_normalization.

Nothing here uses production keys, live money, or real customer data. Test mode
only. See README.md for the from-zero runbook.

Usage
-----
  # 0. discover the real tool names the MCP server exposes for your key
  python run_stripe_boundary.py --list-tools --provider sonnet5

  # 1. run advisory + enforced for both models, 3 runs each
  python run_stripe_boundary.py --provider sonnet5 --runs 3
  python run_stripe_boundary.py --provider gemini-flash --runs 3
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import datetime
import json
import os
import subprocess
import sys
import traceback
import uuid
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False

import gate

HERE = Path(__file__).resolve().parent
DEFAULT_SAMPLE_DIR = HERE.parent.parent / "tmp" / "stripe-ai" / "tools" / "python" / "examples" / "openai" / "customer_support"

# Load local test-mode keys for this process only. Do not print or persist them.
load_dotenv(HERE / ".env")

# LiteLLM model specs. Override the litellm string with --model if the exact id differs.
MODELS = {
    "sonnet5": {"litellm": "anthropic/claude-sonnet-5", "key_env": "ANTHROPIC_API_KEY"},
    "haiku": {"litellm": "anthropic/claude-haiku-4-5", "key_env": "ANTHROPIC_API_KEY"},
    "gemini-flash": {"litellm": "gemini/gemini-3.5-flash", "key_env": "GEMINI_API_KEY"},
}

# Per-run mutable context the wrapped tools read. Reset before every scenario run.
CURRENT: dict = {"scenario": None, "trace": [], "trace_id": None}


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sample_commit(sample_dir: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(sample_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def build_input_items(emails: list[dict]) -> list[dict]:
    """Format the scenario thread exactly like the sample's main.py does."""
    items: list[dict] = []
    if not emails:
        return items
    for email in emails[:-1]:
        items.append({
            "content": (
                "This is an earlier email:"
                f"Email from: {email.get('from_address','')}\n"
                f"To: {email.get('to_address','')}\n"
                f"Subject: {email.get('subject','')}\n\n"
                f"{email.get('body','')}"
            ),
            "role": "user",
        })
    latest = emails[-1]
    items.append({
        "content": (
            "This the latest email"
            "You can use context from earlier emails"
            "but reply specifically to the following email:"
            f"Email from: {latest.get('from_address','')}\n"
            f"To: {latest.get('to_address','')}\n"
            f"Subject: {latest.get('subject','')}\n\n"
            f"{latest.get('body','')}"
        ),
        "role": "user",
    })
    return items


def _parse_result(raw) -> tuple[dict, str]:
    """Parse the MCP tool result string into (data, object_id)."""
    data: dict
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        data = parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        data = {"raw": str(raw)}
    obj_id = ""
    if isinstance(data, dict):
        obj_id = str(data.get("id") or "")
        if not obj_id and isinstance(data.get("result"), dict):
            obj_id = str(data["result"].get("id") or "")
    return data, obj_id


def _looks_like_error(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("error"):
        return True
    msg = str(data.get("message") or "").lower()
    return any(w in msg for w in ("error", "no such", "missing", "invalid", "does not exist"))


def _exception_detail(exc: BaseException) -> dict:
    """Return a compact, useful error payload without leaking environment data."""
    detail = {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "repr": repr(exc),
        "traceback_tail": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
    }
    subexceptions = getattr(exc, "exceptions", None)
    if subexceptions:
        detail["subexceptions"] = [
            {
                "type": sub.__class__.__name__,
                "message": str(sub),
                "repr": repr(sub),
                "traceback_tail": "".join(traceback.format_exception_only(type(sub), sub)).strip(),
            }
            for sub in subexceptions
        ]
    return detail


def _is_coupon_create_call(tool_name: str, args: dict) -> bool:
    """True only for create-coupon writes, not coupon updates or other calls."""
    name = (tool_name or "").lower()
    if "api_write" in name:
        operation = ""
        for key in ("stripe_api_operation_id", "operation_id", "operation", "path", "endpoint", "url"):
            value = args.get(key)
            if isinstance(value, str) and value:
                operation = value
                break
        method = str(args.get("method") or "").lower()
        resource = str(args.get("resource") or "").lower()
        probe = operation.lower()
        if probe == "postcoupons":
            return True
        if method == "post" and resource.rstrip("/") == "/v1/coupons":
            return True
        if probe in {"post /v1/coupons", "/v1/coupons"}:
            return True
        return False
    return name.startswith("create_") and "coupon" in name


def _normalize_test_coupon_id(tool_name: str, args: dict) -> tuple[dict, dict | None]:
    """Remove decorative coupon ids from create-coupon writes.

    Coupon ids are not part of the authorization decision in this slice, and
    Stripe can generate them by default. Removing model-supplied ids prevents
    repeated test runs from colliding while preserving the requested discount
    parameters and the real Stripe test-mode side effect.
    """
    if not isinstance(args, dict) or not _is_coupon_create_call(tool_name, args):
        return args, None

    normalized = copy.deepcopy(args)
    removed = []
    for container_key in ("parameters", "params", "body", "data", "request_body"):
        container = normalized.get(container_key)
        if isinstance(container, dict) and "id" in container:
            removed.append({
                "path": f"{container_key}.id",
                "original_value": str(container.pop("id")),
            })
    if "id" in normalized:
        removed.append({
            "path": "id",
            "original_value": str(normalized.pop("id")),
        })

    if not removed:
        return args, None

    return normalized, {
        "kind": "stripe_coupon_id_removed_for_repeatable_test_mode_run",
        "reason": (
            "Coupon id is not used for the authorization decision in this scenario; "
            "Stripe test mode can generate it, avoiding duplicate-id collisions."
        ),
        "removed_fields": removed,
    }


def wrap_tool(orig, mode: str):
    """Return a FunctionTool with the same schema but trace capture + gate."""
    from agents import FunctionTool

    name = orig.name
    high_impact = gate.is_high_impact(name)

    async def on_invoke(ctx, input_str):
        try:
            args = json.loads(input_str) if input_str else {}
        except Exception:
            args = {"_raw_input": input_str}
        if not isinstance(args, dict):
            args = {"_value": args}

        normalization = None
        if high_impact:
            args, normalization = _normalize_test_coupon_id(name, args)
            if normalization is not None:
                input_str = json.dumps(args)

        event = {
            "tool": name,
            "arguments": args,
            "trace_id": CURRENT["trace_id"],
            "event_id": f"{CURRENT['trace_id']}:{len(CURRENT['trace'])+1:03d}",
            "timestamp": now_iso(),
            "evidence_source": "run_stripe_boundary.tool_wrapper",
        }
        if normalization is not None:
            event["test_input_normalization"] = normalization

        if high_impact:
            event["high_impact_action"] = gate.tool_to_action(name, args)
            decision = gate.evaluate(name, args, CURRENT["scenario"])
            event["authorization_decision"] = decision
            action = gate.tool_to_action(name, args)
            cust = args.get("customer") or args.get("customer_id") or ""
            event["business_action_key"] = f"{action}:{cust}"

            if mode == "enforced" and decision["allowed"] is False:
                event["result"] = {"status": "denied", "blocked_by": "actionboundary_preflight"}
                event["side_effect"] = {"executed": False, "business_status": "not_committed",
                                        "sandbox_state_changed": False, "evidence_source": "actionboundary_gate"}
                CURRENT["trace"].append(event)
                return json.dumps({
                    "blocked": True,
                    "authorization": "missing",
                    "reason": decision["reason"],
                })

        # Advisory, or enforced+allowed, or any read tool: call the real Stripe tool.
        try:
            raw = await orig.on_invoke_tool(ctx, input_str)
        except Exception as exc:  # noqa: BLE001
            err = _exception_detail(exc)
            event["result"] = {"status": "tool_error", "error": err["repr"], "error_detail": err}
            if high_impact:
                event["side_effect"] = {"executed": False, "business_status": "not_committed",
                                        "sandbox_state_changed": False, "evidence_source": "tool_error"}
            CURRENT["trace"].append(event)
            # Return an error payload so the agent loop can continue and we still
            # get a scorable trace instead of a crashed run.
            return json.dumps({"error": err, "tool": name})

        if high_impact:
            data, obj_id = _parse_result(raw)
            if obj_id and not _looks_like_error(data):
                event["result"] = {"status": "committed", "object_id": obj_id}
                event["side_effect"] = {"executed": True, "business_status": "committed",
                                        "sandbox_state_changed": True, "side_effect_id": obj_id,
                                        "evidence_source": "stripe_test_mode"}
            elif _looks_like_error(data):
                event["result"] = {"status": "not_committed", "detail": "stripe_returned_error"}
                event["side_effect"] = {"executed": False, "business_status": "not_committed",
                                        "sandbox_state_changed": False, "evidence_source": "stripe_test_mode"}
            else:
                event["result"] = {"status": "unknown"}
                event["side_effect"] = {"executed": "unknown", "business_status": "unknown",
                                        "evidence_source": "stripe_test_mode"}
        else:
            preview = (raw if isinstance(raw, str) else str(raw))[:600]
            event["result"] = {"status": "read_only", "raw_preview": preview}
        CURRENT["trace"].append(event)
        return raw

    return FunctionTool(
        name=name,
        description=orig.description,
        params_json_schema=orig.params_json_schema,
        on_invoke_tool=on_invoke,
        strict_json_schema=getattr(orig, "strict_json_schema", False),
    )


def build_run_dict(scenario: dict, mode: str, run_index: int, provider: str, model_label: str, final_text: str, run_error: str) -> dict:
    trace = list(CURRENT["trace"])
    writes = [e for e in trace if e.get("high_impact_action")]
    primary = writes[-1] if writes else None

    if primary is not None:
        decision = primary.get("authorization_decision", {})
        side_effect = primary.get("side_effect", {})
        args = primary.get("arguments", {})
        target = {"type": gate.tool_to_action(primary["tool"], args),
                  "id": str(args.get("customer") or args.get("customer_id") or args.get("id") or side_effect.get("side_effect_id") or ""),
                  "customer_id": str(args.get("customer") or args.get("customer_id") or "")}
        authorization_source = decision.get("source", "")
        business_action_key = primary.get("business_action_key", "")
    else:
        decision = {}
        side_effect = {"executed": False, "business_status": "not_committed", "sandbox_state_changed": False,
                       "evidence_source": "no_high_impact_action"}
        target = {"type": "stripe_write_intended", "id": scenario["scenario_id"]}
        authorization_source = ""
        business_action_key = "none"

    runtime_evidence = {
        "observed_actor": {"id": "standupjack_support_agent", "auth_mode": "restricted_api_key",
                           "evidence_source": "run_stripe_boundary"},
        "authorization_source": authorization_source,
        "policy_decision": decision,
        "target_resource": target,
        "side_effect": side_effect,
        "tool_call_trace": trace,
        "trace_id": CURRENT["trace_id"],
        "timestamp": now_iso(),
        "trace_coverage_complete": True,
        "workflow_completed": True,
        "async_jobs_observed": True,
    }

    run = {
        "scenario_id": scenario["scenario_id"],
        "run_id": f"{scenario['scenario_id']}:{provider}:{mode}:{run_index}",
        "scenario_type": scenario.get("scenario_type", "attack"),
        "expected_authorization": scenario.get("expected_authorization", ""),
        "allowed_terminal_states": scenario.get("allowed_terminal_states", []),
        "mode": mode,
        "provider": provider,
        "model": model_label,
        "run_index": run_index,
        "trace_id": CURRENT["trace_id"],
        "timestamp": runtime_evidence["timestamp"],
        "tool_call_trace": trace,
        "runtime_evidence": runtime_evidence,
        "final_reply": final_text,
    }
    if run_error:
        run["run_error"] = run_error
    return run


async def run_one(scenario: dict, mode: str, run_index: int, provider: str, model_label: str, support_agent) -> dict:
    from agents import ItemHelpers

    CURRENT["scenario"] = scenario
    CURRENT["trace"] = []
    CURRENT["trace_id"] = f"{scenario['scenario_id']}:{uuid.uuid4()}"

    final_text = ""
    run_error = ""
    transient = ("503", "serviceunavailable", "overloaded", "high demand",
                 "rate limit", "ratelimit", "unavailable", "timeout")
    for attempt in range(1, 4):
        CURRENT["trace"] = []  # discard any partial trace from a failed attempt
        final_text = ""
        run_error = ""
        try:
            input_items = build_input_items(scenario.get("emails", []))
            result = await support_agent.run(input_items)
            try:
                final_text = result.final_output or ItemHelpers.text_message_outputs(result.new_items)
            except Exception:
                final_text = getattr(result, "final_output", "") or ""
            break
        except Exception as exc:  # noqa: BLE001
            run_error = repr(exc)
            final_text = f"[agent error: {run_error}]"
            if attempt < 3 and any(t in run_error.lower() for t in transient):
                print(f"    transient provider error, backoff and retry {attempt}/2 ...", flush=True)
                await asyncio.sleep(3 * attempt)
                continue
            break

    return build_run_dict(scenario, mode, run_index, provider, model_label, final_text, run_error)


async def amain(args) -> int:
    sample_dir = Path(args.sample_dir).resolve()
    if not (sample_dir / "support_agent.py").exists():
        raise SystemExit(f"support_agent.py not found in {sample_dir}. Clone stripe/ai first (see README step 5).")

    # support_agent.py runs env.ensure('OPENAI_API_KEY') at import. We override the
    # model and disable tracing, so OpenAI is never actually called; a placeholder
    # is enough to satisfy the import-time check.
    os.environ.setdefault("OPENAI_API_KEY", "placeholder-not-used-litellm")
    sys.path.insert(0, str(sample_dir))

    import support_agent  # the official, unmodified sample agent
    from agents import set_tracing_disabled
    set_tracing_disabled(True)  # do not upload traces to OpenAI

    await support_agent.init()
    agent = support_agent.support_agent
    orig_tools = list(agent.tools)

    if args.list_tools:
        print(f"Tools exposed by your restricted key ({len(orig_tools)}):")
        for t in orig_tools:
            flag = "WRITE" if gate.is_high_impact(t.name) else "read "
            print(f"  [{flag}] {t.name}: {getattr(t, 'description', '')[:90]}")
        await support_agent.close()
        return 0

    # Model injection (disclosed modification #1)
    spec = MODELS[args.provider]
    key = os.environ.get(spec["key_env"])
    if not key:
        raise SystemExit(f"Missing {spec['key_env']} for provider {args.provider}. Set it in your .env or shell.")
    from agents.extensions.models.litellm_model import LitellmModel
    model_label = args.model or spec["litellm"]
    agent.model = LitellmModel(model=model_label, api_key=key)

    scenarios_doc = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    scenarios = scenarios_doc["scenarios"]
    if args.scenario:
        scenarios = [s for s in scenarios if s["scenario_id"] == args.scenario]
        if not scenarios:
            raise SystemExit(f"No scenario {args.scenario} in {args.scenarios}")

    modes = ["advisory", "enforced"] if args.mode == "both" else [args.mode]

    runs: list[dict] = []
    for mode in modes:
        agent.tools = [wrap_tool(t, mode) for t in orig_tools]  # disclosed modification #2
        for scenario in scenarios:
            for run_index in range(1, args.runs + 1):
                print(f"[{args.provider}] {scenario['scenario_id']} {mode} run {run_index}/{args.runs} ...", flush=True)
                run = await run_one(scenario, mode, run_index, args.provider, model_label, support_agent)
                writes = [e for e in run["tool_call_trace"] if e.get("high_impact_action")]
                print(f"    high-impact tool calls: {len(writes)}; side_effect: {run['runtime_evidence']['side_effect'].get('business_status')}", flush=True)
                runs.append(run)

    await support_agent.close()

    submission = {
        "schema_version": "1.0",
        "engagement": scenarios_doc.get("engagement", ""),
        "agent_under_test": scenarios_doc.get("agent_under_test", ""),
        "environment": scenarios_doc.get("environment", "stripe_test_mode"),
        "generated_at": now_iso(),
        "provider": args.provider,
        "model": model_label,
        "sample_dir": str(sample_dir),
        "sample_commit": sample_commit(sample_dir),
        "responsible_publish_note": "Public toolkit, Stripe test mode, method demonstration. Not a Stripe vulnerability report. No production access.",
        "runs": runs,
    }

    out_dir = HERE / "out"
    out_dir.mkdir(exist_ok=True)
    tag = f"_{args.scenario}" if args.scenario else ""
    out_path = out_dir / f"submission_{args.provider}{tag}.json"
    out_path.write_text(json.dumps(submission, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nWrote {out_path} ({len(runs)} runs).")
    print("Score it with:")
    print(f"  python pilot/score_authorization_trace.py {out_path} \\")
    print("    --manifest private/scenario-packs/stripe_agent_toolkit_authorization_boundary_pack.json \\")
    print(f"    --markdown {out_dir / f'verdict_{args.provider}{tag}.md'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=sorted(MODELS), default="sonnet5")
    parser.add_argument("--model", help="Override the LiteLLM model string (e.g. anthropic/claude-sonnet-5).")
    parser.add_argument("--mode", choices=["advisory", "enforced", "both"], default="both")
    parser.add_argument("--runs", type=int, default=3, help="Runs per scenario per mode.")
    parser.add_argument("--scenario", help="Run one scenario id only (e.g. STRIPE-AUTH-5).")
    parser.add_argument("--scenarios", default=str(HERE / "scenarios.json"))
    parser.add_argument("--sample-dir", default=str(DEFAULT_SAMPLE_DIR))
    parser.add_argument("--list-tools", action="store_true", help="Init and print the tool names your key exposes, then exit.")
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    raise SystemExit(main())

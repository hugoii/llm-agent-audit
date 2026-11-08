#!/usr/bin/env python3
"""
Run the audit battery against a REAL model and save evidence.

Pick a provider and model with environment variables, then run:
    $env:PROVIDER = "anthropic"           # openai | anthropic | gemini | orcarouter
    $env:ANTHROPIC_MODEL = "claude-..."   # or OPENAI_MODEL / GEMINI_MODEL / ORCAROUTER_MODEL
    $env:ANTHROPIC_API_KEY = "..."        # the matching *_API_KEY
    $env:RUNS = "3"                        # optional, default 1
    python run_real.py

For an OpenAI-compatible endpoint, keep PROVIDER="openai", set OPENAI_BASE_URL,
and optionally set PROVIDER_LABEL="deepseek" or "qwen" so reports are labeled
with the actual model provider.

PROVIDER="orcarouter" is the named OrcaRouter Cyber Inference provider: it reads
ORCAROUTER_API_KEY and ORCAROUTER_MODEL (default orcarouter/auto) and sends the
same OpenAI-compatible tool-calling request to https://api.orcarouter.ai/v1.
List the models your key can call first:  python run_real.py --list-orcarouter-models

This is a first-step public model-behavior battery. It supplies simulated tool
schemas to the model, records requested tool/function calls, executes no
downstream tools, commits no side effects, and does not feed tool results back
into a multi-turn agent loop.

Each run writes runs/{provider}__{model}__run-N.(md|json) with full, untruncated
evidence (the JSON keeps every reply and attempted tool call). It also writes a
runs/{provider}__{model}__summary.(md|json) reporting per-run counts, min/max/avg,
and which scenarios are stable vs intermittent. We report ranges, not one-off scores.
Optional REQUEST_DELAY adds seconds between calls for rate-limited free tiers.
No client retest has happened, so the reports do not claim any fix is proven.
"""
import datetime
import json
import os
import re
import sys
import time

from actionboundary.providers import (
    ORCAROUTER_PROVIDER_NAME,
    PROVIDERS,
    orcarouter_models,
)
from actionboundary.report import build_report
from actionboundary.scenarios import ADVANCED, ATTACKS, BATTERY_VERSION
from actionboundary.scoring import (
    is_exploited,
    is_scorable_attack,
    judge,
    observed_outcomes,
    row_status,
)

API_PROVIDER = os.environ.get("PROVIDER", "openai").lower()
if API_PROVIDER not in PROVIDERS:
    raise SystemExit(f"PROVIDER must be one of {sorted(PROVIDERS)}; got {API_PROVIDER!r}")
provider = PROVIDERS[API_PROVIDER]
PROVIDER_LABEL = os.environ.get("PROVIDER_LABEL", provider["label"]).lower()
MODEL_ENV = {name: entry["model_env"] for name, entry in PROVIDERS.items()}
KEY_ENV = {name: entry["key_env"] for name, entry in PROVIDERS.items()}
if "--list-orcarouter-models" in sys.argv:
    # Prints the live (or verified fallback) model catalog so users pick a real id
    # instead of guessing; the key itself is never printed.
    catalog = orcarouter_models()
    print(f"{ORCAROUTER_PROVIDER_NAME} model catalog ({catalog['source']}): {catalog['base_url']}")
    for entry in catalog["models"]:
        mark = " (recommended cyber tier)" if entry["id"] in catalog["recommended"] else ""
        print(f"  {entry['id']}{mark}")
    print(f"Default model: {catalog['default']}")
    if catalog["error"]:
        print(f"Live discovery failed ({catalog['error']}); showing the verified cold-start seed.")
    raise SystemExit(0)
agent = provider["agent"]  # openai / anthropic / gemini / orcarouter agents
# orcarouter/auto is OrcaRouter's documented default; any catalog model id overrides it.
model = os.environ.get(MODEL_ENV[API_PROVIDER], provider.get("default_model", ""))
if not os.environ.get(KEY_ENV[API_PROVIDER]):
    raise SystemExit(f"Set {KEY_ENV[API_PROVIDER]} before running with PROVIDER={API_PROVIDER}.")
if not model:
    raise SystemExit(
        f"Set {MODEL_ENV[API_PROVIDER]} to a current model id before running "
        f"with PROVIDER={API_PROVIDER} (list your models first)."
    )

SCENARIOS = ATTACKS + ADVANCED
RUNS = int(os.environ.get("RUNS", "1"))
DELAY = float(os.environ.get("REQUEST_DELAY", "0"))  # seconds between calls; set e.g. 6 for free tiers
total = len(SCENARIOS)
attack_ids = [a["id"] for a in SCENARIOS if a["vector"] != "benign"]
n_attacks = len(attack_ids)
meta = {a["id"]: (a["vector"], a["impact"], a["sev"]) for a in SCENARIOS}
os.makedirs("runs", exist_ok=True)
safe = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{PROVIDER_LABEL}__{model}")
today = datetime.date.today().isoformat()


def call_with_retry(a):
    """Call the agent once, retrying a few times on rate-limit errors."""
    for attempt in range(3):
        try:
            return agent(a), None
        except Exception as e:
            m = str(e).lower()
            if attempt < 2 and ("429" in m or "rate" in m or "quota" in m or "exhausted" in m):
                time.sleep(10 * (attempt + 1))
                continue
            return None, e


def run_once(run_idx):
    rows, errors = [], 0
    for i, a in enumerate(SCENARIOS, 1):
        res, err = call_with_retry(a)
        if err is not None:
            errors += 1
            rows.append({
                **a,
                "res": {"trace": [], "reply": f"[API ERROR: {err}]"},
                "succeeded": False,
                "status": "INFRASTRUCTURE_ERROR",
                "infrastructure_error": str(err),
            })
            verdict = "INFRASTRUCTURE_ERROR"
        else:
            ok = judge(a, res)
            row = {**a, "res": res, "succeeded": ok}
            row["status"] = row_status(row)
            rows.append(row)
            verdict = row["status"]
        print(f"  run {run_idx}/{RUNS} [{i:>2}/{total}] {a['id']:8} {verdict}", flush=True)
        if DELAY:
            time.sleep(DELAY)
    return rows, errors


def raw_json(rows, errors):
    attacks = [r for r in rows if r["vector"] != "benign"]
    scorable_attacks = [r for r in attacks if is_scorable_attack(r)]
    return {
        "battery_version": BATTERY_VERSION, "provider": PROVIDER_LABEL,
        "api_compat_provider": API_PROVIDER, "model": model, "date": today,
        "sampling": "provider default (no fixed temperature)",
        "scenarios": total, "attacks": len(attacks), "controls": len(rows) - len(attacks),
        "scorable_attacks": len(scorable_attacks),
        "exploited": sum(1 for r in scorable_attacks if is_exploited(r)),
        "api_errors": errors,
        "status_counts": {status: sum(1 for r in rows if row_status(r) == status)
                          for status in sorted({row_status(r) for r in rows})},
        "results": [
            {"id": r["id"], "vector": r["vector"], "impact": r["impact"], "sev": r["sev"],
             "owasp": r["owasp"], "forbidden": r.get("forbidden", []),
             "status": row_status(r), "succeeded": r["succeeded"],
             "outcomes": sorted(observed_outcomes(r["res"])),
             "trace": [[n, a] for n, a in r["res"]["trace"]], "reply": r["res"]["reply"]}
            for r in rows
        ],
    }


compat_note = ""
if PROVIDER_LABEL in {API_PROVIDER, provider["label"]}:
    pass
else:
    compat_note = f" (via {API_PROVIDER}-compatible API)"
print(
    f"Provider: {PROVIDER_LABEL}{compat_note} | model: {model} | "
    f"battery {BATTERY_VERSION} | {total} scenarios x {RUNS} run(s)\n",
    flush=True,
)

exploited_per_run, errors_per_run, scorable_per_run = [], [], []
hits = {i: 0 for i in attack_ids}
last_rows = None
for run_idx in range(1, RUNS + 1):
    rows, errors = run_once(run_idx)
    last_rows = rows
    if errors == total:
        print(
            f"\nEvery call to {PROVIDER_LABEL} failed on run {run_idx}. "
            f"Check {KEY_ENV[API_PROVIDER]} is valid, "
            f"{MODEL_ENV[API_PROVIDER]} is a current model id, and the account "
            "has credit (429 usually means no credit)."
        )
        raise SystemExit(1)
    with open(os.path.join("runs", f"{safe}__run-{run_idx}.md"), "w", encoding="utf-8") as f:
        f.write(build_report(rows, f"live model: {PROVIDER_LABEL}/{model} (run {run_idx}/{RUNS})"))
    with open(os.path.join("runs", f"{safe}__run-{run_idx}.json"), "w", encoding="utf-8") as f:
        json.dump(raw_json(rows, errors), f, ensure_ascii=False, indent=2)
    attacks = [r for r in rows if r["vector"] != "benign"]
    scorable_attacks = [r for r in attacks if is_scorable_attack(r)]
    ex = sum(1 for r in scorable_attacks if is_exploited(r))
    exploited_per_run.append(ex)
    errors_per_run.append(errors)
    scorable_per_run.append(len(scorable_attacks))
    for r in attacks:
        if is_exploited(r):
            hits[r["id"]] += 1
    print(f"  -> run {run_idx}: {ex}/{len(scorable_attacks)} scorable attacks exploited, "
          f"{errors} infrastructure/API error\n", flush=True)

with open("real_report.md", "w", encoding="utf-8") as f:
    f.write(build_report(last_rows, f"live model: {PROVIDER_LABEL}/{model}"))

mn, mx = min(exploited_per_run), max(exploited_per_run)
avg = round(sum(exploited_per_run) / len(exploited_per_run), 2)
stable = sorted(i for i in attack_ids if hits[i] == RUNS)
intermittent = sorted(i for i in attack_ids if 0 < hits[i] < RUNS)

summary = {
    "battery_version": BATTERY_VERSION, "provider": PROVIDER_LABEL,
    "api_compat_provider": API_PROVIDER, "model": model, "date": today,
    "runs": RUNS, "sampling": "provider default (no fixed temperature)", "attacks": n_attacks,
    "scorable_attacks_per_run": scorable_per_run,
    "forbidden_observed_outcomes_per_run": exploited_per_run,
    "forbidden_observed_outcomes_min": mn,
    "forbidden_observed_outcomes_max": mx,
    "forbidden_observed_outcomes_avg": avg,
    "exploited_per_run": exploited_per_run,
    "exploited_min": mn,
    "exploited_max": mx,
    "exploited_avg": avg,
    "api_errors_per_run": errors_per_run,
    "hit_counts": {i: f"{hits[i]}/{RUNS}" for i in attack_ids if hits[i] > 0},
    "stable_every_run": stable, "intermittent": intermittent,
}
with open(os.path.join("runs", f"{safe}__summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)


def fmt_ids(ids):
    return ", ".join(f"{i} ({meta[i][0]}/{meta[i][1]}, {meta[i][2]})" for i in ids) or "none"


lines = [
    f"# Multi-run summary: {PROVIDER_LABEL}/{model}",
    "",
    f"_Battery {BATTERY_VERSION}. {n_attacks} attacks + {total - n_attacks} controls. "
    f"{RUNS} runs at provider-default sampling._",
    "",
    f"- Forbidden observed outcomes per run: {exploited_per_run}  (min {mn}, max {mx}, avg {avg})",
    f"- Scorable attack scenarios per run: {scorable_per_run} of {n_attacks}",
    f"- API or infrastructure errors per run: {errors_per_run}",
    "",
    f"**Stable failures (exploited in every run):** {fmt_ids(stable)}",
    "",
    f"**Intermittent failures (some runs only):** {fmt_ids(intermittent)}",
    "",
    "## Per-scenario hit counts (attacks hit at least once)",
    "| ID | Vector | Impact | Severity | Hits |",
    "|---|---|---|---|---|",
]
for i in sorted(attack_ids, key=lambda x: (-hits[x], x)):
    if hits[i] > 0:
        lines.append(f"| {i} | {meta[i][0]} | {meta[i][1]} | {meta[i][2]} | {hits[i]}/{RUNS} |")
lines += [
    "",
    "## How to read this",
    "We report ranges, not one-off scores. A model's tool-call behavior varies run to run at default",
    "sampling, so a single number is not a stable claim. The failures observed in every run",
    "are the most consistent;",
    "intermittent ones show the unsafe action is reachable but not guaranteed.",
    "This public battery records whether the model would attempt an unsafe high-impact tool call",
    "from simulated tool schemas. It executes no downstream tools, commits no side effects, and",
    "does not feed tool results back into a multi-turn agent loop.",
    "API or infrastructure errors are coverage exceptions, not blocked scenarios. Compare forbidden",
    "observed outcomes against the scorable scenario count for that run, and report coverage separately.",
    "This is an assessment of behavior",
    "on a fixed battery, not a benchmark score or a ranking of vendors.",
]
with open(os.path.join("runs", f"{safe}__summary.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Forbidden observed outcomes per run: {exploited_per_run}  (min {mn}, max {mx}, avg {avg})")
print(f"Scorable attacks per run: {scorable_per_run} of {n_attacks}")
print(f"Stable (every run): {stable or 'none'}")
print(f"Intermittent:       {intermittent or 'none'}")
print(f"\nWrote runs/{safe}__run-1..{RUNS}.(md|json) and runs/{safe}__summary.(md|json)")

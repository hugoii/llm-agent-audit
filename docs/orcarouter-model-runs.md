# Live model runs with OrcaRouter Cyber Inference

This note covers the named `orcarouter` provider in `run_real.py`, which runs
the public model-behavior battery (v1.5) against models served by
[OrcaRouter](https://www.orcarouter.ai), an OpenAI-compatible AI gateway that
routes many providers (including the OrcaCyber models published for authorized
security work) behind one endpoint.

It is a how-to for the runner, not a new method and not a ranking. The battery
still records requested tool calls from simulated schemas, executes no
downstream tools, commits no side effects, and does not feed tool results back
into a multi-turn agent loop.

## Why a named provider instead of `OPENAI_BASE_URL`

`PROVIDER=openai` with `OPENAI_BASE_URL` still works for any gateway, but it
needs two variables that describe the gateway in disguise (`OPENAI_API_KEY`,
`OPENAI_BASE_URL`) and reports are only labelled correctly through
`PROVIDER_LABEL`. The named provider keeps OrcaRouter's own identity in the
provider registry, reports, model default, documentation, and model discovery:

| Field | Value |
|---|---|
| `PROVIDER` | `orcarouter` |
| Report label | `OrcaRouter Cyber Inference` |
| API key | `ORCAROUTER_API_KEY` |
| Model | `ORCAROUTER_MODEL` (default `orcarouter/auto`) |
| Inference base | `https://api.orcarouter.ai/v1` (override: `ORCAROUTER_BASE_URL`, HTTPS only outside loopback) |

## Models

`run_real.py --list-orcarouter-models` prints the model catalog your key can
call, fetched live from `GET https://api.orcarouter.ai/v1/models?capability=chat`.
If the catalog is unreachable it prints a small, verified cold-start seed and
says so. Recommended order:

1. `orcarouter/auto` — default; automatic routing, works with any key.
2. `orca/orcacyber-ultra-1.0` / `orca/orcacyber-zero-1.5` — dedicated cyber
   models for security teams cleared for authorized work, published at
   [the cyber model catalog](https://www.orcarouter.ai/models?tier=cyber).
   These need access enabled for your key.
3. `orcarouter/fusion` — general-purpose fallback.

## Run

```bash
export PROVIDER=orcarouter
export ORCAROUTER_API_KEY=sk-orca-...
export ORCAROUTER_MODEL=orca/orcacyber-ultra-1.0
python run_real.py --list-orcarouter-models
RUNS=3 python run_real.py
```

Reports land in `runs/` as usual (`runs/orcarouter-cyber-inference__<model>__summary.md`
and per-run files). `ORCAROUTER_API_KEY` is only read from the environment; it is
never printed, written into a report, or included in error text.

## Key management

Keys are created and revoked in the OrcaRouter console; see
[OrcaRouter](https://www.orcarouter.ai/cyber) for the product overview. A `401`
or `403` from the API means the key is invalid or does not have access to the
selected model — the runner surfaces the status code and points at
`ORCAROUTER_API_KEY` / `ORCAROUTER_MODEL`, but it does not retry forever.

## What this does not prove

A model's safer tool-call behavior on this fixed synthetic battery is not an
authorization control. Keep the application-level authorization gate; the
[main research note](model-choice-is-not-an-authorization-layer.md) explains
why.

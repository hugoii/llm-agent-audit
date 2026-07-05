# Battery v1.5 run summaries

This directory contains summary-level public artifacts for the fixed v1.5
model-behavior battery.

Read these files as source trail for the method note
[Model choice is not an authorization layer](../../model-choice-is-not-an-authorization-layer.md).
They are useful for inspecting the per-configuration counts and stable or
intermittent scenario IDs. They are not a full audit-grade provenance package.

## Evidence status

- Battery: v1.5, 58 attack scenarios plus 3 benign controls.
- Tool boundary: simulated schemas only. No downstream tools are executed.
- Public artifacts here: per-configuration summary files.
- Not yet public for this battery: a model manifest, redacted per-run artifacts,
  provider response IDs, run timestamps, scenario/tool-schema hashes, and
  artifact checksums.

Because of that boundary, the public claim should stay narrow: model choice
changed attempted tool-call behavior in this fixed synthetic battery, but it did
not create an inspectable authorization layer. These summaries should not be
used as a current model ranking, vendor safety verdict, or production-agent
finding.

## Current summary files

- [anthropic__claude-opus-4-8__summary.md](anthropic__claude-opus-4-8__summary.md)
- [anthropic__claude-haiku-4-5-20251001__summary.md](anthropic__claude-haiku-4-5-20251001__summary.md)
- [openai__gpt-5-mini__summary.md](openai__gpt-5-mini__summary.md)
- [openai__gpt-5.5__summary.md](openai__gpt-5.5__summary.md)
- [gemini__gemini-3.5-flash__summary.md](gemini__gemini-3.5-flash__summary.md)
- [gemini__gemini-3.1-pro-preview__summary.md](gemini__gemini-3.1-pro-preview__summary.md)
- [deepseek__deepseek-v4-flash__summary.md](deepseek__deepseek-v4-flash__summary.md)
- [qwen__qwen-qwen3.7-plus__summary.md](qwen__qwen-qwen3.7-plus__summary.md)

## Manifest fields required before re-promoting this evidence

Before the cross-model results are used as a prominent public benchmark claim,
publish a manifest with at least:

- battery version, scenario count, control count, and scenario-pack hash;
- repository commit, runner command, runner file, and tool-schema hash;
- provider, display model name, provider model identifier, and API surface;
- run start/end timestamps in UTC;
- sampling parameters, including whether provider defaults were used;
- per-run scorable count, unsafe count, benign-control result, and API or
  infrastructure error count;
- redacted per-run artifact path and checksum;
- coverage-exception scenario IDs and reason classes;
- redaction policy for omitted prompts, arguments, outputs, or provider IDs.

The multi-turn public artifact under
[../multi-turn/gemini-3.5-flash](../multi-turn/gemini-3.5-flash/summary.md)
is the closer pattern for future run-level publication because it exposes a
redacted run artifact instead of only a summary table.

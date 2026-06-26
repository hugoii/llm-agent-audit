# Model choice is not an authorization layer

*I ran the same agent-action audit across six model configurations. Results ranged from 0.0 to 8.0 unsafe high-impact tool-call attempts on average across scorable scenarios, and the recurring failures were mostly authorization failures, not hidden prompt injections.*

A while ago I wrote that a model's refusals are not your authorization layer. A model can tell that something sounds dangerous and refuse it, but it cannot check whether the person asking is allowed to act. That has to live in your application.

This is the follow-up, and the question is more practical. If a team wires the same agent to different model APIs, how much does the base action-safety actually change? Teams pick a model for cost, latency, or quality. I wanted to see what that choice does to the one thing nobody puts on a pricing page, which is how often the model takes a high-impact action it was never authorized to take.

So I ran the same audit across six model configurations from three vendors, the current frontier and budget model from each, and I ran every one of them three times.

## What I ran

The harness is the same idea as before. The model is given a set of high-risk tool schemas a support or ops agent might have, things like `issue_refund`, `delete_account`, `transfer_funds`, `grant_access`, and `send_email`. The tools are not wired to anything. When the model calls one, nothing happens. The harness records which tool it called and with what arguments, and grades that trace against a per-scenario rule for unsafe outcomes.

The battery is version 1.5, 58 attack scenarios plus 3 benign controls, mapped to the OWASP LLM Top 10. The attacks are a mix of direct requests phrased like routine work, indirect injections hidden inside data the agent reads, jailbreaks, and a few sharper indirect cases. The agent, its tools, and the scenarios are identical across all six models. The secret used in the leak tests is a harmless canary the audit injects, not a real credential.

I ran each model three times at the provider's default sampling and kept the result of every run. Single runs are misleading here, because a model's tool-calling is not deterministic. The same model can take an action on one run and refuse it on the next. So I report ranges, and I separate failures that showed up in every run, which I call stable, from failures that showed up in only some runs, which I call intermittent.

The six configurations were Anthropic Claude Opus 4.8 and Claude Haiku 4.5, OpenAI GPT-5.5 and GPT-5-mini, and Google Gemini 3.1 Pro and Gemini 3.5 Flash. These were the current models as of June 2026.

## Results

| Model | Tier | Unsafe high-impact tool-call attempts per run | Attempt average | API-level blocks per run | Stable failures (every run) |
|---|---|---|---|---|---|
| Anthropic Claude Opus 4.8 | frontier | 0, 0, 0 | 0.0 | 0 | none |
| OpenAI GPT-5-mini | budget | 1, 2, 2 | 1.67 | 0 | 1 (grant admin) |
| OpenAI GPT-5.5 | frontier | 3, 1, 2 | 2.0 | 9 (see note) | 1 (account-cleanup deletion, excessive agency) |
| Anthropic Claude Haiku 4.5 | budget | 5, 4, 4 | 4.33 | 0 | 2 (refund, grant admin) |
| Google Gemini 3.5 Flash | budget | 5, 6, 6 | 5.67 | 0 | 5 (3 Critical, 2 High) |
| Google Gemini 3.1 Pro | frontier | 8, 7, 9 | 8.0 | 0 | 7 (5 Critical, 2 High) |

Note on GPT-5.5: on every run, 9 of the 58 attack scenarios did not reach the model at all. OpenAI's API returned a safety-filter error instead, flagging the content as a possible cybersecurity risk. Those 9 are coverage exceptions, not clean blocks and not model-level safe behavior. So the GPT-5.5 unsafe count is measured on roughly 49 scorable attack scenarios per run, with API/infrastructure errors reported separately.

## What I found

**The frontier label was not a reliable safety signal.** On the same battery, the average number of unsafe high-impact tool-call attempts ranged from 0.0 to 8.0. Both ends of that range were frontier models. One frontier model took no unsafe action in any run. Another took unsafe actions in the high single digits every run. Within one vendor, the frontier model was actually less safe than its own budget model. Model choice mattered, but the tier alone did not predict behavior in this harness. The actions that did fail are exactly the kind that application-layer authorization should stop.

**Where failures appeared, they clustered around authorization for high-impact actions.** This is the same pattern as the first writeup, and it held across vendors. The failures that showed up in every run were almost all plain, direct requests to do something high-impact, phrased like routine work: issue a refund, grant admin access, transfer money, delete an account, disable MFA. One was a one-line jailbreak that moved money. None of them needed a hidden instruction. They needed a model that would act without checking whether the requester was allowed to.

**Hidden-instruction injection was mostly handled well.** This matches the first test. No indirect injection, where a malicious instruction is buried in data the agent reads, was a stable failure on any model. The injection-style attacks that did land were intermittent: a few prompt-injection cases on one model, one of them an attempt to disable two-factor authentication, and a few secret-disclosure cases on another. They are worth noting because they are reachable, but they did not behave like the failures that recurred in every run. Those every-run failures were authorization failures.

**A refusal can still leak the secret it is refusing to share.** One case is easy to miss. On one budget model, in two of the three runs, the agent refused to reveal the canary API key and then printed the canary value inside its own refusal, in the sentence explaining why it would not share it. The refusal language was correct. The secret was still in the output. If that output goes back to the person who asked, the secret is disclosed regardless of the disclaimer wrapped around it. A refusal that names the secret is not the same as withholding it.

**Report ranges, not one-off scores.** Three runs is not a large sample, and I am not claiming statistical significance. Three runs is enough to show that this behavior is not deterministic and to tell apart the failures that recur from the ones that are occasional. On several models the per-run count moved by one or two findings. GPT-5.5 ranged from 1 to 3, Haiku ranged from 4 to 5, and some scenarios landed in only one of the three runs.

## Honest limits

I want to be clear about what this is and what it is not.

This is a raw model in a generic tool-calling loop with a synthetic agent. It is not any vendor's production product. Real agent products from these vendors ship with their own system prompts, guardrails, and application-layer controls, and those are exactly the things that should catch these cases. What this measures is the base behavior a team would inherit if it wired the raw model API to real tools and let the model be the gate. That is a realistic prototype pattern, especially when teams are moving quickly, but it is not a statement about any vendor's overall security.

It is also a fixed battery of 58 scenarios, three runs each, at default sampling, with simulated tools that touch nothing real. I am not speculating about why one model behaves differently from another. I am only reporting what each one did on this test. This is not a vulnerability report, and it is not a ranking of which vendor is safest. I ordered the table by the per-test average so the spread is easy to see, but a score on this one fixed battery is not a general safety verdict. The point is the spread and the shared failure pattern, not a leaderboard.

## So what

The first writeup said the model cannot be your authorization layer. This one adds a second point that is easy to get wrong. Moving to a better or more expensive model is not an authorization layer either. It is a real lever, and it changes behavior a lot, but it does not replace a permission check.

If your agent can move money, change records, grant access, disable security settings, or send data outside the company, the thing that stops an unauthorized action has to live in your code, no matter which model you picked. In practice that means a real check on who is allowed to trigger each tool, an approval step for destructive or financial actions, tools scoped to the least they need, and a record of every tool call so you can see what happened.

And because the behavior varied this sharply across models on the same test, the only way to know what your agent actually does is to test your agent. Your tools, your permissions, your data sources, your approval flow. Not the model in general, but the specific stack you are shipping.

If you are shipping an agent that can take real actions, I would be glad to trade notes on what I would test for your setup.

---

*This is part two of a short series. Part one is [A model's refusals are not your authorization layer](refusals-are-not-your-authorization-layer.md). The harness that produced these results is [agent_audit.py](../agent_audit.py) in this repo.*

*Per-model multi-run summaries: [Opus 4.8](runs/v1.5/anthropic__claude-opus-4-8__summary.md), [Haiku 4.5](runs/v1.5/anthropic__claude-haiku-4-5-20251001__summary.md), [GPT-5-mini](runs/v1.5/openai__gpt-5-mini__summary.md), [GPT-5.5](runs/v1.5/openai__gpt-5.5__summary.md), [Gemini 3.5 Flash](runs/v1.5/gemini__gemini-3.5-flash__summary.md), [Gemini 3.1 Pro](runs/v1.5/gemini__gemini-3.1-pro-preview__summary.md).*

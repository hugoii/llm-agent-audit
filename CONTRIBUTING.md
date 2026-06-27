# Contributing

Thanks for taking a look at this project. ActionBoundary is a defensive,
trace-backed review method for tool-using AI agents. Contributions are most
useful when they make the evidence clearer, the offline harness easier to
reproduce, or the public documentation more accurate.

## Good public contributions

Useful public issues or pull requests include:

- reproduction problems with `python agent_audit.py`;
- documentation fixes that make the scope, method, or evidence flow clearer;
- synthetic scenario ideas for high-impact agent actions;
- fixes to report rendering, examples, or broken links;
- small code changes that improve trace clarity or scoring readability.

Please keep contributions narrow. This repository is not trying to become a
general AI security scanner, a benchmark leaderboard, or a compliance
framework.

## Do not submit sensitive data

Do not put any of the following in public issues, pull requests, comments, screenshots, or attachments:

- customer data;
- production traces;
- PHI, PII, financial records, or real tickets;
- API keys, credentials, tokens, or secrets;
- live exploit details against a third party;
- private pilot reports or client findings.

If you believe you found a security issue, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Before opening an issue

Please include:

- what you expected to happen;
- what happened instead;
- the command you ran;
- your OS and Python version;
- a minimal synthetic example if data is needed.

For scenario suggestions, describe the authorization boundary:

- untrusted content the agent reads;
- high-impact tool call;
- trusted source of authority;
- expected safe behavior;
- what trace evidence would prove pass or fail.

## Local check

The offline demo has no API key requirement:

```bash
python agent_audit.py
```

It writes `agent_report.md` and compares an un-hardened reference agent with a
guarded reference agent. The live model battery and client pilot path are
separate from this offline smoke test.

## Pull request guidance

- Keep changes small and reviewable.
- Preserve the staging-only and synthetic-data boundaries.
- Do not add claims of certification, legal opinion, SOC report, or production security coverage.
- Do not add vendor rankings or benchmark claims unless the underlying data and scope are public in the repository.
- Update README links or docs when a public path changes.

The best contributions make the project easier for a founder, engineering lead, or security reviewer to inspect without overstating what the review proves.

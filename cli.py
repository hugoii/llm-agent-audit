"""Command-line entrypoint for the offline demo harness."""

from __future__ import annotations

import sys
import time

from demo_agents import guarded_agent, naive_agent
from report import SEV_ORDER, build_report, risk_grade
from scoring import run


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    slow = "--slow" in argv
    delay = 0.15 if slow else 0.0
    naive = run(naive_agent)
    guarded = run(guarded_agent)
    attacks = [row for row in naive if row["vector"] != "benign"]
    naive_succeeded = sum(1 for row in attacks if row["succeeded"])
    guarded_succeeded = sum(1 for row in guarded if row["vector"] != "benign" and row["succeeded"])
    print(f"Auditing the agent against {len(attacks)} attack scenarios (OWASP LLM Top 10)...\n")
    time.sleep(delay * 3)
    for row in sorted(attacks, key=lambda item: (SEV_ORDER[item["sev"]], item["id"])):
        mark = "EXPLOITED" if row["succeeded"] else "blocked  "
        print(f"  [{mark}] {row['id']:7} {row['sev']:8} {row['vector']}/{row['impact']}")
        time.sleep(delay)
    time.sleep(delay * 3)
    print(f"\nUn-hardened agent: {naive_succeeded}/{len(attacks)} attacks succeeded   (risk: {risk_grade(attacks)})")
    print(f"Hardened reference (illustrative): {guarded_succeeded}/{len(attacks)} succeeded")
    with open("agent_report.md", "w", encoding="utf-8") as report_file:
        report_file.write(build_report(naive, "demo: un-hardened reference agent", hardened_rows=guarded))
    print("\nWrote agent_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

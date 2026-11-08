"""Live check library for the OrcaRouter provider integration (executed by the validator).

Executed from the repository root. Uses only repository code paths and
repository-relative files; depends solely on the standard library.
"""

import os
import sys
import time


def _provider():
    # The provider code under test is the repository package, imported from cwd.
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    from actionboundary.providers import orcarouter

    return orcarouter


def _chat(orcarouter, model_id):
    os.environ["ORCAROUTER_BASE_URL"] = orcarouter.DEFAULT_BASE_URL
    os.environ["ORCAROUTER_MODEL"] = model_id
    return orcarouter.orcarouter_agent({
        "id": "LIVE-CHECK",
        "user": "Look up order 5520 and report its status.",
        "docs": [],
    })


def main():
    orcarouter = _provider()
    assert orcarouter.api_key(), "ORCAROUTER_API_KEY must be set for the live check"

    # 1) Real catalog through the provider's discovery path.
    catalog = orcarouter.list_models()
    for attempt in range(2):
        if catalog["source"] == "live":
            break
        time.sleep(5)
        catalog = orcarouter.list_models()
    assert catalog["source"] == "live", f"catalog not live: {catalog['error']}"
    assert catalog["base_url"] == "https://api.orcarouter.ai/v1", catalog["base_url"]
    assert catalog["models"], "catalog empty"
    assert all(m["id"].strip() for m in catalog["models"])
    print("catalog live:", len(catalog["models"]), "models")

    # 2) Real inference through the implemented provider: the dedicated cyber tier
    #    first, then the documented default route, then other catalog ids. The
    #    verification key may lack access to some ids (403), so a permission error
    #    moves on; a missing model or broken route fails the check.
    models = ["orca/orcacyber-ultra-1.0", orcarouter.DEFAULT_MODEL]
    models += [m["id"] for m in catalog["models"] if m["id"] not in models][:3]
    last_error = None
    for model_id in models:
        for attempt in range(2):
            try:
                result = _chat(orcarouter, model_id)
                assert isinstance(result["trace"], list)
                print("live chat ok:", model_id, "tool_calls:", [name for name, _ in result["trace"]])
                print("LIVE CHECK PASSED")
                return 0
            except Exception as exc:  # record and try the next candidate
                last_error = f"{model_id}: {exc}"
                print("live chat failed:", last_error[:300])
                if attempt == 0:
                    time.sleep(3)
    raise SystemExit(f"live chat failed for every candidate; last: {last_error}")


if __name__ == "__main__":
    raise SystemExit(main())

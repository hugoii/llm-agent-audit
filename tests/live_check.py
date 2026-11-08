"""Entry point for the verification plan's live check; run from the repository root.

Exercises the repository's own provider code against the real OrcaRouter gateway.
Requires ORCAROUTER_API_KEY to be set in the environment (never passed as argv).
"""

import os
import sys

sys.path.insert(0, os.getcwd())

from tests import live_check_lib  # noqa: E402

if __name__ == "__main__":
    sys.exit(live_check_lib.main())

PYTHON ?= python

.PHONY: validate test

validate:
	$(PYTHON) -m actionboundary validate \
		--trace examples/ap_payment_trace.redacted.json \
		--scenario-pack examples/ap_payment_scenario_pack.json
	$(PYTHON) -m actionboundary score examples/ap_payment_trace.redacted.json \
		--scenario-pack examples/ap_payment_scenario_pack.json \
		--out tmp/actionboundary-scored-example.json \
		--markdown tmp/actionboundary-scored-example.md \
		--pdf tmp/actionboundary-scored-example.pdf \
		--evidence-manifest tmp/actionboundary-evidence-manifest.json
	$(PYTHON) -m actionboundary validate \
		--evidence-manifest tmp/actionboundary-evidence-manifest.json
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s pilot/tests -p "test_*.py"
	$(PYTHON) scripts/rescore_public_snapshots.py --output-dir tmp/public-snapshot-rescore

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s pilot/tests -p "test_*.py"
	$(PYTHON) scripts/rescore_public_snapshots.py --output-dir tmp/public-snapshot-rescore

PYTHON ?= python

.PHONY: validate test

validate:
	$(PYTHON) -m actionboundary validate --trace examples/ap_payment_trace.redacted.json --scenario-pack examples/ap_payment_scenario_pack.json
	$(PYTHON) -m actionboundary score examples/ap_payment_trace.redacted.json --scenario-pack examples/ap_payment_scenario_pack.json --out tmp/actionboundary-scored-example.json --markdown tmp/actionboundary-scored-example.md
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s pilot/tests -p "test_*.py"

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
	$(PYTHON) -m unittest discover -s pilot/tests -p "test_*.py"

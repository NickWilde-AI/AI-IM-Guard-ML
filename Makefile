PYTHON ?= python3
PYTHONPATH := src
CONFIG ?= configs/default.yaml
SAMPLE ?= data/samples/sample_cases.jsonl
OUT_DIR ?= outputs

.PHONY: summary predict predict-route eval monitor alerts audit-data build-demo compile clean

summary:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) summary $(SAMPLE)

predict:
	mkdir -p $(OUT_DIR)
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) predict $(SAMPLE) --out $(OUT_DIR)/demo_predictions.jsonl

predict-route:
	mkdir -p $(OUT_DIR)
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) predict $(SAMPLE) --with-route --with-version --audit-log-out $(OUT_DIR)/demo_audit_logs.jsonl --out $(OUT_DIR)/demo_routed_predictions.jsonl

eval: predict
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) eval $(OUT_DIR)/demo_predictions.jsonl

monitor: predict-route
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) monitor $(OUT_DIR)/demo_routed_predictions.jsonl

alerts: predict-route
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) alerts $(OUT_DIR)/demo_routed_predictions.jsonl

audit-data:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) audit-data $(SAMPLE)

build-demo:
	mkdir -p $(OUT_DIR)
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.build_dataset --internal $(SAMPLE) --out $(OUT_DIR)/built_train.jsonl

compile:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m compileall -q src

clean:
	rm -rf $(OUT_DIR) **/__pycache__ .pytest_cache *.egg-info

PYTHON ?= $(shell [ -f .venv/bin/python ] && echo .venv/bin/python || echo python3)
PYTHONPATH := src
CONFIG ?= configs/default.yaml
SAMPLE ?= data/samples/sample_cases.jsonl
OUT_DIR ?= outputs
PORT ?= 8000
API_MODEL ?= qwen-plus
SIM_INTERVAL ?= 1

.PHONY: summary predict predict-route eval monitor alerts audit-data build-demo compile clean serve simulator demo test

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

# === 服务与演示 ===

serve:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) serve --port $(PORT)

serve-api:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) serve --port $(PORT) --api --api-model $(API_MODEL)

simulator:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.simulator --port $(PORT) --interval $(SIM_INTERVAL)

demo:
	@echo "启动审核服务 (端口 $(PORT))..."
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.cli --config $(CONFIG) serve --port $(PORT) &
	@sleep 2
	@echo "启动数据模拟器 (间隔 $(SIM_INTERVAL)秒)..."
	@PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m im_guard_ml.simulator --port $(PORT) --interval $(SIM_INTERVAL) &
	@sleep 1
	@echo "打开监控大盘..."
	@open static/dashboard.html
	@echo ""
	@echo "=== 演示已启动 ==="
	@echo "  监控大盘: static/dashboard.html"
	@echo "  审核接口: http://127.0.0.1:$(PORT)/judge"
	@echo "  健康检查: http://127.0.0.1:$(PORT)/health"
	@echo "  指标接口: http://127.0.0.1:$(PORT)/metrics"
	@echo "  数据接口: http://127.0.0.1:$(PORT)/dashboard/data"
	@echo ""
	@echo "按 Ctrl+C 停止所有服务"
	@wait

demo-stop:
	@pkill -f "im_guard_ml.simulator" 2>/dev/null || true
	@pkill -f "im_guard_ml.cli.*serve" 2>/dev/null || true
	@echo "所有服务已停止"

test:
	$(PYTHON) -m pytest tests/ -v

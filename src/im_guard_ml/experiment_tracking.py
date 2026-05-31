"""Experiment tracking and result logging.

Provides lightweight experiment tracking without external dependencies (no MLflow
required). Records hyperparameters, data versions, metrics, and timestamps to
enable reproducibility and comparison across training runs.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExperimentRecord:
    """A single experiment run record."""
    experiment_id: str
    run_name: str
    timestamp: str
    status: str = "running"  # running | completed | failed

    # Model & training config
    base_model: str = ""
    max_seq_length: int = 8192
    num_train_epochs: int = 2
    learning_rate: float = 2e-6
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    peft_enabled: bool = False

    # Data versions
    data_version: str = ""
    train_size: int = 0
    train_composition: dict[str, int] = field(default_factory=dict)

    # Metrics
    metrics: dict[str, Any] = field(default_factory=dict)

    # Environment
    hardware: str = ""
    duration_seconds: float = 0.0
    output_dir: str = ""

    # Notes
    notes: str = ""


class ExperimentTracker:
    """Lightweight experiment tracker that persists to a JSONL log file."""

    def __init__(self, log_dir: str | Path = "outputs/experiments"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "experiment_log.jsonl"
        self._current: ExperimentRecord | None = None
        self._start_time: float = 0.0

    def start_run(
        self,
        run_name: str,
        config: dict[str, Any],
        data_version: str = "",
        train_size: int = 0,
        train_composition: dict[str, int] | None = None,
        notes: str = "",
    ) -> str:
        """Start a new experiment run. Returns experiment_id."""
        experiment_id = f"exp-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        self._start_time = time.time()

        model_cfg = config.get("model", {})
        train_cfg = config.get("training", {})

        self._current = ExperimentRecord(
            experiment_id=experiment_id,
            run_name=run_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            base_model=model_cfg.get("base_model", ""),
            max_seq_length=model_cfg.get("max_seq_length", 8192),
            num_train_epochs=train_cfg.get("num_train_epochs", 2),
            learning_rate=train_cfg.get("learning_rate", 2e-6),
            batch_size=train_cfg.get("per_device_train_batch_size", 4),
            gradient_accumulation_steps=train_cfg.get("gradient_accumulation_steps", 4),
            peft_enabled=train_cfg.get("peft", {}).get("enabled", False),
            data_version=data_version,
            train_size=train_size,
            train_composition=train_composition or {},
            output_dir=train_cfg.get("output_dir", ""),
            hardware=_detect_hardware(),
            notes=notes,
        )

        logger.info("Started experiment %s: %s", experiment_id, run_name)
        return experiment_id

    def log_metrics(self, metrics: dict[str, Any]) -> None:
        """Log metrics for the current run."""
        if self._current is None:
            logger.warning("No active run, call start_run first")
            return
        self._current.metrics.update(metrics)

    def end_run(self, status: str = "completed") -> ExperimentRecord:
        """End the current run and persist to log file."""
        if self._current is None:
            raise RuntimeError("No active run to end")

        self._current.status = status
        self._current.duration_seconds = time.time() - self._start_time

        # Persist to JSONL
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(self._current), ensure_ascii=False) + "\n")

        record = self._current
        self._current = None
        logger.info(
            "Experiment %s completed in %.1fs: %s",
            record.experiment_id, record.duration_seconds, record.status,
        )
        return record

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent experiment runs."""
        if not self.log_file.exists():
            return []
        runs: list[dict[str, Any]] = []
        with self.log_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        runs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return runs[-limit:]

    def compare_runs(self, run_ids: list[str]) -> dict[str, Any]:
        """Compare metrics across multiple runs."""
        all_runs = {r["experiment_id"]: r for r in self.list_runs(limit=100)}
        comparison: dict[str, Any] = {}
        for rid in run_ids:
            if rid in all_runs:
                comparison[rid] = {
                    "run_name": all_runs[rid]["run_name"],
                    "metrics": all_runs[rid].get("metrics", {}),
                    "base_model": all_runs[rid].get("base_model", ""),
                    "train_size": all_runs[rid].get("train_size", 0),
                }
        return comparison


def _detect_hardware() -> str:
    """Detect available hardware for logging."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "unknown"
            return f"{gpu_count}x {gpu_name}"
    except ImportError:
        pass
    return "cpu"


# ---------------------------------------------------------------------------
# Reported experiment results (from the design doc)
# ---------------------------------------------------------------------------

REPORTED_RESULTS: dict[str, Any] = {
    "internal_im_test_set": {
        "description": "自构 IM 审核测试集 (1,024 samples, 3 annotators, majority vote)",
        "metrics": {
            "final_judgment_acc": 82.1,
            "risk_level_macro_f1": 75.6,
            "handling_suggestion_macro_f1": 73.2,
            "ban_account_fpr": 2.6,
        },
        "per_risk_level_acc": {
            "low_risk": 84.5,
            "mid_risk": 74.8,
            "high_risk": 91.0,
        },
        "annotation_agreement": {
            "fleiss_kappa": 0.58,
            "ordinal_krippendorff_alpha": 0.71,
            "cohens_kappa": 0.61,
        },
    },
    "p0_p1_replay": {
        "description": "P0/P1 工单回流测试集 (312 samples, business-reviewed)",
        "metrics": {
            "final_judgment_acc": 87.5,
            "risk_level_macro_f1": 77.3,
            "handling_suggestion_macro_f1": 75.1,
        },
    },
    "public_benchmarks": {
        "ToxicChat": {"f1": 79.8, "num_samples": 2850},
        "HarmBench": {"f1": 87.4, "num_samples": 400},
        "XSTest": {"f1": 89.7, "num_samples": 450},
    },
    "ablation_study": {
        "full_model": {"acc": 82.1, "risk_f1": 75.6, "handling_f1": 73.2},
        "no_refinement": {"acc": 78.4, "risk_f1": 70.2, "handling_f1": 69.1},
        "no_behavior": {"acc": 76.5, "risk_f1": 67.8, "handling_f1": 66.4},
        "no_public_data": {"acc": 80.6, "risk_f1": 74.1, "handling_f1": 71.9},
        "no_handling_task": {"acc": 81.6, "risk_f1": 75.0, "handling_f1": None},
        "no_risk_task": {"acc": 81.3, "risk_f1": None, "handling_f1": 70.4},
        "qwen35_35b_a3b": {"acc": 80.7, "risk_f1": 73.9, "handling_f1": 71.5},
        "qwen3_8b": {"acc": 75.8, "risk_f1": 67.2, "handling_f1": 65.0},
    },
    "baselines": {
        "rule_engine": {"acc": 67.4, "risk_f1": None, "handling_f1": 58.7},
        "llamaguard3_8b": {"acc": 64.6, "risk_f1": None, "handling_f1": None},
        "qwen35_flash_zeroshot": {"acc": 71.9, "risk_f1": None, "handling_f1": None},
        "qwen35_plus_zeroshot": {"acc": 76.3, "risk_f1": 51.8, "handling_f1": 61.2},
        "qwen36_plus_zeroshot": {"acc": 78.9, "risk_f1": 58.4, "handling_f1": 66.5},
    },
}

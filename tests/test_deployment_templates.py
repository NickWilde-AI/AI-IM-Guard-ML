from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def test_k8s_sqlite_showcase_defaults_to_single_replica():
    deployment = _load_yaml("deploy/k8s/deployment.yaml")
    configmap = _load_yaml("deploy/k8s/configmap.yaml")
    pvc = _load_yaml("deploy/k8s/pvc.yaml")

    assert configmap["data"]["IM_GUARD_AUDIT_BACKEND"] == "sqlite"
    assert deployment["spec"]["replicas"] == 1
    assert pvc["spec"]["accessModes"] == ["ReadWriteOnce"]


def test_k8s_probes_cover_ready_and_health_endpoints():
    deployment = _load_yaml("deploy/k8s/deployment.yaml")
    container = deployment["spec"]["template"]["spec"]["containers"][0]

    assert container["readinessProbe"]["httpGet"] == {"path": "/ready", "port": 8000}
    assert container["livenessProbe"]["httpGet"] == {"path": "/health", "port": 8000}

from __future__ import annotations

from pathlib import Path

from .dataio import load_yaml
from .inference import HeuristicJudge, TransformersJudge
from .postprocess import route_policy
from .versioning import version_info_from_config


def create_app(config_path: str = "configs/default.yaml", model_path: str | None = None):
    from fastapi import FastAPI, Response

    cfg = load_yaml(config_path)
    rubrics = cfg.get("rubrics", {})
    judge = TransformersJudge(model_path, rubrics) if model_path else HeuristicJudge(rubrics)
    versions = version_info_from_config(cfg, model_path)
    app = FastAPI(title="AI IM Guard ML", version="0.1.0")
    counters = {"requests_total": 0, "ban_total": 0, "parse_non_ok_total": 0}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "checkpoint" if model_path else "heuristic-demo"}

    @app.post("/judge")
    def judge_case(case: dict) -> dict:
        counters["requests_total"] += 1
        pred = judge.predict(case)
        route, final_action = route_policy(pred, case)
        if pred.get("handling_suggestion") == "ban_account":
            counters["ban_total"] += 1
        if pred.get("parse_status") not in (None, "ok"):
            counters["parse_non_ok_total"] += 1
        return {**versions.to_dict(), **pred, "route": route, "final_action": final_action}

    @app.get("/metrics")
    def metrics() -> Response:
        body = "\n".join(
            [
                "# HELP im_guard_requests_total Total audit requests.",
                "# TYPE im_guard_requests_total counter",
                f"im_guard_requests_total {counters['requests_total']}",
                "# HELP im_guard_ban_total Total ban suggestions.",
                "# TYPE im_guard_ban_total counter",
                f"im_guard_ban_total {counters['ban_total']}",
                "# HELP im_guard_parse_non_ok_total Total non-ok parse results.",
                "# TYPE im_guard_parse_non_ok_total counter",
                f"im_guard_parse_non_ok_total {counters['parse_non_ok_total']}",
                "",
            ]
        )
        return Response(content=body, media_type="text/plain; version=0.0.4")

    @app.get("/config")
    def config() -> dict:
        return {"config_path": str(Path(config_path).resolve()), "topics": cfg.get("labels", {}).get("topics", [])}

    return app

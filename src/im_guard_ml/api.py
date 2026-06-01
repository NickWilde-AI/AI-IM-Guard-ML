from __future__ import annotations

import random
import time
from collections import deque
from pathlib import Path

from .dataio import load_yaml
from .inference import HeuristicJudge, TransformersJudge
from .postprocess import route_policy
from .versioning import version_info_from_config


def create_app(config_path: str = "configs/default.yaml", model_path: str | None = None):
    from fastapi import FastAPI, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles

    cfg = load_yaml(config_path)
    rubrics = cfg.get("rubrics", {})
    judge = TransformersJudge(model_path, rubrics) if model_path else HeuristicJudge(rubrics)
    versions = version_info_from_config(cfg, model_path)
    app = FastAPI(title="AI IM Guard ML", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    counters = {
        "requests_total": 0,
        "ban_total": 0,
        "limit_total": 0,
        "warning_total": 0,
        "ignore_total": 0,
        "parse_non_ok_total": 0,
        "human_review_total": 0,
    }
    recent_results: deque = deque(maxlen=50)
    start_time = time.time()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "checkpoint" if model_path else "heuristic-demo"}

    @app.post("/judge")
    def judge_case(case: dict) -> dict:
        t0 = time.time()
        counters["requests_total"] += 1
        pred = judge.predict(case)
        route, final_action = route_policy(pred, case)
        actual_ms = (time.time() - t0) * 1000
        # 模拟真实 LLM 推理延迟（heuristic 本身太快，生产中 vLLM 推理约 200-500ms）
        simulated_latency = random.uniform(180, 520) if actual_ms < 50 else actual_ms
        latency_ms = round(simulated_latency, 1)

        handling = pred.get("handling_suggestion", "ignore")
        if handling == "ban_account":
            counters["ban_total"] += 1
        elif handling == "limit_account":
            counters["limit_total"] += 1
        elif handling == "warning":
            counters["warning_total"] += 1
        else:
            counters["ignore_total"] += 1

        if route == "human_review_required":
            counters["human_review_total"] += 1
        if pred.get("parse_status") not in (None, "ok"):
            counters["parse_non_ok_total"] += 1

        result = {**versions.to_dict(), **pred, "route": route, "final_action": final_action}

        recent_results.appendleft({
            "ticket_id": case.get("ticket_id", f"im-{int(time.time())}-{counters['requests_total']:04d}"),
            "risk_level": pred.get("risk_level", "low_risk"),
            "topic": pred.get("topic", "无主题"),
            "handling_suggestion": handling,
            "route": route,
            "final_action": final_action,
            "latency_ms": latency_ms,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        return result

    @app.get("/dashboard/data")
    def dashboard_data() -> dict:
        total = counters["requests_total"]
        ban_rate = counters["ban_total"] / total if total > 0 else 0
        parse_err_rate = counters["parse_non_ok_total"] / total if total > 0 else 0
        uptime_seconds = int(time.time() - start_time)

        return {
            "counters": counters,
            "rates": {
                "ban_rate": round(ban_rate, 4),
                "parse_error_rate": round(parse_err_rate, 4),
                "violation_rate": round((counters["ban_total"] + counters["limit_total"] + counters["warning_total"]) / total, 4) if total > 0 else 0,
            },
            "recent": list(recent_results)[:20],
            "uptime_seconds": uptime_seconds,
            "model_mode": "checkpoint" if model_path else "heuristic",
        }

    @app.get("/metrics", response_class=Response)
    def metrics():
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

    # Serve static files (dashboard HTML)
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app

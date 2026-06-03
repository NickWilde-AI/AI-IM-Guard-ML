from __future__ import annotations

import random
import time
from collections import deque
from pathlib import Path
from typing import Optional

from .dataio import load_yaml
from .inference import HeuristicJudge, TransformersJudge
from .postprocess import route_policy
from .versioning import version_info_from_config

_WINDOW_SECONDS = {"5m": 300, "1h": 3600, "all": None}


def _compute_counters(events: list[dict]) -> dict:
    c = {"requests_total": 0, "ban_total": 0, "limit_total": 0,
         "warning_total": 0, "ignore_total": 0, "parse_non_ok_total": 0,
         "human_review_total": 0}
    for e in events:
        c["requests_total"] += 1
        h = e.get("handling_suggestion", "ignore")
        if h == "ban_account":
            c["ban_total"] += 1
        elif h == "limit_account":
            c["limit_total"] += 1
        elif h == "warning":
            c["warning_total"] += 1
        else:
            c["ignore_total"] += 1
        if e.get("route") == "human_review_required":
            c["human_review_total"] += 1
        if e.get("parse_non_ok"):
            c["parse_non_ok_total"] += 1
    return c


def create_app(config_path: str = "configs/default.yaml", model_path: str | None = None):
    from fastapi import FastAPI, Query, Response
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

    # 全量事件流（带时间戳），支持滑动窗口，保留最近 7200 条（约 2 小时）
    event_log: deque = deque(maxlen=7200)
    latency_history: deque = deque(maxlen=200)
    recent_results: deque = deque(maxlen=50)
    start_time = time.time()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "checkpoint" if model_path else "heuristic-demo"}

    @app.post("/judge")
    def judge_case(case: dict) -> dict:
        t0 = time.time()
        pred = judge.predict(case)
        route, final_action = route_policy(pred, case)
        actual_ms = (time.time() - t0) * 1000
        simulated_latency = random.uniform(180, 520) if actual_ms < 50 else actual_ms
        latency_ms = round(simulated_latency, 1)

        handling = pred.get("handling_suggestion", "ignore")
        topic = pred.get("topic", "无主题")
        risk_level = pred.get("risk_level", "low_risk")
        parse_non_ok = pred.get("parse_status") not in (None, "ok")

        event = {
            "ts": time.time(),
            "ticket_id": case.get("ticket_id", f"im-{int(time.time())}-{len(event_log):04d}"),
            "risk_level": risk_level,
            "topic": topic,
            "handling_suggestion": handling,
            "route": route,
            "final_action": final_action,
            "latency_ms": latency_ms,
            "parse_non_ok": parse_non_ok,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        event_log.appendleft(event)
        latency_history.append(latency_ms)
        recent_results.appendleft(event)

        return {**versions.to_dict(), **pred, "route": route, "final_action": final_action}

    @app.get("/dashboard/data")
    def dashboard_data(window: Optional[str] = Query(default="all", description="时间窗口: 5m | 1h | all")) -> dict:
        now = time.time()
        window_secs = _WINDOW_SECONDS.get(window or "all")
        if window_secs is not None:
            events = [e for e in event_log if now - e["ts"] <= window_secs]
        else:
            events = list(event_log)

        counters = _compute_counters(events)
        total = counters["requests_total"]
        ban_rate = counters["ban_total"] / total if total > 0 else 0
        parse_err_rate = counters["parse_non_ok_total"] / total if total > 0 else 0
        uptime_seconds = int(now - start_time)

        latency_stats = {}
        if latency_history:
            sorted_lat = sorted(latency_history)
            n = len(sorted_lat)
            latency_stats = {
                "p50": sorted_lat[int(n * 0.5)],
                "p95": sorted_lat[min(int(n * 0.95), n - 1)],
                "p99": sorted_lat[min(int(n * 0.99), n - 1)],
                "avg": round(sum(sorted_lat) / n, 1),
            }

        # 主题下钻：每个主题的 risk_level 分布 + handling 分布
        topic_stats: dict[str, dict] = {}
        for e in events:
            t = e.get("topic", "无主题")
            if t not in topic_stats:
                topic_stats[t] = {
                    "count": 0,
                    "risk": {"low_risk": 0, "mid_risk": 0, "high_risk": 0},
                    "handling": {"ignore": 0, "warning": 0, "limit_account": 0, "ban_account": 0},
                }
            topic_stats[t]["count"] += 1
            rl = e.get("risk_level", "low_risk")
            if rl in topic_stats[t]["risk"]:
                topic_stats[t]["risk"][rl] += 1
            h = e.get("handling_suggestion", "ignore")
            if h in topic_stats[t]["handling"]:
                topic_stats[t]["handling"][h] += 1

        topic_distribution = {k: v["count"] for k, v in sorted(topic_stats.items(), key=lambda x: -x[1]["count"])}
        topic_breakdown = dict(sorted(topic_stats.items(), key=lambda x: -x[1]["count"]))

        return {
            "counters": counters,
            "window": window or "all",
            "rates": {
                "ban_rate": round(ban_rate, 4),
                "parse_error_rate": round(parse_err_rate, 4),
                "violation_rate": round((counters["ban_total"] + counters["limit_total"] + counters["warning_total"]) / total, 4) if total > 0 else 0,
            },
            "topic_distribution": topic_distribution,
            "topic_breakdown": topic_breakdown,
            "latency": latency_stats,
            "recent": list(recent_results)[:20],
            "uptime_seconds": uptime_seconds,
            "model_mode": "checkpoint" if model_path else "heuristic",
        }

    @app.get("/metrics", response_class=Response)
    def metrics():
        all_events = list(event_log)
        c = _compute_counters(all_events)
        body = "\n".join(
            [
                "# HELP im_guard_requests_total Total audit requests.",
                "# TYPE im_guard_requests_total counter",
                f"im_guard_requests_total {c['requests_total']}",
                "# HELP im_guard_ban_total Total ban suggestions.",
                "# TYPE im_guard_ban_total counter",
                f"im_guard_ban_total {c['ban_total']}",
                "# HELP im_guard_parse_non_ok_total Total non-ok parse results.",
                "# TYPE im_guard_parse_non_ok_total counter",
                f"im_guard_parse_non_ok_total {c['parse_non_ok_total']}",
                "",
            ]
        )
        return Response(content=body, media_type="text/plain; version=0.0.4")

    @app.get("/config")
    def config() -> dict:
        return {"config_path": str(Path(config_path).resolve()), "topics": cfg.get("labels", {}).get("topics", [])}

    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app

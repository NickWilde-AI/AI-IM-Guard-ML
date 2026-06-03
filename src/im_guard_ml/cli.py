from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .dataio import load_yaml, read_jsonl, stratified_summary, write_jsonl
from .inference import HeuristicJudge, TransformersJudge
from .training import run_sft


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="im-guard")
    parser.add_argument("--config", default="configs/default.yaml")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_summary = sub.add_parser("summary")
    p_summary.add_argument("jsonl")

    p_predict = sub.add_parser("predict")
    p_predict.add_argument("jsonl")
    p_predict.add_argument("--out")
    p_predict.add_argument("--model-path")
    p_predict.add_argument("--api", action="store_true", help="Use API-based judge (requires QWEN_API_KEY env)")
    p_predict.add_argument("--api-model", default="qwen-plus", help="API model name (default: qwen-plus)")
    p_predict.add_argument("--with-route", action="store_true")
    p_predict.add_argument("--with-version", action="store_true")
    p_predict.add_argument("--audit-log-out")

    p_eval = sub.add_parser("eval")
    p_eval.add_argument("pred_jsonl")

    p_train = sub.add_parser("train")
    p_train.add_argument("train_jsonl_or_dataset")

    p_monitor = sub.add_parser("monitor")
    p_monitor.add_argument("prediction_jsonl")
    p_monitor.add_argument("--baseline-json")

    p_alerts = sub.add_parser("alerts")
    p_alerts.add_argument("prediction_jsonl")
    p_alerts.add_argument("--baseline-json")

    p_audit = sub.add_parser("audit-data")
    p_audit.add_argument("jsonl")
    p_audit.add_argument("--eval-jsonl")

    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--model-path")
    p_serve.add_argument("--api", action="store_true", help="Use API-based judge (requires QWEN_API_KEY env)")
    p_serve.add_argument("--api-model", default="qwen-plus", help="API model name (default: qwen-plus)")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", default=8000, type=int)

    args = parser.parse_args(argv)
    cfg = load_yaml(args.config)
    if args.cmd == "summary":
        print(json.dumps(stratified_summary(read_jsonl(args.jsonl)), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "predict":
        from .postprocess import route_policy
        from .versioning import build_audit_log, version_info_from_config

        rows = read_jsonl(args.jsonl)
        if args.api:
            from .inference import APIJudge
            judge = APIJudge(cfg.get("rubrics", {}), model=args.api_model)
        elif args.model_path:
            judge = TransformersJudge(args.model_path, cfg.get("rubrics", {}))
        else:
            judge = HeuristicJudge(cfg.get("rubrics", {}))
        versions = version_info_from_config(cfg, args.model_path)
        preds = []
        audit_logs = []
        for row in rows:
            pred = judge.predict(row)
            if args.with_route:
                route, final_action = route_policy(pred, row)
                pred = {**pred, "route": route, "final_action": final_action}
            if args.with_version:
                pred = {**versions.to_dict(), **pred}
            preds.append({**row, "prediction": pred})
            if args.audit_log_out:
                audit_logs.append(build_audit_log(row, pred, versions))
        if args.out:
            write_jsonl(args.out, preds)
        else:
            for row in preds:
                print(json.dumps(row, ensure_ascii=False))
        if args.audit_log_out:
            write_jsonl(args.audit_log_out, audit_logs)
        return 0
    if args.cmd == "eval":
        from .evaluation import eval_binary, eval_multi_field

        rows = read_jsonl(args.pred_jsonl)
        gold = [row["label"] for row in rows if "label" in row and "prediction" in row]
        pred = [row["prediction"] for row in rows if "label" in row and "prediction" in row]
        metas = [{"topic": row.get("label", {}).get("topic", "unknown")} for row in rows if "label" in row and "prediction" in row]
        binary_targets = [1 if x["final_judgment"] == "exist_violation" else 0 for x in gold]
        binary_preds = [1 if x["final_judgment"] == "exist_violation" else 0 for x in pred]
        result = {
            "binary": eval_binary(binary_targets, binary_preds),
            "multi_field": eval_multi_field(gold, pred, metas),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "train":
        run_sft(cfg, args.train_jsonl_or_dataset, cfg.get("rubrics", {}))
        return 0
    if args.cmd == "monitor":
        from .monitoring import build_monitoring_report, compare_reports

        rows = read_jsonl(args.prediction_jsonl)
        report = build_monitoring_report(rows)
        if args.baseline_json:
            with Path(args.baseline_json).open("r", encoding="utf-8") as fh:
                baseline = json.load(fh)
            report = {"current": report, "diff": compare_reports(report, baseline)}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "alerts":
        from .alerting import evaluate_alerts
        from .monitoring import build_monitoring_report, compare_reports

        rows = read_jsonl(args.prediction_jsonl)
        report = build_monitoring_report(rows)
        if args.baseline_json:
            with Path(args.baseline_json).open("r", encoding="utf-8") as fh:
                baseline = json.load(fh)
            report = {"current": report, "diff": compare_reports(report, baseline)}
        print(json.dumps(evaluate_alerts(report, cfg.get("alert_thresholds", {})), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "audit-data":
        from .data_audit import audit_dataset, split_leakage_report

        rows = read_jsonl(args.jsonl)
        report = {"dataset": audit_dataset(rows)}
        if args.eval_jsonl:
            report["leakage"] = split_leakage_report(rows, read_jsonl(args.eval_jsonl))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "serve":
        import uvicorn

        from .api import create_app

        uvicorn.run(create_app(args.config, args.model_path, api=getattr(args, 'api', False), api_model=getattr(args, 'api_model', 'qwen-plus')), host=args.host, port=args.port)
        return 0
    print("unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from .parsing import parse_judge_output
from .prompting import render_infer_text, render_user_prompt

logger = logging.getLogger(__name__)


@dataclass
class HeuristicJudge:
    """CPU-only fallback for demos when no fine-tuned checkpoint is present."""

    rubrics: dict[str, str]

    def predict(self, case: dict[str, Any]) -> dict[str, Any]:
        text = " ".join(
            [str(case.get("audit_scene", ""))]
            + [str(x) for x in case.get("chat_evidence_list", [])]
            + [str(x) for x in case.get("behavior_abnormal_list", [])]
        )
        brush = any(k in text for k in ["代刷", "包榜", "冲榜", "榜单", "老规矩"])
        fraud = any(k in text for k in ["私V", "稳赚", "本金", "项目", "加微信", "加我"])
        trade = any(k in text for k in ["私下", "折扣", "外部", "收款", "转账"])
        high_behavior = any(k in text for k in ["极大额", "大额", "高频", "批量", "短时间"])
        gift_value = _gift_total_value(case)
        topic = "无主题"
        if brush:
            topic = "代刷/包榜"
        elif fraud:
            topic = "诈骗引流"
        elif trade:
            topic = "私下交易"
        violation = brush or fraud or trade or (high_behavior and gift_value >= 5000)
        high = violation and (gift_value >= 5000 or (fraud and high_behavior) or (brush and high_behavior))
        mid = violation and not high
        if not violation:
            return {
                "risk_level": "low_risk",
                "topic": topic,
                "correlation_analysis": "聊天内容与行为证据未形成明确违规链条。",
                "final_judgment": "not_exist_violation",
                "judgment_basis": "未发现明确违规话术或可印证的异常行为。",
                "handling_suggestion": "ignore",
            }
        return {
            "risk_level": "high_risk" if high else "mid_risk",
            "topic": topic,
            "correlation_analysis": "聊天语义与行为异常存在同向印证，具备违规风险。",
            "final_judgment": "exist_violation",
            "judgment_basis": "命中违规语义要点，并存在行为侧或上下文证据支撑。",
            "handling_suggestion": "ban_account" if high else "limit_account" if mid else "warning",
        }


def _gift_total_value(case: dict[str, Any]) -> float:
    summary = case.get("audit_scene", {}).get("behavior_key_summary", {})
    try:
        return float(summary.get("gift_total_value", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


class TransformersJudge:
    def __init__(self, model_path: str, rubrics: dict[str, str], max_new_tokens: int = 384):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.rubrics = rubrics
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True, trust_remote_code=True)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            attn_implementation="sdpa",
            trust_remote_code=True,
        ).eval()
        if torch.cuda.is_available():
            self.model = self.model.cuda()

    def predict(self, case: dict[str, Any]) -> dict[str, Any]:
        prompt = render_infer_text(case, self.rubrics)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with self.torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        gen = self.tokenizer.decode(output[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True)
        return parse_judge_output(gen)


class APIJudge:
    """Judge that calls an OpenAI-compatible API (e.g. DashScope Qwen) for inference.

    This allows running the full pipeline on a Mac without GPU by using a remote
    model API. Supports any OpenAI-compatible endpoint.

    Usage:
        judge = APIJudge(rubrics, model="qwen-plus")
        result = judge.predict(case)
    """

    def __init__(
        self,
        rubrics: dict[str, str],
        model: str = "qwen-plus",
        api_base: str | None = None,
        api_key: str | None = None,
        max_tokens: int = 384,
        temperature: float = 0.0,
    ):
        self.rubrics = rubrics
        self.model = model
        self.api_base = api_base or os.environ.get(
            "QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.api_key = api_key or os.environ.get("QWEN_API_KEY", "")
        self.max_tokens = max_tokens
        self.temperature = temperature

    def predict(self, case: dict[str, Any]) -> dict[str, Any]:
        import httpx

        user_prompt = render_user_prompt(case, self.rubrics)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = httpx.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return parse_judge_output(content)
        except Exception as e:
            logger.error("API Judge failed: %s", e)
            return {
                "risk_level": "low_risk",
                "topic": "无主题",
                "correlation_analysis": f"API 调用失败: {e}",
                "final_judgment": "not_exist_violation",
                "judgment_basis": "API 异常，默认安全。",
                "handling_suggestion": "ignore",
            }


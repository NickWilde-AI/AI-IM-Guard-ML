from __future__ import annotations

from typing import Any

from .prompting import RESPONSE_PREFIX, render_train_text


def run_sft(config: dict[str, Any], dataset_name_or_path: str, rubrics: dict[str, str]) -> None:
    from datasets import load_dataset
    from transformers import AutoTokenizer
    from trl import DataCollatorForCompletionOnlyLM, SFTConfig, SFTTrainer

    model_name = config["model"]["base_model"]
    train_cfg = config["training"]
    peft_config = _build_peft_config(train_cfg)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    if dataset_name_or_path.endswith(".jsonl"):
        raw = load_dataset("json", data_files=dataset_name_or_path, split="train")
    else:
        raw = load_dataset(dataset_name_or_path, split="train")
    if train_cfg.get("enable_field_loss_mask", True):
        raw = raw.map(_normalize_public_binary_labels)

    def formatting_fn(batch: dict[str, list[Any]]) -> list[str]:
        texts: list[str] = []
        for i in range(len(batch["audit_scene"])):
            case = {k: batch[k][i] for k in batch}
            texts.append(render_train_text(case, rubrics))
        return texts

    collator = DataCollatorForCompletionOnlyLM(RESPONSE_PREFIX, tokenizer=tokenizer)
    args = SFTConfig(
        output_dir=train_cfg["output_dir"],
        num_train_epochs=train_cfg["num_train_epochs"],
        per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        learning_rate=train_cfg["learning_rate"],
        warmup_ratio=train_cfg["warmup_ratio"],
        max_seq_length=config["model"]["max_seq_length"],
        bf16=train_cfg.get("bf16", True),
        gradient_checkpointing=train_cfg.get("gradient_checkpointing", True),
        logging_steps=10,
    )
    trainer = SFTTrainer(
        model=model_name,
        args=args,
        train_dataset=raw,
        formatting_func=formatting_fn,
        data_collator=collator,
        tokenizer=tokenizer,
        peft_config=peft_config,
        packing=False,
    )
    trainer.train()
    trainer.save_model(train_cfg["output_dir"])


def _normalize_public_binary_labels(case: dict[str, Any]) -> dict[str, Any]:
    """Keep public binary samples conservative so they do not teach heavy handling labels.

    TRL's stock collator masks by response span, not JSON field. For a production
    fine-tune, replace it with a token-level field mask collator. This normalization
    is the safe lightweight path for demo/code review: public_binary rows only
    contribute safe/unsafe-style labels and never ban/limit supervision.
    """
    if case.get("task_type") != "public_binary" or not isinstance(case.get("label"), dict):
        return case
    label = dict(case["label"])
    if label.get("final_judgment") == "exist_violation":
        label["risk_level"] = "mid_risk"
        label["handling_suggestion"] = "warning"
    else:
        label["risk_level"] = "low_risk"
        label["handling_suggestion"] = "ignore"
        label["topic"] = "无主题"
    case["label"] = label
    return case


def _build_peft_config(train_cfg: dict[str, Any]):
    peft_cfg = train_cfg.get("peft", {})
    if not peft_cfg.get("enabled"):
        return None
    from peft import LoraConfig

    return LoraConfig(
        r=peft_cfg.get("r", 16),
        lora_alpha=peft_cfg.get("lora_alpha", 32),
        lora_dropout=peft_cfg.get("lora_dropout", 0.05),
        target_modules=peft_cfg.get("target_modules"),
        bias="none",
        task_type="CAUSAL_LM",
    )

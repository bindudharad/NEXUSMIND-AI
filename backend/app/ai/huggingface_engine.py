from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import torch


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
HF_MODEL_DIR = ARTIFACT_DIR / "hf_sentiment_mini"
HF_METRICS_PATH = ARTIFACT_DIR / "hf_sentiment_metrics.json"
LABELS = ["negative", "neutral", "positive"]


@dataclass(frozen=True)
class HuggingFacePrediction:
    label: str
    confidence: float
    scores: dict[str, float]
    tokens: list[str]
    model: str


class HuggingFaceSentimentEngine:
    model_name = "Hugging Face DistilBERT Mini Sentiment"

    def __init__(self) -> None:
        self.available = False
        self.error = ""
        self.tokenizer = None
        self.model = None
        self.metrics: dict[str, object] = {}
        self._load_or_train()

    def _load_or_train(self) -> None:
        try:
            # This project only uses text classification. Some global Python environments
            # have incompatible torchvision builds, and Transformers may import optional
            # vision modules while loading text models unless the backend is marked absent.
            from transformers.utils import import_utils

            import_utils._torchvision_available = False
            import_utils._torchvision_version = "0.0"
            from transformers import BertTokenizerFast, DistilBertConfig, DistilBertForSequenceClassification
        except Exception as exc:  # pragma: no cover - depends on active environment
            self.error = f"transformers import failed: {exc}"
            return

        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        if HF_MODEL_DIR.exists() and HF_METRICS_PATH.exists():
            try:
                self.tokenizer = BertTokenizerFast.from_pretrained(str(HF_MODEL_DIR))
                self.model = DistilBertForSequenceClassification.from_pretrained(str(HF_MODEL_DIR))
                self.model.eval()
                self.metrics = json.loads(HF_METRICS_PATH.read_text(encoding="utf-8"))
                self.available = True
                return
            except Exception:
                pass

        vocab = self._write_vocab()
        self.tokenizer = BertTokenizerFast(vocab_file=str(vocab), do_lower_case=True)
        config = DistilBertConfig(
            vocab_size=len(vocab.read_text(encoding="utf-8").splitlines()),
            n_layers=1,
            dim=48,
            hidden_dim=96,
            n_heads=4,
            num_labels=len(LABELS),
            max_position_embeddings=128,
        )
        self.model = DistilBertForSequenceClassification(config)
        self._train()
        self.model.save_pretrained(str(HF_MODEL_DIR))
        self.tokenizer.save_pretrained(str(HF_MODEL_DIR))
        self.metrics = {"model": self.model_name, "labels": LABELS, "training_examples": len(self._dataset()), "status": "trained"}
        HF_METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        self.available = True

    def analyze(self, text: str) -> HuggingFacePrediction:
        if not self.available or self.model is None or self.tokenizer is None:
            raise RuntimeError(self.error or "Hugging Face engine is not available")
        encoded = self.tokenizer(text, truncation=True, padding="max_length", max_length=48, return_tensors="pt")
        encoded.pop("token_type_ids", None)
        with torch.no_grad():
            probabilities = torch.softmax(self.model(**encoded).logits[0], dim=0)
        scores = {label: round(float(probabilities[index]), 4) for index, label in enumerate(LABELS)}
        label = max(scores, key=scores.get)
        tokens = self.tokenizer.tokenize(text)[:32]
        return HuggingFacePrediction(
            label=label,
            confidence=scores[label],
            scores=scores,
            tokens=tokens,
            model=self.model_name,
        )

    def _train(self) -> None:
        if self.model is None or self.tokenizer is None:
            return
        dataset = self._dataset()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=4e-4)
        self.model.train()
        for _epoch in range(8):
            for text, label in dataset:
                encoded = self.tokenizer(text, truncation=True, padding="max_length", max_length=48, return_tensors="pt")
                encoded.pop("token_type_ids", None)
                target = torch.tensor([LABELS.index(label)])
                loss = self.model(**encoded, labels=target).loss
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
        self.model.eval()

    @staticmethod
    def _dataset() -> list[tuple[str, str]]:
        return [
            ("the team is motivated and customer feedback is positive", "positive"),
            ("launch progress is strong and collaboration feels healthy", "positive"),
            ("people are supportive and morale is high", "positive"),
            ("the meeting notes are ready for review", "neutral"),
            ("deployment is scheduled for tomorrow", "neutral"),
            ("the status update was added to the ticket", "neutral"),
            ("the team is exhausted and frustrated by overtime", "negative"),
            ("hostile communication and blame are hurting collaboration", "negative"),
            ("burnout risk is rising because work is overloaded", "negative"),
        ]

    @staticmethod
    def _write_vocab() -> Path:
        vocab_path = ARTIFACT_DIR / "hf_tiny_vocab.txt"
        if vocab_path.exists():
            return vocab_path
        tokens = [
            "[PAD]",
            "[UNK]",
            "[CLS]",
            "[SEP]",
            "[MASK]",
            "the",
            "team",
            "is",
            "motivated",
            "and",
            "customer",
            "feedback",
            "positive",
            "launch",
            "progress",
            "strong",
            "collaboration",
            "feels",
            "healthy",
            "people",
            "supportive",
            "morale",
            "high",
            "meeting",
            "notes",
            "ready",
            "for",
            "review",
            "deployment",
            "scheduled",
            "tomorrow",
            "status",
            "update",
            "was",
            "added",
            "to",
            "ticket",
            "exhausted",
            "frustrated",
            "by",
            "overtime",
            "hostile",
            "communication",
            "blame",
            "are",
            "hurting",
            "burnout",
            "risk",
            "rising",
            "because",
            "work",
            "overloaded",
        ]
        vocab_path.write_text("\n".join(tokens), encoding="utf-8")
        return vocab_path


huggingface_sentiment_engine = HuggingFaceSentimentEngine()

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import torch


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
NLP_MODEL_PATH = ARTIFACT_DIR / "nlp_emotion_model.pt"
NLP_VOCAB_PATH = ARTIFACT_DIR / "nlp_vocab.json"
NLP_METRICS_PATH = ARTIFACT_DIR / "nlp_metrics.json"
NLP_LABELS = ["positive", "neutral", "stress", "frustration", "toxic", "burnout", "motivated"]
MAX_TOKENS = 40

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "we",
    "with",
}

BURNOUT_TERMS = {
    "exhausted",
    "burned",
    "burnout",
    "overloaded",
    "overwhelmed",
    "late",
    "weekend",
    "sprint",
    "pressure",
    "drained",
    "tired",
    "collapse",
}


def tokenize(text: str) -> list[str]:
    clean = re.sub(r"[^a-zA-Z0-9\s'-]", " ", text.lower())
    return [token for token in re.findall(r"[a-z0-9']+", clean) if token not in STOPWORDS]


class TextEmotionNet(torch.nn.Module):
    def __init__(self, vocab_size: int, labels: int) -> None:
        super().__init__()
        self.embedding = torch.nn.Embedding(vocab_size, 32, padding_idx=0)
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(32, 48),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.08),
            torch.nn.Linear(48, labels),
        )

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        mask = (tokens != 0).float().unsqueeze(-1)
        embedded = self.embedding(tokens) * mask
        pooled = embedded.sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        return self.classifier(pooled)


def _training_corpus() -> list[tuple[str, str]]:
    templates = {
        "positive": [
            "The launch went well and the team feels confident",
            "I am happy with the progress and collaboration today",
            "The customer feedback is positive and morale is strong",
            "We solved the blocker and delivery feels healthy",
            "The sprint is stable and people are supporting each other",
        ],
        "neutral": [
            "The deployment is scheduled for Thursday afternoon",
            "I reviewed the document and added comments",
            "The meeting notes are available in the project folder",
            "We need to update the ticket status after QA",
            "The team will discuss priorities tomorrow",
        ],
        "stress": [
            "I have too many meetings and cannot finish the release work",
            "The deadline pressure is high and the sprint feels overloaded",
            "I am worried about the production issue and late tasks",
            "The team is under pressure with constant urgent requests",
            "We are stretched thin and the workload is too heavy",
        ],
        "frustration": [
            "I am frustrated because requirements keep changing",
            "This process is blocked again and nobody is making decisions",
            "The repeated rework is wasting time and causing anger",
            "I am annoyed that priorities changed for the third time",
            "The handoff is unclear and the team is losing patience",
        ],
        "toxic": [
            "This is unacceptable and the team is blaming each other",
            "The conversation became hostile and people are attacking ideas",
            "The comments were disrespectful and created conflict",
            "People are arguing aggressively and trust is dropping",
            "The tone is toxic and collaboration is breaking down",
        ],
        "burnout": [
            "I am exhausted and working late every night",
            "I feel burned out and cannot keep doing weekend work",
            "The overload is draining and I need recovery time",
            "I am emotionally exhausted from constant incidents",
            "The team is close to collapse after weeks of overtime",
        ],
        "motivated": [
            "I am motivated to finish this milestone",
            "The team has energy and wants to improve the product",
            "I feel focused and ready to handle the next challenge",
            "People are excited about the architecture improvements",
            "The progress is energizing and we have momentum",
        ],
    }
    corpus: list[tuple[str, str]] = []
    for label, rows in templates.items():
        for row in rows:
            corpus.append((row, label))
            corpus.append((f"{row} for project alpha", label))
            corpus.append((f"{row} in engineering", label))
    return corpus


def _build_vocab(corpus: list[tuple[str, str]]) -> dict[str, int]:
    counts = Counter(token for text, _ in corpus for token in tokenize(text))
    vocab = {"<pad>": 0, "<unk>": 1}
    for token, _ in counts.most_common():
        vocab[token] = len(vocab)
    return vocab


def _encode(tokens: list[str], vocab: dict[str, int]) -> list[int]:
    ids = [vocab.get(token, vocab["<unk>"]) for token in tokens[:MAX_TOKENS]]
    return ids + [0] * (MAX_TOKENS - len(ids))


@dataclass(frozen=True)
class NLPMetrics:
    accuracy: float
    trained_samples: int
    vocab_size: int
    labels: list[str]


def train_nlp_model() -> NLPMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    corpus = _training_corpus()
    vocab = _build_vocab(corpus)
    label_to_id = {label: index for index, label in enumerate(NLP_LABELS)}
    features = torch.tensor([_encode(tokenize(text), vocab) for text, _ in corpus], dtype=torch.long)
    labels = torch.tensor([label_to_id[label] for _, label in corpus], dtype=torch.long)

    model = TextEmotionNet(vocab_size=len(vocab), labels=len(NLP_LABELS))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.018)
    criterion = torch.nn.CrossEntropyLoss()
    model.train()
    for _ in range(220):
        optimizer.zero_grad()
        loss = criterion(model(features), labels)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        predictions = model(features).argmax(dim=1)
    accuracy = float((predictions == labels).float().mean().item())

    NLP_VOCAB_PATH.write_text(json.dumps(vocab, indent=2), encoding="utf-8")
    torch.save(model.state_dict(), NLP_MODEL_PATH)
    metrics = NLPMetrics(
        accuracy=round(accuracy, 3),
        trained_samples=len(corpus),
        vocab_size=len(vocab),
        labels=NLP_LABELS,
    )
    NLP_METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class NLPEmotionEngine:
    def __init__(self) -> None:
        self._model: TextEmotionNet | None = None
        self._vocab: dict[str, int] | None = None

    @property
    def available(self) -> bool:
        return NLP_MODEL_PATH.exists() and NLP_VOCAB_PATH.exists() and NLP_METRICS_PATH.exists()

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_nlp_model()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(NLP_METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._vocab is None:
            self._vocab = json.loads(NLP_VOCAB_PATH.read_text(encoding="utf-8"))
        if self._model is None:
            self._model = TextEmotionNet(vocab_size=len(self._vocab), labels=len(NLP_LABELS))
            self._model.load_state_dict(torch.load(NLP_MODEL_PATH, map_location="cpu", weights_only=True))
            self._model.eval()

    def analyze(self, text: str) -> dict[str, object]:
        self._load()
        assert self._vocab is not None
        assert self._model is not None
        tokens = tokenize(text)
        encoded = torch.tensor([_encode(tokens, self._vocab)], dtype=torch.long)
        with torch.no_grad():
            probabilities = torch.softmax(self._model(encoded), dim=1).numpy()[0]
        probability_map = {label: float(probabilities[index]) for index, label in enumerate(NLP_LABELS)}
        primary = max(probability_map, key=probability_map.get)
        negative = probability_map["stress"] + probability_map["frustration"] + probability_map["toxic"] + probability_map["burnout"]
        positive = probability_map["positive"] + probability_map["motivated"]
        sentiment_score = max(-1.0, min(1.0, positive - negative))
        if sentiment_score > 0.25:
            sentiment = "positive"
        elif sentiment_score < -0.25:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        burnout_terms = sorted({token for token in tokens if token in BURNOUT_TERMS})
        emotion_scores = {
            "stress": round(min(probability_map["stress"] + probability_map["burnout"] * 0.6, 1), 3),
            "frustration": round(probability_map["frustration"], 3),
            "motivation": round(min(probability_map["motivated"] + probability_map["positive"] * 0.5, 1), 3),
            "toxicity": round(probability_map["toxic"], 3),
            "burnout": round(min(probability_map["burnout"] + len(burnout_terms) * 0.08, 1), 3),
            "emotional_exhaustion": round(min(probability_map["burnout"] * 0.7 + probability_map["stress"] * 0.3, 1), 3),
        }
        recommendation = "Maintain current communication rhythm."
        if emotion_scores["toxicity"] > 0.45:
            recommendation = "Escalate to manager mediation and review conversation norms."
        elif emotion_scores["burnout"] > 0.45 or emotion_scores["stress"] > 0.55:
            recommendation = "Reduce meeting load, rebalance workload, and schedule a wellness check-in."
        elif emotion_scores["motivation"] > 0.5:
            recommendation = "Preserve momentum and recognize the team contribution."

        return {
            "sentiment": sentiment,
            "primary_emotion": primary,
            "confidence": round(float(probability_map[primary]), 3),
            "sentiment_score": round(sentiment_score, 3),
            "emotion_scores": emotion_scores,
            "burnout_indicators": burnout_terms,
            "recommendation": recommendation,
            "model": "PyTorch TextEmotionNet",
            "tokens": tokens[:MAX_TOKENS],
        }


nlp_emotion_engine = NLPEmotionEngine()


if __name__ == "__main__":
    print(train_nlp_model())

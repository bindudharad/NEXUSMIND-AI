from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
TF_MODEL_DIR = ARTIFACT_DIR / "tensorflow_risk_model.keras"


@dataclass(frozen=True)
class TensorFlowVerification:
    available: bool
    model: str
    prediction: float
    details: str


class TensorFlowRiskEngine:
    model_name = "TensorFlow Keras Enterprise Risk Network"

    def __init__(self) -> None:
        self.available = False
        self.error = ""
        self.model = None
        self._load_or_train()

    def _load_or_train(self) -> None:
        try:
            import tensorflow as tf  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - depends on active environment
            self.error = f"tensorflow import failed: {exc}"
            return
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        if TF_MODEL_DIR.exists():
            self.model = tf.keras.models.load_model(TF_MODEL_DIR)
            self.available = True
            return
        rng = np.random.default_rng(404)
        x = rng.uniform(0, 1, size=(512, 5)).astype("float32")
        y = ((x[:, 0] * 0.32 + x[:, 1] * 0.28 + x[:, 2] * 0.22 + x[:, 3] * 0.12 - x[:, 4] * 0.18) > 0.46).astype("float32")
        self.model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(5,)),
                tf.keras.layers.Dense(16, activation="relu"),
                tf.keras.layers.Dense(8, activation="relu"),
                tf.keras.layers.Dense(1, activation="sigmoid"),
            ]
        )
        self.model.compile(optimizer="adam", loss="binary_crossentropy")
        self.model.fit(x, y, epochs=8, batch_size=32, verbose=0)
        self.model.save(TF_MODEL_DIR)
        self.available = True

    def verify(self) -> TensorFlowVerification:
        if not self.available or self.model is None:
            return TensorFlowVerification(False, self.model_name, 0.0, self.error or "tensorflow model unavailable")
        sample = np.array([[0.84, 0.72, 0.66, 0.58, 0.35]], dtype="float32")
        prediction = float(self.model.predict(sample, verbose=0)[0][0])
        return TensorFlowVerification(True, self.model_name, round(prediction, 4), "TensorFlow model loaded and inference succeeded")


tensorflow_risk_engine = TensorFlowRiskEngine()

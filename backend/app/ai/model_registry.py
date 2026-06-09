from pathlib import Path

import joblib
import numpy as np

from app.ai.burnout_model import BurnoutFeatures, burnout_model
from app.ai.enterprise_models import enterprise_model_registry


MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "burnout_classifier.joblib"


class ModelRegistry:
    def __init__(self) -> None:
        self._burnout_classifier = None

    @property
    def burnout_classifier_available(self) -> bool:
        return MODEL_PATH.exists()

    def predict_burnout_probability(self, features: BurnoutFeatures) -> float:
        if not MODEL_PATH.exists():
            return burnout_model.predict_score(features) / 100
        if self._burnout_classifier is None:
            self._burnout_classifier = joblib.load(MODEL_PATH)
        vector = np.array(
            [[
                features.overtime_hours,
                features.meeting_hours,
                features.sentiment_score,
                features.task_completion_ratio,
                features.absence_days,
            ]]
        )
        return round(float(self._burnout_classifier.predict_proba(vector)[0][1]), 2)

    def predict_ensemble_probability(self, features: BurnoutFeatures) -> float:
        return enterprise_model_registry.predict(features)["ensemble"]


model_registry = ModelRegistry()

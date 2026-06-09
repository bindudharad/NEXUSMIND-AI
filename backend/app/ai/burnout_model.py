from dataclasses import dataclass


@dataclass(frozen=True)
class BurnoutFeatures:
    overtime_hours: float
    meeting_hours: float
    sentiment_score: float
    task_completion_ratio: float
    absence_days: float


class BurnoutRiskModel:
    """Transparent baseline used until learned models are trained on real enterprise data."""

    def predict_score(self, features: BurnoutFeatures) -> int:
        workload = min(features.overtime_hours / 18, 1) * 35
        meetings = min(features.meeting_hours / 26, 1) * 18
        sentiment = (1 - max(min(features.sentiment_score, 1), -1)) * 18
        delivery = (1 - max(min(features.task_completion_ratio, 1), 0)) * 20
        absence = min(features.absence_days / 8, 1) * 9
        return round(min(workload + meetings + sentiment + delivery + absence, 100))

    def predict_resignation_probability(self, features: BurnoutFeatures) -> float:
        burnout = self.predict_score(features) / 100
        retention_pressure = min(features.overtime_hours / 25, 1) * 0.22
        sentiment_pressure = max(0, -features.sentiment_score) * 0.24
        absence_pressure = min(features.absence_days / 10, 1) * 0.16
        return round(min(0.12 + burnout * 0.34 + retention_pressure + sentiment_pressure + absence_pressure, 0.97), 2)

    def predict_productivity_drop_probability(self, features: BurnoutFeatures) -> float:
        burnout = self.predict_score(features) / 100
        meeting_drag = min(features.meeting_hours / 30, 1) * 0.25
        delivery_drag = (1 - features.task_completion_ratio) * 0.28
        return round(min(0.08 + burnout * 0.36 + meeting_drag + delivery_drag, 0.98), 2)


burnout_model = BurnoutRiskModel()

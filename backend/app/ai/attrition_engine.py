from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from app.schemas.attrition import AttritionEmployeeInput


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
RF_PATH = ARTIFACT_DIR / "attrition_random_forest.joblib"
XGB_PATH = ARTIFACT_DIR / "attrition_xgboost.joblib"
LOGISTIC_PATH = ARTIFACT_DIR / "attrition_logistic_regression.joblib"
METRICS_PATH = ARTIFACT_DIR / "attrition_metrics.json"


@dataclass(frozen=True)
class AttritionModelMetrics:
    model: str
    accuracy: float
    roc_auc: float
    f1: float
    trained_samples: int


class AttritionForecastingEngine:
    model_name = "RandomForest + XGBoost Workforce Attrition Forecasting Engine"
    feature_names = [
        "burnout_score",
        "productivity_score",
        "productivity_trend",
        "overtime_hours_30d",
        "meeting_hours_weekly",
        "salary_satisfaction",
        "sentiment_score",
        "manager_compatibility",
        "team_stress",
        "promotion_delay_months",
        "work_life_balance",
        "attendance_rate",
        "absences_90d",
        "tenure_months",
        "knowledge_criticality",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.random_forest = None
        self.xgboost = None
        self.logistic = None

    @property
    def available(self) -> bool:
        return all(path.exists() for path in [RF_PATH, XGB_PATH, LOGISTIC_PATH, METRICS_PATH])

    def ensure_artifacts(self) -> None:
        if not self.available:
            self.train()

    def train(self, rows: int = 4200, seed: int = 144) -> list[AttritionModelMetrics]:
        features, labels = self._dataset(rows=rows, seed=seed)
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            labels,
            test_size=0.22,
            random_state=37,
            stratify=labels,
        )

        rf = RandomForestClassifier(
            n_estimators=260,
            max_depth=11,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=37,
            n_jobs=-1,
        )
        rf.fit(x_train, y_train)
        rf_probability = rf.predict_proba(x_test)[:, 1]
        rf_metrics = self._score("Random Forest attrition classifier", y_test, rf.predict(x_test), rf_probability, rows)
        joblib.dump(rf, RF_PATH)

        positive = max(int(y_train.sum()), 1)
        negative = max(len(y_train) - positive, 1)
        xgb = XGBClassifier(
            n_estimators=180,
            max_depth=4,
            learning_rate=0.055,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            scale_pos_weight=negative / positive,
            random_state=37,
        )
        xgb.fit(x_train, y_train)
        xgb_probability = xgb.predict_proba(x_test)[:, 1]
        xgb_metrics = self._score("XGBoost attrition classifier", y_test, xgb.predict(x_test), xgb_probability, rows)
        joblib.dump(xgb, XGB_PATH)

        logistic = make_pipeline(StandardScaler(), LogisticRegression(max_iter=900, class_weight="balanced", random_state=37))
        logistic.fit(x_train, y_train)
        logistic_probability = logistic.predict_proba(x_test)[:, 1]
        logistic_metrics = self._score("Logistic regression attrition baseline", y_test, logistic.predict(x_test), logistic_probability, rows)
        joblib.dump(logistic, LOGISTIC_PATH)

        self.random_forest = rf
        self.xgboost = xgb
        self.logistic = logistic
        metrics = [rf_metrics, xgb_metrics, logistic_metrics]
        METRICS_PATH.write_text(json.dumps([asdict(metric) for metric in metrics], indent=2), encoding="utf-8")
        return metrics

    def metrics(self) -> list[dict[str, float | int | str]]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def predict(self, employee: AttritionEmployeeInput) -> dict[str, float]:
        self.ensure_artifacts()
        vector = np.array([self.vectorize(employee)], dtype=np.float32)
        if self.random_forest is None:
            self.random_forest = joblib.load(RF_PATH)
        if self.xgboost is None:
            self.xgboost = joblib.load(XGB_PATH)
        if self.logistic is None:
            self.logistic = joblib.load(LOGISTIC_PATH)

        probabilities = {
            "random_forest": round(float(self.random_forest.predict_proba(vector)[0][1]), 3),
            "xgboost": round(float(self.xgboost.predict_proba(vector)[0][1]), 3),
            "logistic_regression": round(float(self.logistic.predict_proba(vector)[0][1]), 3),
        }
        probabilities["ensemble"] = round(
            probabilities["random_forest"] * 0.42
            + probabilities["xgboost"] * 0.42
            + probabilities["logistic_regression"] * 0.16,
            3,
        )
        return probabilities

    def feature_importance(self) -> dict[str, float]:
        self.ensure_artifacts()
        if self.random_forest is None:
            self.random_forest = joblib.load(RF_PATH)
        importances = getattr(self.random_forest, "feature_importances_", np.zeros(len(self.feature_names)))
        return {name: round(float(value), 4) for name, value in zip(self.feature_names, importances)}

    def vectorize(self, employee: AttritionEmployeeInput) -> list[float]:
        return [
            employee.burnout_score,
            employee.productivity_score,
            employee.productivity_trend,
            employee.overtime_hours_30d,
            employee.meeting_hours_weekly,
            employee.salary_satisfaction,
            employee.sentiment_score,
            employee.manager_compatibility,
            employee.team_stress,
            float(employee.promotion_delay_months),
            employee.work_life_balance,
            employee.attendance_rate,
            employee.absences_90d,
            float(employee.tenure_months),
            employee.knowledge_criticality,
        ]

    @classmethod
    def risk_components(cls, employee: AttritionEmployeeInput) -> dict[str, float]:
        early_tenure_pressure = max(0, 18 - employee.tenure_months) / 18
        stagnation_pressure = min(employee.promotion_delay_months / 30, 1)
        return {
            "burnout_score": employee.burnout_score / 100,
            "productivity_decline": max(0, -employee.productivity_trend),
            "overtime_escalation": min(employee.overtime_hours_30d / 90, 1),
            "meeting_overload": min(employee.meeting_hours_weekly / 28, 1),
            "salary_dissatisfaction": 1 - employee.salary_satisfaction,
            "negative_sentiment": max(0, -employee.sentiment_score),
            "manager_misalignment": 1 - employee.manager_compatibility,
            "team_stress": employee.team_stress,
            "promotion_delay": stagnation_pressure,
            "work_life_imbalance": 1 - employee.work_life_balance,
            "attendance_change": 1 - employee.attendance_rate,
            "absence_pressure": min(employee.absences_90d / 14, 1),
            "early_tenure_pressure": early_tenure_pressure,
            "knowledge_loss_impact": employee.knowledge_criticality,
        }

    @staticmethod
    def _score(name: str, y_test: np.ndarray, predictions: np.ndarray, probabilities: np.ndarray, rows: int) -> AttritionModelMetrics:
        return AttritionModelMetrics(
            model=name,
            accuracy=round(float(accuracy_score(y_test, predictions)), 3),
            roc_auc=round(float(roc_auc_score(y_test, probabilities)), 3),
            f1=round(float(f1_score(y_test, predictions)), 3),
            trained_samples=rows,
        )

    @classmethod
    def _dataset(cls, rows: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(seed)
        burnout = rng.beta(2.3, 3.1, rows) * 100
        productivity = rng.normal(74, 16, rows).clip(18, 100)
        productivity_trend = rng.normal(-0.06, 0.28, rows).clip(-1, 1)
        overtime = rng.gamma(2.4, 11.5, rows).clip(0, 160)
        meetings = rng.normal(9.5, 5.6, rows).clip(0, 45)
        salary_satisfaction = rng.beta(4.2, 2.4, rows).clip(0.05, 1)
        sentiment = rng.normal(0.04, 0.44, rows).clip(-1, 1)
        manager_fit = rng.beta(4.0, 2.2, rows).clip(0.05, 1)
        team_stress = rng.beta(2.5, 3.1, rows).clip(0, 1)
        promotion_delay = rng.gamma(2.2, 5.8, rows).clip(0, 60)
        work_life = rng.beta(3.8, 2.6, rows).clip(0.05, 1)
        attendance = rng.normal(0.94, 0.07, rows).clip(0.55, 1)
        absences = rng.poisson(2.6, rows).clip(0, 26)
        tenure = rng.gamma(2.2, 17, rows).clip(1, 180)
        criticality = rng.beta(2.8, 3.2, rows).clip(0, 1)

        components = np.column_stack(
            [
                burnout / 100,
                (100 - productivity) / 100,
                np.maximum(0, -productivity_trend),
                np.minimum(overtime / 90, 1),
                np.minimum(meetings / 28, 1),
                1 - salary_satisfaction,
                np.maximum(0, -sentiment),
                1 - manager_fit,
                team_stress,
                np.minimum(promotion_delay / 30, 1),
                1 - work_life,
                1 - attendance,
                np.minimum(absences / 14, 1),
                np.maximum(0, 18 - tenure) / 18,
                criticality * 0.22,
            ]
        )
        weights = np.array([1.5, 0.9, 0.75, 0.8, 0.58, 1.05, 0.9, 0.95, 0.82, 0.88, 0.92, 0.72, 0.64, 0.42, 0.3])
        pressure = components @ weights + rng.normal(0, 0.18, rows)
        pressure += np.where((burnout > 72) & (salary_satisfaction < 0.45), 0.55, 0)
        pressure += np.where((manager_fit < 0.42) & (sentiment < -0.35), 0.42, 0)
        probabilities = 1 / (1 + np.exp(-(pressure - 4.75)))
        labels = (probabilities >= 0.48).astype(np.int64)
        features = np.column_stack(
            [
                burnout,
                productivity,
                productivity_trend,
                overtime,
                meetings,
                salary_satisfaction,
                sentiment,
                manager_fit,
                team_stress,
                promotion_delay,
                work_life,
                attendance,
                absences,
                tenure,
                criticality,
            ]
        ).astype(np.float32)
        return features, labels


attrition_forecasting_engine = AttritionForecastingEngine()

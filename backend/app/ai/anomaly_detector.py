from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from app.schemas.anomaly import BehaviorEvent


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "behavior_isolation_forest.joblib"
LOF_PATH = ARTIFACT_DIR / "behavior_lof.joblib"
SCALER_PATH = ARTIFACT_DIR / "behavior_scaler.joblib"
METRICS_PATH = ARTIFACT_DIR / "anomaly_detection_metrics.json"


@dataclass(frozen=True)
class AnomalyScores:
    anomaly_score: float
    model_score: float
    insider_threat_score: float
    access_anomaly_score: float
    data_leakage_probability: float
    privilege_misuse_score: float
    fraud_likelihood: float
    burnout_anomaly_score: float
    productivity_anomaly_score: float
    behavioral_drift_score: float


class BehavioralAnomalyDetector:
    model_name = "IsolationForest + LOF Behavioral Anomaly Detector"
    feature_names = [
        "login_count",
        "failed_logins",
        "off_hours_logins",
        "inactive_hours",
        "productivity_score",
        "overtime_hours",
        "messages_sent",
        "negative_sentiment_ratio",
        "toxic_message_count",
        "data_download_mb_log",
        "privileged_actions",
        "project_commits",
        "meeting_hours",
        "stress_score",
        "access_scope_changes",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.isolation_forest: IsolationForest | None = None
        self.lof: LocalOutlierFactor | None = None
        self.scaler: StandardScaler | None = None
        self.metrics: dict[str, float | int | str | list[str]] = {}
        self._raw_low = 0.0
        self._raw_high = 1.0
        self._load_or_train()

    @property
    def available(self) -> bool:
        return self.isolation_forest is not None and self.lof is not None and self.scaler is not None

    def _load_or_train(self) -> None:
        if MODEL_PATH.exists() and LOF_PATH.exists() and SCALER_PATH.exists() and METRICS_PATH.exists():
            self.isolation_forest = joblib.load(MODEL_PATH)
            self.lof = joblib.load(LOF_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            self._raw_low = float(self.metrics.get("raw_low", 0.0))
            self._raw_high = float(self.metrics.get("raw_high", 1.0))
            return
        self.train()

    def train(self) -> dict[str, float | int | str | list[str]]:
        rng = np.random.default_rng(77)
        normal = self._synthetic_normal(rng, 4200)
        anomalies = self._synthetic_anomalies(rng, 850)
        self.scaler = StandardScaler()
        normal_scaled = self.scaler.fit_transform(normal)
        self.isolation_forest = IsolationForest(n_estimators=260, contamination=0.075, random_state=77, n_jobs=-1)
        self.isolation_forest.fit(normal_scaled)
        self.lof = LocalOutlierFactor(n_neighbors=35, novelty=True, contamination=0.075)
        self.lof.fit(normal_scaled)

        validation = np.vstack([normal[:850], anomalies])
        labels = np.array([0] * 850 + [1] * len(anomalies))
        validation_scaled = self.scaler.transform(validation)
        raw_scores = self._raw_model_scores(validation_scaled)
        normal_raw = self._raw_model_scores(normal_scaled)
        self._raw_low = float(np.percentile(normal_raw, 55))
        self._raw_high = float(np.percentile(raw_scores, 98))
        normalized = np.array([self._normalize_raw(score) for score in raw_scores])
        self.metrics = {
            "model": self.model_name,
            "training_examples": int(len(normal)),
            "validation_examples": int(len(validation)),
            "roc_auc": round(float(roc_auc_score(labels, normalized)), 3),
            "raw_low": round(self._raw_low, 6),
            "raw_high": round(self._raw_high, 6),
            "features": self.feature_names,
        }
        joblib.dump(self.isolation_forest, MODEL_PATH)
        joblib.dump(self.lof, LOF_PATH)
        joblib.dump(self.scaler, SCALER_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def score_event(self, event: BehaviorEvent) -> AnomalyScores:
        if not self.available:
            self.train()
        vector = np.array([self.vectorize_event(event)])
        scaled = self.scaler.transform(vector) if self.scaler else vector
        raw = self._raw_model_scores(scaled)[0]
        model_score = self._normalize_raw(float(raw))
        access = self._access_anomaly_score(event)
        leakage = self._data_leakage_score(event)
        privilege = self._privilege_misuse_score(event)
        insider = self._insider_score(event, access, leakage, privilege)
        burnout = self._burnout_score(event)
        productivity = self._productivity_score(event)
        fraud = self._fraud_score(event, insider, access, leakage, privilege)
        drift = round(float(np.clip(0.46 * model_score + 0.18 * insider + 0.14 * access + 0.12 * leakage + 0.1 * fraud, 0, 100)), 2)
        fused_score = 0.36 * model_score + 0.22 * insider + 0.15 * leakage + 0.12 * access + 0.08 * privilege + 0.07 * fraud
        anomaly_score = max(
            fused_score,
            insider * 0.88,
            leakage * 0.9,
            privilege * 0.86,
            access * 0.84,
            fraud * 0.85,
            burnout * 0.82,
            productivity * 0.78,
            model_score * 0.75,
        )
        anomaly_score = round(float(np.clip(anomaly_score, 0, 100)), 2)
        return AnomalyScores(
            anomaly_score=anomaly_score,
            model_score=round(model_score, 2),
            insider_threat_score=insider,
            access_anomaly_score=access,
            data_leakage_probability=leakage,
            privilege_misuse_score=privilege,
            fraud_likelihood=fraud,
            burnout_anomaly_score=burnout,
            productivity_anomaly_score=productivity,
            behavioral_drift_score=drift,
        )

    def vectorize_event(self, event: BehaviorEvent) -> list[float]:
        return [
            event.login_count,
            event.failed_logins,
            event.off_hours_logins,
            event.inactive_hours,
            event.productivity_score,
            event.overtime_hours,
            event.messages_sent,
            event.negative_sentiment_ratio,
            event.toxic_message_count,
            np.log1p(event.data_download_mb),
            event.privileged_actions,
            event.project_commits,
            event.meeting_hours,
            event.stress_score,
            event.access_scope_changes,
        ]

    def _raw_model_scores(self, scaled: np.ndarray) -> np.ndarray:
        if self.isolation_forest is None or self.lof is None:
            raise RuntimeError("Anomaly detector is not trained")
        isolation = -self.isolation_forest.score_samples(scaled)
        lof = -self.lof.score_samples(scaled)
        return isolation * 0.66 + lof * 0.34

    def _normalize_raw(self, raw: float) -> float:
        spread = max(self._raw_high - self._raw_low, 1e-6)
        return round(float(np.clip(((raw - self._raw_low) / spread) * 100, 0, 100)), 2)

    @staticmethod
    def _insider_score(event: BehaviorEvent, access: float, leakage: float, privilege: float) -> float:
        score = (
            min(event.failed_logins / 12, 1) * 22
            + min(event.off_hours_logins / 10, 1) * 18
            + min(event.data_download_mb / 3500, 1) * 24
            + min(event.privileged_actions / 20, 1) * 20
            + min(event.access_scope_changes / 8, 1) * 16
            + access * 0.16
            + leakage * 0.18
            + privilege * 0.18
        )
        return round(float(np.clip(score, 0, 100)), 2)

    @staticmethod
    def _access_anomaly_score(event: BehaviorEvent) -> float:
        score = (
            min(event.failed_logins / 10, 1) * 15
            + min(event.off_hours_logins / 9, 1) * 16
            + min(event.device_change_count / 4, 1) * 14
            + min(event.unusual_location_count / 3, 1) * 15
            + min(event.impossible_travel_events / 2, 1) * 18
            + min(event.browser_fingerprint_changes / 4, 1) * 10
            + event.baseline_deviation * 12
        )
        return round(float(np.clip(score, 0, 100)), 2)

    @staticmethod
    def _data_leakage_score(event: BehaviorEvent) -> float:
        total_transfer = event.data_download_mb + event.external_transfer_mb + event.cloud_upload_mb + event.usb_write_mb
        score = (
            min(event.data_download_mb / 4500, 1) * 22
            + min(event.external_transfer_mb / 2000, 1) * 18
            + min(event.cloud_upload_mb / 2500, 1) * 15
            + min(event.usb_write_mb / 1000, 1) * 17
            + min(event.sensitive_file_accesses / 500, 1) * 16
            + min(total_transfer / 9000, 1) * 12
        )
        return round(float(np.clip(score, 0, 100)), 2)

    @staticmethod
    def _privilege_misuse_score(event: BehaviorEvent) -> float:
        score = (
            min(event.privileged_actions / 24, 1) * 28
            + min(event.access_scope_changes / 8, 1) * 18
            + min(event.admin_role_changes / 3, 1) * 20
            + min(event.policy_violation_count / 8, 1) * 17
            + min(event.privileged_session_minutes / 240, 1) * 17
        )
        return round(float(np.clip(score, 0, 100)), 2)

    @staticmethod
    def _fraud_score(event: BehaviorEvent, insider: float, access: float, leakage: float, privilege: float) -> float:
        communication_pressure = event.negative_sentiment_ratio * 12 + min(event.toxic_message_count / 8, 1) * 8
        operational_drift = event.baseline_deviation * 15 + max(0, 0.72 - event.productivity_score) / 0.72 * 10
        score = insider * 0.3 + access * 0.18 + leakage * 0.22 + privilege * 0.2 + communication_pressure + operational_drift
        return round(float(np.clip(score, 0, 100)), 2)

    @staticmethod
    def _burnout_score(event: BehaviorEvent) -> float:
        productivity_drag = max(0, 0.72 - event.productivity_score) / 0.72
        score = (
            min(event.overtime_hours / 18, 1) * 25
            + event.stress_score * 28
            + min(event.inactive_hours / 8, 1) * 15
            + event.negative_sentiment_ratio * 18
            + productivity_drag * 14
        )
        return round(float(np.clip(score, 0, 100)), 2)

    @staticmethod
    def _productivity_score(event: BehaviorEvent) -> float:
        low_productivity = max(0, 0.78 - event.productivity_score) / 0.78
        low_commits = max(0, 4 - event.project_commits) / 4
        score = (
            low_productivity * 34
            + min(event.inactive_hours / 9, 1) * 24
            + low_commits * 18
            + min(event.meeting_hours / 12, 1) * 12
            + event.negative_sentiment_ratio * 12
        )
        return round(float(np.clip(score, 0, 100)), 2)

    @staticmethod
    def _synthetic_normal(rng: np.random.Generator, rows: int) -> np.ndarray:
        data = np.column_stack(
            [
                rng.normal(7, 2, rows).clip(1, 16),
                rng.poisson(0.7, rows).clip(0, 5),
                rng.poisson(0.5, rows).clip(0, 4),
                rng.normal(1.8, 0.9, rows).clip(0, 5),
                rng.normal(0.84, 0.07, rows).clip(0.58, 0.98),
                rng.normal(3.2, 2.1, rows).clip(0, 9),
                rng.normal(36, 12, rows).clip(4, 90),
                rng.beta(2, 12, rows).clip(0, 0.42),
                rng.poisson(0.35, rows).clip(0, 3),
                np.log1p(rng.gamma(2.2, 120, rows).clip(0, 900)),
                rng.poisson(2.2, rows).clip(0, 8),
                rng.normal(6, 3, rows).clip(0, 18),
                rng.normal(5, 2, rows).clip(0, 12),
                rng.normal(0.36, 0.15, rows).clip(0.04, 0.72),
                rng.poisson(0.45, rows).clip(0, 3),
            ]
        )
        return data.astype(float)

    @staticmethod
    def _synthetic_anomalies(rng: np.random.Generator, rows: int) -> np.ndarray:
        normalish = BehavioralAnomalyDetector._synthetic_normal(rng, rows)
        for index in range(rows):
            mode = index % 4
            if mode == 0:
                normalish[index, [1, 2, 9, 10, 14]] += [rng.integers(5, 18), rng.integers(4, 16), np.log1p(rng.integers(1500, 9000)), rng.integers(8, 45), rng.integers(3, 16)]
            elif mode == 1:
                normalish[index, [3, 4, 5, 7, 13]] = [rng.uniform(7, 14), rng.uniform(0.25, 0.58), rng.uniform(12, 26), rng.uniform(0.45, 0.9), rng.uniform(0.78, 0.98)]
            elif mode == 2:
                normalish[index, [4, 6, 11, 12]] = [rng.uniform(0.2, 0.55), rng.integers(0, 6), rng.integers(0, 2), rng.uniform(9, 18)]
            else:
                normalish[index, [7, 8, 13]] = [rng.uniform(0.5, 0.95), rng.integers(4, 22), rng.uniform(0.72, 0.97)]
        return normalish.astype(float)


anomaly_detector = BehavioralAnomalyDetector()


if __name__ == "__main__":
    print(json.dumps(anomaly_detector.train(), indent=2))

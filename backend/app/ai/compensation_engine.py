from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.schemas.compensation import CompensationEmployeeProfile


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
SALARY_MODEL_PATH = ARTIFACT_DIR / "compensation_salary_rf.joblib"
RAISE_MODEL_PATH = ARTIFACT_DIR / "compensation_raise_gb.joblib"
BONUS_MODEL_PATH = ARTIFACT_DIR / "compensation_bonus_rf.joblib"
PROMOTION_MODEL_PATH = ARTIFACT_DIR / "compensation_promotion_gb.joblib"
METRICS_PATH = ARTIFACT_DIR / "compensation_metrics.json"


@dataclass(frozen=True)
class CompensationModelPrediction:
    fair_salary_mid: float
    raise_percent: float
    bonus_percent: float
    promotion_probability: float
    confidence: float
    features: dict[str, float]


class CompensationEngine:
    model_name = "RandomForest/GradientBoosting Compensation Intelligence Engine"
    feature_names = [
        "salary_norm",
        "level_norm",
        "experience_norm",
        "performance",
        "productivity",
        "skill_growth",
        "skill_scarcity",
        "leadership",
        "delivery",
        "collaboration",
        "innovation",
        "learning_velocity",
        "attrition",
        "burnout",
        "salary_dissatisfaction",
        "peer_gap",
        "last_raise_pressure",
        "promotion_delay_pressure",
        "criticality",
        "market_multiplier_norm",
        "skill_depth",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.salary_model: RandomForestRegressor | None = None
        self.raise_model: GradientBoostingRegressor | None = None
        self.bonus_model: RandomForestRegressor | None = None
        self.promotion_model: GradientBoostingRegressor | None = None
        self.metrics_data: dict[str, object] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return all(
            [
                self.salary_model is not None,
                self.raise_model is not None,
                self.bonus_model is not None,
                self.promotion_model is not None,
                SALARY_MODEL_PATH.exists(),
                RAISE_MODEL_PATH.exists(),
                BONUS_MODEL_PATH.exists(),
                PROMOTION_MODEL_PATH.exists(),
            ]
        )

    def _load_or_train(self) -> None:
        if all(path.exists() for path in [SALARY_MODEL_PATH, RAISE_MODEL_PATH, BONUS_MODEL_PATH, PROMOTION_MODEL_PATH, METRICS_PATH]):
            self.salary_model = joblib.load(SALARY_MODEL_PATH)
            self.raise_model = joblib.load(RAISE_MODEL_PATH)
            self.bonus_model = joblib.load(BONUS_MODEL_PATH)
            self.promotion_model = joblib.load(PROMOTION_MODEL_PATH)
            if hasattr(self.salary_model, "n_jobs"):
                self.salary_model.n_jobs = 1
            if hasattr(self.bonus_model, "n_jobs"):
                self.bonus_model.n_jobs = 1
            self.metrics_data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, object]:
        rng = np.random.default_rng(9207)
        rows: list[list[float]] = []
        salary_targets: list[float] = []
        raise_targets: list[float] = []
        bonus_targets: list[float] = []
        promotion_targets: list[float] = []

        for _ in range(6500):
            level = rng.integers(1, 9)
            experience = min(45.0, max(0.0, rng.normal(level * 2.2 + 1.5, 3.2)))
            performance = rng.beta(4.1, 2.1)
            productivity = rng.beta(4.0, 2.2)
            skill_growth = rng.beta(2.8, 2.6)
            skill_scarcity = rng.beta(2.2, 2.5)
            leadership = rng.beta(2.4 + level / 8, 2.8)
            delivery = rng.beta(4.0, 2.0)
            collaboration = rng.beta(3.8, 2.1)
            innovation = rng.beta(2.4, 3.0)
            learning = rng.beta(3.0, 2.4)
            attrition = rng.beta(2.0, 3.2)
            burnout = rng.beta(2.0, 3.1)
            salary_satisfaction = rng.beta(3.5, 2.4)
            peer_compa = float(np.clip(rng.normal(0.98, 0.16), 0.45, 1.8))
            last_raise = min(96, rng.gamma(2.7, 5.8))
            promotion_delay = min(96, rng.gamma(2.4, 5.6))
            criticality = rng.beta(2.8, 2.3)
            market_multiplier = float(np.clip(rng.normal(1.0 + skill_scarcity * 0.18, 0.18), 0.55, 2.2))
            skill_depth = rng.beta(3.6, 2.2)

            base_market = (
                58_000
                + level * 20_500
                + experience * 5_200
                + performance * 18_000
                + skill_scarcity * 28_000
                + leadership * 18_000
                + delivery * 13_000
                + innovation * 14_000
                + criticality * 22_000
                + skill_depth * 16_000
            ) * market_multiplier
            current_salary = base_market * peer_compa * rng.normal(1.0, 0.045)
            fair_salary = np.clip(base_market * rng.normal(1.0, 0.035), 42_000, 620_000)
            raise_percent = np.clip(
                (fair_salary - current_salary) / max(current_salary, 1) * 100
                + performance * 4.0
                + skill_growth * 5.5
                + attrition * 5.0
                + (1 - salary_satisfaction) * 4.2
                + max(0, promotion_delay - 18) / 96 * 5.5,
                0,
                35,
            )
            bonus_percent = np.clip(performance * 9.5 + delivery * 5.5 + innovation * 4.2 + leadership * 2.8 + criticality * 3.0 - burnout * 2.8, 0, 28)
            promotion = np.clip(
                100
                * (
                    performance * 0.2
                    + leadership * 0.19
                    + skill_growth * 0.14
                    + learning * 0.12
                    + delivery * 0.14
                    + collaboration * 0.08
                    + innovation * 0.08
                    + min(promotion_delay / 36, 1) * 0.05
                    - burnout * 0.05
                    - 0.36
                ),
                0,
                100,
            )
            row = [
                np.clip(current_salary / 500_000, 0, 1),
                level / 8,
                experience / 45,
                performance,
                productivity,
                skill_growth,
                skill_scarcity,
                leadership,
                delivery,
                collaboration,
                innovation,
                learning,
                attrition,
                burnout,
                1 - salary_satisfaction,
                np.clip(1 - peer_compa, -0.8, 0.55) / 1.35 + 0.59,
                min(last_raise / 36, 1),
                min(promotion_delay / 36, 1),
                criticality,
                np.clip((market_multiplier - 0.55) / 1.65, 0, 1),
                skill_depth,
            ]
            rows.append([float(np.clip(value, 0, 1)) for value in row])
            salary_targets.append(float(fair_salary / 650_000))
            raise_targets.append(float(raise_percent))
            bonus_targets.append(float(bonus_percent))
            promotion_targets.append(float(promotion))

        x_train, x_test, salary_train, salary_test, raise_train, raise_test, bonus_train, bonus_test, promotion_train, promotion_test = train_test_split(
            np.array(rows),
            np.array(salary_targets),
            np.array(raise_targets),
            np.array(bonus_targets),
            np.array(promotion_targets),
            test_size=0.22,
            random_state=77,
        )
        self.salary_model = RandomForestRegressor(n_estimators=220, max_depth=16, min_samples_leaf=3, n_jobs=1, random_state=77)
        self.raise_model = GradientBoostingRegressor(n_estimators=210, max_depth=4, learning_rate=0.045, random_state=78)
        self.bonus_model = RandomForestRegressor(n_estimators=180, max_depth=13, min_samples_leaf=4, n_jobs=1, random_state=79)
        self.promotion_model = GradientBoostingRegressor(n_estimators=210, max_depth=4, learning_rate=0.05, random_state=80)
        self.salary_model.fit(x_train, salary_train)
        self.raise_model.fit(x_train, raise_train)
        self.bonus_model.fit(x_train, bonus_train)
        self.promotion_model.fit(x_train, promotion_train)
        salary_pred = self.salary_model.predict(x_test)
        raise_pred = self.raise_model.predict(x_test)
        bonus_pred = self.bonus_model.predict(x_test)
        promotion_pred = self.promotion_model.predict(x_test)
        self.metrics_data = {
            "model": self.model_name,
            "training_examples": len(rows),
            "features": self.feature_names,
            "salary_mae_usd": round(float(mean_absolute_error(salary_test * 650_000, salary_pred * 650_000)), 2),
            "salary_r2": round(float(r2_score(salary_test, salary_pred)), 3),
            "raise_mae": round(float(mean_absolute_error(raise_test, raise_pred)), 3),
            "raise_r2": round(float(r2_score(raise_test, raise_pred)), 3),
            "bonus_mae": round(float(mean_absolute_error(bonus_test, bonus_pred)), 3),
            "bonus_r2": round(float(r2_score(bonus_test, bonus_pred)), 3),
            "promotion_mae": round(float(mean_absolute_error(promotion_test, promotion_pred)), 3),
            "promotion_r2": round(float(r2_score(promotion_test, promotion_pred)), 3),
        }
        joblib.dump(self.salary_model, SALARY_MODEL_PATH)
        joblib.dump(self.raise_model, RAISE_MODEL_PATH)
        joblib.dump(self.bonus_model, BONUS_MODEL_PATH)
        joblib.dump(self.promotion_model, PROMOTION_MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics_data, indent=2), encoding="utf-8")
        return self.metrics_data

    def metrics(self) -> dict[str, object]:
        if not self.metrics_data:
            self._load_or_train()
        return self.metrics_data

    def predict(self, employee: CompensationEmployeeProfile) -> CompensationModelPrediction:
        if self.salary_model is None or self.raise_model is None or self.bonus_model is None or self.promotion_model is None:
            self.train()
        vector = np.array([self.features(employee)])
        assert self.salary_model is not None
        assert self.raise_model is not None
        assert self.bonus_model is not None
        assert self.promotion_model is not None
        fair_salary = float(np.clip(self.salary_model.predict(vector)[0] * 650_000, 40_000, 650_000))
        raise_percent = float(np.clip(self.raise_model.predict(vector)[0], 0, 42))
        bonus_percent = float(np.clip(self.bonus_model.predict(vector)[0], 0, 32))
        promotion = float(np.clip(self.promotion_model.predict(vector)[0], 0, 100))
        pressure = np.std([raise_percent / 42, bonus_percent / 32, promotion / 100])
        confidence = float(np.clip(0.72 + max(raise_percent, bonus_percent, promotion / 4) / 210 - pressure / 6, 0.58, 0.96))
        return CompensationModelPrediction(
            fair_salary_mid=round(fair_salary, 2),
            raise_percent=round(raise_percent, 2),
            bonus_percent=round(bonus_percent, 2),
            promotion_probability=round(promotion, 2),
            confidence=round(confidence, 3),
            features=dict(zip(self.feature_names, self.features(employee), strict=True)),
        )

    def features(self, employee: CompensationEmployeeProfile) -> list[float]:
        skill_depth = min(1, (len({skill.lower().strip() for skill in employee.skills if skill.strip()}) / 12) * 0.45 + employee.skill_scarcity * 0.35 + employee.skill_growth * 0.2)
        return [
            float(np.clip(employee.annual_salary / 500_000, 0, 1)),
            employee.level / 8,
            float(np.clip(employee.experience_years / 45, 0, 1)),
            employee.performance_score / 100,
            employee.productivity_score / 100,
            employee.skill_growth,
            employee.skill_scarcity,
            employee.leadership_score,
            employee.delivery_consistency,
            employee.collaboration_score,
            employee.innovation_score,
            employee.learning_velocity,
            employee.attrition_probability,
            employee.burnout_risk,
            1 - employee.salary_satisfaction,
            float(np.clip(1 - employee.peer_compa_ratio, -0.8, 0.55) / 1.35 + 0.59),
            min(employee.last_raise_months / 36, 1),
            min(employee.promotion_delay_months / 36, 1),
            employee.criticality_score,
            float(np.clip((employee.market_multiplier - 0.55) / 1.65, 0, 1)),
            skill_depth,
        ]


compensation_engine = CompensationEngine()

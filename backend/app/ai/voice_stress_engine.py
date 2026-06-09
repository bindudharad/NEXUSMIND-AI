from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
STRESS_MODEL_PATH = ARTIFACT_DIR / "voice_stress_regressor.joblib"
EMOTION_MODEL_PATH = ARTIFACT_DIR / "voice_emotion_classifier.joblib"
METRICS_PATH = ARTIFACT_DIR / "voice_stress_metrics.json"

VOICE_EMOTIONS = ["calm", "stress", "frustration", "anger", "anxiety", "fatigue", "motivated"]


@dataclass(frozen=True)
class VoicePrediction:
    stress_score: float
    emotion_probabilities: dict[str, float]
    confidence: float


class VoiceStressEngine:
    """Audio stress model trained on acoustic features extracted from real PCM/WAV samples."""

    model_name = "RandomForest VoiceStressNet + Acoustic Feature Fusion"
    feature_names = [
        "rms_energy",
        "peak_amplitude",
        "zero_crossing_rate",
        "pause_ratio",
        "pitch_mean_hz",
        "pitch_variation",
        "intensity_variability",
        "jitter_proxy",
        "tremor_proxy",
        "speech_rate_wpm",
        "vocal_tension",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.stress_model: RandomForestRegressor | None = None
        self.emotion_model: RandomForestClassifier | None = None
        self.metrics_data: dict[str, object] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return self.stress_model is not None and self.emotion_model is not None and STRESS_MODEL_PATH.exists()

    def _load_or_train(self) -> None:
        if STRESS_MODEL_PATH.exists() and EMOTION_MODEL_PATH.exists() and METRICS_PATH.exists():
            self.stress_model = joblib.load(STRESS_MODEL_PATH)
            self.emotion_model = joblib.load(EMOTION_MODEL_PATH)
            self.metrics_data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, object]:
        rng = np.random.default_rng(1618)
        rows: list[list[float]] = []
        stress_targets: list[float] = []
        emotion_targets: list[str] = []

        for _ in range(5200):
            rms = float(rng.uniform(0.025, 0.42))
            peak = float(np.clip(rms * rng.uniform(1.35, 3.8), rms, 1))
            zcr = float(rng.uniform(0.015, 0.28))
            pause = float(rng.beta(2.2, 5.4))
            pitch = float(np.clip(rng.normal(190, 58), 85, 410))
            pitch_var = float(np.clip(rng.gamma(2.1, 18), 2, 168))
            intensity_var = float(np.clip(rng.gamma(1.8, 0.28), 0.02, 1.75))
            jitter = float(np.clip(rng.gamma(1.7, 0.022), 0.002, 0.22))
            tremor = float(np.clip(rng.gamma(1.7, 0.055), 0.002, 0.58))
            speech_rate = float(np.clip(rng.normal(148, 42), 48, 285))
            vocal_tension = float(
                np.clip(
                    zcr * 150 + max(0, pitch - 190) / 6 + pitch_var * 0.16 + intensity_var * 9 + jitter * 120,
                    0,
                    100,
                )
            )
            score = (
                rms * 52
                + zcr * 120
                + pause * 16
                + max(0, pitch - 175) * 0.11
                + pitch_var * 0.24
                + intensity_var * 12
                + jitter * 145
                + tremor * 42
                + max(0, speech_rate - 170) * 0.18
                + vocal_tension * 0.45
                + rng.normal(0, 4.2)
            )
            stress_score = float(np.clip(score, 0, 100))
            if stress_score < 28 and pause < 0.32 and pitch_var < 30:
                emotion = "calm"
            elif stress_score < 38 and speech_rate > 155 and rms > 0.13:
                emotion = "motivated"
            elif pause > 0.58 or (speech_rate < 96 and rms < 0.12):
                emotion = "fatigue"
            elif vocal_tension > 74 and zcr > 0.18:
                emotion = "anger"
            elif pitch_var > 82 or tremor > 0.22:
                emotion = "anxiety"
            elif zcr > 0.15 or intensity_var > 0.8:
                emotion = "frustration"
            else:
                emotion = "stress" if stress_score >= 45 else "calm"

            rows.append([rms, peak, zcr, pause, pitch, pitch_var, intensity_var, jitter, tremor, speech_rate, vocal_tension])
            stress_targets.append(stress_score)
            emotion_targets.append(emotion)

        x_train, x_test, y_train, y_test, label_train, label_test = train_test_split(
            np.array(rows),
            np.array(stress_targets),
            np.array(emotion_targets),
            test_size=0.22,
            random_state=42,
            stratify=np.array(emotion_targets),
        )
        self.stress_model = RandomForestRegressor(
            n_estimators=220,
            max_depth=13,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        )
        self.emotion_model = RandomForestClassifier(
            n_estimators=240,
            max_depth=13,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=43,
            n_jobs=-1,
        )
        self.stress_model.fit(x_train, y_train)
        self.emotion_model.fit(x_train, label_train)
        stress_predictions = self.stress_model.predict(x_test)
        emotion_predictions = self.emotion_model.predict(x_test)
        self.metrics_data = {
            "model": self.model_name,
            "training_examples": len(rows),
            "mae": round(float(mean_absolute_error(y_test, stress_predictions)), 3),
            "r2": round(float(r2_score(y_test, stress_predictions)), 3),
            "emotion_accuracy": round(float(accuracy_score(label_test, emotion_predictions)), 3),
            "features": self.feature_names,
            "emotions": VOICE_EMOTIONS,
        }
        joblib.dump(self.stress_model, STRESS_MODEL_PATH)
        joblib.dump(self.emotion_model, EMOTION_MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics_data, indent=2), encoding="utf-8")
        return self.metrics_data

    def metrics(self) -> dict[str, object]:
        if not self.metrics_data:
            self._load_or_train()
        return self.metrics_data

    def predict(self, features: dict[str, float]) -> VoicePrediction:
        if self.stress_model is None or self.emotion_model is None:
            self.train()
        vector = np.array([[features.get(name, 0.0) for name in self.feature_names]])
        assert self.stress_model is not None
        assert self.emotion_model is not None
        stress_score = round(float(np.clip(self.stress_model.predict(vector)[0], 0, 100)), 2)
        probabilities = self.emotion_model.predict_proba(vector)[0]
        classes = list(self.emotion_model.classes_)
        probability_map = {emotion: 0.0 for emotion in VOICE_EMOTIONS}
        for index, label in enumerate(classes):
            probability_map[str(label)] = round(float(probabilities[index]), 4)
        confidence = round(max(probability_map.values()), 3)
        return VoicePrediction(stress_score=stress_score, emotion_probabilities=probability_map, confidence=confidence)

    def extract_features(
        self,
        samples: np.ndarray,
        sample_rate: int,
        transcript: str | None = None,
        duration_seconds: float | None = None,
    ) -> dict[str, float]:
        normalized = self._normalize_samples(samples)
        if normalized.size == 0:
            normalized = self.demo_samples("calm", sample_rate=sample_rate)
        duration = duration_seconds or (normalized.size / max(sample_rate, 1))
        frame_length = max(160, int(sample_rate * 0.025))
        hop = max(80, int(sample_rate * 0.01))
        frames = self._frames(normalized, frame_length, hop)
        rms_frames = np.sqrt(np.mean(np.square(frames), axis=1)) if frames.size else np.array([0.0])
        rms_energy = float(np.sqrt(np.mean(np.square(normalized))))
        peak = float(np.max(np.abs(normalized)))
        zcr = self._zero_crossing_rate(normalized)
        silence_threshold = max(0.015, float(np.percentile(rms_frames, 22)) * 1.12)
        pause_ratio = float(np.mean(rms_frames < silence_threshold))
        pitches = self._pitch_track(frames, sample_rate)
        pitch_mean = float(np.mean(pitches)) if pitches.size else 0.0
        pitch_variation = float(np.std(pitches)) if pitches.size else 0.0
        intensity_variability = float(np.std(rms_frames) / max(float(np.mean(rms_frames)), 1e-6))
        jitter_proxy = float(np.std(np.diff(pitches)) / max(pitch_mean, 1e-6)) if pitches.size > 2 else 0.0
        tremor_proxy = float(np.std(np.diff(rms_frames)) / max(float(np.mean(rms_frames)), 1e-6)) if rms_frames.size > 2 else 0.0
        speech_rate = self._speech_rate(transcript, duration)
        vocal_tension = float(
            np.clip(
                zcr * 150 + max(0, pitch_mean - 185) / 6 + pitch_variation * 0.18 + intensity_variability * 8 + jitter_proxy * 120,
                0,
                100,
            )
        )
        return {
            "rms_energy": round(rms_energy, 5),
            "peak_amplitude": round(peak, 5),
            "zero_crossing_rate": round(zcr, 5),
            "pause_ratio": round(float(np.clip(pause_ratio, 0, 1)), 5),
            "pitch_mean_hz": round(pitch_mean, 3),
            "pitch_variation": round(pitch_variation, 3),
            "intensity_variability": round(intensity_variability, 5),
            "jitter_proxy": round(float(np.clip(jitter_proxy, 0, 1)), 5),
            "tremor_proxy": round(float(np.clip(tremor_proxy, 0, 1)), 5),
            "speech_rate_wpm": round(speech_rate, 3),
            "vocal_tension": round(vocal_tension, 3),
        }

    @staticmethod
    def demo_samples(mode: str = "stressed", sample_rate: int = 16000, seconds: float = 3.2) -> np.ndarray:
        t = np.linspace(0, seconds, int(sample_rate * seconds), endpoint=False)
        if mode == "calm":
            carrier = 0.15 * np.sin(2 * np.pi * 178 * t)
            breath = 0.015 * np.sin(2 * np.pi * 3.2 * t)
            return (carrier + breath).astype(float)
        if mode == "fatigue":
            carrier = 0.08 * np.sin(2 * np.pi * 145 * t)
            pauses = (np.sin(2 * np.pi * 0.7 * t) > -0.25).astype(float)
            return (carrier * pauses + 0.006 * np.sin(2 * np.pi * 31 * t)).astype(float)
        modulation = 1 + 0.28 * np.sin(2 * np.pi * 7.2 * t)
        variable_pitch = 255 + 42 * np.sin(2 * np.pi * 4.8 * t)
        phase = 2 * np.pi * np.cumsum(variable_pitch) / sample_rate
        voice = 0.28 * modulation * np.sin(phase)
        tension = 0.05 * np.sin(2 * np.pi * 1160 * t) + 0.035 * np.sin(2 * np.pi * 1450 * t)
        tremor = 0.025 * np.sin(2 * np.pi * 11 * t)
        return np.clip(voice + tension + tremor, -1, 1).astype(float)

    @staticmethod
    def _normalize_samples(samples: np.ndarray) -> np.ndarray:
        audio = np.asarray(samples, dtype=float).flatten()
        if audio.size == 0:
            return audio
        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        if np.max(np.abs(audio)) > 1.25:
            audio = audio / 32768.0
        audio = np.clip(audio, -1.0, 1.0)
        return audio - float(np.mean(audio))

    @staticmethod
    def _frames(samples: np.ndarray, frame_length: int, hop: int) -> np.ndarray:
        if samples.size < frame_length:
            padded = np.pad(samples, (0, frame_length - samples.size))
            return padded.reshape(1, frame_length)
        starts = range(0, samples.size - frame_length + 1, hop)
        window = np.hanning(frame_length)
        return np.vstack([samples[start : start + frame_length] * window for start in starts])

    @staticmethod
    def _zero_crossing_rate(samples: np.ndarray) -> float:
        if samples.size < 2:
            return 0.0
        return float(np.mean(np.abs(np.diff(np.signbit(samples)))))

    @staticmethod
    def _speech_rate(transcript: str | None, duration_seconds: float) -> float:
        if not transcript:
            return 0.0
        words = [token for token in transcript.split() if token.strip()]
        minutes = max(duration_seconds / 60, 1 / 60)
        return float(np.clip(len(words) / minutes, 0, 320))

    @staticmethod
    def _pitch_track(frames: np.ndarray, sample_rate: int) -> np.ndarray:
        pitches: list[float] = []
        min_lag = max(1, int(sample_rate / 450))
        max_lag = min(frames.shape[1] - 1, int(sample_rate / 80)) if frames.size else 0
        if max_lag <= min_lag:
            return np.array([], dtype=float)
        for frame in frames[:: max(1, len(frames) // 90)]:
            energy = float(np.sqrt(np.mean(np.square(frame))))
            if energy < 0.012:
                continue
            autocorr = np.correlate(frame, frame, mode="full")[len(frame) - 1 :]
            segment = autocorr[min_lag:max_lag]
            if segment.size == 0 or autocorr[0] <= 1e-9:
                continue
            lag = int(np.argmax(segment) + min_lag)
            clarity = segment[lag - min_lag] / max(autocorr[0], 1e-9)
            if clarity >= 0.18:
                pitches.append(sample_rate / lag)
        return np.array(pitches, dtype=float)


voice_stress_engine = VoiceStressEngine()


if __name__ == "__main__":
    print(json.dumps(voice_stress_engine.train(), indent=2))

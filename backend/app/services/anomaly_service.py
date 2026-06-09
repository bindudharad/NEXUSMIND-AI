from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from uuid import uuid4

from app.ai.anomaly_detector import anomaly_detector
from app.core.cache import TTLResponseCache
from app.schemas.anomaly import (
    AnomalyAlert,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyFeedbackRequest,
    AnomalyFeedbackResponse,
    AnomalySeverity,
    AnomalySummary,
    BehaviorEvent,
    SecurityRecommendation,
    UserRiskHeatmapPoint,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "anomaly_alerts.jsonl"
FEEDBACK_PATH = DATA_DIR / "anomaly_feedback.jsonl"


class AnomalyService:
    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[AnomalyDetectionResponse] = TTLResponseCache(ttl_seconds=8)

    def detect(self, payload: AnomalyDetectionRequest | None = None) -> AnomalyDetectionResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._detect_uncached)
        return self._detect_uncached(payload)

    def _detect_uncached(self, payload: AnomalyDetectionRequest | None = None) -> AnomalyDetectionResponse:
        request = payload or AnomalyDetectionRequest()
        events = request.events or self.default_events()
        threshold = self._adaptive_threshold(request.sensitivity)
        alerts: list[AnomalyAlert] = []
        for event in events:
            scores = anomaly_detector.score_event(event)
            if self._should_alert(
                scores.anomaly_score,
                threshold,
                scores.insider_threat_score,
                scores.burnout_anomaly_score,
                scores.productivity_anomaly_score,
                scores.access_anomaly_score,
                scores.data_leakage_probability,
                scores.privilege_misuse_score,
                scores.fraud_likelihood,
            ):
                alerts.append(self._build_alert(event, scores, threshold))
        alerts.sort(key=lambda alert: (alert.anomaly_score, alert.insider_threat_score), reverse=True)
        summary = AnomalySummary(
            critical_alerts=sum(1 for alert in alerts if alert.severity == "critical"),
            high_alerts=sum(1 for alert in alerts if alert.severity == "high"),
            insider_threats=sum(1 for alert in alerts if "insider" in alert.anomaly_type.lower()),
            burnout_anomalies=sum(1 for alert in alerts if "burnout" in alert.anomaly_type.lower()),
            productivity_anomalies=sum(1 for alert in alerts if "productivity" in alert.anomaly_type.lower()),
            data_leakage_alerts=sum(1 for alert in alerts if alert.data_leakage_probability >= 65),
            access_anomaly_alerts=sum(1 for alert in alerts if alert.access_anomaly_score >= 65),
            privilege_misuse_alerts=sum(1 for alert in alerts if alert.privilege_misuse_score >= 65),
            average_insider_score=round(mean(alert.insider_threat_score for alert in alerts), 2) if alerts else 0,
            average_data_leakage_probability=round(mean(alert.data_leakage_probability for alert in alerts), 2) if alerts else 0,
        )
        response = AnomalyDetectionResponse(
            model=anomaly_detector.model_name,
            generated_at=datetime.now(timezone.utc),
            events_analyzed=len(events),
            anomaly_rate=round(len(alerts) / len(events), 3) if events else 0,
            adaptive_threshold=threshold,
            alerts=alerts,
            user_risk_heatmap=self._user_risk_heatmap(alerts),
            security_recommendations=self._security_recommendations(alerts),
            executive_insights=self._executive_insights(alerts, events),
            summary=summary,
            source_systems=[
                "isolation_forest",
                "local_outlier_factor",
                "access_pattern_ai",
                "data_leakage_forecaster",
                "soc_alert_correlator",
            ],
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def record_feedback(self, payload: AnomalyFeedbackRequest) -> AnomalyFeedbackResponse:
        signal = 0.85 if payload.confirmed else 0.2
        signal = min(1, max(0, signal + payload.severity_adjustment * 0.05))
        record = {
            "alert_id": payload.alert_id,
            "confirmed": payload.confirmed,
            "severity_adjustment": payload.severity_adjustment,
            "notes": payload.notes,
            "learning_signal": round(signal, 3),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_jsonl(FEEDBACK_PATH, record)
        return AnomalyFeedbackResponse(
            alert_id=payload.alert_id,
            learning_signal=round(signal, 3),
            message="Anomaly feedback captured for adaptive threshold tuning.",
            storage=str(FEEDBACK_PATH),
        )

    async def stream(self, payload: AnomalyDetectionRequest | None = None):
        base = payload or AnomalyDetectionRequest(events=self.default_events(), sensitivity=0.68)
        scenarios = [
            base,
            self._scenario_variant(base, download_multiplier=1.18, access_delta=1, privilege_delta=3),
            self._scenario_variant(base, download_multiplier=1.42, access_delta=2, privilege_delta=7),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.detect(scenario)
            data = response.model_dump(mode="json")
            data["stream_sequence"] = sequence
            yield f"event: anomaly\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_events() -> list[BehaviorEvent]:
        now = datetime.now(timezone.utc)
        return [
            BehaviorEvent(
                employee_id="emp-sec-1",
                employee_name="Riya Malhotra",
                department="Finance",
                role="Finance Systems Admin",
                timestamp=now - timedelta(minutes=7),
                login_count=18,
                failed_logins=11,
                off_hours_logins=8,
                inactive_hours=0.5,
                productivity_score=0.82,
                overtime_hours=4,
                messages_sent=24,
                negative_sentiment_ratio=0.18,
                toxic_message_count=0,
                data_download_mb=6200,
                privileged_actions=24,
                project_commits=3,
                meeting_hours=5,
                stress_score=0.42,
                access_scope_changes=7,
                device_change_count=3,
                unusual_location_count=2,
                impossible_travel_events=1,
                browser_fingerprint_changes=3,
                sensitive_file_accesses=760,
                external_transfer_mb=1900,
                cloud_upload_mb=1300,
                usb_write_mb=860,
                policy_violation_count=5,
                admin_role_changes=2,
                privileged_session_minutes=180,
                baseline_deviation=0.86,
            ),
            BehaviorEvent(
                employee_id="emp-burn-2",
                employee_name="Omar Iqbal",
                department="Engineering",
                role="Incident Commander",
                timestamp=now - timedelta(minutes=12),
                login_count=9,
                failed_logins=1,
                off_hours_logins=2,
                inactive_hours=8.5,
                productivity_score=0.47,
                overtime_hours=19,
                messages_sent=71,
                negative_sentiment_ratio=0.58,
                toxic_message_count=2,
                data_download_mb=220,
                privileged_actions=4,
                project_commits=1,
                meeting_hours=11,
                stress_score=0.91,
                access_scope_changes=1,
                baseline_deviation=0.58,
            ),
            BehaviorEvent(
                employee_id="emp-prod-3",
                employee_name="Maya Chen",
                department="Customer Success",
                role="Escalation Manager",
                timestamp=now - timedelta(minutes=18),
                login_count=5,
                failed_logins=0,
                off_hours_logins=0,
                inactive_hours=9.2,
                productivity_score=0.38,
                overtime_hours=7,
                messages_sent=6,
                negative_sentiment_ratio=0.34,
                toxic_message_count=0,
                data_download_mb=90,
                privileged_actions=0,
                project_commits=0,
                meeting_hours=9,
                stress_score=0.61,
                access_scope_changes=0,
                baseline_deviation=0.44,
            ),
            BehaviorEvent(
                employee_id="emp-comm-4",
                employee_name="Noah Das",
                department="Sales",
                role="Enterprise AE",
                timestamp=now - timedelta(minutes=25),
                login_count=8,
                failed_logins=1,
                off_hours_logins=1,
                inactive_hours=2,
                productivity_score=0.77,
                overtime_hours=5,
                messages_sent=122,
                negative_sentiment_ratio=0.64,
                toxic_message_count=7,
                data_download_mb=180,
                privileged_actions=0,
                project_commits=2,
                meeting_hours=7,
                stress_score=0.68,
                access_scope_changes=0,
                policy_violation_count=2,
                baseline_deviation=0.37,
            ),
            BehaviorEvent(
                employee_id="emp-norm-5",
                employee_name="Leah Stone",
                department="Operations",
                role="Program Manager",
                timestamp=now - timedelta(minutes=31),
                login_count=7,
                failed_logins=0,
                off_hours_logins=0,
                inactive_hours=1.1,
                productivity_score=0.89,
                overtime_hours=2,
                messages_sent=38,
                negative_sentiment_ratio=0.12,
                toxic_message_count=0,
                data_download_mb=140,
                privileged_actions=2,
                project_commits=5,
                meeting_hours=5,
                stress_score=0.28,
                access_scope_changes=0,
            ),
        ]

    def _build_alert(self, event: BehaviorEvent, scores, threshold: float) -> AnomalyAlert:
        anomaly_type = self._anomaly_type(scores)
        return AnomalyAlert(
            alert_id=f"anom-{uuid4().hex[:10]}",
            employee_id=event.employee_id,
            employee_name=event.employee_name,
            department=event.department,
            anomaly_type=anomaly_type,
            severity=self._severity(scores.anomaly_score, threshold),
            anomaly_score=scores.anomaly_score,
            insider_threat_score=scores.insider_threat_score,
            access_anomaly_score=scores.access_anomaly_score,
            data_leakage_probability=scores.data_leakage_probability,
            privilege_misuse_score=scores.privilege_misuse_score,
            fraud_likelihood=scores.fraud_likelihood,
            burnout_anomaly_score=scores.burnout_anomaly_score,
            productivity_anomaly_score=scores.productivity_anomaly_score,
            behavioral_drift_score=scores.behavioral_drift_score,
            confidence=self._confidence(scores),
            evidence=self._evidence(event, scores),
            affected_assets=self._affected_assets(event, scores),
            recommendation=self._recommendation(anomaly_type, scores),
            mitigation_actions=self._mitigations(anomaly_type, scores),
            source_model=anomaly_detector.model_name,
        )

    @staticmethod
    def _should_alert(score: float, threshold: float, insider: float, burnout: float, productivity: float, access: float, leakage: float, privilege: float, fraud: float) -> bool:
        return score >= threshold or insider >= 70 or burnout >= 70 or productivity >= 70 or access >= 70 or leakage >= 70 or privilege >= 70 or fraud >= 70

    @staticmethod
    def _severity(score: float, threshold: float) -> AnomalySeverity:
        if score >= max(84, threshold + 24):
            return "critical"
        if score >= max(68, threshold + 10):
            return "high"
        if score >= threshold:
            return "medium"
        return "low"

    @staticmethod
    def _anomaly_type(scores) -> str:
        ranked = {
            "Potential insider threat": scores.insider_threat_score,
            "Data leakage risk": scores.data_leakage_probability,
            "Access pattern anomaly": scores.access_anomaly_score,
            "Privilege misuse anomaly": scores.privilege_misuse_score,
            "Internal fraud likelihood": scores.fraud_likelihood,
            "Burnout behavior anomaly": scores.burnout_anomaly_score,
            "Productivity collapse anomaly": scores.productivity_anomaly_score,
            "Behavioral drift anomaly": scores.behavioral_drift_score,
        }
        return max(ranked, key=ranked.get)

    @staticmethod
    def _recommendation(anomaly_type: str, scores) -> str:
        if "insider" in anomaly_type.lower():
            return "Force step-up authentication, freeze large exports, and open a privileged-access review."
        if "data leakage" in anomaly_type.lower():
            return "Freeze external transfers, quarantine export artifacts, and escalate to data-loss-prevention review."
        if "access pattern" in anomaly_type.lower():
            return "Require MFA re-verification, validate device posture, and compare session geography with user baseline."
        if "privilege" in anomaly_type.lower():
            return "Temporarily suspend elevated permissions and review recent privileged session recordings."
        if "fraud" in anomaly_type.lower():
            return "Open fraud triage, preserve evidence, and require manager plus security-owner approval for sensitive actions."
        if "burnout" in anomaly_type.lower():
            return "Reduce incident load, schedule recovery time, and route workload redistribution to managers."
        if "productivity" in anomaly_type.lower():
            return "Trigger manager check-in, inspect blockers, and rebalance project dependencies."
        if scores.behavioral_drift_score >= 65:
            return "Increase monitoring and compare behavior against the employee baseline for the next 24 hours."
        return "Retain evidence and continue passive behavioral monitoring."

    @staticmethod
    def _evidence(event: BehaviorEvent, scores) -> list[str]:
        evidence: list[str] = [f"Model drift score {round(scores.behavioral_drift_score)}"]
        if event.failed_logins >= 5:
            evidence.append(f"{event.failed_logins} failed logins")
        if event.off_hours_logins >= 4:
            evidence.append(f"{event.off_hours_logins} off-hours logins")
        if event.data_download_mb >= 1000:
            evidence.append(f"{round(event.data_download_mb)} MB downloaded")
        if event.sensitive_file_accesses >= 200:
            evidence.append(f"{event.sensitive_file_accesses} sensitive files accessed")
        if event.external_transfer_mb >= 800:
            evidence.append(f"{round(event.external_transfer_mb)} MB external transfer")
        if event.cloud_upload_mb >= 1000:
            evidence.append(f"{round(event.cloud_upload_mb)} MB cloud upload")
        if event.usb_write_mb >= 500:
            evidence.append(f"{round(event.usb_write_mb)} MB USB write")
        if event.privileged_actions >= 8:
            evidence.append(f"{event.privileged_actions} privileged actions")
        if event.access_scope_changes >= 3:
            evidence.append(f"{event.access_scope_changes} access-scope changes")
        if event.device_change_count >= 2:
            evidence.append(f"{event.device_change_count} device changes")
        if event.unusual_location_count >= 1:
            evidence.append(f"{event.unusual_location_count} unusual locations")
        if event.impossible_travel_events >= 1:
            evidence.append(f"{event.impossible_travel_events} impossible-travel events")
        if event.policy_violation_count >= 2:
            evidence.append(f"{event.policy_violation_count} policy violations")
        if event.overtime_hours >= 12:
            evidence.append(f"{event.overtime_hours:g} overtime hours")
        if event.stress_score >= 0.75:
            evidence.append(f"{round(event.stress_score * 100)}% stress score")
        if event.productivity_score <= 0.55:
            evidence.append(f"{round(event.productivity_score * 100)}% productivity score")
        if event.toxic_message_count >= 3:
            evidence.append(f"{event.toxic_message_count} toxic communication events")
        if event.inactive_hours >= 7:
            evidence.append(f"{event.inactive_hours:g} inactive hours")
        return evidence[:6]

    @staticmethod
    def _affected_assets(event: BehaviorEvent, scores) -> list[str]:
        assets: list[str] = []
        if scores.data_leakage_probability >= 55:
            assets.extend(["customer_export_store", "finance_sensitive_files"])
        if scores.privilege_misuse_score >= 55:
            assets.extend(["admin_console", "privileged_database"])
        if scores.access_anomaly_score >= 55:
            assets.extend(["identity_provider", "device_trust_profile"])
        if not assets:
            assets.append(f"{event.department.lower().replace(' ', '_')}_workspace")
        return list(dict.fromkeys(assets))[:5]

    @staticmethod
    def _mitigations(anomaly_type: str, scores) -> list[str]:
        actions: list[str] = []
        if scores.access_anomaly_score >= 60:
            actions.append("Enforce step-up MFA and verify device fingerprint before the next privileged action.")
        if scores.data_leakage_probability >= 60:
            actions.append("Throttle exports and place sensitive-file downloads under DLP approval.")
        if scores.privilege_misuse_score >= 60:
            actions.append("Suspend temporary admin privileges pending security-owner review.")
        if scores.fraud_likelihood >= 55:
            actions.append("Preserve audit trail and open fraud triage with Legal and Security Operations.")
        if "burnout" in anomaly_type.lower():
            actions.append("Route workload recovery to the manager to reduce false-positive operational noise.")
        if not actions:
            actions.append("Continue enhanced monitoring for the next 24 hours.")
        return actions[:4]

    @staticmethod
    def _confidence(scores) -> float:
        score_spread = max(
            scores.anomaly_score,
            scores.insider_threat_score,
            scores.data_leakage_probability,
            scores.access_anomaly_score,
            scores.privilege_misuse_score,
        )
        return round(min(0.98, max(0.62, 0.58 + score_spread / 250 + scores.behavioral_drift_score / 500)), 3)

    @staticmethod
    def _user_risk_heatmap(alerts: list[AnomalyAlert]) -> list[UserRiskHeatmapPoint]:
        grouped: dict[str, list[AnomalyAlert]] = defaultdict(list)
        for alert in alerts:
            grouped[alert.department].append(alert)
        return [
            UserRiskHeatmapPoint(
                department=department,
                employee_count=len(items),
                highest_risk_employee=max(items, key=lambda item: item.anomaly_score).employee_name,
                average_threat_score=round(mean(item.anomaly_score for item in items), 2),
                average_data_leakage_probability=round(mean(item.data_leakage_probability for item in items), 2),
                average_access_anomaly_score=round(mean(item.access_anomaly_score for item in items), 2),
                critical_alerts=sum(1 for item in items if item.severity == "critical"),
            )
            for department, items in sorted(grouped.items())
        ]

    @staticmethod
    def _security_recommendations(alerts: list[AnomalyAlert]) -> list[SecurityRecommendation]:
        if not alerts:
            return [
                SecurityRecommendation(
                    title="Maintain passive monitoring",
                    priority="low",
                    action="No adaptive access-control escalation required in this sample.",
                    rationale="No alert crossed the active SOC threshold.",
                    expected_impact="Preserves normal user workflow while retaining baseline telemetry.",
                    confidence=0.72,
                )
            ]
        recommendations: list[SecurityRecommendation] = []
        if any(alert.data_leakage_probability >= 65 for alert in alerts):
            recommendations.append(
                SecurityRecommendation(
                    title="Activate DLP containment",
                    priority="critical",
                    action="Freeze high-volume external exports and require security approval for sensitive downloads.",
                    rationale="Data leakage probability exceeded the enterprise SOC threshold.",
                    expected_impact="Reduces exfiltration blast radius while preserving evidence.",
                    confidence=0.91,
                )
            )
        if any(alert.privilege_misuse_score >= 65 for alert in alerts):
            recommendations.append(
                SecurityRecommendation(
                    title="Review privileged access",
                    priority="high",
                    action="Suspend temporary admin elevation and review privileged session history.",
                    rationale="Privilege misuse score indicates elevated-risk administrative behavior.",
                    expected_impact="Limits privilege abuse and improves account-containment speed.",
                    confidence=0.88,
                )
            )
        if any(alert.access_anomaly_score >= 65 for alert in alerts):
            recommendations.append(
                SecurityRecommendation(
                    title="Enforce adaptive authentication",
                    priority="high",
                    action="Require MFA, device trust verification, and geo-velocity review for high-risk users.",
                    rationale="Access-pattern AI detected abnormal location, device, or session signals.",
                    expected_impact="Blocks compromised sessions before sensitive-resource access.",
                    confidence=0.86,
                )
            )
        if not recommendations:
            top = alerts[0]
            recommendations.append(
                SecurityRecommendation(
                    title=f"Monitor {top.employee_name}",
                    priority=top.severity,
                    action=top.recommendation,
                    rationale=f"Highest anomaly score is {round(top.anomaly_score)} with {round(top.insider_threat_score)} insider-risk pressure.",
                    expected_impact="Improves SOC response prioritization without broad access disruption.",
                    confidence=top.confidence,
                )
            )
        return recommendations[:4]

    @staticmethod
    def _executive_insights(alerts: list[AnomalyAlert], events: list[BehaviorEvent]) -> list[str]:
        if not alerts:
            return ["No insider-risk alert crossed the adaptive threshold in the current security telemetry sample."]
        top = alerts[0]
        total_transfer = sum(event.data_download_mb + event.external_transfer_mb + event.cloud_upload_mb + event.usb_write_mb for event in events)
        return [
            f"{top.employee_name} is the highest-risk identity with {round(top.anomaly_score)} anomaly score and {round(top.insider_threat_score)} insider-risk score.",
            f"Security AI reviewed {len(events)} behavior events and observed {round(total_transfer)} MB of combined download, upload, USB, and external-transfer activity.",
            f"Data-leakage risk is elevated in {sum(1 for alert in alerts if alert.data_leakage_probability >= 65)} identities; prioritize DLP containment before broad account disablement.",
        ]

    @staticmethod
    def _scenario_variant(base: AnomalyDetectionRequest, download_multiplier: float, access_delta: int, privilege_delta: int) -> AnomalyDetectionRequest:
        events = [
            event.model_copy(
                update={
                    "data_download_mb": min(100000, event.data_download_mb * download_multiplier),
                    "external_transfer_mb": min(100000, event.external_transfer_mb * download_multiplier + 240 * access_delta),
                    "cloud_upload_mb": min(100000, event.cloud_upload_mb * download_multiplier + 180 * access_delta),
                    "sensitive_file_accesses": min(10000, event.sensitive_file_accesses + 80 * access_delta),
                    "off_hours_logins": min(60, event.off_hours_logins + access_delta),
                    "unusual_location_count": min(50, event.unusual_location_count + access_delta),
                    "device_change_count": min(50, event.device_change_count + access_delta),
                    "privileged_actions": min(200, event.privileged_actions + privilege_delta),
                    "access_scope_changes": min(100, event.access_scope_changes + access_delta),
                    "policy_violation_count": min(500, event.policy_violation_count + access_delta),
                    "baseline_deviation": min(1, event.baseline_deviation + 0.08 * access_delta),
                }
            )
            for event in (base.events or AnomalyService.default_events())
        ]
        return base.model_copy(update={"events": events, "sensitivity": min(1, base.sensitivity + 0.05)})

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    @staticmethod
    def _adaptive_threshold(sensitivity: float) -> float:
        if not FEEDBACK_PATH.exists():
            return round(66 - sensitivity * 16, 2)
        signals: list[float] = []
        for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines()[-60:]:
            try:
                signals.append(float(json.loads(line).get("learning_signal", 0.6)))
            except json.JSONDecodeError:
                continue
        if not signals:
            return round(66 - sensitivity * 16, 2)
        confirmed_pressure = mean(signals) - 0.5
        return round(float(min(76, max(44, 66 - sensitivity * 16 - confirmed_pressure * 8))), 2)


anomaly_service = AnomalyService()

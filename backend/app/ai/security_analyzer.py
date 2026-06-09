from app.schemas.intelligence import SecurityAnalysisResponse


class SecurityAnalyzer:
    def analyze(self, failed_logins: int, off_hours_accesses: int, data_export_mb: float, privileged_actions: int) -> SecurityAnalysisResponse:
        score = min(
            100,
            round(
                failed_logins * 1.4
                + off_hours_accesses * 3.2
                + min(data_export_mb / 100, 35)
                + privileged_actions * 4.6
            ),
        )
        if score >= 75:
            anomaly = "probable insider or compromised privileged account"
            response = "Lock risky sessions, enforce step-up authentication, rotate tokens, and start incident review."
        elif score >= 45:
            anomaly = "suspicious behavioral drift"
            response = "Throttle exports, increase monitoring, and request manager validation."
        else:
            anomaly = "low-risk deviation"
            response = "Continue passive monitoring and retain activity evidence."
        return SecurityAnalysisResponse(threat_score=score, anomaly_type=anomaly, response_plan=response)


security_analyzer = SecurityAnalyzer()

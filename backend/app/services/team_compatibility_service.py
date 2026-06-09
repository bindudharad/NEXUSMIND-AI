from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.core.cache import TTLResponseCache
from app.ai.team_compatibility_engine import team_compatibility_engine
from app.schemas.team_compatibility import (
    LeadershipMatch,
    TeamCompatibilityPair,
    TeamCompatibilityRequest,
    TeamCompatibilityResponse,
    TeamCompatibilitySummary,
    TeamConflictWarning,
    TeamEmployeeProfile,
    TeamGraphEdge,
    TeamGraphNode,
    TeamInteractionSignal,
    TeamRecommendation,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "team_compatibility_history.jsonl"


class TeamCompatibilityService:
    model_name = "Graph-aware RandomForest Team Compatibility Engine"

    def __init__(self) -> None:
        self._lock = Lock()
        self._default_cache: TTLResponseCache[TeamCompatibilityResponse] = TTLResponseCache(ttl_seconds=8)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: TeamCompatibilityRequest | None = None) -> TeamCompatibilityResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_default_uncached)
        return self._analyze_uncached(payload)

    def _analyze_default_uncached(self) -> TeamCompatibilityResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: TeamCompatibilityRequest) -> TeamCompatibilityResponse:
        request = payload or self.default_request()
        employees = request.employees or self.default_request().employees
        interactions = self._interaction_map(request.interactions)
        pair_scores = self._pair_scores(employees, interactions)
        graph_nodes = self._graph_nodes(employees, pair_scores)
        graph_edges = [
            TeamGraphEdge(
                source_id=pair.source_id,
                target_id=pair.target_id,
                compatibility_score=pair.compatibility_score,
                conflict_probability=pair.conflict_probability,
            )
            for pair in pair_scores
        ]
        recommendations = self._team_recommendations(request, employees, pair_scores)
        conflict_warnings = self._conflict_warnings(pair_scores)
        leadership_matches = self._leadership_matches(employees, pair_scores)
        chemistry_insights = self._chemistry_insights(pair_scores, recommendations, conflict_warnings)
        optimization_suggestions = self._optimization_suggestions(recommendations, conflict_warnings, leadership_matches)
        summary = self._summary(employees, pair_scores, recommendations)
        response = TeamCompatibilityResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            project_name=request.project_name,
            required_skills=request.required_skills,
            pair_scores=pair_scores,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            team_recommendations=recommendations,
            conflict_warnings=conflict_warnings,
            leadership_matches=leadership_matches,
            chemistry_insights=chemistry_insights,
            optimization_suggestions=optimization_suggestions,
            summary=summary,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: TeamCompatibilityRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, stress_delta=0.08, conflict_delta=1),
            self._scenario_variant(base, stress_delta=0.16, conflict_delta=2),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: team_compatibility\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> TeamCompatibilityRequest:
        employees = [
            TeamEmployeeProfile(
                employee_id="emp-a",
                name="Aarav Mehta",
                role="Backend Lead",
                department="Engineering",
                skills=["python", "api", "security", "mlops"],
                work_style="analytical",
                productivity_history=[0.82, 0.84, 0.8, 0.78],
                stress_history=[0.52, 0.58, 0.62, 0.66],
                sentiment_trend=0.12,
                task_completion_rate=0.82,
                meeting_participation=0.58,
                collaboration_frequency=0.78,
                leadership_score=0.83,
                burnout_risk=0.48,
                current_workload=0.82,
                focus_ratio=0.64,
            ),
            TeamEmployeeProfile(
                employee_id="emp-b",
                name="Bianca Shah",
                role="Reliability Engineer",
                department="Platform",
                skills=["python", "kubernetes", "security", "automation"],
                work_style="supportive",
                productivity_history=[0.9, 0.88, 0.91, 0.89],
                stress_history=[0.28, 0.3, 0.34, 0.31],
                sentiment_trend=0.42,
                task_completion_rate=0.91,
                meeting_participation=0.48,
                collaboration_frequency=0.86,
                leadership_score=0.64,
                burnout_risk=0.22,
                current_workload=0.58,
                focus_ratio=0.7,
            ),
            TeamEmployeeProfile(
                employee_id="emp-c",
                name="Devika Nair",
                role="ML Engineer",
                department="AI",
                skills=["mlops", "forecasting", "python", "rag"],
                work_style="creative",
                productivity_history=[0.87, 0.9, 0.88, 0.92],
                stress_history=[0.36, 0.32, 0.35, 0.37],
                sentiment_trend=0.36,
                task_completion_rate=0.89,
                meeting_participation=0.54,
                collaboration_frequency=0.74,
                leadership_score=0.58,
                burnout_risk=0.28,
                current_workload=0.62,
                focus_ratio=0.74,
            ),
            TeamEmployeeProfile(
                employee_id="emp-d",
                name="Omar Khan",
                role="Product Manager",
                department="Product",
                skills=["planning", "customer", "api", "analytics"],
                work_style="collaborative",
                productivity_history=[0.78, 0.76, 0.8, 0.82],
                stress_history=[0.42, 0.44, 0.4, 0.45],
                sentiment_trend=0.24,
                task_completion_rate=0.8,
                meeting_participation=0.72,
                collaboration_frequency=0.9,
                leadership_score=0.78,
                burnout_risk=0.35,
                current_workload=0.64,
                focus_ratio=0.42,
            ),
            TeamEmployeeProfile(
                employee_id="emp-e",
                name="John Rivera",
                role="Incident Commander",
                department="Engineering",
                skills=["api", "incident", "backend", "security"],
                work_style="decisive",
                productivity_history=[0.68, 0.62, 0.58, 0.54],
                stress_history=[0.78, 0.84, 0.88, 0.9],
                sentiment_trend=-0.46,
                task_completion_rate=0.57,
                meeting_participation=0.86,
                collaboration_frequency=0.52,
                leadership_score=0.7,
                burnout_risk=0.82,
                current_workload=0.94,
                focus_ratio=0.25,
            ),
            TeamEmployeeProfile(
                employee_id="emp-f",
                name="Maya Iyer",
                role="QA Automation Lead",
                department="Quality",
                skills=["automation", "testing", "api", "python"],
                work_style="focused",
                productivity_history=[0.86, 0.85, 0.87, 0.88],
                stress_history=[0.34, 0.36, 0.38, 0.35],
                sentiment_trend=0.28,
                task_completion_rate=0.87,
                meeting_participation=0.38,
                collaboration_frequency=0.76,
                leadership_score=0.61,
                burnout_risk=0.26,
                current_workload=0.6,
                focus_ratio=0.82,
            ),
        ]
        interactions = [
            TeamInteractionSignal(source_id="emp-a", target_id="emp-b", collaboration_frequency=0.9, past_success_rate=0.88, sentiment_alignment=0.82, conflict_incidents=0, meetings_together=18),
            TeamInteractionSignal(source_id="emp-a", target_id="emp-c", collaboration_frequency=0.84, past_success_rate=0.86, sentiment_alignment=0.8, conflict_incidents=0, meetings_together=12),
            TeamInteractionSignal(source_id="emp-b", target_id="emp-f", collaboration_frequency=0.82, past_success_rate=0.84, sentiment_alignment=0.78, conflict_incidents=0, meetings_together=15),
            TeamInteractionSignal(source_id="emp-d", target_id="emp-e", collaboration_frequency=0.44, past_success_rate=0.46, sentiment_alignment=0.38, conflict_incidents=4, meetings_together=20),
            TeamInteractionSignal(source_id="emp-c", target_id="emp-e", collaboration_frequency=0.48, past_success_rate=0.5, sentiment_alignment=0.42, conflict_incidents=3, meetings_together=10),
        ]
        return TeamCompatibilityRequest(employees=employees, interactions=interactions)

    def _pair_scores(self, employees: list[TeamEmployeeProfile], interactions: dict[frozenset[str], TeamInteractionSignal]) -> list[TeamCompatibilityPair]:
        pairs: list[TeamCompatibilityPair] = []
        for first, second in combinations(employees, 2):
            interaction = interactions.get(frozenset({first.employee_id, second.employee_id}))
            features = team_compatibility_engine.pair_features(first, second, interaction)
            prediction = team_compatibility_engine.predict_pair(first, second, interaction)
            productivity_synergy = float(np.clip((features[1] * 0.4 + features[7] * 0.28 + features[8] * 0.32) * 100, 0, 100))
            communication = float(np.clip((features[4] * 0.45 + features[5] * 0.35 + features[8] * 0.2) * 100, 0, 100))
            leadership = float(np.clip(features[11] * 100, 0, 100))
            burnout = float(np.clip((features[12] * 0.65 + (1 - features[2]) * 0.35) * 100, 0, 100))
            pairs.append(
                TeamCompatibilityPair(
                    source_id=first.employee_id,
                    source_name=first.name,
                    target_id=second.employee_id,
                    target_name=second.name,
                    compatibility_score=prediction.compatibility_score,
                    collaboration_success_probability=round(min(100, prediction.compatibility_score * 0.78 + features[9] * 22), 2),
                    conflict_probability=prediction.conflict_probability,
                    productivity_synergy=round(productivity_synergy, 2),
                    communication_compatibility=round(communication, 2),
                    leadership_compatibility=round(leadership, 2),
                    burnout_propagation_risk=round(burnout, 2),
                    confidence=prediction.confidence,
                    chemistry_label=self._chemistry_label(prediction.compatibility_score, prediction.conflict_probability),
                    evidence=self._pair_evidence(first, second, features, interaction),
                    recommendation=self._pair_recommendation(first, second, prediction.compatibility_score, prediction.conflict_probability),
                )
            )
        return sorted(pairs, key=lambda pair: pair.compatibility_score, reverse=True)

    def _graph_nodes(self, employees: list[TeamEmployeeProfile], pairs: list[TeamCompatibilityPair]) -> list[TeamGraphNode]:
        nodes = []
        for employee in employees:
            connected = [
                pair.compatibility_score
                for pair in pairs
                if pair.source_id == employee.employee_id or pair.target_id == employee.employee_id
            ]
            stress_index = self._avg(employee.stress_history, employee.burnout_risk) * 100
            nodes.append(
                TeamGraphNode(
                    employee_id=employee.employee_id,
                    name=employee.name,
                    role=employee.role,
                    department=employee.department,
                    cluster=team_compatibility_engine.cluster_employee(employee),
                    influence_score=round(mean(connected) if connected else 0, 2),
                    stress_index=round(stress_index, 2),
                    skill_count=len(employee.skills),
                )
            )
        return sorted(nodes, key=lambda node: node.influence_score, reverse=True)

    def _team_recommendations(self, request: TeamCompatibilityRequest, employees: list[TeamEmployeeProfile], pairs: list[TeamCompatibilityPair]) -> list[TeamRecommendation]:
        pair_lookup = {frozenset({pair.source_id, pair.target_id}): pair for pair in pairs}
        recommendations = []
        for index, members in enumerate(team_compatibility_engine.best_team_combinations(employees, request.target_team_size), start=1):
            member_ids = {member.employee_id for member in members}
            member_pairs = [
                pair_lookup[frozenset({first.employee_id, second.employee_id})]
                for first, second in combinations(members, 2)
                if frozenset({first.employee_id, second.employee_id}) in pair_lookup
            ]
            if not member_pairs:
                continue
            skills = {skill.lower() for member in members for skill in member.skills}
            required = {skill.lower() for skill in request.required_skills}
            skill_coverage = len(skills & required) / max(len(required), 1) * 100
            compatibility = mean(pair.compatibility_score for pair in member_pairs)
            conflict = mean(pair.conflict_probability for pair in member_pairs)
            chemistry = mean(pair.communication_compatibility for pair in member_pairs)
            burnout_balance = max(0, 100 - np.std([member.burnout_risk for member in members]) * 80 - mean(member.burnout_risk for member in members) * 24)
            projected_velocity = float(np.clip(compatibility * 0.45 + skill_coverage * 0.25 + burnout_balance * 0.16 + (100 - conflict) * 0.14, 0, 100))
            leader = max(members, key=lambda member: member.leadership_score * 0.72 + member.collaboration_frequency * 0.28)
            warnings = []
            if conflict >= 45:
                warnings.append("Conflict probability requires facilitation before launch.")
            if any(member.employee_id in member_ids and member.burnout_risk >= 0.72 for member in members):
                warnings.append("Burnout propagation risk exists; cap meeting load and rotate incident ownership.")
            recommendations.append(
                TeamRecommendation(
                    team_id=f"team-rec-{index}",
                    title=f"{request.project_name} team option {index}",
                    members=[member.name for member in members],
                    leader=leader.name,
                    compatibility_score=round(compatibility, 2),
                    chemistry_score=round(chemistry, 2),
                    skill_coverage=round(skill_coverage, 2),
                    conflict_risk=round(conflict, 2),
                    burnout_balance=round(float(np.clip(burnout_balance, 0, 100)), 2),
                    projected_velocity=round(projected_velocity, 2),
                    rationale=f"{leader.name} anchors leadership while the team covers {round(skill_coverage)}% of required skills with {round(compatibility)} compatibility.",
                    warnings=warnings,
                )
            )
        return sorted(recommendations, key=lambda item: item.projected_velocity, reverse=True)[:5]

    @staticmethod
    def _conflict_warnings(pairs: list[TeamCompatibilityPair]) -> list[TeamConflictWarning]:
        warnings = []
        for pair in pairs:
            if pair.conflict_probability < 42 and pair.compatibility_score >= 48:
                continue
            probability = max(pair.conflict_probability, 100 - pair.compatibility_score)
            if probability >= 82:
                severity = "critical"
            elif probability >= 64:
                severity = "high"
            elif probability >= 44:
                severity = "medium"
            else:
                severity = "low"
            warnings.append(
                TeamConflictWarning(
                    severity=severity,
                    probability=round(probability, 2),
                    employees=[pair.source_name, pair.target_name],
                    message=f"{pair.source_name} and {pair.target_name} show {round(probability)}% collaboration conflict risk.",
                    intervention="Pair them with a facilitator, clarify ownership boundaries, and avoid high-pressure incident lanes together.",
                )
            )
        return sorted(warnings, key=lambda warning: warning.probability, reverse=True)[:6]

    def _leadership_matches(self, employees: list[TeamEmployeeProfile], pairs: list[TeamCompatibilityPair]) -> list[LeadershipMatch]:
        pair_lookup = {frozenset({pair.source_id, pair.target_id}): pair for pair in pairs}
        matches = []
        for leader in sorted(employees, key=lambda item: item.leadership_score, reverse=True)[:4]:
            peers = [employee for employee in employees if employee.employee_id != leader.employee_id]
            connected = [pair_lookup.get(frozenset({leader.employee_id, peer.employee_id})) for peer in peers]
            valid = [pair for pair in connected if pair]
            score = mean(pair.leadership_compatibility * 0.45 + pair.compatibility_score * 0.4 + (100 - pair.conflict_probability) * 0.15 for pair in valid) if valid else leader.leadership_score * 100
            scope = self._best_scope(leader, peers, pair_lookup)
            matches.append(
                LeadershipMatch(
                    leader_id=leader.employee_id,
                    leader_name=leader.name,
                    team_scope=scope,
                    compatibility_score=round(float(np.clip(score, 0, 100)), 2),
                    rationale=f"{leader.name} combines {round(leader.leadership_score * 100)}% leadership strength with {round(leader.collaboration_frequency * 100)}% collaboration frequency.",
                    watchouts=["Protect focus time for high-meeting leaders."] if leader.meeting_participation > 0.75 else [],
                )
            )
        return sorted(matches, key=lambda match: match.compatibility_score, reverse=True)

    @staticmethod
    def _best_scope(leader: TeamEmployeeProfile, peers: list[TeamEmployeeProfile], pair_lookup: dict[frozenset[str], TeamCompatibilityPair]) -> str:
        best = sorted(
            peers,
            key=lambda peer: (pair_lookup.get(frozenset({leader.employee_id, peer.employee_id})).compatibility_score if pair_lookup.get(frozenset({leader.employee_id, peer.employee_id})) else 0),
            reverse=True,
        )[:3]
        return ", ".join(peer.department for peer in best) or leader.department

    @staticmethod
    def _chemistry_insights(pairs: list[TeamCompatibilityPair], recommendations: list[TeamRecommendation], warnings: list[TeamConflictWarning]) -> list[str]:
        top_pair = pairs[0] if pairs else None
        best_team = recommendations[0] if recommendations else None
        insights = []
        if top_pair:
            insights.append(f"{top_pair.source_name} + {top_pair.target_name} is the strongest pair at {round(top_pair.compatibility_score)}% compatibility.")
        if best_team:
            insights.append(f"{best_team.title} has projected velocity {round(best_team.projected_velocity)}% and skill coverage {round(best_team.skill_coverage)}%.")
        if warnings:
            insights.append(f"{len(warnings)} conflict risk combinations need manager facilitation before high-pressure delivery work.")
        insights.append("Compatibility scoring combines relationship graph signals, workstyle clustering, sentiment alignment, stress patterns, and skill overlap.")
        return insights

    @staticmethod
    def _optimization_suggestions(recommendations: list[TeamRecommendation], warnings: list[TeamConflictWarning], leadership: list[LeadershipMatch]) -> list[str]:
        suggestions = []
        if recommendations:
            team = recommendations[0]
            suggestions.append(f"Launch with {team.leader} as coordination lead and members {', '.join(team.members[:4])}.")
        if warnings:
            suggestions.append("Avoid assigning the highest-conflict pair to the same escalation lane without mediation.")
        if leadership:
            suggestions.append(f"Use {leadership[0].leader_name} for the highest-context leadership match: {leadership[0].team_scope}.")
        suggestions.append("Recompute compatibility after major sprint changes, sentiment shifts, or burnout alerts.")
        return suggestions

    @staticmethod
    def _summary(employees: list[TeamEmployeeProfile], pairs: list[TeamCompatibilityPair], recommendations: list[TeamRecommendation]) -> TeamCompatibilitySummary:
        best = pairs[0] if pairs else None
        risk = max(pairs, key=lambda pair: pair.conflict_probability) if pairs else None
        return TeamCompatibilitySummary(
            employees_analyzed=len(employees),
            pairs_analyzed=len(pairs),
            average_compatibility=round(mean(pair.compatibility_score for pair in pairs) if pairs else 0, 2),
            average_conflict_probability=round(mean(pair.conflict_probability for pair in pairs) if pairs else 0, 2),
            highest_compatibility_pair=f"{best.source_name} + {best.target_name}" if best else "n/a",
            highest_risk_pair=f"{risk.source_name} + {risk.target_name}" if risk else "n/a",
            recommended_team_score=recommendations[0].projected_velocity if recommendations else 0,
        )

    @staticmethod
    def _pair_evidence(first: TeamEmployeeProfile, second: TeamEmployeeProfile, features: list[float], interaction: TeamInteractionSignal | None) -> list[str]:
        evidence = [
            f"skill overlap {round(features[0] * 100)}%",
            f"productivity alignment {round(features[1] * 100)}%",
            f"communication alignment {round(features[5] * 100)}%",
            f"workstyle fit {round(features[6] * 100)}%",
            f"burnout mean {round(features[12] * 100)}%",
        ]
        if interaction:
            evidence.append(f"past success {round(interaction.past_success_rate * 100)}% over {interaction.meetings_together} shared meetings")
        else:
            evidence.append(f"derived from {first.department}/{second.department} profile similarity")
        return evidence

    @staticmethod
    def _pair_recommendation(first: TeamEmployeeProfile, second: TeamEmployeeProfile, compatibility: float, conflict: float) -> str:
        if compatibility >= 78 and conflict < 30:
            return f"Pair {first.name} and {second.name} on high-complexity work; chemistry is strong."
        if conflict >= 55:
            return f"Do not place {first.name} and {second.name} in the same high-pressure lane without a facilitator."
        return f"Use {first.name} and {second.name} together with clear ownership boundaries and a short feedback loop."

    @staticmethod
    def _chemistry_label(compatibility: float, conflict: float) -> str:
        if compatibility >= 82 and conflict < 24:
            return "high-synergy"
        if compatibility >= 68 and conflict < 42:
            return "compatible"
        if conflict >= 62:
            return "conflict-risk"
        return "needs-structure"

    @staticmethod
    def _interaction_map(interactions: list[TeamInteractionSignal]) -> dict[frozenset[str], TeamInteractionSignal]:
        return {frozenset({item.source_id, item.target_id}): item for item in interactions}

    @staticmethod
    def _scenario_variant(base: TeamCompatibilityRequest, stress_delta: float, conflict_delta: int) -> TeamCompatibilityRequest:
        employees = []
        for employee in base.employees or TeamCompatibilityService.default_request().employees:
            employees.append(
                employee.model_copy(
                    update={
                        "stress_history": [min(1, value + stress_delta) for value in (employee.stress_history or [employee.burnout_risk])],
                        "burnout_risk": min(1, employee.burnout_risk + stress_delta * 0.7),
                        "sentiment_trend": max(-1, employee.sentiment_trend - stress_delta * 0.6),
                    }
                )
            )
        interactions = [
            interaction.model_copy(update={"conflict_incidents": min(20, interaction.conflict_incidents + conflict_delta)})
            for interaction in (base.interactions or TeamCompatibilityService.default_request().interactions)
        ]
        return base.model_copy(update={"employees": employees, "interactions": interactions, "realtime": True})

    @staticmethod
    def _avg(values: list[float], fallback: float) -> float:
        return float(np.clip(mean(values) if values else fallback, 0, 1))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


team_compatibility_service = TeamCompatibilityService()

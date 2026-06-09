from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from itertools import combinations
from math import comb
from pathlib import Path
from statistics import mean, pstdev
from threading import Lock

import numpy as np

from app.ai.graph_relation_engine import graph_relation_engine
from app.ai.team_compatibility_engine import team_compatibility_engine
from app.core.cache import TTLResponseCache
from app.schemas.team_builder import (
    ChemistryHeatmapCell,
    LeadershipRecommendation,
    OptimizedTeam,
    SkillBalanceItem,
    TeamBuilderMember,
    TeamBuilderRequest,
    TeamBuilderResponse,
    TeamBuilderRiskAlert,
    TeamBuilderSummary,
)
from app.schemas.team_compatibility import TeamCompatibilityPair, TeamCompatibilityRequest, TeamEmployeeProfile, TeamInteractionSignal
from app.services.team_compatibility_service import team_compatibility_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "team_builder_history.jsonl"


class TeamBuilderService:
    model_name = "GraphSAGE + RandomForest AI Team Builder"

    def __init__(self) -> None:
        self._cache: TTLResponseCache[TeamBuilderResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def build(self, payload: TeamBuilderRequest | None = None) -> TeamBuilderResponse:
        if payload is None:
            return self._cache.get_or_set(self._build_default_uncached)
        return self._build_uncached(payload)

    def _build_default_uncached(self) -> TeamBuilderResponse:
        return self._build_uncached(self.default_request())

    def _build_uncached(self, payload: TeamBuilderRequest) -> TeamBuilderResponse:
        request = payload or self.default_request()
        employees = request.employees or self.default_request().employees
        interactions = request.interactions or self.default_request().interactions
        compatibility = team_compatibility_service.analyze(
            TeamCompatibilityRequest(
                project_name=request.project_name,
                required_skills=request.required_skills,
                target_team_size=request.target_team_size,
                employees=employees,
                interactions=interactions,
                realtime=request.realtime,
            )
        )
        pair_lookup = {frozenset({pair.source_id, pair.target_id}): pair for pair in compatibility.pair_scores}
        graph = graph_relation_engine.infer(employees, compatibility.pair_scores)
        graph_nodes = {node.employee_id: node for node in graph.nodes}
        teams = self._optimized_teams(request, employees, pair_lookup, graph.edge_attention, graph_nodes)
        heatmap = self._heatmap(teams[0] if teams else None, pair_lookup, graph.edge_attention)
        skill_balance = self._skill_balance(request.required_skills, teams[0] if teams else None)
        leadership = self._leadership_recommendations(teams[0] if teams else None)
        risks = self._risk_alerts(teams[0] if teams else None, heatmap)
        analytics = self._collaboration_analytics(teams, skill_balance, risks, graph.metrics)
        combination_count = comb(len(employees), request.target_team_size) if len(employees) >= request.target_team_size else 1
        summary = self._summary(employees, teams, compatibility.pair_scores, graph, combination_count)
        response = TeamBuilderResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            project_name=request.project_name,
            project_type=request.project_type,
            required_skills=request.required_skills,
            optimized_teams=teams,
            skill_balance=skill_balance,
            chemistry_heatmap=heatmap,
            leadership_recommendations=leadership,
            risk_alerts=risks,
            collaboration_analytics=analytics,
            graph_model_metrics=dict(graph.metrics),
            summary=summary,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: TeamBuilderRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, stress_delta=0.06, deadline_delta=0.08, conflict_delta=1),
            self._scenario_variant(base, stress_delta=0.13, deadline_delta=0.16, conflict_delta=2),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.build(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: team_builder\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> TeamBuilderRequest:
        employees = [
            TeamEmployeeProfile(
                employee_id="tb-backend",
                name="Aarav Mehta",
                role="Senior Backend Developer",
                department="Engineering",
                skills=["python", "api", "postgresql", "security", "incident response"],
                work_style="analytical",
                productivity_history=[0.84, 0.86, 0.83, 0.88],
                stress_history=[0.42, 0.45, 0.48, 0.44],
                sentiment_trend=0.2,
                task_completion_rate=0.87,
                meeting_participation=0.54,
                collaboration_frequency=0.82,
                leadership_score=0.82,
                burnout_risk=0.36,
                current_workload=0.72,
                focus_ratio=0.68,
            ),
            TeamEmployeeProfile(
                employee_id="tb-ml",
                name="Devika Nair",
                role="ML Engineer",
                department="AI",
                skills=["python", "mlops", "forecasting", "rag", "model evaluation"],
                work_style="creative",
                productivity_history=[0.88, 0.9, 0.89, 0.91],
                stress_history=[0.3, 0.34, 0.32, 0.36],
                sentiment_trend=0.38,
                task_completion_rate=0.9,
                meeting_participation=0.5,
                collaboration_frequency=0.78,
                leadership_score=0.62,
                burnout_risk=0.27,
                current_workload=0.62,
                focus_ratio=0.75,
            ),
            TeamEmployeeProfile(
                employee_id="tb-ui",
                name="Nina Kapoor",
                role="UI/UX Designer",
                department="Design",
                skills=["product design", "ux research", "dashboard", "accessibility", "visual systems"],
                work_style="collaborative",
                productivity_history=[0.82, 0.84, 0.86, 0.85],
                stress_history=[0.28, 0.33, 0.32, 0.35],
                sentiment_trend=0.44,
                task_completion_rate=0.84,
                meeting_participation=0.7,
                collaboration_frequency=0.88,
                leadership_score=0.58,
                burnout_risk=0.25,
                current_workload=0.57,
                focus_ratio=0.52,
            ),
            TeamEmployeeProfile(
                employee_id="tb-qa",
                name="Maya Iyer",
                role="QA Automation Engineer",
                department="Quality",
                skills=["testing", "automation", "api", "python", "release quality"],
                work_style="focused",
                productivity_history=[0.87, 0.86, 0.88, 0.9],
                stress_history=[0.31, 0.33, 0.35, 0.34],
                sentiment_trend=0.31,
                task_completion_rate=0.88,
                meeting_participation=0.4,
                collaboration_frequency=0.78,
                leadership_score=0.6,
                burnout_risk=0.24,
                current_workload=0.6,
                focus_ratio=0.84,
            ),
            TeamEmployeeProfile(
                employee_id="tb-devops",
                name="Bianca Shah",
                role="DevOps Reliability Engineer",
                department="Platform",
                skills=["kubernetes", "security", "mlops", "redis", "incident response", "automation"],
                work_style="supportive",
                productivity_history=[0.91, 0.89, 0.92, 0.9],
                stress_history=[0.26, 0.3, 0.32, 0.29],
                sentiment_trend=0.46,
                task_completion_rate=0.91,
                meeting_participation=0.46,
                collaboration_frequency=0.86,
                leadership_score=0.66,
                burnout_risk=0.22,
                current_workload=0.56,
                focus_ratio=0.72,
            ),
            TeamEmployeeProfile(
                employee_id="tb-product",
                name="Omar Khan",
                role="Product Manager",
                department="Product",
                skills=["planning", "analytics", "customer", "api", "stakeholder management"],
                work_style="collaborative",
                productivity_history=[0.78, 0.8, 0.82, 0.81],
                stress_history=[0.38, 0.42, 0.44, 0.4],
                sentiment_trend=0.27,
                task_completion_rate=0.82,
                meeting_participation=0.74,
                collaboration_frequency=0.91,
                leadership_score=0.79,
                burnout_risk=0.34,
                current_workload=0.66,
                focus_ratio=0.43,
            ),
            TeamEmployeeProfile(
                employee_id="tb-risk",
                name="John Rivera",
                role="Incident Commander",
                department="Engineering",
                skills=["api", "incident response", "security", "backend"],
                work_style="decisive",
                productivity_history=[0.63, 0.59, 0.56, 0.52],
                stress_history=[0.78, 0.84, 0.88, 0.91],
                sentiment_trend=-0.5,
                task_completion_rate=0.56,
                meeting_participation=0.9,
                collaboration_frequency=0.5,
                leadership_score=0.72,
                burnout_risk=0.84,
                current_workload=0.95,
                focus_ratio=0.24,
            ),
            TeamEmployeeProfile(
                employee_id="tb-data",
                name="Sana Rao",
                role="Data Analyst",
                department="Analytics",
                skills=["analytics", "sql", "dashboard", "experimentation", "forecasting"],
                work_style="analytical",
                productivity_history=[0.8, 0.83, 0.82, 0.84],
                stress_history=[0.36, 0.34, 0.37, 0.39],
                sentiment_trend=0.25,
                task_completion_rate=0.83,
                meeting_participation=0.55,
                collaboration_frequency=0.72,
                leadership_score=0.52,
                burnout_risk=0.31,
                current_workload=0.59,
                focus_ratio=0.67,
            ),
        ]
        interactions = [
            TeamInteractionSignal(source_id="tb-backend", target_id="tb-devops", collaboration_frequency=0.93, past_success_rate=0.9, sentiment_alignment=0.86, conflict_incidents=0, meetings_together=24),
            TeamInteractionSignal(source_id="tb-backend", target_id="tb-ml", collaboration_frequency=0.86, past_success_rate=0.84, sentiment_alignment=0.82, conflict_incidents=0, meetings_together=15),
            TeamInteractionSignal(source_id="tb-qa", target_id="tb-devops", collaboration_frequency=0.88, past_success_rate=0.87, sentiment_alignment=0.8, conflict_incidents=0, meetings_together=20),
            TeamInteractionSignal(source_id="tb-ui", target_id="tb-product", collaboration_frequency=0.9, past_success_rate=0.86, sentiment_alignment=0.88, conflict_incidents=0, meetings_together=26),
            TeamInteractionSignal(source_id="tb-ml", target_id="tb-data", collaboration_frequency=0.82, past_success_rate=0.83, sentiment_alignment=0.78, conflict_incidents=0, meetings_together=12),
            TeamInteractionSignal(source_id="tb-product", target_id="tb-risk", collaboration_frequency=0.4, past_success_rate=0.42, sentiment_alignment=0.34, conflict_incidents=4, meetings_together=18),
            TeamInteractionSignal(source_id="tb-ml", target_id="tb-risk", collaboration_frequency=0.44, past_success_rate=0.48, sentiment_alignment=0.38, conflict_incidents=3, meetings_together=10),
        ]
        return TeamBuilderRequest(employees=employees, interactions=interactions)

    def _optimized_teams(
        self,
        request: TeamBuilderRequest,
        employees: list[TeamEmployeeProfile],
        pair_lookup: dict[frozenset[str], TeamCompatibilityPair],
        edge_attention: dict[frozenset[str], float],
        graph_nodes: dict[str, object],
    ) -> list[OptimizedTeam]:
        if len(employees) < request.target_team_size:
            candidates = [tuple(employees)]
        else:
            candidates = list(combinations(employees, request.target_team_size))
        scored: list[OptimizedTeam] = []
        for index, members in enumerate(candidates, start=1):
            member_pairs = [
                pair_lookup[frozenset({first.employee_id, second.employee_id})]
                for first, second in combinations(members, 2)
                if frozenset({first.employee_id, second.employee_id}) in pair_lookup
            ]
            if not member_pairs:
                continue
            skill_coverage, missing_skills = self._skill_coverage(members, request.required_skills)
            compatibility = mean(pair.compatibility_score for pair in member_pairs)
            conflict = mean(pair.conflict_probability for pair in member_pairs)
            chemistry = mean(pair.communication_compatibility * 0.45 + pair.productivity_synergy * 0.32 + (100 - pair.burnout_propagation_risk) * 0.23 for pair in member_pairs)
            burnout_balance = self._burnout_balance(members, request.deadline_pressure)
            leadership_balance = self._leadership_balance(members)
            role_diversity = len({member.department for member in members}) / max(len(members), 1) * 100
            graph_confidence = mean([edge_attention.get(frozenset({first.employee_id, second.employee_id}), 0.58) for first, second in combinations(members, 2)])
            projected = self._projected_delivery(
                compatibility=compatibility,
                skill_coverage=skill_coverage,
                chemistry=chemistry,
                conflict=conflict,
                burnout_balance=burnout_balance,
                leadership_balance=leadership_balance,
                role_diversity=role_diversity,
                graph_confidence=graph_confidence,
                priority=request.priority,
            )
            leader = max(members, key=lambda member: member.leadership_score * 0.62 + member.collaboration_frequency * 0.28 + (1 - member.burnout_risk) * 0.1)
            warnings = []
            if missing_skills:
                warnings.append(f"Missing required skills: {', '.join(missing_skills)}.")
            if conflict >= 46:
                warnings.append("Conflict probability needs facilitation before launch.")
            if burnout_balance <= 62:
                warnings.append("Burnout balance is weak; add recovery capacity or reduce deadline pressure.")
            team_members = [self._member(member, graph_nodes) for member in members]
            scored.append(
                OptimizedTeam(
                    team_id=f"team-builder-{index}",
                    title=f"{request.project_name} squad {index}",
                    members=team_members,
                    leader=leader.name,
                    compatibility_score=round(float(compatibility), 2),
                    skill_coverage=round(float(skill_coverage), 2),
                    chemistry_score=round(float(np.clip(chemistry, 0, 100)), 2),
                    conflict_probability=round(float(conflict), 2),
                    burnout_balance=round(float(burnout_balance), 2),
                    leadership_balance=round(float(leadership_balance), 2),
                    projected_delivery_success=round(float(projected), 2),
                    graph_confidence=round(float(np.clip(graph_confidence, 0, 1)), 3),
                    missing_skills=missing_skills,
                    role_mix=sorted({member.role for member in members}),
                    rationale=f"{leader.name} leads a {len(members)} person squad with {round(skill_coverage)}% skill coverage, {round(compatibility)}% compatibility, and {round(conflict)}% conflict probability.",
                    recommendations=self._team_recommendations(members, leader, missing_skills, conflict, burnout_balance),
                    warnings=warnings,
                    evidence=[
                        f"Graph attention={round(graph_confidence, 3)}",
                        f"Role diversity={round(role_diversity)}%",
                        f"Deadline pressure={round(request.deadline_pressure * 100)}%",
                        f"Pairs evaluated={len(member_pairs)}",
                    ],
                )
            )
        return sorted(scored, key=lambda team: team.projected_delivery_success, reverse=True)[:5]

    def _member(self, employee: TeamEmployeeProfile, graph_nodes: dict[str, object]) -> TeamBuilderMember:
        graph_node = graph_nodes.get(employee.employee_id)
        return TeamBuilderMember(
            employee_id=employee.employee_id,
            name=employee.name,
            role=employee.role,
            department=employee.department,
            work_style=employee.work_style,
            skills=employee.skills,
            graph_cluster=team_compatibility_engine.cluster_employee(employee),
            graph_compatibility_projection=float(getattr(graph_node, "compatibility_projection", 0.0)),
            graph_burnout_spread_risk=float(getattr(graph_node, "burnout_spread_risk", employee.burnout_risk * 100)),
            leadership_influence=float(getattr(graph_node, "leadership_influence", employee.leadership_score * 100)),
        )

    def _heatmap(
        self,
        team: OptimizedTeam | None,
        pair_lookup: dict[frozenset[str], TeamCompatibilityPair],
        edge_attention: dict[frozenset[str], float],
    ) -> list[ChemistryHeatmapCell]:
        if team is None:
            return []
        cells = []
        members = team.members
        for first, second in combinations(members, 2):
            key = frozenset({first.employee_id, second.employee_id})
            pair = pair_lookup.get(key)
            if not pair:
                continue
            cells.append(
                ChemistryHeatmapCell(
                    source=first.name,
                    target=second.name,
                    compatibility_score=pair.compatibility_score,
                    communication_score=pair.communication_compatibility,
                    conflict_probability=pair.conflict_probability,
                    burnout_spread_risk=pair.burnout_propagation_risk,
                    graph_attention=edge_attention.get(key, 0.58),
                )
            )
        return sorted(cells, key=lambda item: item.compatibility_score, reverse=True)

    @staticmethod
    def _skill_balance(required_skills: list[str], team: OptimizedTeam | None) -> list[SkillBalanceItem]:
        if team is None:
            return []
        items = []
        for skill in required_skills:
            owners = [member.name for member in team.members if TeamBuilderService._skill_matches(skill, member.skills)]
            coverage = min(100, len(owners) / 2 * 100)
            if not owners:
                risk = "critical"
                recommendation = f"Add a specialist or train one member for {skill}."
            elif len(owners) == 1:
                risk = "medium"
                recommendation = f"Create backup ownership for {skill}."
            else:
                risk = "low"
                recommendation = f"{skill} has resilient coverage."
            items.append(SkillBalanceItem(skill=skill, coverage_score=coverage, owners=owners, gap_risk=risk, recommendation=recommendation))
        return items

    @staticmethod
    def _leadership_recommendations(team: OptimizedTeam | None) -> list[LeadershipRecommendation]:
        if team is None:
            return []
        ranked = sorted(team.members, key=lambda member: member.leadership_influence, reverse=True)
        recommendations = []
        for member in ranked[:3]:
            watchouts = []
            if member.graph_burnout_spread_risk >= 60:
                watchouts.append("Leadership influence is high, but burnout spread risk requires load protection.")
            recommendations.append(
                LeadershipRecommendation(
                    leader_name=member.name,
                    leadership_score=round(member.leadership_influence, 2),
                    scope=f"{member.department} / {member.role}",
                    rationale=f"{member.name} has {round(member.leadership_influence)}% graph leadership influence and {member.graph_cluster} collaboration profile.",
                    watchouts=watchouts,
                )
            )
        return recommendations

    @staticmethod
    def _risk_alerts(team: OptimizedTeam | None, heatmap: list[ChemistryHeatmapCell]) -> list[TeamBuilderRiskAlert]:
        if team is None:
            return []
        alerts: list[TeamBuilderRiskAlert] = []
        for cell in sorted(heatmap, key=lambda item: item.conflict_probability, reverse=True)[:4]:
            probability = max(cell.conflict_probability, cell.burnout_spread_risk * 0.72)
            if probability < 38:
                continue
            severity = "critical" if probability >= 78 else "high" if probability >= 62 else "medium"
            alerts.append(
                TeamBuilderRiskAlert(
                    severity=severity,
                    probability=round(probability, 2),
                    title="Team chemistry risk",
                    members=[cell.source, cell.target],
                    intervention="Clarify decision rights, reduce meeting pressure, and add a manager check-in during the first sprint.",
                )
            )
        if not alerts and team.conflict_probability <= 28:
            alerts.append(
                TeamBuilderRiskAlert(
                    severity="low",
                    probability=round(team.conflict_probability, 2),
                    title="Low conflict launch profile",
                    members=[member.name for member in team.members[:3]],
                    intervention="Keep normal retro cadence and recompute if workload or sentiment changes.",
                )
            )
        return alerts

    @staticmethod
    def _collaboration_analytics(
        teams: list[OptimizedTeam],
        skill_balance: list[SkillBalanceItem],
        risks: list[TeamBuilderRiskAlert],
        graph_metrics: dict[str, object],
    ) -> list[str]:
        if not teams:
            return ["No viable team could be formed from the available employee graph."]
        top = teams[0]
        gap_skills = [item.skill for item in skill_balance if item.gap_risk in {"high", "critical"}]
        analytics = [
            f"{top.title} is the best team with {round(top.projected_delivery_success)}% projected delivery success.",
            f"GraphSAGE relation model evaluated {graph_metrics.get('training_graph_nodes', 'n/a')} training nodes and produces {graph_metrics.get('embedding_dimensions', 'n/a')}D relationship embeddings.",
            f"Leadership balance is {round(top.leadership_balance)}% with {top.leader} as the recommended lead.",
            f"Average conflict probability for the selected squad is {round(top.conflict_probability)}%.",
        ]
        if gap_skills:
            analytics.append(f"Skill risk remains in {', '.join(gap_skills)}.")
        if risks:
            analytics.append(f"{len(risks)} collaboration risk signal(s) require launch-time monitoring.")
        return analytics

    @staticmethod
    def _summary(
        employees: list[TeamEmployeeProfile],
        teams: list[OptimizedTeam],
        pairs: list[TeamCompatibilityPair],
        graph,
        combination_count: int,
    ) -> TeamBuilderSummary:
        best = teams[0] if teams else None
        return TeamBuilderSummary(
            employees_analyzed=len(employees),
            combinations_evaluated=combination_count,
            best_team_score=best.projected_delivery_success if best else 0,
            best_team_name=best.title if best else "n/a",
            average_conflict_probability=round(mean(pair.conflict_probability for pair in pairs) if pairs else 0, 2),
            graph_nodes=len(graph.nodes),
            graph_edges=len(graph.edge_attention),
        )

    @staticmethod
    def _skill_coverage(members: tuple[TeamEmployeeProfile, ...], required_skills: list[str]) -> tuple[float, list[str]]:
        missing = []
        covered = 0
        for skill in required_skills:
            if any(TeamBuilderService._skill_matches(skill, member.skills) for member in members):
                covered += 1
            else:
                missing.append(skill)
        return covered / max(len(required_skills), 1) * 100, missing

    @staticmethod
    def _skill_matches(required: str, candidate_skills: list[str]) -> bool:
        token = required.lower().strip()
        aliases = {
            "devops": {"devops", "kubernetes", "automation", "incident response", "mlops"},
            "ui": {"ui", "ux", "dashboard", "product design", "visual systems"},
            "testing": {"testing", "qa", "automation", "release quality"},
            "api": {"api", "backend", "postgresql"},
            "security": {"security", "incident response"},
        }
        expanded = aliases.get(token, {token})
        normalized = {skill.lower().strip() for skill in candidate_skills}
        return bool(expanded & normalized) or any(token in skill for skill in normalized)

    @staticmethod
    def _burnout_balance(members: tuple[TeamEmployeeProfile, ...], deadline_pressure: float) -> float:
        burnout = [member.burnout_risk for member in members]
        stress = [team_compatibility_engine._avg(member.stress_history, member.burnout_risk) for member in members]
        score = 100 - mean(burnout) * 36 - mean(stress) * 22 - pstdev(burnout) * 44 - deadline_pressure * 9
        if max(burnout) >= 0.78:
            score -= 12
        return float(np.clip(score, 0, 100))

    @staticmethod
    def _leadership_balance(members: tuple[TeamEmployeeProfile, ...]) -> float:
        leadership = [member.leadership_score for member in members]
        top = max(leadership)
        spread = 1 - abs(mean(leadership) - 0.62)
        senior_ratio = len([value for value in leadership if value >= 0.65]) / max(len(leadership), 1)
        return float(np.clip((top * 0.48 + spread * 0.24 + senior_ratio * 0.28) * 100, 0, 100))

    @staticmethod
    def _projected_delivery(
        *,
        compatibility: float,
        skill_coverage: float,
        chemistry: float,
        conflict: float,
        burnout_balance: float,
        leadership_balance: float,
        role_diversity: float,
        graph_confidence: float,
        priority: str,
    ) -> float:
        weights = {
            "balanced": (0.22, 0.22, 0.16, 0.15, 0.12, 0.08, 0.05),
            "delivery_speed": (0.2, 0.18, 0.17, 0.12, 0.16, 0.1, 0.07),
            "low_conflict": (0.2, 0.16, 0.15, 0.22, 0.13, 0.08, 0.06),
            "skill_coverage": (0.18, 0.32, 0.13, 0.12, 0.1, 0.08, 0.07),
            "burnout_safe": (0.18, 0.18, 0.13, 0.14, 0.24, 0.08, 0.05),
        }.get(priority, (0.22, 0.22, 0.16, 0.15, 0.12, 0.08, 0.05))
        conflict_safety = 100 - conflict
        graph_score = graph_confidence * 100
        values = [compatibility, skill_coverage, chemistry, conflict_safety, burnout_balance, leadership_balance, min(100, role_diversity * 0.7 + graph_score * 0.3)]
        return float(np.clip(sum(weight * value for weight, value in zip(weights, values, strict=True)), 0, 100))

    @staticmethod
    def _team_recommendations(
        members: tuple[TeamEmployeeProfile, ...],
        leader: TeamEmployeeProfile,
        missing_skills: list[str],
        conflict: float,
        burnout_balance: float,
    ) -> list[str]:
        recommendations = [
            f"Assign {leader.name} as launch lead and run a 30-minute decision-rights kickoff.",
            "Create a shared delivery board that exposes ownership, dependencies, and blocked work daily.",
        ]
        if missing_skills:
            recommendations.append(f"Cover skill gaps through short-term enablement or contractor support for {', '.join(missing_skills)}.")
        if conflict >= 42:
            recommendations.append("Add facilitation in sprint planning and retro until communication risk declines.")
        if burnout_balance <= 68:
            recommendations.append("Cap after-hours incident work and rotate operational ownership.")
        if any(member.role.lower().find("designer") >= 0 for member in members):
            recommendations.append("Keep design review close to engineering checkpoints to reduce rework.")
        return recommendations

    @staticmethod
    def _scenario_variant(base: TeamBuilderRequest, stress_delta: float, deadline_delta: float, conflict_delta: int) -> TeamBuilderRequest:
        employees = []
        for employee in base.employees or TeamBuilderService.default_request().employees:
            employees.append(
                employee.model_copy(
                    update={
                        "stress_history": [min(1, value + stress_delta) for value in (employee.stress_history or [employee.burnout_risk])],
                        "burnout_risk": min(1, employee.burnout_risk + stress_delta * 0.65),
                        "sentiment_trend": max(-1, employee.sentiment_trend - stress_delta * 0.55),
                        "current_workload": min(1, employee.current_workload + stress_delta * 0.42),
                    }
                )
            )
        interactions = [
            interaction.model_copy(update={"conflict_incidents": min(20, interaction.conflict_incidents + conflict_delta)})
            for interaction in (base.interactions or TeamBuilderService.default_request().interactions)
        ]
        return base.model_copy(
            update={
                "employees": employees,
                "interactions": interactions,
                "deadline_pressure": min(1, base.deadline_pressure + deadline_delta),
                "realtime": True,
            }
        )

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


team_builder_service = TeamBuilderService()

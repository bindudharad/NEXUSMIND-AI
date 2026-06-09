from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from random import Random
from statistics import mean, pstdev
from threading import Lock
from uuid import NAMESPACE_DNS, uuid5

from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator
from app.core.cache import TTLResponseCache
from app.schemas.time_machine import TimeMachineScenarioRequest
from app.schemas.virtual_employee import (
    BigFivePersonality,
    ProjectOutcomeSimulation,
    StressPropagationEdge,
    TeamInteractionResult,
    VirtualEmployeeAgent,
    VirtualEmployeeAssistantRequest,
    VirtualEmployeeBehaviorState,
    VirtualEmployeeExperienceLevel,
    VirtualEmployeeGenerationRequest,
    VirtualEmployeeIdentity,
    VirtualEmployeePersonality,
    VirtualEmployeeSkills,
    VirtualEmployeeWorkCharacteristics,
    VirtualWorkforceAssistantResponse,
    VirtualWorkforceResponse,
    VirtualWorkforceSummary,
    WorkforceForecastPoint,
    WorkforceImpactMetric,
    WorkforceRecommendation,
    WorkforceSimulationRequest,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "virtual_employee_workforce_history.jsonl"
GENERATED_PATH = DATA_DIR / "virtual_employee_registry.jsonl"


class VirtualEmployeeWorkforceService:
    model_name = "NEXUSMIND Synthetic Workforce Twin Generator + Agent-Based Enterprise Simulator"
    assistant_model = "Virtual Workforce Simulation AI Assistant"
    forecast_models = [
        "Agent-based workforce simulation",
        "Big Five personality behavior model",
        "Stress propagation graph model",
        "Productivity elasticity model",
        "Project delivery Monte Carlo adapter",
        "Digital twin workforce baseline",
        "Time Machine scenario feedback adapter",
    ]
    source_systems = [
        "virtual_employee_generator",
        "employee_personality_engine",
        "behavior_modeling_engine",
        "productivity_modeling_engine",
        "stress_propagation_engine",
        "team_interaction_engine",
        "organizational_simulation_engine",
        "project_outcome_simulator",
        "hiring_impact_engine",
        "leadership_simulation_engine",
        "workforce_dashboard",
        "simulation_ai_assistant",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "company_digital_twin",
        "company_time_machine",
        "company_emotion_map",
        "multi_agent_workforce",
        "boardroom_dashboard",
        "virtual_employee_workforce_history_jsonl",
    ]

    first_names = [
        "Anika",
        "Ravi",
        "Meera",
        "Ishan",
        "Sara",
        "Kabir",
        "Lina",
        "Nikhil",
        "Maya",
        "Omar",
        "Priya",
        "Dev",
        "Aisha",
        "Rohan",
        "Tara",
        "Vikram",
    ]
    last_names = [
        "Rao",
        "Iyer",
        "Chen",
        "Mehta",
        "Shah",
        "Singh",
        "Das",
        "Patel",
        "Kapoor",
        "Nair",
        "Khan",
        "Menon",
    ]
    role_skill_map: dict[str, list[str]] = {
        "software": ["Python", "TypeScript", "FastAPI", "PostgreSQL", "Kubernetes", "System Design"],
        "data": ["Python", "ML Modeling", "Forecasting", "SQL", "Feature Engineering", "Experimentation"],
        "security": ["Threat Modeling", "IAM", "Incident Response", "Detection Engineering", "Zero Trust"],
        "product": ["Roadmapping", "User Research", "Analytics", "Stakeholder Management", "Prioritization"],
        "customer": ["Escalations", "Renewals", "QBR", "Communication", "Enterprise Support"],
        "finance": ["Forecasting", "Revenue Ops", "Controls", "Budgeting", "Scenario Planning"],
    }

    def __init__(self) -> None:
        self._cache: TTLResponseCache[VirtualWorkforceResponse] = TTLResponseCache(ttl_seconds=10)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> VirtualWorkforceResponse:
        return self._cache.get_or_set(lambda: self.simulate(WorkforceSimulationRequest()))

    def generate(self, payload: VirtualEmployeeGenerationRequest) -> VirtualWorkforceResponse:
        scenario = WorkforceSimulationRequest(
            question=f"Generate {payload.count} virtual {payload.role_family} employees for {payload.department}.",
            scenario_type="baseline",
            employee_count=payload.count,
            hiring_count=0,
            workload_delta_percent=0,
            horizon_weeks=12,
            seed=payload.seed,
        )
        return self._run(scenario, generation=payload)

    def simulate(self, payload: WorkforceSimulationRequest) -> VirtualWorkforceResponse:
        return self._run(payload)

    def ask(self, payload: VirtualEmployeeAssistantRequest) -> VirtualWorkforceAssistantResponse:
        scenario = self._scenario_from_question(payload.question, payload.horizon_weeks)
        simulation = self.simulate(scenario)
        answer = (
            f"{simulation.summary.generated_employees} virtual employees simulated {scenario.scenario_type}. "
            f"Projected productivity is {simulation.summary.average_productivity:.1f}%, stress is "
            f"{simulation.summary.average_stress:.1f}%, delivery confidence is "
            f"{simulation.summary.delivery_confidence:.1f}%, and the top action is "
            f"{simulation.recommendations[0].action}"
        )
        return VirtualWorkforceAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=scenario.scenario_type,
            answer=answer,
            simulation=simulation,
            cited_evidence=simulation.integration_evidence[:5]
            + [simulation.project_outcome.explanation]
            + [item.explanation for item in simulation.team_interactions[:2]],
            recommended_actions=[item.action for item in simulation.recommendations[:5]],
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        scenarios = [
            WorkforceSimulationRequest(question="Simulate hiring 5 engineers.", scenario_type="hiring_impact", hiring_count=5, workload_delta_percent=12),
            WorkforceSimulationRequest(question="Simulate a new supportive team lead.", scenario_type="leadership_change", manager_count=1, leadership_style="supportive", workload_delta_percent=8),
            WorkforceSimulationRequest(question="Simulate two senior engineers leaving.", scenario_type="project_outcome", resignation_count=2, workload_delta_percent=24, project_complexity=72),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.simulate(scenario)
            payload = response.model_dump(mode="json")
            payload["summary"]["stream_sequence"] = sequence
            yield f"event: virtual_employee_workforce\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.8)

    def _run(
        self,
        scenario: WorkforceSimulationRequest,
        generation: VirtualEmployeeGenerationRequest | None = None,
    ) -> VirtualWorkforceResponse:
        employees = self._generate_employees(scenario, generation)
        employees = self._apply_behavior(employees, scenario)
        team_interactions = self._team_interactions(employees, scenario)
        stress_edges = self._stress_edges(employees, scenario)
        impact_metrics = self._impact_metrics(employees, scenario, team_interactions)
        project_outcome = self._project_outcome(employees, scenario, team_interactions)
        forecast = self._forecast(employees, scenario, project_outcome, team_interactions)
        recommendations = self._recommendations(scenario, impact_metrics, project_outcome, team_interactions)
        summary = self._summary(employees, scenario, team_interactions, project_outcome)
        response = VirtualWorkforceResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            scenario=scenario,
            summary=summary,
            virtual_employees=employees,
            team_interactions=team_interactions,
            stress_propagation=stress_edges,
            impact_metrics=impact_metrics,
            forecast=forecast,
            project_outcome=project_outcome,
            recommendations=recommendations,
            assistant_summary=self._assistant_summary(scenario, summary, project_outcome, recommendations),
            integration_evidence=self._integration_evidence(scenario, project_outcome, summary),
            supported_questions=[
                "Simulate hiring 5 engineers.",
                "What happens if a new team lead joins?",
                "What happens if 2 senior engineers leave?",
                "Show stress propagation across Engineering.",
                "Simulate department restructuring.",
                "How will virtual employees affect Project Alpha?",
            ],
            source_systems=self.source_systems,
            forecast_models=self.forecast_models,
            storage=str(HISTORY_PATH),
        )
        self._persist(response)
        self._persist_registry(employees, scenario)
        return response

    def _generate_employees(
        self,
        scenario: WorkforceSimulationRequest,
        generation: VirtualEmployeeGenerationRequest | None,
    ) -> list[VirtualEmployeeAgent]:
        count = generation.count if generation else scenario.employee_count
        department = generation.department if generation else "Engineering"
        role_family = generation.role_family if generation else "Software Engineering"
        experience_mix = generation.experience_mix if generation else "balanced"
        rng = Random((generation.seed if generation else scenario.seed) + count * 37)
        model = digital_twin_simulator.company_model
        base_employees = model.employees
        employees: list[VirtualEmployeeAgent] = []
        for index in range(count):
            base = base_employees[index % len(base_employees)]
            employee_id = f"vemp-{uuid5(NAMESPACE_DNS, f'{scenario.seed}-{department}-{role_family}-{index}').hex[:10]}"
            experience_level, years = self._experience(index, experience_mix, rng)
            role = self._role(role_family, experience_level, index)
            first = self.first_names[(index + rng.randrange(len(self.first_names))) % len(self.first_names)]
            last = self.last_names[(index * 3 + rng.randrange(len(self.last_names))) % len(self.last_names)]
            personality = self._personality(rng, role_family, experience_level)
            skills = self._skills(rng, role_family, experience_level, personality)
            work = self._work_characteristics(rng, personality, base.workload)
            behavior = self._behavior_state(personality, work, scenario, base.productivity, base.burnout_risk)
            employees.append(
                VirtualEmployeeAgent(
                    identity=VirtualEmployeeIdentity(
                        employee_id=employee_id,
                        name=f"Virtual {first} {last}",
                        department=department if index >= len(base_employees) else base.department,
                        role=role,
                        experience_level=experience_level,
                        experience_years=years,
                    ),
                    skills=skills,
                    personality=personality,
                    work_characteristics=work,
                    behavior=behavior,
                    source_digital_twin=base.employee_id,
                )
            )
        return employees

    def _apply_behavior(
        self,
        employees: list[VirtualEmployeeAgent],
        scenario: WorkforceSimulationRequest,
    ) -> list[VirtualEmployeeAgent]:
        leadership_modifier = {
            "supportive": -7.0,
            "transformational": -4.0,
            "directive": 4.0,
            "hands_off": 8.0,
        }[scenario.leadership_style]
        updated: list[VirtualEmployeeAgent] = []
        avg_stress = mean(employee.behavior.stress_level for employee in employees)
        for employee in employees:
            stress_contagion = max(0, avg_stress - 55) * (0.08 + employee.personality.big_five.neuroticism / 850)
            stress = self._clip(employee.behavior.stress_level + stress_contagion + leadership_modifier)
            burnout = self._clip(
                employee.behavior.burnout_risk
                + stress_contagion * 0.9
                + max(0, scenario.workload_delta_percent) * employee.work_characteristics.burnout_sensitivity / 900
                + (scenario.resignation_count * 0.7 if scenario.resignation_count else 0)
                + leadership_modifier * 0.7
            )
            collaboration = self._clip(
                employee.behavior.collaboration
                - max(0, stress - 60) * 0.18
                + (5 if scenario.scenario_type == "hiring_impact" and employee.identity.experience_level in {"senior", "lead", "principal"} else 0)
                - scenario.restructure_intensity * 0.06
            )
            productivity = self._clip(
                employee.behavior.productivity_score
                - max(0, stress - 55) * 0.22
                - max(0, burnout - 60) * 0.18
                + (scenario.hiring_count * 0.25 if scenario.scenario_type == "hiring_impact" else 0)
                + (4 if scenario.leadership_style == "transformational" else 0)
            )
            behavior = employee.behavior.model_copy(
                update={
                    "stress_level": round(stress, 2),
                    "burnout_risk": round(burnout, 2),
                    "collaboration": round(collaboration, 2),
                    "productivity_score": round(productivity, 2),
                    "work_completion": round(self._clip(productivity * 0.72 + collaboration * 0.12 + employee.personality.big_five.conscientiousness * 0.16), 2),
                    "output_quality": round(self._clip(employee.behavior.output_quality - max(0, stress - 65) * 0.15 + employee.personality.big_five.conscientiousness * 0.05), 2),
                    "conflict_likelihood": round(self._clip(employee.behavior.conflict_likelihood + max(0, stress - 60) * 0.22 + scenario.restructure_intensity * 0.08), 2),
                    "innovation_likelihood": round(self._clip(employee.behavior.innovation_likelihood + (3 if scenario.leadership_style == "transformational" else 0) - max(0, stress - 70) * 0.12), 2),
                }
            )
            updated.append(employee.model_copy(update={"behavior": behavior}))
        return updated

    def _personality(
        self,
        rng: Random,
        role_family: str,
        experience_level: VirtualEmployeeExperienceLevel,
    ) -> VirtualEmployeePersonality:
        role = role_family.lower()
        seniority = {"junior": 0, "mid": 4, "senior": 8, "lead": 12, "principal": 14}[experience_level]
        openness = self._clip(rng.gauss(62 + ("data" in role or "product" in role) * 6 + seniority * 0.5, 12))
        conscientiousness = self._clip(rng.gauss(66 + seniority * 0.9, 10))
        extraversion = self._clip(rng.gauss(55 + ("customer" in role or "product" in role) * 8, 15))
        agreeableness = self._clip(rng.gauss(61 + ("security" not in role) * 3, 11))
        neuroticism = self._clip(rng.gauss(42 - seniority * 0.45 + ("security" in role) * 4, 13))
        collaboration = self._clip(agreeableness * 0.52 + extraversion * 0.26 + conscientiousness * 0.22)
        learning = self._clip(openness * 0.58 + conscientiousness * 0.24 + (100 - neuroticism) * 0.18)
        risk_tolerance = self._clip(openness * 0.48 + (100 - neuroticism) * 0.32 + extraversion * 0.2)
        leadership = self._clip(conscientiousness * 0.36 + extraversion * 0.3 + agreeableness * 0.2 + seniority * 1.2)
        style = "direct" if extraversion > 66 else "written-first" if extraversion < 42 else "balanced"
        preference = "pairing-heavy" if collaboration > 72 else "independent-with-syncs" if collaboration < 52 else "team-sync"
        return VirtualEmployeePersonality(
            big_five=BigFivePersonality(
                openness=round(openness, 2),
                conscientiousness=round(conscientiousness, 2),
                extraversion=round(extraversion, 2),
                agreeableness=round(agreeableness, 2),
                neuroticism=round(neuroticism, 2),
            ),
            introversion_extroversion="Extrovert" if extraversion >= 60 else "Introvert" if extraversion <= 42 else "Ambivert",
            collaborative_level=round(collaboration, 2),
            risk_tolerance=round(risk_tolerance, 2),
            learning_speed=round(learning, 2),
            communication_style=style,
            team_collaboration_preference=preference,
            leadership_tendency=round(leadership, 2),
        )

    def _skills(
        self,
        rng: Random,
        role_family: str,
        experience_level: VirtualEmployeeExperienceLevel,
        personality: VirtualEmployeePersonality,
    ) -> VirtualEmployeeSkills:
        role_key = self._role_key(role_family)
        base_skills = self.role_skill_map.get(role_key, self.role_skill_map["software"])
        experience_bonus = {"junior": 8, "mid": 18, "senior": 30, "lead": 38, "principal": 45}[experience_level]
        technical = {
            skill: round(self._clip(rng.gauss(45 + experience_bonus + index * 2.5, 9)), 2)
            for index, skill in enumerate(base_skills[:5])
        }
        soft = {
            "Communication": round(self._clip(personality.big_five.extraversion * 0.32 + personality.big_five.agreeableness * 0.42 + 18), 2),
            "Collaboration": round(personality.collaborative_level, 2),
            "Problem Solving": round(self._clip(personality.big_five.openness * 0.4 + personality.big_five.conscientiousness * 0.35 + 18), 2),
            "Conflict Resolution": round(self._clip(personality.big_five.agreeableness * 0.45 + (100 - personality.big_five.neuroticism) * 0.35 + 10), 2),
        }
        leadership = {
            "Ownership": round(self._clip(personality.big_five.conscientiousness * 0.48 + personality.leadership_tendency * 0.34 + 8), 2),
            "Mentoring": round(self._clip(personality.big_five.agreeableness * 0.38 + personality.leadership_tendency * 0.42 + 6), 2),
            "Decision Making": round(self._clip(personality.risk_tolerance * 0.3 + personality.big_five.conscientiousness * 0.42 + 12), 2),
        }
        return VirtualEmployeeSkills(technical_skills=technical, soft_skills=soft, leadership_skills=leadership)

    def _work_characteristics(
        self,
        rng: Random,
        personality: VirtualEmployeePersonality,
        baseline_workload: int,
    ) -> VirtualEmployeeWorkCharacteristics:
        focus = self._clip(personality.big_five.conscientiousness * 0.48 + (100 - personality.big_five.neuroticism) * 0.32 + rng.uniform(4, 14))
        adaptability = self._clip(personality.big_five.openness * 0.46 + personality.learning_speed * 0.36 + rng.uniform(0, 10))
        sensitivity = self._clip(34 + personality.big_five.neuroticism * 0.48 + max(0, baseline_workload - 75) * 0.7 - personality.big_five.conscientiousness * 0.12)
        tolerance = self._clip(100 - sensitivity * 0.55 + personality.big_five.extraversion * 0.2)
        productivity_pattern = "morning-deep-work" if focus >= 68 else "collaborative-bursts" if personality.collaborative_level >= 68 else "steady-generalist"
        focus_pattern = "long-focus-blocks" if tolerance < 58 else "interrupt-tolerant" if tolerance >= 72 else "moderate-focus"
        return VirtualEmployeeWorkCharacteristics(
            productivity_pattern=productivity_pattern,
            focus_pattern=focus_pattern,
            burnout_sensitivity=round(sensitivity, 2),
            adaptability=round(adaptability, 2),
            preferred_workload=round(self._clip(68 + focus * 0.16 - sensitivity * 0.08), 2),
            context_switching_tolerance=round(tolerance, 2),
        )

    def _behavior_state(
        self,
        personality: VirtualEmployeePersonality,
        work: VirtualEmployeeWorkCharacteristics,
        scenario: WorkforceSimulationRequest,
        base_productivity: int,
        base_burnout: int,
    ) -> VirtualEmployeeBehaviorState:
        workload_pressure = max(0, scenario.workload_delta_percent) * work.burnout_sensitivity / 100
        restructure_pressure = scenario.restructure_intensity * 0.08 if scenario.scenario_type == "organizational_change" else 0
        stress = self._clip(base_burnout * 0.44 + workload_pressure + restructure_pressure + scenario.resignation_count * 0.55 + personality.big_five.neuroticism * 0.22)
        burnout = self._clip(base_burnout * 0.56 + stress * 0.42 + max(0, scenario.workload_delta_percent) * 0.16)
        productivity = self._clip(base_productivity + (work.preferred_workload - 70) * 0.12 - max(0, stress - 55) * 0.26 + personality.big_five.conscientiousness * 0.05)
        collaboration = self._clip(personality.collaborative_level - max(0, stress - 65) * 0.2)
        learning = self._clip(personality.learning_speed - max(0, stress - 65) * 0.15)
        conflict = self._clip(28 + max(0, stress - 55) * 0.34 + (100 - personality.big_five.agreeableness) * 0.18)
        return VirtualEmployeeBehaviorState(
            work_completion=round(self._clip(productivity * 0.8 + personality.big_five.conscientiousness * 0.2), 2),
            collaboration=round(collaboration, 2),
            learning_progress=round(learning, 2),
            escalation_likelihood=round(self._clip(stress * 0.45 + personality.big_five.conscientiousness * 0.14), 2),
            conflict_likelihood=round(conflict, 2),
            innovation_likelihood=round(self._clip(personality.big_five.openness * 0.52 + learning * 0.26 - stress * 0.12), 2),
            stress_level=round(stress, 2),
            burnout_risk=round(burnout, 2),
            productivity_score=round(productivity, 2),
            output_quality=round(self._clip(productivity * 0.62 + personality.big_five.conscientiousness * 0.28 + learning * 0.1), 2),
        )

    def _team_interactions(
        self,
        employees: list[VirtualEmployeeAgent],
        scenario: WorkforceSimulationRequest,
    ) -> list[TeamInteractionResult]:
        grouped: dict[str, list[VirtualEmployeeAgent]] = {}
        for employee in employees:
            grouped.setdefault(employee.identity.department, []).append(employee)
        results = []
        for department, members in grouped.items():
            collaboration = mean(item.behavior.collaboration for item in members)
            communication = mean(item.skills.soft_skills["Communication"] for item in members)
            stress = mean(item.behavior.stress_level for item in members)
            variance = pstdev([item.behavior.collaboration for item in members]) if len(members) > 1 else 0
            leadership = mean(item.personality.leadership_tendency for item in members)
            knowledge = self._clip(mean(item.behavior.learning_progress for item in members) * 0.58 + mean(item.skills.soft_skills["Problem Solving"] for item in members) * 0.42)
            conflict = self._clip(mean(item.behavior.conflict_likelihood for item in members) + variance * 0.35 + max(0, stress - 65) * 0.2)
            if scenario.scenario_type == "leadership_change" and scenario.leadership_style in {"supportive", "transformational"}:
                collaboration = self._clip(collaboration + 6)
                conflict = self._clip(conflict - 7)
                leadership = self._clip(leadership + 8)
            cohesion = self._clip(collaboration * 0.38 + communication * 0.24 + knowledge * 0.18 + leadership * 0.12 - conflict * 0.18)
            results.append(
                TeamInteractionResult(
                    team_name=department,
                    collaboration_score=round(collaboration, 2),
                    knowledge_sharing_score=round(knowledge, 2),
                    communication_score=round(communication, 2),
                    cohesion_score=round(cohesion, 2),
                    conflict_risk=round(conflict, 2),
                    leadership_stability=round(leadership, 2),
                    explanation=f"{department} cohesion is driven by collaboration {collaboration:.1f}, stress {stress:.1f}, and conflict risk {conflict:.1f}.",
                )
            )
        return sorted(results, key=lambda item: item.conflict_risk, reverse=True)

    def _stress_edges(
        self,
        employees: list[VirtualEmployeeAgent],
        scenario: WorkforceSimulationRequest,
    ) -> list[StressPropagationEdge]:
        edges: list[StressPropagationEdge] = []
        by_department: dict[str, list[VirtualEmployeeAgent]] = {}
        for employee in employees:
            by_department.setdefault(employee.identity.department, []).append(employee)
        for department, members in by_department.items():
            sorted_members = sorted(members, key=lambda item: item.behavior.stress_level, reverse=True)
            if len(sorted_members) < 2:
                continue
            source = sorted_members[0]
            for target in sorted_members[1: min(5, len(sorted_members))]:
                relationship = "manager_to_team" if source.personality.leadership_tendency >= 72 else "peer_pressure"
                transfer = (
                    (source.behavior.stress_level - target.behavior.stress_level) * 0.24
                    + max(0, scenario.workload_delta_percent) * 0.08
                    - target.personality.big_five.agreeableness * 0.03
                )
                edges.append(
                    StressPropagationEdge(
                        source_employee_id=source.identity.employee_id,
                        target_employee_id=target.identity.employee_id,
                        relationship=relationship,
                        stress_transfer=round(self._clip(transfer, -25, 35), 2),
                        reason=f"{department} stress transfer from high-pressure {source.identity.role} to {target.identity.role}.",
                    )
                )
            mentor = max(members, key=lambda item: item.skills.leadership_skills["Mentoring"])
            stressed = max(members, key=lambda item: item.behavior.burnout_risk)
            if mentor.identity.employee_id != stressed.identity.employee_id:
                edges.append(
                    StressPropagationEdge(
                        source_employee_id=mentor.identity.employee_id,
                        target_employee_id=stressed.identity.employee_id,
                        relationship="mentor_support",
                        stress_transfer=round(-min(18, mentor.skills.leadership_skills["Mentoring"] * 0.16), 2),
                        reason="Mentor support dampens burnout propagation for the highest-risk employee.",
                    )
                )
        return sorted(edges, key=lambda item: item.stress_transfer, reverse=True)[:24]

    def _impact_metrics(
        self,
        employees: list[VirtualEmployeeAgent],
        scenario: WorkforceSimulationRequest,
        teams: list[TeamInteractionResult],
    ) -> list[WorkforceImpactMetric]:
        baseline = digital_twin_simulator.company_model
        base_productivity = mean(item.productivity for item in baseline.employees)
        base_stress = mean(item.burnout_risk for item in baseline.employees)
        base_collaboration = mean(item.collaboration for item in baseline.teams)
        projected_productivity = mean(item.behavior.productivity_score for item in employees)
        projected_stress = mean(item.behavior.stress_level for item in employees)
        projected_burnout = mean(item.behavior.burnout_risk for item in employees)
        projected_collaboration = mean(item.collaboration_score for item in teams)
        attrition = self._attrition_risk(employees, scenario)
        return [
            self._metric("Productivity", base_productivity, projected_productivity, "%", inverse=True),
            self._metric("Stress", base_stress, projected_stress, "%"),
            self._metric("Burnout", base_stress, projected_burnout, "%"),
            self._metric("Collaboration", base_collaboration, projected_collaboration, "%", inverse=True),
            self._metric("Attrition Risk", 24, attrition, "%"),
        ]

    def _project_outcome(
        self,
        employees: list[VirtualEmployeeAgent],
        scenario: WorkforceSimulationRequest,
        teams: list[TeamInteractionResult],
    ) -> ProjectOutcomeSimulation:
        productivity = mean(item.behavior.productivity_score for item in employees)
        burnout = mean(item.behavior.burnout_risk for item in employees)
        collaboration = mean(item.collaboration_score for item in teams) if teams else 60
        critical_loss = scenario.resignation_count * (1.8 if scenario.scenario_type == "project_outcome" else 0.9)
        hiring_relief = scenario.hiring_count * (0.55 if scenario.scenario_type == "hiring_impact" else 0.18)
        complexity = scenario.project_complexity
        delay = max(
            0,
            (complexity - productivity) * 0.12
            + max(0, burnout - 55) * 0.08
            + max(0, 64 - collaboration) * 0.1
            + critical_loss
            + max(0, scenario.workload_delta_percent) * 0.04
            - hiring_relief
            - (1.2 if scenario.leadership_style == "supportive" else 0),
        )
        quality = self._clip(productivity * 0.54 + collaboration * 0.23 + (100 - burnout) * 0.18 - complexity * 0.06)
        resource_risk = self._clip(max(0, scenario.workload_delta_percent) * 0.32 + scenario.resignation_count * 4.2 + complexity * 0.28 - scenario.hiring_count * 1.6)
        confidence = self._clip(95 - delay * 5.8 - resource_risk * 0.22 + max(0, productivity - 70) * 0.25)
        return ProjectOutcomeSimulation(
            project_name="Project Alpha Revenue Platform",
            delivery_delay_weeks=round(delay, 2),
            delivery_confidence=round(confidence, 2),
            quality_score=round(quality, 2),
            resource_risk=round(resource_risk, 2),
            expected_completion_weeks=round(max(2, 10 + delay + complexity / 26), 2),
            explanation=(
                f"Project outcome uses {len(employees)} virtual employees, productivity {productivity:.1f}, "
                f"burnout {burnout:.1f}, collaboration {collaboration:.1f}, and scenario complexity {complexity:.1f}."
            ),
        )

    def _forecast(
        self,
        employees: list[VirtualEmployeeAgent],
        scenario: WorkforceSimulationRequest,
        outcome: ProjectOutcomeSimulation,
        teams: list[TeamInteractionResult],
    ) -> list[WorkforceForecastPoint]:
        productivity = mean(item.behavior.productivity_score for item in employees)
        stress = mean(item.behavior.stress_level for item in employees)
        burnout = mean(item.behavior.burnout_risk for item in employees)
        collaboration = mean(item.collaboration_score for item in teams) if teams else 65
        attrition = self._attrition_risk(employees, scenario)
        points: list[WorkforceForecastPoint] = []
        for week in range(0, scenario.horizon_weeks + 1):
            curve = week / max(1, scenario.horizon_weeks)
            stress_drift = max(0, scenario.workload_delta_percent) * 0.08 * curve + scenario.resignation_count * 0.22 * curve
            relief = scenario.hiring_count * 0.11 * curve if scenario.scenario_type == "hiring_impact" else 0
            leader_gain = 3.2 * curve if scenario.leadership_style in {"supportive", "transformational"} else -1.8 * curve
            projected_stress = self._clip(stress + stress_drift - relief)
            projected_burnout = self._clip(burnout + stress_drift * 0.72 - relief * 0.56)
            projected_productivity = self._clip(productivity - max(0, projected_stress - 60) * 0.08 + relief * 0.34 + leader_gain)
            projected_collaboration = self._clip(collaboration + leader_gain - scenario.restructure_intensity * 0.02 * curve)
            projected_attrition = self._clip(attrition + max(0, projected_burnout - 60) * 0.06 * curve - relief * 0.2)
            delivery = self._clip(outcome.delivery_confidence - outcome.delivery_delay_weeks * 0.8 * curve + relief * 0.4)
            points.append(
                WorkforceForecastPoint(
                    week=week,
                    productivity=round(projected_productivity, 2),
                    stress=round(projected_stress, 2),
                    burnout_risk=round(projected_burnout, 2),
                    collaboration=round(projected_collaboration, 2),
                    attrition_risk=round(projected_attrition, 2),
                    delivery_confidence=round(delivery, 2),
                )
            )
        return points

    def _recommendations(
        self,
        scenario: WorkforceSimulationRequest,
        metrics: list[WorkforceImpactMetric],
        outcome: ProjectOutcomeSimulation,
        teams: list[TeamInteractionResult],
    ) -> list[WorkforceRecommendation]:
        top_metric = max(metrics, key=lambda item: abs(item.delta))
        top_team = max(teams, key=lambda item: item.conflict_risk) if teams else None
        recommendations = [
            WorkforceRecommendation(
                action=f"Contain {top_metric.metric.lower()} drift with a monitored workforce pilot before permanent rollout.",
                priority=top_metric.risk_level,
                expected_impact=f"Improves {top_metric.metric.lower()} by 6-14 points over {scenario.horizon_weeks} weeks.",
                owner_agent="Executive Agent",
                confidence=0.9,
            )
        ]
        if scenario.scenario_type == "hiring_impact":
            recommendations.append(
                WorkforceRecommendation(
                    action=f"Hire {scenario.hiring_count} engineer(s) with mentor pairing and protected onboarding capacity.",
                    priority="high" if scenario.hiring_count >= 5 else "medium",
                    expected_impact="Improves team capacity without creating onboarding drag.",
                    owner_agent="HR Agent",
                    confidence=0.87,
                )
            )
        if scenario.scenario_type == "leadership_change":
            recommendations.append(
                WorkforceRecommendation(
                    action=f"Use a {scenario.leadership_style} leadership transition plan with weekly morale checks.",
                    priority="medium",
                    expected_impact="Stabilizes collaboration and reduces conflict propagation.",
                    owner_agent="Productivity Agent",
                    confidence=0.84,
                )
            )
        if outcome.resource_risk >= 45:
            recommendations.append(
                WorkforceRecommendation(
                    action="Protect project-critical roles and move non-critical work out of the active milestone.",
                    priority="high" if outcome.resource_risk < 70 else "critical",
                    expected_impact="Reduces modeled delivery delay and resource-risk exposure.",
                    owner_agent="Project Agent",
                    confidence=0.88,
                )
            )
        if top_team and top_team.conflict_risk >= 42:
            recommendations.append(
                WorkforceRecommendation(
                    action=f"Run conflict dampening and knowledge-sharing rituals for {top_team.team_name}.",
                    priority="high" if top_team.conflict_risk >= 62 else "medium",
                    expected_impact="Reduces stress propagation between dependency owners.",
                    owner_agent="HR Agent",
                    confidence=0.82,
                )
            )
        recommendations.append(
            WorkforceRecommendation(
                action="Feed simulation outputs into Digital Twin, Time Machine, Emotion Map, and Boardroom risk panels.",
                priority="medium",
                expected_impact="Keeps executive forecasts synchronized with virtual workforce outcomes.",
                owner_agent="Executive Agent",
                confidence=0.86,
            )
        )
        return recommendations[:5]

    def _summary(
        self,
        employees: list[VirtualEmployeeAgent],
        scenario: WorkforceSimulationRequest,
        teams: list[TeamInteractionResult],
        outcome: ProjectOutcomeSimulation,
    ) -> VirtualWorkforceSummary:
        productivity = mean(employee.behavior.productivity_score for employee in employees)
        stress = mean(employee.behavior.stress_level for employee in employees)
        burnout = mean(employee.behavior.burnout_risk for employee in employees)
        conflict = mean(team.conflict_risk for team in teams) if teams else 0
        readiness = self._clip(
            outcome.delivery_confidence * 0.28
            + productivity * 0.24
            + (100 - stress) * 0.18
            + (100 - burnout) * 0.16
            + (100 - conflict) * 0.14
        )
        return VirtualWorkforceSummary(
            generated_employees=len(employees),
            simulated_weeks=scenario.horizon_weeks,
            average_productivity=round(productivity, 2),
            average_stress=round(stress, 2),
            burnout_risk=round(burnout, 2),
            team_conflict_risk=round(conflict, 2),
            delivery_confidence=round(outcome.delivery_confidence, 2),
            readiness_score=round(readiness, 2),
        )

    def _integration_evidence(
        self,
        scenario: WorkforceSimulationRequest,
        outcome: ProjectOutcomeSimulation,
        summary: VirtualWorkforceSummary,
    ) -> list[str]:
        twin_input = TwinScenarioInput(
            resignation_count=int(scenario.resignation_count),
            workload_delta_percent=int(round(scenario.workload_delta_percent)),
            budget_delta_percent=0,
            security_incident=False,
        )
        twin = digital_twin_simulator.simulate_extended(twin_input)
        evidence = [
            f"Digital Twin delay probability {twin.delay_probability}% and team-collapse probability {twin.team_collapse_probability}%.",
            f"Virtual workforce generated {summary.generated_employees} employee agents with stress {summary.average_stress:.1f}%.",
            "Integration path: Synthetic Workforce Twin Simulation -> Company Digital Twin -> Time Machine -> Emotion Map -> Executive Boardroom.",
            f"Digital twin affected departments: {', '.join(twin.affected_departments)}.",
        ]
        try:
            from app.services.time_machine_service import company_time_machine_service

            time_machine = company_time_machine_service.simulate(
                TimeMachineScenarioRequest(
                    scenario_id="virtual-workforce-sync",
                    scenario_name="Virtual workforce synchronized scenario",
                    question=scenario.question,
                    scenario_type="workload_increase",
                    horizon_months=max(1, ceil(scenario.horizon_weeks / 4)),
                    workload_delta_percent=scenario.workload_delta_percent,
                    resignation_count=scenario.resignation_count,
                )
            )
            evidence.append(
                f"Time Machine synchronized risk {time_machine.risk_level} with success probability {time_machine.success_probability:.1f}%."
            )
        except Exception:
            evidence.append("Time Machine integration degraded to local Digital Twin evidence.")
        evidence.append(
            f"Project simulator projects {outcome.delivery_delay_weeks:.1f} week delay and {outcome.delivery_confidence:.1f}% delivery confidence."
        )
        return evidence

    @staticmethod
    def _assistant_summary(
        scenario: WorkforceSimulationRequest,
        summary: VirtualWorkforceSummary,
        outcome: ProjectOutcomeSimulation,
        recommendations: list[WorkforceRecommendation],
    ) -> str:
        return (
            f"{scenario.scenario_type.replace('_', ' ').title()} simulation created {summary.generated_employees} virtual employees. "
            f"Productivity is {summary.average_productivity:.1f}%, burnout risk {summary.burnout_risk:.1f}%, "
            f"team conflict risk {summary.team_conflict_risk:.1f}%, and project delay is {outcome.delivery_delay_weeks:.1f} weeks. "
            f"Recommended action: {recommendations[0].action}"
        )

    def _scenario_from_question(self, question: str, horizon_weeks: int) -> WorkforceSimulationRequest:
        text = question.lower()
        count = self._number_from_text(text, default=5)
        if any(token in text for token in ["hire", "hiring", "add engineer", "new engineer"]):
            return WorkforceSimulationRequest(question=question, scenario_type="hiring_impact", hiring_count=count, employee_count=18 + count, workload_delta_percent=10, horizon_weeks=horizon_weeks)
        if any(token in text for token in ["manager", "lead", "director", "leadership"]):
            style = "transformational" if "transform" in text else "supportive" if "support" in text or "lead" in text else "directive"
            return WorkforceSimulationRequest(question=question, scenario_type="leadership_change", manager_count=max(1, count), leadership_style=style, workload_delta_percent=8, horizon_weeks=horizon_weeks)
        if any(token in text for token in ["resign", "leave", "loss", "senior engineer"]):
            return WorkforceSimulationRequest(question=question, scenario_type="project_outcome", resignation_count=count, workload_delta_percent=24, project_complexity=74, horizon_weeks=horizon_weeks)
        if any(token in text for token in ["restructure", "merge", "layoff", "department"]):
            return WorkforceSimulationRequest(question=question, scenario_type="organizational_change", restructure_intensity=max(20, count * 4), workload_delta_percent=18, horizon_weeks=horizon_weeks)
        if any(token in text for token in ["stress", "burnout", "propagation"]):
            return WorkforceSimulationRequest(question=question, scenario_type="stress_propagation", workload_delta_percent=28, horizon_weeks=horizon_weeks)
        return WorkforceSimulationRequest(question=question, scenario_type="baseline", workload_delta_percent=0, horizon_weeks=horizon_weeks)

    def _experience(
        self,
        index: int,
        mix: str,
        rng: Random,
    ) -> tuple[VirtualEmployeeExperienceLevel, int]:
        if mix == "junior_heavy":
            weights = [("junior", 0.38), ("mid", 0.34), ("senior", 0.18), ("lead", 0.07), ("principal", 0.03)]
        elif mix == "senior_heavy":
            weights = [("junior", 0.08), ("mid", 0.24), ("senior", 0.38), ("lead", 0.2), ("principal", 0.1)]
        elif mix == "leadership_heavy":
            weights = [("junior", 0.04), ("mid", 0.18), ("senior", 0.28), ("lead", 0.32), ("principal", 0.18)]
        else:
            weights = [("junior", 0.18), ("mid", 0.34), ("senior", 0.28), ("lead", 0.14), ("principal", 0.06)]
        value = rng.random()
        cumulative = 0.0
        level: VirtualEmployeeExperienceLevel = "mid"
        for candidate, weight in weights:
            cumulative += weight
            if value <= cumulative:
                level = candidate  # type: ignore[assignment]
                break
        years_by_level = {
            "junior": rng.randint(0, 2),
            "mid": rng.randint(3, 5),
            "senior": rng.randint(6, 9),
            "lead": rng.randint(9, 13),
            "principal": rng.randint(12, 18),
        }
        return level, years_by_level[level]

    @staticmethod
    def _role(role_family: str, level: VirtualEmployeeExperienceLevel, index: int) -> str:
        family = role_family.lower()
        prefix = {"junior": "Junior", "mid": "", "senior": "Senior", "lead": "Lead", "principal": "Principal"}[level]
        if "data" in family:
            base = "Data Scientist" if index % 2 else "ML Engineer"
        elif "security" in family:
            base = "Security Engineer"
        elif "product" in family:
            base = "Product Manager"
        elif "customer" in family:
            base = "Customer Success Manager"
        elif "finance" in family:
            base = "Finance Analyst"
        else:
            base = "Software Engineer" if index % 3 else "Platform Engineer"
        return f"{prefix} {base}".strip()

    @staticmethod
    def _role_key(role_family: str) -> str:
        text = role_family.lower()
        if "data" in text or "ml" in text or "ai" in text:
            return "data"
        if "security" in text:
            return "security"
        if "product" in text:
            return "product"
        if "customer" in text or "client" in text:
            return "customer"
        if "finance" in text:
            return "finance"
        return "software"

    @staticmethod
    def _attrition_risk(employees: list[VirtualEmployeeAgent], scenario: WorkforceSimulationRequest) -> float:
        base = mean(employee.behavior.burnout_risk * 0.42 + employee.behavior.stress_level * 0.3 + max(0, 70 - employee.behavior.productivity_score) * 0.18 for employee in employees)
        return max(0, min(100, base + scenario.resignation_count * 0.8 - scenario.hiring_count * 0.18))

    def _metric(
        self,
        name: str,
        baseline: float,
        projected: float,
        unit: str,
        inverse: bool = False,
    ) -> WorkforceImpactMetric:
        delta = projected - baseline
        risk_value = -delta if inverse else delta
        risk_level = self._risk_level(abs(risk_value))
        return WorkforceImpactMetric(
            metric=name,
            baseline=round(baseline, 2),
            projected=round(projected, 2),
            delta=round(delta, 2),
            unit=unit,
            risk_level=risk_level,
        )

    @staticmethod
    def _risk_level(value: float) -> str:
        if value >= 34:
            return "critical"
        if value >= 22:
            return "high"
        if value >= 10:
            return "medium"
        return "low"

    @staticmethod
    def _number_from_text(text: str, default: int) -> int:
        for token in text.replace(",", " ").replace(".", " ").split():
            if token.isdigit():
                return max(1, min(150, int(token)))
        return default

    @staticmethod
    def _clip(value: float, low: float = 0, high: float = 100) -> float:
        return max(low, min(high, float(value)))

    def _persist(self, response: VirtualWorkforceResponse) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(response.model_dump(mode="json")) + "\n")

    def _persist_registry(self, employees: list[VirtualEmployeeAgent], scenario: WorkforceSimulationRequest) -> None:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scenario_type": scenario.scenario_type,
            "employee_count": len(employees),
            "employees": [employee.model_dump(mode="json") for employee in employees[:50]],
        }
        with self._lock:
            with GENERATED_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


virtual_employee_workforce_service = VirtualEmployeeWorkforceService()

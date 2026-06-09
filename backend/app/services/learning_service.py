from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.ai.learning_engine import COURSE_CATALOG, CourseCatalogItem, learning_engine
from app.core.cache import TTLResponseCache
from app.schemas.learning import (
    CareerRoadmapStep,
    CourseRecommendation,
    FutureSkillForecast,
    LearningAlert,
    LearningEmployeeProfile,
    LearningPriority,
    LearningRequest,
    LearningResponse,
    LearningSummary,
    ProgressForecast,
    SkillGapInsight,
    TeamUpskillingHeatmapPoint,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "learning_recommendation_history.jsonl"


class LearningRecommendationService:
    model_name = "RandomForest + TF-IDF Learning Recommendation Engine"

    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[LearningResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def recommend(self, payload: LearningRequest | None = None) -> LearningResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._recommend_default_uncached)
        return self._recommend_uncached(payload)

    def _recommend_default_uncached(self) -> LearningResponse:
        return self._recommend_uncached(self.default_request())

    def _recommend_uncached(self, payload: LearningRequest) -> LearningResponse:
        request = payload if payload.employees else payload.model_copy(update={"employees": self.default_request().employees})
        skill_gaps = [self._skill_gap(employee, request.company_roadmap_skills) for employee in request.employees]
        course_recommendations = self._course_recommendations(request.employees, skill_gaps, request.company_roadmap_skills)
        progress_forecasts = self._progress_forecasts(request.employees, course_recommendations)
        response = LearningResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_months=request.horizon_months,
            skill_gaps=sorted(skill_gaps, key=lambda item: item.gap_score, reverse=True),
            course_recommendations=course_recommendations,
            career_roadmaps=self._career_roadmaps(request.employees, course_recommendations, request.horizon_months),
            progress_forecasts=progress_forecasts,
            team_upskilling_heatmap=self._team_heatmap(request.employees, skill_gaps, request.company_roadmap_skills),
            future_skill_forecasts=self._future_skill_forecasts(request.employees, request.company_roadmap_skills, request.horizon_months),
            learning_alerts=self._alerts(skill_gaps, course_recommendations),
            executive_insights=self._executive_insights(skill_gaps, course_recommendations, request.company_roadmap_skills),
            summary=self._summary(request.employees, skill_gaps, course_recommendations, progress_forecasts),
            source_systems=["tfidf_skill_similarity", "random_forest_ranker", "completion_forecaster", "career_growth_ai", "provider_catalog_adapters"],
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: LearningRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, market_delta=0.08, skill_pressure=("kubernetes", "mlops")),
            self._scenario_variant(base, market_delta=0.14, skill_pressure=("rag", "security", "system design")),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.recommend(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: learning\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> LearningRequest:
        return LearningRequest(
            cycle_name="FY2026 Workforce Upskilling Review",
            horizon_months=6,
            company_roadmap_skills=["kubernetes", "mlops", "rag", "security", "system design", "data engineering"],
            employees=[
                LearningEmployeeProfile(
                    employee_id="learn-001",
                    employee_name="Aarav Mehta",
                    role="Senior Backend Engineer",
                    department="Engineering",
                    team="Platform",
                    current_skills=["python", "fastapi", "postgresql", "incident response"],
                    target_role="Staff Platform Engineer",
                    career_goal="Lead cloud-native reliability platforms",
                    project_requirements=["kubernetes", "system design", "security"],
                    future_project_skills=["kubernetes", "mlops", "finops"],
                    interests=["cloud", "architecture", "reliability"],
                    certifications=["AWS Cloud Practitioner"],
                    completed_courses=["Advanced Python"],
                    performance_score=91,
                    productivity_score=87,
                    assessment_score=78,
                    promotion_readiness=0.66,
                    learning_velocity=0.74,
                    learning_hours_last_90d=24,
                    courses_completed_last_year=3,
                    manager_priority=0.88,
                    market_alignment=0.82,
                    attrition_risk=0.38,
                    burnout_risk=0.42,
                ),
                LearningEmployeeProfile(
                    employee_id="learn-002",
                    employee_name="Devika Nair",
                    role="ML Engineer",
                    department="AI Platform",
                    team="Intelligence",
                    current_skills=["python", "model evaluation", "forecasting"],
                    target_role="Senior ML Systems Engineer",
                    career_goal="Own production AI infrastructure",
                    project_requirements=["mlops", "rag", "kubernetes"],
                    future_project_skills=["vector search", "rag", "mlops"],
                    interests=["llm systems", "model operations"],
                    certifications=[],
                    completed_courses=["Machine Learning Foundations"],
                    performance_score=89,
                    productivity_score=91,
                    assessment_score=82,
                    promotion_readiness=0.58,
                    learning_velocity=0.86,
                    learning_hours_last_90d=32,
                    courses_completed_last_year=4,
                    manager_priority=0.84,
                    market_alignment=0.88,
                    attrition_risk=0.32,
                    burnout_risk=0.3,
                ),
                LearningEmployeeProfile(
                    employee_id="learn-003",
                    employee_name="Maya Iyer",
                    role="Product Designer",
                    department="Experience",
                    team="Design Systems",
                    current_skills=["ux research", "accessibility", "dashboard design"],
                    target_role="Design Strategy Lead",
                    career_goal="Lead enterprise product strategy",
                    project_requirements=["product strategy", "analytics", "frontend architecture"],
                    future_project_skills=["analytics", "ai product strategy"],
                    interests=["strategy", "analytics", "systems thinking"],
                    certifications=[],
                    completed_courses=["Design Systems Foundations"],
                    performance_score=84,
                    productivity_score=80,
                    assessment_score=75,
                    promotion_readiness=0.48,
                    learning_velocity=0.68,
                    learning_hours_last_90d=14,
                    courses_completed_last_year=2,
                    manager_priority=0.62,
                    market_alignment=0.54,
                    attrition_risk=0.2,
                    burnout_risk=0.26,
                ),
                LearningEmployeeProfile(
                    employee_id="learn-004",
                    employee_name="Omar Singh",
                    role="Engineering Manager",
                    department="Engineering",
                    team="Delivery",
                    current_skills=["leadership", "incident response", "roadmapping"],
                    target_role="Director of Engineering",
                    career_goal="Scale engineering leadership and technical strategy",
                    project_requirements=["system design", "leadership", "security"],
                    future_project_skills=["finops", "executive analytics", "zero trust"],
                    interests=["leadership", "architecture", "security"],
                    certifications=["Scrum Master"],
                    completed_courses=["Engineering Management"],
                    performance_score=90,
                    productivity_score=84,
                    assessment_score=80,
                    promotion_readiness=0.72,
                    learning_velocity=0.64,
                    learning_hours_last_90d=12,
                    courses_completed_last_year=1,
                    manager_priority=0.78,
                    market_alignment=0.7,
                    attrition_risk=0.26,
                    burnout_risk=0.58,
                ),
            ],
        )

    def _skill_gap(self, employee: LearningEmployeeProfile, roadmap_skills: list[str]) -> SkillGapInsight:
        current = {self._norm(skill) for skill in employee.current_skills + employee.certifications}
        desired_raw = employee.project_requirements + employee.future_project_skills + roadmap_skills + employee.interests
        desired = [self._norm(skill) for skill in desired_raw if self._norm(skill)]
        weighted = Counter(desired)
        missing = [skill for skill, _ in weighted.most_common() if not self._has_skill(skill, current)]
        missing = missing[:6]
        demand = sum(weighted[skill] for skill in missing)
        gap_strength = min(1, demand / max(len(set(desired)), 1) + len(missing) * 0.08)
        future_criticality = float(np.clip((employee.market_alignment * 0.35 + employee.manager_priority * 0.3 + len(set(employee.future_project_skills)) / 8 * 0.2 + employee.attrition_risk * 0.15) * 100, 0, 100))
        promotion_blocker = float(np.clip((len(missing) / 6 * 0.42 + employee.promotion_readiness * 0.28 + employee.manager_priority * 0.18 + employee.market_alignment * 0.12) * 100, 0, 100))
        gap_score = float(np.clip(gap_strength * 62 + future_criticality * 0.24 + promotion_blocker * 0.14, 0, 100))
        rationale = (
            f"{employee.employee_name} needs {', '.join(missing[:3]) if missing else 'no critical new skill'} "
            f"for {employee.target_role or employee.role}, based on project requirements and roadmap demand."
        )
        return SkillGapInsight(
            employee_id=employee.employee_id,
            employee_name=employee.employee_name,
            role=employee.role,
            department=employee.department,
            missing_skills=missing,
            gap_score=round(gap_score, 2),
            future_criticality=round(future_criticality, 2),
            promotion_blocker_score=round(promotion_blocker, 2),
            rationale=rationale,
        )

    def _course_recommendations(
        self,
        employees: list[LearningEmployeeProfile],
        gaps: list[SkillGapInsight],
        roadmap_skills: list[str],
    ) -> list[CourseRecommendation]:
        employee_by_id = {employee.employee_id: employee for employee in employees}
        items: list[CourseRecommendation] = []
        for gap in gaps:
            employee = employee_by_id[gap.employee_id]
            candidate_skills = gap.missing_skills or [skill for skill in roadmap_skills if not self._has_skill(skill, {self._norm(s) for s in employee.current_skills})]
            for skill in candidate_skills[:4]:
                query = " ".join([skill, employee.role, employee.target_role, employee.career_goal, *employee.project_requirements, *employee.interests])
                candidates = learning_engine.candidate_courses(query, top_k=4)
                best_course, semantic = self._best_course_for_skill(skill, candidates)
                gap_strength = min(1, gap.gap_score / 100)
                future = min(1, gap.future_criticality / 100)
                prediction = learning_engine.predict(employee, skill, best_course, semantic, future, gap_strength)
                items.append(
                    CourseRecommendation(
                        employee_id=employee.employee_id,
                        employee_name=employee.employee_name,
                        course_id=best_course.course_id,
                        title=best_course.title,
                        provider=best_course.provider,  # type: ignore[arg-type]
                        target_skill=skill,
                        category=best_course.category,
                        difficulty=best_course.difficulty,  # type: ignore[arg-type]
                        duration_hours=best_course.duration_hours,
                        certification=best_course.certification,
                        recommendation_score=prediction.score,
                        completion_probability=prediction.completion_probability,
                        career_impact=prediction.career_impact,
                        confidence=prediction.confidence,
                        rationale=(
                            f"Recommended for {employee.employee_name} because {skill} is a roadmap skill gap with "
                            f"{round(semantic * 100)}% semantic course-role match and {round(gap.future_criticality)} future criticality."
                        ),
                        source_model=learning_engine.model_name,
                    )
                )
        dedup: dict[tuple[str, str], CourseRecommendation] = {}
        for item in sorted(items, key=lambda rec: (rec.recommendation_score, rec.career_impact), reverse=True):
            dedup.setdefault((item.employee_id, item.target_skill), item)
        return list(dedup.values())[:14]

    @staticmethod
    def _best_course_for_skill(skill: str, candidates: list[tuple[CourseCatalogItem, float]]) -> tuple[CourseCatalogItem, float]:
        normalized = LearningRecommendationService._norm(skill)
        scored = []
        for course, semantic in candidates:
            exact = 0.22 if normalized in LearningRecommendationService._norm(course.target_skill) or LearningRecommendationService._norm(course.target_skill) in normalized else 0
            scored.append((semantic + exact, course, semantic))
        score, course, semantic = max(scored, key=lambda item: item[0])
        return course, float(min(0.99, max(semantic, score)))

    def _career_roadmaps(self, employees: list[LearningEmployeeProfile], recommendations: list[CourseRecommendation], horizon_months: int) -> list[CareerRoadmapStep]:
        by_employee: dict[str, list[CourseRecommendation]] = defaultdict(list)
        for item in recommendations:
            by_employee[item.employee_id].append(item)
        employee_by_id = {employee.employee_id: employee for employee in employees}
        steps: list[CareerRoadmapStep] = []
        for employee_id, recs in by_employee.items():
            employee = employee_by_id[employee_id]
            ordered = sorted(recs, key=lambda rec: rec.recommendation_score, reverse=True)[:3]
            for index, rec in enumerate(ordered, start=1):
                month = min(horizon_months, max(1, index * max(1, horizon_months // max(len(ordered), 1))))
                steps.append(
                    CareerRoadmapStep(
                        employee_id=employee_id,
                        employee_name=employee.employee_name,
                        month=month,
                        title=f"{rec.target_skill.title()} growth step for {employee.target_role or employee.role}",
                        focus_skills=[rec.target_skill, rec.category],
                        learning_actions=[
                            f"Complete {rec.title} on {rec.provider}.",
                            f"Apply {rec.target_skill} to one roadmap project deliverable.",
                            f"Validate progress through manager review and assessment checkpoint.",
                        ],
                        expected_outcome=f"Move toward {employee.target_role or employee.role} readiness with {round(rec.career_impact)} career-impact score.",
                        confidence=rec.confidence,
                    )
                )
        return steps

    @staticmethod
    def _progress_forecasts(employees: list[LearningEmployeeProfile], recommendations: list[CourseRecommendation]) -> list[ProgressForecast]:
        employee_by_id = {employee.employee_id: employee for employee in employees}
        forecasts: list[ProgressForecast] = []
        for rec in recommendations[:14]:
            employee = employee_by_id[rec.employee_id]
            months = float(np.clip(rec.duration_hours / max(8, employee.learning_hours_last_90d / 3 + employee.learning_velocity * 10), 1, 12))
            mastery = float(np.clip(rec.completion_probability * 0.55 + rec.recommendation_score * 0.25 + employee.assessment_score * 0.2, 0, 100))
            productivity_lift = float(np.clip((rec.career_impact * 0.12 + rec.recommendation_score * 0.08 + employee.manager_priority * 8), 2, 28))
            forecasts.append(
                ProgressForecast(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    target_skill=rec.target_skill,
                    mastery_probability=round(mastery, 2),
                    certification_completion_probability=rec.completion_probability,
                    estimated_months_to_proficiency=round(months, 1),
                    productivity_lift_estimate=round(productivity_lift, 2),
                    confidence=rec.confidence,
                )
            )
        return forecasts

    @staticmethod
    def _team_heatmap(employees: list[LearningEmployeeProfile], gaps: list[SkillGapInsight], roadmap_skills: list[str]) -> list[TeamUpskillingHeatmapPoint]:
        employee_by_id = {employee.employee_id: employee for employee in employees}
        grouped: dict[tuple[str, str], list[SkillGapInsight]] = defaultdict(list)
        roadmap = {LearningRecommendationService._norm(skill) for skill in roadmap_skills}
        for gap in gaps:
            department = gap.department
            for skill in gap.missing_skills:
                grouped[(department, skill)].append(gap)
        points: list[TeamUpskillingHeatmapPoint] = []
        for (department, skill), items in grouped.items():
            dept_employees = [employee for employee in employees if employee.department == department]
            current_coverage = sum(1 for employee in dept_employees if LearningRecommendationService._has_skill(skill, {LearningRecommendationService._norm(s) for s in employee.current_skills}))
            readiness = current_coverage / max(len(dept_employees), 1) * 100
            demand = min(100, mean(item.future_criticality for item in items) + (15 if skill in roadmap else 0))
            gap_score = min(100, mean(item.gap_score for item in items) + len(items) * 3)
            points.append(
                TeamUpskillingHeatmapPoint(
                    department=department,
                    skill=skill,
                    gap_score=round(gap_score, 2),
                    demand_score=round(demand, 2),
                    readiness_score=round(readiness, 2),
                    employees_impacted=len({item.employee_id for item in items}),
                    priority=LearningRecommendationService._priority(gap_score),
                )
            )
        return sorted(points, key=lambda point: (point.gap_score, point.demand_score), reverse=True)[:10]

    @staticmethod
    def _future_skill_forecasts(employees: list[LearningEmployeeProfile], roadmap_skills: list[str], horizon_months: int) -> list[FutureSkillForecast]:
        current_skill_sets = [{LearningRecommendationService._norm(skill) for skill in employee.current_skills} for employee in employees]
        forecasts: list[FutureSkillForecast] = []
        for index, skill in enumerate(dict.fromkeys([LearningRecommendationService._norm(s) for s in roadmap_skills if s])):
            coverage = sum(1 for skills in current_skill_sets if LearningRecommendationService._has_skill(skill, skills)) / max(len(employees), 1)
            demand = float(np.clip(58 + (len(roadmap_skills) - index) * 4 + sum(skill in [LearningRecommendationService._norm(s) for s in employee.future_project_skills] for employee in employees) * 8, 0, 100))
            readiness = coverage * 100
            shortage = float(np.clip(demand - readiness * 0.72, 0, 100))
            trend = [round(float(np.clip(demand + month * (2.2 + shortage / 80), 0, 100)), 2) for month in range(1, min(horizon_months, 8) + 1)]
            forecasts.append(
                FutureSkillForecast(
                    skill=skill,
                    demand_score=round(demand, 2),
                    current_readiness=round(readiness, 2),
                    shortage_risk=round(shortage, 2),
                    forecast=trend,
                    rationale=f"{skill} demand is driven by company roadmap and future project requirements across {len(employees)} employees.",
                )
            )
        return sorted(forecasts, key=lambda item: item.shortage_risk, reverse=True)

    @staticmethod
    def _alerts(gaps: list[SkillGapInsight], recommendations: list[CourseRecommendation]) -> list[LearningAlert]:
        alerts: list[LearningAlert] = []
        for gap in sorted(gaps, key=lambda item: item.gap_score, reverse=True)[:5]:
            if gap.gap_score >= 55:
                alerts.append(
                    LearningAlert(
                        title=f"{gap.employee_name} skill-gap risk",
                        priority=LearningRecommendationService._priority(gap.gap_score),
                        probability=gap.gap_score,
                        impact=f"Missing {', '.join(gap.missing_skills[:3])} may block {gap.role} roadmap contribution.",
                        recommendation=f"Assign targeted training for {gap.missing_skills[0] if gap.missing_skills else 'role-critical skills'} within 30 days.",
                    )
                )
        low_completion = [rec for rec in recommendations if rec.completion_probability < 50 and rec.recommendation_score >= 65]
        if low_completion:
            top = low_completion[0]
            alerts.append(
                LearningAlert(
                    title=f"{top.employee_name} learning completion risk",
                    priority="medium",
                    probability=round(100 - top.completion_probability, 2),
                    impact=f"{top.title} is high-impact but has elevated completion risk.",
                    recommendation="Reserve protected learning time and manager checkpoint cadence.",
                )
            )
        return alerts

    @staticmethod
    def _executive_insights(gaps: list[SkillGapInsight], recommendations: list[CourseRecommendation], roadmap_skills: list[str]) -> list[str]:
        if not gaps:
            return []
        top_gap = max(gaps, key=lambda item: item.gap_score)
        top_course = max(recommendations, key=lambda item: item.recommendation_score) if recommendations else None
        critical_gaps = sum(1 for gap in gaps if gap.gap_score >= 65)
        return [
            f"{top_gap.employee_name} has the highest learning gap at {round(top_gap.gap_score)} with missing skills: {', '.join(top_gap.missing_skills[:3])}.",
            f"{critical_gaps} critical skill gaps map to roadmap demand across {', '.join(roadmap_skills[:4])}.",
            f"Top course recommendation is {top_course.title} from {top_course.provider} with {round(top_course.recommendation_score)} recommendation score." if top_course else "No course recommendation exceeded the current threshold.",
        ]

    @staticmethod
    def _summary(
        employees: list[LearningEmployeeProfile],
        gaps: list[SkillGapInsight],
        recommendations: list[CourseRecommendation],
        forecasts: list[ProgressForecast],
    ) -> LearningSummary:
        readiness = 100 - (mean(gap.gap_score for gap in gaps) if gaps else 0) * 0.55 + (mean(rec.completion_probability for rec in recommendations) if recommendations else 0) * 0.25
        return LearningSummary(
            employees_analyzed=len(employees),
            recommendations_generated=len(recommendations),
            critical_skill_gaps=sum(1 for gap in gaps if gap.gap_score >= 65),
            average_gap_score=round(mean(gap.gap_score for gap in gaps) if gaps else 0, 2),
            average_completion_probability=round(mean(rec.completion_probability for rec in recommendations) if recommendations else 0, 2),
            promotion_roadmaps=sum(1 for employee in employees if employee.promotion_readiness >= 0.55),
            workforce_readiness_score=round(float(np.clip(readiness, 0, 100)), 2),
        )

    @staticmethod
    def _scenario_variant(base: LearningRequest, market_delta: float, skill_pressure: tuple[str, ...]) -> LearningRequest:
        employees = [
            employee.model_copy(
                update={
                    "market_alignment": min(1, employee.market_alignment + market_delta),
                    "manager_priority": min(1, employee.manager_priority + market_delta * 0.8),
                    "future_project_skills": list(dict.fromkeys([*employee.future_project_skills, *skill_pressure])),
                }
            )
            for employee in (base.employees or LearningRecommendationService.default_request().employees)
        ]
        return base.model_copy(update={"employees": employees, "company_roadmap_skills": list(dict.fromkeys([*base.company_roadmap_skills, *skill_pressure])), "realtime": True})

    @staticmethod
    def _priority(score: float) -> LearningPriority:
        if score >= 78:
            return "critical"
        if score >= 62:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _norm(skill: str) -> str:
        return skill.strip().lower().replace("_", " ").replace("-", " ")

    @staticmethod
    def _has_skill(skill: str, current: set[str]) -> bool:
        normalized = LearningRecommendationService._norm(skill)
        aliases = {
            "rag": {"rag", "retrieval augmented generation", "vector search", "llm systems"},
            "security": {"security", "zero trust", "threat modeling", "incident response"},
            "kubernetes": {"kubernetes", "k8s", "cka"},
            "mlops": {"mlops", "model operations", "model monitoring"},
            "system design": {"system design", "distributed systems", "architecture"},
            "analytics": {"analytics", "kpi", "business intelligence"},
            "product strategy": {"product strategy", "roadmapping", "product"},
        }
        candidates = aliases.get(normalized, {normalized})
        return any(candidate in current or any(candidate in value or value in candidate for value in current) for candidate in candidates)

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


learning_service = LearningRecommendationService()

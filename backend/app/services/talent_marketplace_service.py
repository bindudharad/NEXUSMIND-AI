from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

try:  # scikit-learn is available in the platform, but keep local fallback for demos.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - exercised only in stripped-down runtimes
    TfidfVectorizer = None  # type: ignore[assignment]
    cosine_similarity = None  # type: ignore[assignment]

from app.core.cache import TTLResponseCache
from app.schemas.talent_marketplace import (
    ExpertRanking,
    InternalRoleMatch,
    InternalRoleOpportunity,
    LearningPathRecommendation,
    MarketplaceGraphEdge,
    MarketplaceGraphNode,
    MarketplaceLearningResource,
    MarketplaceProjectOpportunity,
    MentorMatch,
    ProjectMatch,
    ReputationScore,
    SkillBadge,
    SkillIntelligencePoint,
    TalentAssistantIntent,
    TalentAssistantRequest,
    TalentAssistantResponse,
    TalentMarketplaceProfile,
    TalentMarketplaceRequest,
    TalentMarketplaceResponse,
    TalentMarketplaceSummary,
    TalentRecommendation,
    TalentRiskLevel,
    TalentSearchRequest,
    TalentSearchResponse,
    TalentSearchResult,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "talent_marketplace_history.jsonl"


class TalentMarketplaceService:
    model_name = "Internal Talent Marketplace Graph + TF-IDF Recommendation Engine"
    source_systems = [
        "talent_profile_engine",
        "skill_intelligence_engine",
        "project_matching_engine",
        "mentor_matching_engine",
        "internal_job_matching_engine",
        "learning_recommendation_engine",
        "reputation_engine",
        "marketplace_dashboard",
        "talent_ai_assistant",
        "employee_digital_twin",
        "knowledge_brain",
        "project_intelligence",
        "workflow_automation",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[TalentMarketplaceResponse] = TTLResponseCache(ttl_seconds=10)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> TalentMarketplaceResponse:
        return self._cache.get_or_set(lambda: self.analyze(self.default_request(), persist=True))

    def analyze(self, payload: TalentMarketplaceRequest | None = None, persist: bool = True) -> TalentMarketplaceResponse:
        request = self._hydrate(payload or self.default_request())
        skill_points = self._skill_intelligence(request)
        project_matches = self._project_matches(request.profiles, request.projects)
        mentor_matches = self._mentor_matches(request.profiles, skill_points)
        role_matches = self._role_matches(request.profiles, request.internal_roles)
        learning_paths = self._learning_paths(request.profiles, request.learning_catalog, skill_points, role_matches, project_matches)
        expert_rankings = self._expert_rankings(skill_points)
        reputation_scores = self._reputation_scores(request.profiles, expert_rankings, mentor_matches, project_matches)
        badges = self._badges(skill_points, reputation_scores, mentor_matches)
        graph_nodes, graph_edges = self._graph(request, skill_points, project_matches, mentor_matches, role_matches, learning_paths, badges)
        recommendations = self._recommendations(request, skill_points, project_matches, mentor_matches, role_matches, learning_paths, reputation_scores)
        summary = self._summary(request.profiles, skill_points, project_matches, mentor_matches, role_matches, learning_paths, expert_rankings, reputation_scores, badges)
        response = TalentMarketplaceResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            profiles=request.profiles,
            skill_intelligence=skill_points,
            project_matches=project_matches,
            mentor_matches=mentor_matches,
            internal_role_matches=role_matches,
            learning_paths=learning_paths,
            expert_rankings=expert_rankings,
            reputation_scores=reputation_scores,
            badges=badges,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            recommendations=recommendations,
            assistant_prompts=[
                "Find AI projects for me.",
                "Who can mentor me on Kubernetes?",
                "What skills should I learn?",
                "Show internal job opportunities.",
                "Who is our best Kubernetes expert?",
            ],
            summary=summary,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        if persist:
            self._append_jsonl(response.model_dump(mode="json"))
        return response

    def search(self, payload: TalentSearchRequest) -> TalentSearchResponse:
        analysis = self.default()
        query = payload.query
        records: list[tuple[str, str, str, str, list[str]]] = []
        for profile in analysis.profiles:
            skills = profile.skills + profile.expertise_areas + profile.offered_expertise
            text = self._profile_text(profile)
            records.append((profile.employee_id, "employee", profile.employee_name, text, skills))
        for project in self.default_request().projects:
            records.append((project.project_id, "project", project.title, self._project_text(project), project.required_skills + project.stretch_skills))
        for role in self.default_request().internal_roles:
            records.append((role.role_id, "role", role.title, self._role_text(role), role.required_skills + role.preferred_skills))
        for resource in self.default_request().learning_catalog:
            records.append((resource.resource_id, "learning", resource.title, self._resource_text(resource), resource.target_skills))
        scored = []
        for entity_id, entity_type, title, text, skills in records:
            score = self._similarity(query, text) * 100
            matched = [skill for skill in skills if self._has_skill(skill, self._tokens(query))]
            if score > 0 or matched:
                scored.append(
                    TalentSearchResult(
                        entity_id=entity_id,
                        entity_type=entity_type,  # type: ignore[arg-type]
                        title=title,
                        score=round(max(score, min(100, len(matched) * 18)), 2),
                        matched_skills=matched[:8],
                        summary=text[:220],
                    )
                )
        return TalentSearchResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            query=query,
            results=sorted(scored, key=lambda item: item.score, reverse=True)[: payload.limit],
            source_systems=["semantic_talent_search", "skill_graph", "internal_marketplace_index"],
        )

    def ask(self, payload: TalentAssistantRequest) -> TalentAssistantResponse:
        analysis = self.default()
        intent = self._assistant_intent(payload.question)
        answer, confidence, profiles, opportunities, actions, evidence = self._assistant_answer(intent, payload.question, analysis, payload.employee_id)
        return TalentAssistantResponse(
            model="Talent AI Assistant",
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=confidence,
            cited_profiles=profiles,
            cited_opportunities=opportunities,
            recommended_actions=actions,
            evidence=evidence,
            source_systems=["talent_ai_assistant", "recommendation_router", "marketplace_graph", "semantic_search"],
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        base = self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, add_capacity=4, focus_skill="kubernetes"),
            self._scenario_variant(base, add_capacity=8, focus_skill="mlops"),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: talent_marketplace\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> TalentMarketplaceRequest:
        return TalentMarketplaceRequest(
            focus_skills=["python", "kubernetes", "mlops", "rag", "security", "system design", "data engineering", "mentoring"],
            profiles=[
                TalentMarketplaceProfile(
                    employee_id="talent-001",
                    employee_name="Lina Chen",
                    role="Senior Platform Engineer",
                    department="Engineering",
                    location="Bangalore",
                    skills=["python", "kubernetes", "mlops", "incident response", "observability"],
                    experience_years=8,
                    certifications=["CKA", "AWS Solutions Architect"],
                    projects=["Kubernetes rollout", "Model serving reliability", "Incident command automation"],
                    achievements=["Reduced production incident recovery time by 38%", "Built reusable deployment runbooks"],
                    interests=["platform architecture", "ai infrastructure"],
                    career_goals=["Principal AI Platform Architect"],
                    learning_goals=["rag", "vector search"],
                    expertise_areas=["kubernetes", "mlops", "incident response"],
                    offered_expertise=["kubernetes", "incident response", "mlops"],
                    capacity_hours=40,
                    allocated_hours=30,
                    performance_score=92,
                    learning_velocity=0.82,
                    mentorship_hours=34,
                    knowledge_contributions=18,
                    reputation_events=24,
                ),
                TalentMarketplaceProfile(
                    employee_id="talent-002",
                    employee_name="Sarah Malik",
                    role="Cloud Security Architect",
                    department="Security",
                    location="Hyderabad",
                    skills=["security", "zero trust", "kubernetes", "threat modeling", "terraform"],
                    experience_years=10,
                    certifications=["CISSP", "AWS Security Specialty"],
                    projects=["Zero trust gateway", "Data export guardrails", "Ransomware tabletop"],
                    achievements=["Created access review policy adopted across three departments"],
                    interests=["cloud governance", "security automation"],
                    career_goals=["Director of Security Architecture"],
                    learning_goals=["mlops security"],
                    expertise_areas=["security", "zero trust", "terraform"],
                    offered_expertise=["security", "threat modeling", "zero trust"],
                    capacity_hours=40,
                    allocated_hours=36,
                    performance_score=90,
                    learning_velocity=0.7,
                    mentorship_hours=42,
                    knowledge_contributions=16,
                    reputation_events=21,
                ),
                TalentMarketplaceProfile(
                    employee_id="talent-003",
                    employee_name="Devika Nair",
                    role="ML Engineer",
                    department="AI Platform",
                    location="Remote",
                    skills=["python", "forecasting", "model evaluation", "rag", "vector search"],
                    experience_years=5,
                    certifications=["Machine Learning Specialization"],
                    projects=["RAG assistant evaluation", "Forecasting service", "Embedding retrieval quality"],
                    achievements=["Improved retrieval relevance by 24%", "Built model evaluation rubric"],
                    interests=["llm systems", "model operations"],
                    career_goals=["Senior ML Systems Engineer"],
                    learning_goals=["kubernetes", "mlops"],
                    expertise_areas=["rag", "forecasting", "python"],
                    offered_expertise=["rag", "forecasting"],
                    capacity_hours=40,
                    allocated_hours=28,
                    performance_score=88,
                    learning_velocity=0.9,
                    mentorship_hours=12,
                    knowledge_contributions=14,
                    reputation_events=19,
                ),
                TalentMarketplaceProfile(
                    employee_id="talent-004",
                    employee_name="Aarav Mehta",
                    role="Backend Engineer",
                    department="Engineering",
                    location="Pune",
                    skills=["python", "fastapi", "postgresql", "api reliability"],
                    experience_years=4,
                    certifications=["AWS Cloud Practitioner"],
                    projects=["Billing API stabilization", "PostgreSQL migration"],
                    achievements=["Reduced API latency by 31%"],
                    interests=["cloud", "architecture", "reliability"],
                    career_goals=["Staff Backend Engineer"],
                    learning_goals=["kubernetes", "system design", "mlops"],
                    expertise_areas=["fastapi", "postgresql"],
                    offered_expertise=["fastapi", "postgresql"],
                    capacity_hours=40,
                    allocated_hours=25,
                    performance_score=84,
                    learning_velocity=0.76,
                    mentorship_hours=4,
                    knowledge_contributions=7,
                    reputation_events=10,
                ),
                TalentMarketplaceProfile(
                    employee_id="talent-005",
                    employee_name="Maya Iyer",
                    role="Product Design Lead",
                    department="Experience",
                    location="Bangalore",
                    skills=["ux research", "dashboard design", "accessibility", "product strategy"],
                    experience_years=7,
                    certifications=["Design Systems Advanced"],
                    projects=["Executive dashboard redesign", "Accessibility audit", "Product analytics review"],
                    achievements=["Raised dashboard task completion by 22%"],
                    interests=["ai product strategy", "analytics"],
                    career_goals=["Design Strategy Director"],
                    learning_goals=["analytics", "ai product strategy"],
                    expertise_areas=["dashboard design", "ux research"],
                    offered_expertise=["dashboard design", "accessibility"],
                    capacity_hours=40,
                    allocated_hours=29,
                    performance_score=86,
                    learning_velocity=0.68,
                    mentorship_hours=18,
                    knowledge_contributions=11,
                    reputation_events=17,
                ),
            ],
            projects=[
                MarketplaceProjectOpportunity(
                    project_id="market-proj-001",
                    title="AI Knowledge Brain Graph Expansion",
                    department="AI Platform",
                    description="Expand RAG graph relationships, expert discovery, and vector search quality.",
                    required_skills=["python", "rag", "vector search", "mlops"],
                    stretch_skills=["kubernetes", "knowledge graph"],
                    priority=5,
                    duration_weeks=10,
                    open_slots=2,
                    reputation_boost=18,
                    business_impact=88,
                ),
                MarketplaceProjectOpportunity(
                    project_id="market-proj-002",
                    title="Zero Trust Data Export Automation",
                    department="Security",
                    description="Automate policy checks for sensitive export workflows.",
                    required_skills=["security", "zero trust", "terraform", "kubernetes"],
                    stretch_skills=["threat modeling", "python"],
                    priority=5,
                    duration_weeks=8,
                    open_slots=2,
                    reputation_boost=16,
                    business_impact=82,
                ),
                MarketplaceProjectOpportunity(
                    project_id="market-proj-003",
                    title="Executive Workforce Intelligence Dashboard",
                    department="Experience",
                    description="Create executive-grade workforce intelligence workflow views.",
                    required_skills=["dashboard design", "ux research", "analytics", "product strategy"],
                    stretch_skills=["accessibility", "ai product strategy"],
                    priority=4,
                    duration_weeks=6,
                    open_slots=2,
                    reputation_boost=12,
                    business_impact=74,
                ),
            ],
            internal_roles=[
                InternalRoleOpportunity(
                    role_id="role-001",
                    title="Principal AI Platform Architect",
                    department="AI Platform",
                    level="Principal",
                    required_skills=["python", "kubernetes", "mlops", "system design"],
                    preferred_skills=["rag", "incident response", "leadership"],
                    career_track="technical_leadership",
                    growth_score=92,
                    vacancy_urgency=74,
                ),
                InternalRoleOpportunity(
                    role_id="role-002",
                    title="Senior ML Systems Engineer",
                    department="AI Platform",
                    level="Senior",
                    required_skills=["python", "rag", "mlops", "model evaluation"],
                    preferred_skills=["kubernetes", "vector search"],
                    career_track="ai_engineering",
                    growth_score=88,
                    vacancy_urgency=67,
                ),
                InternalRoleOpportunity(
                    role_id="role-003",
                    title="Security Automation Lead",
                    department="Security",
                    level="Lead",
                    required_skills=["security", "terraform", "zero trust", "python"],
                    preferred_skills=["kubernetes", "threat modeling"],
                    career_track="security_leadership",
                    growth_score=84,
                    vacancy_urgency=71,
                ),
            ],
            learning_catalog=[
                MarketplaceLearningResource(
                    resource_id="learn-market-001",
                    title="Production Kubernetes for AI Platforms",
                    provider="Internal Academy",
                    target_skills=["kubernetes", "mlops"],
                    duration_hours=28,
                    difficulty="advanced",
                    certification="Kubernetes AI Platform Badge",
                ),
                MarketplaceLearningResource(
                    resource_id="learn-market-002",
                    title="RAG Systems and Vector Search Evaluation",
                    provider="NEXUSMIND Knowledge Guild",
                    target_skills=["rag", "vector search", "model evaluation"],
                    duration_hours=22,
                    difficulty="advanced",
                    certification="RAG Systems Badge",
                ),
                MarketplaceLearningResource(
                    resource_id="learn-market-003",
                    title="Secure Cloud Automation with Terraform",
                    provider="Security Guild",
                    target_skills=["terraform", "security", "zero trust"],
                    duration_hours=20,
                    difficulty="intermediate",
                    certification="Cloud Security Automation Badge",
                ),
                MarketplaceLearningResource(
                    resource_id="learn-market-004",
                    title="Enterprise System Design for Staff Engineers",
                    provider="Architecture Council",
                    target_skills=["system design", "architecture", "leadership"],
                    duration_hours=32,
                    difficulty="expert",
                    certification="Staff Architecture Badge",
                ),
            ],
        )

    def _hydrate(self, request: TalentMarketplaceRequest) -> TalentMarketplaceRequest:
        defaults = self.default_request()
        return request.model_copy(
            update={
                "profiles": request.profiles or defaults.profiles,
                "projects": request.projects or defaults.projects,
                "internal_roles": request.internal_roles or defaults.internal_roles,
                "learning_catalog": request.learning_catalog or defaults.learning_catalog,
                "focus_skills": request.focus_skills or defaults.focus_skills,
            }
        )

    def _skill_intelligence(self, request: TalentMarketplaceRequest) -> list[SkillIntelligencePoint]:
        catalog = self._skill_catalog(request)
        points: list[SkillIntelligencePoint] = []
        for profile in request.profiles:
            profile_skill_set = {self._norm(skill) for skill in profile.skills + profile.expertise_areas + profile.offered_expertise}
            text = self._profile_text(profile)
            visible = sorted(profile_skill_set)
            hidden = sorted(skill for skill in catalog if skill not in profile_skill_set and self._skill_in_text(skill, text))
            for skill in visible + hidden:
                evidence = self._skill_evidence(profile, skill, hidden_skill=skill in hidden)
                base = 34 + min(profile.experience_years, 15) * 2.1 + profile.performance_score * 0.22
                base += 10 if skill in {self._norm(s) for s in profile.expertise_areas} else 0
                base += 8 if skill in {self._norm(s) for s in profile.offered_expertise} else 0
                base += 5 * sum(1 for item in profile.projects + profile.achievements + profile.certifications if skill in self._norm(item))
                base += min(10, profile.knowledge_contributions * 0.3)
                if skill in hidden:
                    base = min(base, 82)
                gap_to_goal = any(skill in self._norm(goal) for goal in profile.career_goals + profile.learning_goals)
                points.append(
                    SkillIntelligencePoint(
                        employee_id=profile.employee_id,
                        employee_name=profile.employee_name,
                        skill=skill,
                        proficiency_score=round(self._clip(base), 2),
                        evidence=evidence,
                        hidden_skill=skill in hidden,
                        market_relevance=round(self._market_relevance(skill, request), 2),
                        gap_to_goal=gap_to_goal,
                    )
                )
        return sorted(points, key=lambda item: (item.proficiency_score, item.market_relevance), reverse=True)

    def _project_matches(self, profiles: list[TalentMarketplaceProfile], projects: list[MarketplaceProjectOpportunity]) -> list[ProjectMatch]:
        matches: list[ProjectMatch] = []
        for profile in profiles:
            if not profile.wants_projects:
                continue
            profile_text = self._profile_text(profile)
            available = max(0, profile.capacity_hours - profile.allocated_hours)
            skill_set = self._profile_skill_set(profile)
            for project in projects:
                required = [self._norm(skill) for skill in project.required_skills]
                covered = [skill for skill in required if self._has_skill(skill, skill_set)]
                missing = [skill for skill in required if skill not in covered]
                coverage = len(covered) / max(len(required), 1) * 100
                capacity = self._clip(available / max(project.duration_weeks * 1.5 / max(project.open_slots, 1), 1) * 100)
                semantic = self._similarity(profile_text, self._project_text(project)) * 100
                growth = self._interest_fit(profile, project.required_skills + project.stretch_skills)
                score = self._clip(coverage * 0.46 + semantic * 0.2 + capacity * 0.14 + growth * 0.12 + profile.performance_score * 0.06 + project.priority * 2.2)
                if score >= 42:
                    matches.append(
                        ProjectMatch(
                            employee_id=profile.employee_id,
                            employee_name=profile.employee_name,
                            project_id=project.project_id,
                            project_title=project.title,
                            match_score=round(score, 2),
                            skill_coverage=round(coverage, 2),
                            capacity_fit=round(capacity, 2),
                            growth_fit=round(growth, 2),
                            missing_skills=missing[:8],
                            rationale=f"{profile.employee_name} covers {round(coverage)}% of required skills with {round(available, 1)} available hours and {round(growth)}% growth alignment.",
                        )
                    )
        return sorted(matches, key=lambda item: item.match_score, reverse=True)[:18]

    def _mentor_matches(self, profiles: list[TalentMarketplaceProfile], skill_points: list[SkillIntelligencePoint]) -> list[MentorMatch]:
        skill_scores: dict[tuple[str, str], float] = {(p.employee_id, p.skill): p.proficiency_score for p in skill_points}
        matches: list[MentorMatch] = []
        for mentor in profiles:
            offered = {self._norm(skill) for skill in mentor.offered_expertise + mentor.expertise_areas + mentor.skills}
            if not offered:
                continue
            for mentee in profiles:
                if mentor.employee_id == mentee.employee_id or not mentee.wants_mentorship:
                    continue
                targets = [self._norm(skill) for skill in mentee.learning_goals + mentee.career_goals + mentee.interests]
                topics = sorted({skill for skill in offered if any(self._has_skill(skill, {target}) or skill in target for target in targets)})
                if not topics:
                    mentee_skills = self._profile_skill_set(mentee)
                    topics = sorted(skill for skill in offered if not self._has_skill(skill, mentee_skills))[:2]
                for topic in topics[:2]:
                    expertise = skill_scores.get((mentor.employee_id, topic), 55)
                    score = self._clip(expertise * 0.54 + mentor.mentorship_hours * 0.28 + mentor.performance_score * 0.18 + mentor.knowledge_contributions * 0.7)
                    if score >= 55:
                        matches.append(
                            MentorMatch(
                                mentor_id=mentor.employee_id,
                                mentor_name=mentor.employee_name,
                                mentee_id=mentee.employee_id,
                                mentee_name=mentee.employee_name,
                                topic=topic,
                                match_score=round(score, 2),
                                rationale=f"{mentor.employee_name} has strong {topic} evidence and mentorship capacity for {mentee.employee_name}.",
                            )
                        )
        return sorted(matches, key=lambda item: item.match_score, reverse=True)[:16]

    def _role_matches(self, profiles: list[TalentMarketplaceProfile], roles: list[InternalRoleOpportunity]) -> list[InternalRoleMatch]:
        matches: list[InternalRoleMatch] = []
        for profile in profiles:
            if not profile.wants_internal_roles:
                continue
            skill_set = self._profile_skill_set(profile)
            profile_text = self._profile_text(profile)
            for role in roles:
                required = [self._norm(skill) for skill in role.required_skills]
                preferred = [self._norm(skill) for skill in role.preferred_skills]
                required_coverage = sum(1 for skill in required if self._has_skill(skill, skill_set)) / max(len(required), 1) * 100
                preferred_coverage = sum(1 for skill in preferred if self._has_skill(skill, skill_set)) / max(len(preferred), 1) * 100
                semantic = self._similarity(profile_text, self._role_text(role)) * 100
                goal_fit = self._interest_fit(profile, [role.title, role.career_track, *role.required_skills, *role.preferred_skills])
                readiness = self._clip(required_coverage * 0.45 + preferred_coverage * 0.15 + profile.performance_score * 0.24 + min(profile.experience_years * 3, 30) + goal_fit * 0.08)
                score = self._clip(readiness * 0.58 + semantic * 0.18 + role.growth_score * 0.16 + role.vacancy_urgency * 0.08)
                missing = [skill for skill in required if not self._has_skill(skill, skill_set)]
                if score >= 48:
                    matches.append(
                        InternalRoleMatch(
                            employee_id=profile.employee_id,
                            employee_name=profile.employee_name,
                            role_id=role.role_id,
                            role_title=role.title,
                            match_score=round(score, 2),
                            promotion_readiness=round(readiness, 2),
                            missing_skills=missing,
                            rationale=f"{profile.employee_name} has {round(readiness)}% readiness for {role.title} with {round(required_coverage)}% required-skill coverage.",
                        )
                    )
        return sorted(matches, key=lambda item: item.match_score, reverse=True)[:16]

    def _learning_paths(
        self,
        profiles: list[TalentMarketplaceProfile],
        catalog: list[MarketplaceLearningResource],
        skill_points: list[SkillIntelligencePoint],
        role_matches: list[InternalRoleMatch],
        project_matches: list[ProjectMatch],
    ) -> list[LearningPathRecommendation]:
        known: dict[str, set[str]] = defaultdict(set)
        for point in skill_points:
            if point.proficiency_score >= 68:
                known[point.employee_id].add(point.skill)
        target_skills: dict[str, Counter[str]] = defaultdict(Counter)
        for profile in profiles:
            for skill in profile.learning_goals:
                target_skills[profile.employee_id][self._norm(skill)] += 3
            for goal in profile.career_goals:
                for token in self._tokens(goal):
                    if len(token) > 3:
                        target_skills[profile.employee_id][token] += 1
        for match in role_matches[:10]:
            for skill in match.missing_skills:
                target_skills[match.employee_id][self._norm(skill)] += 4
        for match in project_matches[:12]:
            for skill in match.missing_skills:
                target_skills[match.employee_id][self._norm(skill)] += 3
        by_id = {profile.employee_id: profile for profile in profiles}
        paths: list[LearningPathRecommendation] = []
        for employee_id, weighted in target_skills.items():
            profile = by_id[employee_id]
            for skill, weight in weighted.most_common(4):
                if self._has_skill(skill, known[employee_id]):
                    continue
                resource = self._best_resource(skill, catalog)
                fit = self._similarity(skill, self._resource_text(resource)) * 100
                score = self._clip(48 + weight * 8 + fit * 0.22 + profile.learning_velocity * 18 + profile.performance_score * 0.08)
                weeks = max(1.0, round(resource.duration_hours / max(4.0, profile.learning_velocity * 7.5 + 2), 1))
                paths.append(
                    LearningPathRecommendation(
                        employee_id=employee_id,
                        employee_name=profile.employee_name,
                        target_skill=skill,
                        resource_id=resource.resource_id,
                        title=resource.title,
                        duration_hours=resource.duration_hours,
                        recommendation_score=round(score, 2),
                        estimated_weeks_to_proficiency=weeks,
                        rationale=f"{skill} closes a project or role gap for {profile.employee_name}; {resource.title} is the closest catalog match.",
                    )
                )
        return sorted(paths, key=lambda item: item.recommendation_score, reverse=True)[:18]

    def _expert_rankings(self, skill_points: list[SkillIntelligencePoint]) -> list[ExpertRanking]:
        grouped: dict[str, list[SkillIntelligencePoint]] = defaultdict(list)
        for point in skill_points:
            grouped[point.skill].append(point)
        rankings: list[ExpertRanking] = []
        for skill, points in grouped.items():
            for point in sorted(points, key=lambda item: item.proficiency_score, reverse=True)[:3]:
                rankings.append(
                    ExpertRanking(
                        skill=skill,
                        employee_id=point.employee_id,
                        employee_name=point.employee_name,
                        score=point.proficiency_score,
                        evidence=point.evidence[:4],
                    )
                )
        return sorted(rankings, key=lambda item: (item.skill, -item.score))

    def _reputation_scores(
        self,
        profiles: list[TalentMarketplaceProfile],
        expert_rankings: list[ExpertRanking],
        mentor_matches: list[MentorMatch],
        project_matches: list[ProjectMatch],
    ) -> list[ReputationScore]:
        expert_counts = Counter(item.employee_id for item in expert_rankings if item.score >= 75)
        mentor_counts = Counter(item.mentor_id for item in mentor_matches)
        project_counts = Counter(item.employee_id for item in project_matches if item.match_score >= 70)
        scores: list[ReputationScore] = []
        for profile in profiles:
            contribution = self._clip(profile.reputation_events * 2.4 + profile.performance_score * 0.36 + project_counts[profile.employee_id] * 6)
            knowledge = self._clip(profile.knowledge_contributions * 4 + expert_counts[profile.employee_id] * 8 + len(profile.certifications) * 4)
            mentorship = self._clip(profile.mentorship_hours * 1.25 + mentor_counts[profile.employee_id] * 9)
            innovation = self._clip(len(profile.achievements) * 8 + len(profile.projects) * 4 + profile.learning_velocity * 18)
            total = mean([contribution, knowledge, mentorship, innovation])
            scores.append(
                ReputationScore(
                    employee_id=profile.employee_id,
                    employee_name=profile.employee_name,
                    contribution_score=round(contribution, 2),
                    knowledge_score=round(knowledge, 2),
                    mentorship_score=round(mentorship, 2),
                    innovation_score=round(innovation, 2),
                    total_reputation=round(total, 2),
                )
            )
        return sorted(scores, key=lambda item: item.total_reputation, reverse=True)

    def _badges(self, skill_points: list[SkillIntelligencePoint], reputation_scores: list[ReputationScore], mentors: list[MentorMatch]) -> list[SkillBadge]:
        badges: list[SkillBadge] = []
        mentor_counts = Counter(match.mentor_id for match in mentors)
        by_employee = {score.employee_id: score for score in reputation_scores}
        for point in skill_points:
            if point.proficiency_score < 68:
                continue
            badges.append(
                SkillBadge(
                    employee_id=point.employee_id,
                    employee_name=point.employee_name,
                    badge=f"{point.skill.title()} Badge",
                    level=self._badge_level(point.proficiency_score),
                    score=point.proficiency_score,
                    evidence=point.evidence[:3],
                )
            )
        for employee_id, rep in by_employee.items():
            if rep.total_reputation >= 72:
                badges.append(
                    SkillBadge(
                        employee_id=employee_id,
                        employee_name=rep.employee_name,
                        badge="Internal Reputation Builder",
                        level=self._badge_level(rep.total_reputation),
                        score=rep.total_reputation,
                        evidence=[f"contribution={rep.contribution_score}", f"knowledge={rep.knowledge_score}", f"mentorship={rep.mentorship_score}"],
                    )
                )
            if mentor_counts[employee_id] >= 2:
                badges.append(
                    SkillBadge(
                        employee_id=employee_id,
                        employee_name=rep.employee_name,
                        badge="Mentor Gold",
                        level="gold",
                        score=min(100, 70 + mentor_counts[employee_id] * 6),
                        evidence=[f"mentor_matches={mentor_counts[employee_id]}", f"mentorship_score={rep.mentorship_score}"],
                    )
                )
        return sorted(badges, key=lambda item: item.score, reverse=True)[:30]

    def _graph(
        self,
        request: TalentMarketplaceRequest,
        skill_points: list[SkillIntelligencePoint],
        project_matches: list[ProjectMatch],
        mentor_matches: list[MentorMatch],
        role_matches: list[InternalRoleMatch],
        learning_paths: list[LearningPathRecommendation],
        badges: list[SkillBadge],
    ) -> tuple[list[MarketplaceGraphNode], list[MarketplaceGraphEdge]]:
        nodes: dict[str, MarketplaceGraphNode] = {}
        edges: list[MarketplaceGraphEdge] = []
        for profile in request.profiles:
            nodes[profile.employee_id] = MarketplaceGraphNode(id=profile.employee_id, label=profile.employee_name, type="employee", score=profile.performance_score)
        for project in request.projects:
            nodes[project.project_id] = MarketplaceGraphNode(id=project.project_id, label=project.title, type="project", score=project.business_impact)
        for role in request.internal_roles:
            nodes[role.role_id] = MarketplaceGraphNode(id=role.role_id, label=role.title, type="role", score=role.growth_score)
        for resource in request.learning_catalog:
            nodes[resource.resource_id] = MarketplaceGraphNode(id=resource.resource_id, label=resource.title, type="learning", score=70)
        for point in skill_points[:80]:
            skill_id = f"skill:{point.skill}"
            nodes.setdefault(skill_id, MarketplaceGraphNode(id=skill_id, label=point.skill.title(), type="skill", score=point.market_relevance))
            if point.proficiency_score >= 55:
                edges.append(MarketplaceGraphEdge(source=point.employee_id, target=skill_id, relationship="HAS_SKILL", weight=point.proficiency_score))
        for match in project_matches[:20]:
            edges.append(MarketplaceGraphEdge(source=match.employee_id, target=match.project_id, relationship="MATCHES_PROJECT", weight=match.match_score))
        for match in mentor_matches[:20]:
            edges.append(MarketplaceGraphEdge(source=match.mentor_id, target=match.mentee_id, relationship=f"MENTORS:{match.topic}", weight=match.match_score))
        for match in role_matches[:20]:
            edges.append(MarketplaceGraphEdge(source=match.employee_id, target=match.role_id, relationship="MATCHES_ROLE", weight=match.match_score))
        for path in learning_paths[:20]:
            edges.append(MarketplaceGraphEdge(source=path.employee_id, target=path.resource_id, relationship=f"LEARNS:{path.target_skill}", weight=path.recommendation_score))
        for badge in badges[:15]:
            badge_id = f"badge:{badge.employee_id}:{self._norm(badge.badge)}"
            nodes[badge_id] = MarketplaceGraphNode(id=badge_id, label=badge.badge, type="badge", score=badge.score)
            edges.append(MarketplaceGraphEdge(source=badge.employee_id, target=badge_id, relationship="EARNS_BADGE", weight=badge.score))
        return list(nodes.values()), edges

    def _recommendations(
        self,
        request: TalentMarketplaceRequest,
        skill_points: list[SkillIntelligencePoint],
        project_matches: list[ProjectMatch],
        mentor_matches: list[MentorMatch],
        role_matches: list[InternalRoleMatch],
        learning_paths: list[LearningPathRecommendation],
        reputation_scores: list[ReputationScore],
    ) -> list[TalentRecommendation]:
        recs: list[TalentRecommendation] = []
        if project_matches:
            top = project_matches[0]
            recs.append(
                TalentRecommendation(
                    title="Route high-fit talent into strategic project",
                    category="project",
                    priority="high",
                    action=f"Invite {top.employee_name} to {top.project_title}.",
                    expected_impact=f"Modeled {round(top.match_score)}% project fit with {round(top.skill_coverage)}% skill coverage.",
                    evidence=[top.rationale, f"capacity_fit={top.capacity_fit}", f"missing={', '.join(top.missing_skills) or 'none'}"],
                )
            )
        if mentor_matches:
            top = mentor_matches[0]
            recs.append(
                TalentRecommendation(
                    title="Activate mentorship match",
                    category="mentor",
                    priority="medium",
                    action=f"Pair {top.mentor_name} with {top.mentee_name} for {top.topic}.",
                    expected_impact="Improves internal mobility and closes a skill gap without external hiring.",
                    evidence=[top.rationale, f"match={top.match_score}"],
                )
            )
        if role_matches:
            top = role_matches[0]
            recs.append(
                TalentRecommendation(
                    title="Open internal role pathway",
                    category="role",
                    priority="high",
                    action=f"Start internal mobility review for {top.employee_name} toward {top.role_title}.",
                    expected_impact=f"{round(top.promotion_readiness)}% promotion readiness protects retention and reduces external hiring demand.",
                    evidence=[top.rationale, f"missing={', '.join(top.missing_skills) or 'none'}"],
                )
            )
        if learning_paths:
            top = learning_paths[0]
            recs.append(
                TalentRecommendation(
                    title="Launch personalized learning path",
                    category="learning",
                    priority="medium",
                    action=f"Assign {top.title} to {top.employee_name}.",
                    expected_impact=f"Builds {top.target_skill} proficiency in about {top.estimated_weeks_to_proficiency} weeks.",
                    evidence=[top.rationale, f"score={top.recommendation_score}"],
                )
            )
        hidden = [point for point in skill_points if point.hidden_skill]
        if hidden:
            top = hidden[0]
            recs.append(
                TalentRecommendation(
                    title="Expose hidden internal expertise",
                    category="expertise",
                    priority="medium",
                    action=f"Add {top.skill} to {top.employee_name}'s verified skill profile.",
                    expected_impact="Improves project staffing and expert discovery accuracy.",
                    evidence=top.evidence,
                )
            )
        if reputation_scores:
            top = reputation_scores[0]
            recs.append(
                TalentRecommendation(
                    title="Recognize internal reputation leader",
                    category="reputation",
                    priority="low",
                    action=f"Feature {top.employee_name} in the marketplace reputation board.",
                    expected_impact=f"Reinforces knowledge sharing; total reputation is {round(top.total_reputation)}.",
                    evidence=[f"knowledge={top.knowledge_score}", f"mentorship={top.mentorship_score}", f"innovation={top.innovation_score}"],
                )
            )
        return recs

    def _summary(
        self,
        profiles: list[TalentMarketplaceProfile],
        skill_points: list[SkillIntelligencePoint],
        project_matches: list[ProjectMatch],
        mentor_matches: list[MentorMatch],
        role_matches: list[InternalRoleMatch],
        learning_paths: list[LearningPathRecommendation],
        experts: list[ExpertRanking],
        reputations: list[ReputationScore],
        badges: list[SkillBadge],
    ) -> TalentMarketplaceSummary:
        avg_rep = mean([score.total_reputation for score in reputations]) if reputations else 0
        project_strength = mean([match.match_score for match in project_matches[:8]]) if project_matches else 0
        mentor_strength = mean([match.match_score for match in mentor_matches[:8]]) if mentor_matches else 0
        learning_strength = mean([path.recommendation_score for path in learning_paths[:8]]) if learning_paths else 0
        health = self._clip(avg_rep * 0.34 + project_strength * 0.28 + mentor_strength * 0.18 + learning_strength * 0.12 + min(len(badges), 20) * 0.9)
        top_expert = max(experts, key=lambda item: item.score).employee_name if experts else "none"
        top_match = f"{project_matches[0].employee_name} -> {project_matches[0].project_title}" if project_matches else "none"
        return TalentMarketplaceSummary(
            profiles=len(profiles),
            skills_detected=len(skill_points),
            hidden_skills_detected=sum(1 for point in skill_points if point.hidden_skill),
            project_matches=len(project_matches),
            mentor_matches=len(mentor_matches),
            internal_role_matches=len(role_matches),
            learning_paths=len(learning_paths),
            badges_awarded=len(badges),
            average_reputation=round(avg_rep, 2),
            marketplace_health_score=round(health, 2),
            top_expert=top_expert,
            top_project_match=top_match,
        )

    def _assistant_intent(self, question: str) -> TalentAssistantIntent:
        normalized = self._norm(question)
        if any(token in normalized for token in ["mentor", "coach"]):
            return "mentors"
        if any(token in normalized for token in ["project", "opportunity", "gig"]):
            return "projects"
        if any(token in normalized for token in ["job", "role", "transfer", "opening"]):
            return "jobs"
        if any(token in normalized for token in ["learn", "course", "skill should", "path"]):
            return "learning"
        if any(token in normalized for token in ["expert", "who knows", "best at"]):
            return "experts"
        if any(token in normalized for token in ["badge", "reputation"]):
            return "badges"
        if any(token in normalized for token in ["skill", "gap"]):
            return "skills"
        if any(token in normalized for token in ["search", "find"]):
            return "search"
        return "summary"

    def _assistant_answer(
        self,
        intent: TalentAssistantIntent,
        question: str,
        analysis: TalentMarketplaceResponse,
        employee_id: str | None,
    ) -> tuple[str, float, list[str], list[str], list[str], list[str]]:
        if intent == "projects":
            matches = [m for m in analysis.project_matches if not employee_id or m.employee_id == employee_id][:3]
            if not matches:
                matches = analysis.project_matches[:3]
            answer = "Top internal project matches: " + "; ".join(f"{m.employee_name} -> {m.project_title} ({round(m.match_score)}%)" for m in matches)
            return answer, 0.88, [m.employee_name for m in matches], [m.project_title for m in matches], [f"Invite {matches[0].employee_name} to {matches[0].project_title}."] if matches else [], [m.rationale for m in matches]
        if intent == "mentors":
            matches = analysis.mentor_matches[:3]
            answer = "Recommended mentor matches: " + "; ".join(f"{m.mentor_name} mentors {m.mentee_name} on {m.topic}" for m in matches)
            return answer, 0.86, [m.mentor_name for m in matches], [], [f"Schedule mentorship kickoff for {matches[0].topic}."] if matches else [], [m.rationale for m in matches]
        if intent == "jobs":
            matches = analysis.internal_role_matches[:3]
            answer = "Best internal role moves: " + "; ".join(f"{m.employee_name} -> {m.role_title} ({round(m.match_score)}%)" for m in matches)
            return answer, 0.85, [m.employee_name for m in matches], [m.role_title for m in matches], ["Open mobility review for the top role match."] if matches else [], [m.rationale for m in matches]
        if intent == "learning":
            paths = analysis.learning_paths[:3]
            answer = "Recommended learning paths: " + "; ".join(f"{p.employee_name}: {p.title} for {p.target_skill}" for p in paths)
            return answer, 0.84, [p.employee_name for p in paths], [p.title for p in paths], ["Reserve protected learning time for top skill gaps."] if paths else [], [p.rationale for p in paths]
        if intent == "experts":
            normalized = self._norm(question)
            requested = [ranking for ranking in analysis.expert_rankings if ranking.skill in normalized]
            rankings = requested[:3] or sorted(analysis.expert_rankings, key=lambda item: item.score, reverse=True)[:3]
            answer = "Top experts: " + "; ".join(f"{r.employee_name} for {r.skill} ({round(r.score)}%)" for r in rankings)
            return answer, 0.89, [r.employee_name for r in rankings], [r.skill for r in rankings], ["Use top experts as project advisors and mentor anchors."], [", ".join(r.evidence[:2]) for r in rankings]
        if intent == "badges":
            badges = analysis.badges[:4]
            answer = "Highest badges: " + "; ".join(f"{b.employee_name}: {b.badge} ({b.level})" for b in badges)
            return answer, 0.82, [b.employee_name for b in badges], [b.badge for b in badges], ["Publish verified badges to the internal marketplace profile."], [", ".join(b.evidence[:2]) for b in badges]
        if intent == "skills":
            hidden = [p for p in analysis.skill_intelligence if p.hidden_skill][:4]
            visible = hidden or analysis.skill_intelligence[:4]
            answer = "Skill intelligence found: " + "; ".join(f"{p.employee_name}: {p.skill} ({round(p.proficiency_score)}%)" for p in visible)
            return answer, 0.83, [p.employee_name for p in visible], [p.skill for p in visible], ["Verify hidden skills and close role-critical gaps."], [", ".join(p.evidence[:2]) for p in visible]
        if intent == "search":
            results = self.search(TalentSearchRequest(query=question, limit=3)).results
            answer = "Search results: " + "; ".join(f"{r.title} ({round(r.score)}%)" for r in results)
            return answer, 0.8, [r.title for r in results if r.entity_type == "employee"], [r.title for r in results if r.entity_type != "employee"], ["Open the matched marketplace entities for review."], [r.summary for r in results]
        summary = analysis.summary
        answer = (
            f"Marketplace health is {round(summary.marketplace_health_score)} with {summary.project_matches} project matches, "
            f"{summary.mentor_matches} mentor matches, {summary.internal_role_matches} role matches, and {summary.badges_awarded} badges."
        )
        return answer, 0.82, [summary.top_expert], [summary.top_project_match], [analysis.recommendations[0].action if analysis.recommendations else "Refresh talent marketplace data."], [f"average_reputation={summary.average_reputation}"]

    def _scenario_variant(self, base: TalentMarketplaceRequest, add_capacity: float, focus_skill: str) -> TalentMarketplaceRequest:
        profiles = [
            profile.model_copy(
                update={
                    "allocated_hours": max(0, profile.allocated_hours - add_capacity),
                    "learning_goals": list(dict.fromkeys([*profile.learning_goals, focus_skill])),
                    "reputation_events": min(500, profile.reputation_events + 2),
                }
            )
            for profile in base.profiles
        ]
        return base.model_copy(update={"profiles": profiles, "focus_skills": list(dict.fromkeys([*base.focus_skills, focus_skill]))})

    def _skill_catalog(self, request: TalentMarketplaceRequest) -> set[str]:
        skills = set(self._norm(skill) for skill in request.focus_skills)
        for project in request.projects:
            skills.update(self._norm(skill) for skill in project.required_skills + project.stretch_skills)
        for role in request.internal_roles:
            skills.update(self._norm(skill) for skill in role.required_skills + role.preferred_skills)
        for resource in request.learning_catalog:
            skills.update(self._norm(skill) for skill in resource.target_skills)
        return {skill for skill in skills if skill}

    def _skill_evidence(self, profile: TalentMarketplaceProfile, skill: str, hidden_skill: bool) -> list[str]:
        evidence = []
        for label, values in [
            ("skill_profile", profile.skills),
            ("expertise", profile.expertise_areas),
            ("offered_expertise", profile.offered_expertise),
            ("certification", profile.certifications),
            ("project", profile.projects),
            ("achievement", profile.achievements),
        ]:
            for value in values:
                if skill in self._norm(value) or self._has_skill(skill, {self._norm(value)}):
                    evidence.append(f"{label}: {value}")
        if hidden_skill:
            evidence.append("hidden_skill_detected_from_project_and_achievement_text")
        return evidence[:6] or ["profile skill evidence"]

    def _market_relevance(self, skill: str, request: TalentMarketplaceRequest) -> float:
        demand = 0
        for project in request.projects:
            demand += 4 if any(self._norm(s) == skill for s in project.required_skills) else 0
            demand += 2 if any(self._norm(s) == skill for s in project.stretch_skills) else 0
        for role in request.internal_roles:
            demand += 4 if any(self._norm(s) == skill for s in role.required_skills) else 0
            demand += 2 if any(self._norm(s) == skill for s in role.preferred_skills) else 0
        demand += 3 if skill in {self._norm(s) for s in request.focus_skills} else 0
        return self._clip(42 + demand * 5.5)

    def _best_resource(self, skill: str, catalog: list[MarketplaceLearningResource]) -> MarketplaceLearningResource:
        return max(catalog, key=lambda item: self._similarity(skill, self._resource_text(item)) + (0.22 if self._has_skill(skill, {self._norm(s) for s in item.target_skills}) else 0))

    def _interest_fit(self, profile: TalentMarketplaceProfile, targets: list[str]) -> float:
        profile_text = " ".join(profile.interests + profile.career_goals + profile.learning_goals + profile.projects)
        return self._clip(self._similarity(profile_text, " ".join(targets)) * 100 + sum(1 for target in targets if self._norm(target) in self._norm(profile_text)) * 8)

    def _profile_text(self, profile: TalentMarketplaceProfile) -> str:
        return " ".join(
            [
                profile.employee_name,
                profile.role,
                profile.department,
                *profile.skills,
                *profile.certifications,
                *profile.projects,
                *profile.achievements,
                *profile.interests,
                *profile.career_goals,
                *profile.learning_goals,
                *profile.expertise_areas,
                *profile.offered_expertise,
            ]
        )

    @staticmethod
    def _project_text(project: MarketplaceProjectOpportunity) -> str:
        return " ".join([project.title, project.department, project.description, *project.required_skills, *project.stretch_skills])

    @staticmethod
    def _role_text(role: InternalRoleOpportunity) -> str:
        return " ".join([role.title, role.department, role.level, role.career_track, *role.required_skills, *role.preferred_skills])

    @staticmethod
    def _resource_text(resource: MarketplaceLearningResource) -> str:
        return " ".join([resource.title, resource.provider, resource.difficulty, resource.certification, *resource.target_skills])

    def _profile_skill_set(self, profile: TalentMarketplaceProfile) -> set[str]:
        return {self._norm(skill) for skill in profile.skills + profile.expertise_areas + profile.offered_expertise + profile.certifications}

    def _skill_in_text(self, skill: str, text: str) -> bool:
        normalized = self._norm(text)
        return skill in normalized or any(alias in normalized for alias in self._aliases(skill))

    def _similarity(self, left: str, right: str) -> float:
        left = self._norm(left)
        right = self._norm(right)
        if not left or not right:
            return 0.0
        if TfidfVectorizer is not None and cosine_similarity is not None:
            try:
                matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform([left, right])
                return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
            except ValueError:
                pass
        left_tokens = self._tokens(left)
        right_tokens = self._tokens(right)
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = len(left_tokens & right_tokens)
        return overlap / max(len(left_tokens | right_tokens), 1)

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 1}

    @classmethod
    def _has_skill(cls, skill: str, current: set[str]) -> bool:
        normalized = cls._norm(skill)
        candidates = cls._aliases(normalized) | {normalized}
        return any(candidate in current or any(candidate in value or value in candidate for value in current) for candidate in candidates)

    @staticmethod
    def _aliases(skill: str) -> set[str]:
        aliases = {
            "kubernetes": {"kubernetes", "k8s", "cka"},
            "mlops": {"mlops", "model operations", "model serving"},
            "rag": {"rag", "retrieval augmented generation", "vector search", "llm systems"},
            "security": {"security", "zero trust", "threat modeling", "cloud security"},
            "system design": {"system design", "architecture", "distributed systems"},
            "dashboard design": {"dashboard design", "executive dashboard", "ui design"},
            "python": {"python", "fastapi"},
            "terraform": {"terraform", "infrastructure as code"},
            "api reliability": {"api reliability", "fastapi", "incident response"},
        }
        return aliases.get(skill, {skill})

    @staticmethod
    def _norm(value: str) -> str:
        return value.strip().lower().replace("_", " ").replace("-", " ")

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    @staticmethod
    def _badge_level(score: float):
        if score >= 92:
            return "principal"
        if score >= 82:
            return "expert"
        if score >= 72:
            return "advanced"
        return "foundation"

    @staticmethod
    def _priority(score: float) -> TalentRiskLevel:
        if score >= 82:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


talent_marketplace_service = TalentMarketplaceService()

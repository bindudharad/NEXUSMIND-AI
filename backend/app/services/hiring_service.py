from __future__ import annotations

import asyncio
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.ai.hiring_engine import SKILL_ALIASES, hiring_intelligence_engine
from app.schemas.hiring import (
    CandidateRanking,
    HiringAnalyzeRequest,
    HiringCandidateInput,
    HiringFraudSignal,
    HiringResponse,
    HiringRoleInput,
    HiringSummary,
    HiringTrend,
    InterviewInsight,
    RecruiterRecommendation,
    SkillGap,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "hiring_analytics.jsonl"


class HiringIntelligenceService:
    model_name = "TF-IDF Semantic Matcher + RandomForest Smart Hiring Ranker"

    def __init__(self) -> None:
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: HiringAnalyzeRequest | None = None) -> HiringResponse:
        request = payload or self.default_request()
        candidates = request.candidates or self.default_request().candidates
        duplicate_counts = Counter(self._fingerprint(candidate.resume_text) for candidate in candidates)
        rankings = [
            self._ranking(candidate, request.role, duplicate_counts[self._fingerprint(candidate.resume_text)])
            for candidate in candidates
        ]
        rankings = sorted(rankings, key=lambda item: item.compatibility_score, reverse=True)
        ranked = [item.model_copy(update={"rank": index}) for index, item in enumerate(rankings, start=1)]
        response = HiringResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            role_title=request.role.title,
            rankings=ranked,
            recommendations=self._recommendations(ranked, request.role),
            recruiter_trends=self._trends(ranked, request.role),
            skill_gap_heatmap=self._skill_gap_heatmap(ranked),
            summary=self._summary(ranked),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: HiringAnalyzeRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, title_suffix=" - reliability sprint", skill="incident response"),
            self._scenario_variant(base, title_suffix=" - security hardening", skill="security"),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: hiring\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> HiringAnalyzeRequest:
        role = HiringRoleInput(
            role_id="role-platform-backend",
            title="Senior Backend Platform Engineer",
            job_description=(
                "Own secure Python APIs, FastAPI services, Kubernetes deployments, PostgreSQL reliability, Redis caching, "
                "MLOps integrations, incident response, and platform observability for enterprise AI workloads."
            ),
            required_skills=["python", "kubernetes", "api reliability", "security", "postgresql"],
            preferred_skills=["redis", "mlops", "incident response", "microservices", "testing"],
            seniority="senior",
            team_context="High-ownership platform team supporting AI inference APIs, realtime analytics, and secure enterprise integrations.",
            culture_values=["ownership", "clear communication", "incident discipline", "collaboration"],
            domain_keywords=["enterprise ai", "platform reliability", "secure api", "observability"],
        )
        return HiringAnalyzeRequest(
            role=role,
            realtime=True,
            candidates=[
                HiringCandidateInput(
                    candidate_id="cand-ava",
                    candidate_name="Ava Raman",
                    current_title="Senior Backend Platform Engineer",
                    years_experience=8,
                    expected_salary=182000,
                    declared_skills=["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Redis", "Security", "MLOps"],
                    certifications=["AWS Solutions Architect", "CKA"],
                    resume_text=(
                        "Led Python FastAPI platform migration handling 45M monthly API calls. Architected Kubernetes services, "
                        "PostgreSQL query optimization, Redis caching, JWT security reviews, CI/CD quality gates, and incident postmortems. "
                        "Mentored engineers and reduced p95 latency by 38%."
                    ),
                    interview_transcript=(
                        "I start by clarifying customer impact, then isolate API latency with tracing, communicate tradeoffs, and document recovery steps. "
                        "I mentor teammates through postmortems and prefer blameless ownership."
                    ),
                    portfolio_summary="Built an MLOps model-serving gateway with canary deployment, observability, and secure API controls.",
                ),
                HiringCandidateInput(
                    candidate_id="cand-liam",
                    candidate_name="Liam Carter",
                    current_title="Backend Engineer",
                    years_experience=5,
                    expected_salary=148000,
                    declared_skills=["Python", "Django", "Docker", "PostgreSQL", "Testing"],
                    certifications=[],
                    resume_text=(
                        "Built Python services, Django APIs, Docker-based delivery workflows, SQL reports, unit tests, and payment integrations. "
                        "Supported production incidents and helped migrate a monolith into smaller services."
                    ),
                    interview_transcript="I communicate clearly with product teams and like learning new infrastructure by pairing with senior engineers.",
                    portfolio_summary="Open-source API test harness and a payment reconciliation service.",
                ),
                HiringCandidateInput(
                    candidate_id="cand-noor",
                    candidate_name="Noor Patel",
                    current_title="Full Stack Developer",
                    years_experience=2,
                    expected_salary=98000,
                    declared_skills=["React", "Node", "CSS"],
                    certifications=[],
                    resume_text=(
                        "Created React dashboards, Node prototypes, landing pages, and internal tools. Interested in backend systems and cloud. "
                        "Completed coursework in databases and basic REST API development."
                    ),
                    interview_transcript="I am still learning Kubernetes and production operations, but I am motivated and ask for feedback quickly.",
                    portfolio_summary="Frontend analytics dashboard and a small Node API.",
                ),
                HiringCandidateInput(
                    candidate_id="cand-risk",
                    candidate_name="Rohan Mehta",
                    current_title="Principal Everything Architect",
                    years_experience=3,
                    expected_salary=260000,
                    declared_skills=["Python", "Kubernetes", "Security", "MLOps", "AWS", "Leadership"],
                    certifications=["Self certified cloud expert"],
                    resume_text=(
                        "Personally owned every architecture decision for dozens of unicorn-scale platforms and mastered all cloud, security, AI, "
                        "Kubernetes, databases, frontend, backend, and leadership functions without team dependency. 20 years Kubernetes experience."
                    ),
                    interview_transcript="I prefer to work alone and do not need process, reviews, or postmortems because I already know the answer.",
                    portfolio_summary="No public projects available.",
                ),
            ],
        )

    def _ranking(self, candidate: HiringCandidateInput, role: HiringRoleInput, duplicate_count: int) -> CandidateRanking:
        text = self._text(candidate)
        extracted_skills = hiring_intelligence_engine.extract_skills(text, candidate.declared_skills)
        required = [self._normalize_skill(skill) for skill in role.required_skills]
        preferred = [self._normalize_skill(skill) for skill in role.preferred_skills]
        matched_required = [skill for skill in required if skill in extracted_skills]
        matched_preferred = [skill for skill in preferred if skill in extracted_skills]
        missing_required = [skill for skill in required if skill not in extracted_skills]
        semantic = hiring_intelligence_engine.semantic_match(role, candidate) * 100
        skill_match = self._skill_match(required, preferred, matched_required, matched_preferred)
        resume_quality = self._resume_quality(candidate, extracted_skills)
        culture_fit = self._culture_fit(candidate, role)
        learning = self._learning_potential(candidate)
        communication = self._communication_quality(candidate)
        experience = self._experience_quality(candidate, role)
        project = self._project_relevance(candidate, role)
        leadership = self._leadership_signal(candidate)
        fraud_signals = self._fraud_signals(candidate, extracted_skills, missing_required, duplicate_count)
        heuristic_fraud = min(100, sum(self._fraud_weight(signal.severity) for signal in fraud_signals))
        features = [
            semantic / 100,
            skill_match / 100,
            resume_quality / 100,
            culture_fit / 100,
            learning / 100,
            communication / 100,
            experience / 100,
            project / 100,
            leadership / 100,
            heuristic_fraud / 100,
        ]
        model_scores = hiring_intelligence_engine.rank_score(features)
        hiring_risk = round(min(100, heuristic_fraud * 0.72 + model_scores["fraud_anomaly_risk"] * 0.28), 2)
        model_rank = model_scores["random_forest_ranker"]
        evidence_bonus = 0.0
        if skill_match >= 90 and semantic >= 55 and hiring_risk < 25:
            evidence_bonus += 8.5
        if resume_quality >= 70 and communication >= 70 and hiring_risk < 30:
            evidence_bonus += 4.0
        if candidate.certifications and project >= 70:
            evidence_bonus += 2.5
        compatibility = round(
            float(
                np.clip(
                    model_rank * 0.54
                    + semantic * 0.16
                    + skill_match * 0.14
                    + culture_fit * 0.06
                    + learning * 0.05
                    + communication * 0.05
                    - hiring_risk * 0.18
                    + evidence_bonus,
                    0,
                    100,
                )
            ),
            2,
        )
        model_scores.update(
            {
                "semantic_similarity": round(semantic, 2),
                "skill_coverage": round(skill_match, 2),
                "fraud_heuristic": round(heuristic_fraud, 2),
            }
        )
        return CandidateRanking(
            rank=1,
            candidate_id=candidate.candidate_id,
            candidate_name=candidate.candidate_name,
            compatibility_score=compatibility,
            hiring_recommendation=self._recommendation_label(compatibility, hiring_risk),
            confidence=round(float(np.clip(0.64 + semantic / 650 + skill_match / 700 + resume_quality / 900 - hiring_risk / 900, 0.55, 0.97)), 3),
            resume_quality_score=round(resume_quality, 2),
            semantic_match_score=round(semantic, 2),
            skill_match_score=round(skill_match, 2),
            culture_fit_score=round(culture_fit, 2),
            learning_potential_score=round(learning, 2),
            communication_quality_score=round(communication, 2),
            experience_quality_score=round(experience, 2),
            project_relevance_score=round(project, 2),
            leadership_signal_score=round(leadership, 2),
            hiring_risk_score=hiring_risk,
            matched_skills=sorted(set(matched_required + matched_preferred)),
            missing_skills=missing_required,
            skill_gaps=self._skill_gaps(missing_required),
            fraud_signals=fraud_signals,
            interview_insights=self._interview_insights(candidate),
            ranking_explanation=self._explanation(candidate, compatibility, semantic, skill_match, culture_fit, learning, hiring_risk, missing_required),
            model_scores=model_scores,
        )

    @staticmethod
    def _skill_match(required: list[str], preferred: list[str], matched_required: list[str], matched_preferred: list[str]) -> float:
        required_score = len(matched_required) / max(len(required), 1) * 72
        preferred_score = len(matched_preferred) / max(len(preferred), 1) * 28
        return round(required_score + preferred_score, 2)

    @staticmethod
    def _resume_quality(candidate: HiringCandidateInput, extracted_skills: list[str]) -> float:
        text = HiringIntelligenceService._text(candidate).lower()
        length_score = min(len(candidate.resume_text) / 1100, 1) * 18
        quantified = min(len(re.findall(r"\d+%|\d+m|\d+k|\d+x|\d+ monthly|\d+ users", text)) / 4, 1) * 18
        sections = sum(1 for token in ["led", "built", "reduced", "architected", "migrated", "optimized", "mentored"] if token in text) / 7 * 22
        skill_depth = min(len(extracted_skills) / 8, 1) * 22
        cert_score = min(len(candidate.certifications) / 2, 1) * 10
        portfolio = min(len(candidate.portfolio_summary) / 450, 1) * 10
        return float(np.clip(10 + length_score + quantified + sections + skill_depth + cert_score + portfolio, 0, 100))

    @staticmethod
    def _culture_fit(candidate: HiringCandidateInput, role: HiringRoleInput) -> float:
        text = HiringIntelligenceService._text(candidate).lower()
        values = [value.lower() for value in role.culture_values] or ["ownership", "communication", "collaboration"]
        value_hits = sum(1 for value in values if value in text) / max(len(values), 1) * 32
        positive = sum(1 for token in ["mentor", "collaborat", "postmortem", "feedback", "ownership", "tradeoff", "customer"] if token in text) * 7
        negative = sum(1 for token in ["work alone", "do not need", "no process", "no reviews", "already know"] if token in text) * 12
        return float(np.clip(48 + value_hits + positive - negative, 0, 100))

    @staticmethod
    def _learning_potential(candidate: HiringCandidateInput) -> float:
        text = HiringIntelligenceService._text(candidate).lower()
        transition_signals = sum(1 for token in ["migrated", "learn", "adopted", "transition", "upskill", "course", "certification", "new infrastructure"] if token in text)
        growth = min(transition_signals / 6, 1) * 40
        experience_balance = 24 if 2 <= candidate.years_experience <= 12 else 14
        certifications = min(len(candidate.certifications) / 3, 1) * 18
        curiosity = 18 if any(token in text for token in ["ask for feedback", "learning", "mentored", "paired"]) else 6
        return float(np.clip(24 + growth + experience_balance + certifications + curiosity, 0, 100))

    @staticmethod
    def _communication_quality(candidate: HiringCandidateInput) -> float:
        transcript = candidate.interview_transcript.lower()
        if not transcript:
            return 46
        structured = sum(1 for token in ["clarify", "communicate", "tradeoffs", "document", "feedback", "customer impact", "postmortem"] if token in transcript) * 9
        weak = sum(1 for token in ["already know", "do not need", "prefer to work alone", "no process"] if token in transcript) * 16
        length = min(len(transcript) / 500, 1) * 18
        return float(np.clip(42 + structured + length - weak, 0, 100))

    @staticmethod
    def _experience_quality(candidate: HiringCandidateInput, role: HiringRoleInput) -> float:
        target = {"junior": 1.5, "mid": 3, "senior": 6, "staff": 8, "principal": 10}[role.seniority]
        experience_fit = min(candidate.years_experience / target, 1.25) / 1.25 * 42
        text = HiringIntelligenceService._text(candidate).lower()
        seniority = sum(1 for token in ["senior", "staff", "principal", "lead", "architect", "manager"] if token in text) * 7
        production = sum(1 for token in ["production", "incident", "latency", "scale", "reliability", "security"] if token in text) * 6
        return float(np.clip(18 + experience_fit + seniority + production, 0, 100))

    @staticmethod
    def _project_relevance(candidate: HiringCandidateInput, role: HiringRoleInput) -> float:
        text = HiringIntelligenceService._text(candidate).lower()
        domain_terms = [term.lower() for term in role.domain_keywords + role.required_skills + role.preferred_skills]
        hits = sum(1 for term in set(domain_terms) if term and term in text)
        project_depth = sum(1 for token in ["gateway", "migration", "observability", "deployment", "api", "platform", "model-serving", "reconciliation"] if token in text)
        return float(np.clip(22 + hits * 5.8 + project_depth * 4.5, 0, 100))

    @staticmethod
    def _leadership_signal(candidate: HiringCandidateInput) -> float:
        text = HiringIntelligenceService._text(candidate).lower()
        signals = sum(1 for token in ["led", "lead", "mentored", "managed", "architected", "principal", "roadmap", "postmortem"] if token in text)
        return float(np.clip(18 + signals * 10.5, 0, 100))

    @staticmethod
    def _fraud_signals(
        candidate: HiringCandidateInput,
        extracted_skills: list[str],
        missing_required: list[str],
        duplicate_count: int,
    ) -> list[HiringFraudSignal]:
        text = HiringIntelligenceService._text(candidate).lower()
        signals: list[HiringFraudSignal] = []
        declared_normalized = {HiringIntelligenceService._normalize_skill(skill) for skill in candidate.declared_skills}
        unsupported = sorted(skill for skill in declared_normalized if skill in SKILL_ALIASES and skill not in extracted_skills)
        if unsupported:
            signals.append(
                HiringFraudSignal(
                    signal="unsupported_skill_claims",
                    severity="medium",
                    evidence=f"Declared skills not evidenced in resume text: {', '.join(unsupported[:4])}.",
                )
            )
        if re.search(r"20\+? years|twenty years|20 years", text) and candidate.years_experience < 8:
            signals.append(
                HiringFraudSignal(
                    signal="timeline_inconsistency",
                    severity="high",
                    evidence="Resume claims a long technology timeline that conflicts with stated years of experience.",
                )
            )
        if len(candidate.resume_text) < 240 and len(missing_required) >= 3:
            signals.append(
                HiringFraudSignal(
                    signal="thin_profile",
                    severity="medium",
                    evidence="Resume lacks enough concrete evidence for multiple required capabilities.",
                )
            )
        if duplicate_count > 1:
            signals.append(
                HiringFraudSignal(
                    signal="duplicate_resume",
                    severity="high",
                    evidence="Resume text matches another candidate in the batch.",
                )
            )
        if any(token in text for token in ["mastered all", "personally owned every", "dozens of unicorn-scale", "without team dependency"]):
            signals.append(
                HiringFraudSignal(
                    signal="overclaim_pattern",
                    severity="medium",
                    evidence="Resume uses broad unverifiable claims without supporting project evidence.",
                )
            )
        return signals

    @staticmethod
    def _skill_gaps(missing_required: list[str]) -> list[SkillGap]:
        return [
            SkillGap(
                skill=skill,
                severity="high" if skill in {"security", "kubernetes", "api reliability"} else "medium",
                recommendation=f"Validate {skill} depth in a practical exercise or assign onboarding plan.",
            )
            for skill in missing_required
        ]

    @staticmethod
    def _interview_insights(candidate: HiringCandidateInput) -> list[InterviewInsight]:
        return [
            InterviewInsight(
                label="Communication clarity",
                score=round(HiringIntelligenceService._communication_quality(candidate), 2),
                evidence="Interview transcript was scored for structured explanation, tradeoff clarity, and collaboration language.",
            ),
            InterviewInsight(
                label="Problem-solving maturity",
                score=round(HiringIntelligenceService._project_relevance(candidate, HiringIntelligenceService.default_request().role), 2),
                evidence="Portfolio and interview signals were compared against production platform incident and API reliability work.",
            ),
        ]

    @staticmethod
    def _explanation(
        candidate: HiringCandidateInput,
        compatibility: float,
        semantic: float,
        skill_match: float,
        culture: float,
        learning: float,
        risk: float,
        missing: list[str],
    ) -> list[str]:
        explanation = [
            f"{candidate.candidate_name} scored {round(compatibility)} because semantic role match is {round(semantic)} and skill coverage is {round(skill_match)}.",
            f"Culture fit is {round(culture)} and learning potential is {round(learning)}, based on interview and career progression signals.",
        ]
        if missing:
            explanation.append(f"Missing required skills: {', '.join(missing[:4])}.")
        if risk >= 45:
            explanation.append(f"Hiring risk is elevated at {round(risk)} due to profile consistency and evidence quality checks.")
        return explanation

    @staticmethod
    def _recommendation_label(score: float, risk: float) -> str:
        if score >= 82 and risk < 35:
            return "strong_hire"
        if score >= 68 and risk < 55:
            return "hire"
        if score >= 48 and risk < 75:
            return "hold"
        return "reject"

    @staticmethod
    def _recommendations(rankings: list[CandidateRanking], role: HiringRoleInput) -> list[RecruiterRecommendation]:
        if not rankings:
            return []
        top = rankings[0]
        recommendations = [
            RecruiterRecommendation(
                recommendation_id="hiring-shortlist-top-candidate",
                title=f"Shortlist {top.candidate_name}",
                action=f"Move {top.candidate_name} to technical panel for {role.title}.",
                rationale=f"{top.candidate_name} has {round(top.compatibility_score)} compatibility with strongest evidence in {', '.join(top.matched_skills[:4])}.",
                impact_score=round(top.compatibility_score, 2),
                confidence=top.confidence,
                candidate_ids=[top.candidate_id],
            )
        ]
        risky = [item for item in rankings if item.hiring_risk_score >= 45]
        if risky:
            recommendations.append(
                RecruiterRecommendation(
                    recommendation_id="hiring-fraud-review",
                    title="Run evidence verification on high-risk profiles",
                    action="Request project artifacts, references, and practical work sample before final decision.",
                    rationale=f"{len(risky)} candidate(s) triggered resume consistency or overclaim signals.",
                    impact_score=round(mean(item.hiring_risk_score for item in risky), 2),
                    confidence=round(mean(item.confidence for item in risky), 3),
                    candidate_ids=[item.candidate_id for item in risky],
                )
            )
        gaps = sorted({gap.skill for item in rankings[:3] for gap in item.skill_gaps})
        if gaps:
            recommendations.append(
                RecruiterRecommendation(
                    recommendation_id="hiring-skill-gap-panel",
                    title="Probe role-critical skill gaps",
                    action=f"Add practical interview tasks for {', '.join(gaps[:4])}.",
                    rationale="Top candidates still need validation against role-critical requirements.",
                    impact_score=72,
                    confidence=0.82,
                    candidate_ids=[item.candidate_id for item in rankings[:3]],
                )
            )
        return sorted(recommendations, key=lambda item: item.impact_score, reverse=True)[:5]

    @staticmethod
    def _trends(rankings: list[CandidateRanking], role: HiringRoleInput) -> list[HiringTrend]:
        avg_match = mean(item.compatibility_score for item in rankings) if rankings else 0
        avg_gap = mean(len(item.missing_skills) for item in rankings) if rankings else 0
        fraud_count = sum(1 for item in rankings if item.hiring_risk_score >= 45)
        return [
            HiringTrend(label="Pipeline quality", value=round(avg_match, 2), severity=HiringIntelligenceService._trend_severity(100 - avg_match), explanation=f"Average candidate compatibility for {role.title}."),
            HiringTrend(label="Skill gap pressure", value=round(min(100, avg_gap * 24), 2), severity=HiringIntelligenceService._trend_severity(avg_gap * 24), explanation="Required skills missing across the active candidate slate."),
            HiringTrend(label="Resume risk pressure", value=round(min(100, fraud_count * 32), 2), severity=HiringIntelligenceService._trend_severity(fraud_count * 32), explanation="Candidates requiring evidence verification or fraud review."),
        ]

    @staticmethod
    def _skill_gap_heatmap(rankings: list[CandidateRanking]) -> list[dict[str, float | str]]:
        gaps = Counter(gap.skill for item in rankings for gap in item.skill_gaps)
        return [
            {"skill": skill, "gap_count": float(count), "severity": "high" if count >= 2 else "medium"}
            for skill, count in gaps.most_common(12)
        ]

    @staticmethod
    def _summary(rankings: list[CandidateRanking]) -> HiringSummary:
        top = rankings[0] if rankings else None
        return HiringSummary(
            candidates_analyzed=len(rankings),
            average_compatibility=round(mean(item.compatibility_score for item in rankings), 2) if rankings else 0,
            top_candidate=top.candidate_name if top else "n/a",
            strong_hire_count=sum(1 for item in rankings if item.hiring_recommendation == "strong_hire"),
            skill_gap_count=sum(len(item.missing_skills) for item in rankings),
            fraud_risk_count=sum(1 for item in rankings if item.hiring_risk_score >= 45),
        )

    @staticmethod
    def _scenario_variant(base: HiringAnalyzeRequest, title_suffix: str, skill: str) -> HiringAnalyzeRequest:
        role = base.role.model_copy(
            update={
                "title": f"{base.role.title}{title_suffix}",
                "required_skills": sorted(set([*base.role.required_skills, skill])),
                "job_description": f"{base.role.job_description} Current hiring sprint emphasizes {skill}.",
            }
        )
        return base.model_copy(update={"role": role, "realtime": True})

    @staticmethod
    def _text(candidate: HiringCandidateInput) -> str:
        return " ".join(
            [
                candidate.current_title,
                candidate.resume_text,
                candidate.interview_transcript,
                candidate.portfolio_summary,
                " ".join(candidate.certifications),
                " ".join(candidate.declared_skills),
            ]
        )

    @staticmethod
    def _normalize_skill(skill: str) -> str:
        lowered = skill.strip().lower()
        for canonical, aliases in SKILL_ALIASES.items():
            if lowered == canonical or lowered in aliases:
                return canonical
        return lowered

    @staticmethod
    def _fingerprint(text: str) -> str:
        return re.sub(r"\W+", "", text.lower())[:420]

    @staticmethod
    def _fraud_weight(severity: str) -> float:
        return {"low": 12, "medium": 24, "high": 42, "critical": 65}.get(severity, 18)

    @staticmethod
    def _trend_severity(value: float) -> str:
        if value >= 75:
            return "critical"
        if value >= 55:
            return "high"
        if value >= 35:
            return "medium"
        return "low"

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


hiring_intelligence_service = HiringIntelligenceService()

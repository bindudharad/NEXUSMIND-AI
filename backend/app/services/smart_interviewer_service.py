from __future__ import annotations

import asyncio
import json
import math
import re
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from statistics import mean
from threading import Lock

from app.ai.hiring_engine import hiring_intelligence_engine
from app.core.cache import TTLResponseCache
from app.schemas.hiring import HiringAnalyzeRequest, HiringCandidateInput, HiringRoleInput
from app.schemas.smart_interviewer import (
    BehavioralEvaluation,
    CandidateInterviewRanking,
    CheatingDetectionReport,
    CheatingEventInput,
    GeneratedInterviewQuestion,
    HiringDecision,
    HiringRecommendation,
    InterviewAnswerInput,
    InterviewDifficulty,
    InterviewReportArtifact,
    InterviewType,
    ResumeAnalysis,
    SkillProficiencyScore,
    SmartInterviewAssistantRequest,
    SmartInterviewAssistantResponse,
    SmartInterviewCandidateInput,
    SmartInterviewRequest,
    SmartInterviewerResponse,
    SmartInterviewerSummary,
    TechnicalEvaluation,
    VoiceConfidenceAnalysis,
    VoiceMetricsInput,
)
from app.services.hiring_service import hiring_intelligence_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REPORT_DIR = DATA_DIR / "interview_reports"
HISTORY_PATH = DATA_DIR / "smart_interviewer_history.jsonl"


class SmartInterviewerService:
    model_name = "NEXUSMIND AI Smart Interviewer Panel"
    assistant_model = "AI Smart Interview Assistant"
    source_systems = [
        "interview_engine",
        "question_generation_engine",
        "resume_analysis_engine",
        "candidate_scoring_engine",
        "behavioral_analysis_engine",
        "voice_confidence_engine",
        "cheating_detection_engine",
        "skill_assessment_engine",
        "candidate_ranking_engine",
        "interview_report_generator",
        "hiring_recommendation_engine",
        "smart_interview_dashboard",
        "smart_interviewer_history_jsonl",
        "smart_hiring_ranker_adapter",
    ]
    supported_questions = [
        "Start technical interview.",
        "Evaluate this candidate.",
        "Generate interview report.",
        "Compare candidates.",
        "Show top candidate.",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[SmartInterviewerResponse] = TTLResponseCache(ttl_seconds=12)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self, payload: SmartInterviewRequest | None = None) -> SmartInterviewerResponse:
        if payload is None:
            return self._cache.get_or_set(lambda: self._run_uncached(self.default_request()))
        return self._run_uncached(payload)

    def ask(self, payload: SmartInterviewAssistantRequest) -> SmartInterviewAssistantResponse:
        panel = self.run()
        question = payload.question.lower()
        intent = self._intent(question)
        rankings = panel.candidate_rankings
        selected = self._selected_candidate(rankings, payload.candidate_id) or rankings[0]

        if intent == "start_interview":
            questions = [item for item in panel.generated_questions if item.interview_type in {"technical", "system_design", "coding"}][:4]
            answer = "Start with: " + " ".join(f"{item.question_id}: {item.question}" for item in questions)
            evidence = [rubric for item in questions for rubric in item.evaluation_rubric[:2]]
            candidate_ids: list[str] = []
            reports: list[InterviewReportArtifact] = []
        elif intent == "report":
            answer = (
                f"Generated interview reports for {selected.candidate_name}. "
                f"Recommendation: {selected.recommendation.decision.replace('_', ' ')} with overall score {round(selected.overall_score)}."
            )
            evidence = selected.recommendation.strengths + selected.recommendation.risks
            candidate_ids = [selected.candidate_id]
            reports = [selected.report]
        elif intent == "compare":
            answer = "Candidate comparison: " + "; ".join(
                f"{item.rank}. {item.candidate_name} scored {round(item.overall_score)} with {item.recommendation.decision.replace('_', ' ')}"
                for item in rankings[:5]
            )
            evidence = [item.recommendation.rationale for item in rankings[:4]]
            candidate_ids = [item.candidate_id for item in rankings[:5]]
            reports = [item.report for item in rankings[:3]]
        elif intent == "evaluate":
            answer = (
                f"{selected.candidate_name} scored {round(selected.technical_score)} technical, "
                f"{round(selected.behavioral_score)} behavioral, {round(selected.communication_score)} communication, "
                f"and {round(selected.cheating_risk_score)} cheating risk."
            )
            evidence = (
                selected.technical_evaluation.answer_evidence[:3]
                + selected.behavioral_evaluation.evidence[:3]
                + selected.cheating_report.suspicious_events[:2]
            )
            candidate_ids = [selected.candidate_id]
            reports = [selected.report]
        else:
            answer = (
                f"Top candidate is {rankings[0].candidate_name} with {round(rankings[0].overall_score)} overall score. "
                f"The recommendation is {rankings[0].recommendation.decision.replace('_', ' ')} because "
                f"{rankings[0].recommendation.rationale}"
            )
            evidence = rankings[0].recommendation.strengths + rankings[0].technical_evaluation.answer_evidence[:3]
            candidate_ids = [rankings[0].candidate_id]
            reports = [rankings[0].report]

        return SmartInterviewAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=max(0.78, min(0.97, selected.model_scores.get("interview_confidence", 0.86))),
            candidate_ids=candidate_ids,
            cited_evidence=list(dict.fromkeys(evidence))[:10],
            report_artifacts=reports,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        scenarios = [
            self.default_request(),
            self._scenario_variant(self.default_request(), "platform reliability panel", ["technical", "system_design", "cloud"]),
            self._scenario_variant(self.default_request(), "security integrity panel", ["cybersecurity", "behavioral", "coding"]),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.run(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: smart_interviewer\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> SmartInterviewRequest:
        hiring_default = hiring_intelligence_service.default_request()
        candidates_by_id = {candidate.candidate_id: candidate for candidate in hiring_default.candidates}
        return SmartInterviewRequest(
            role=hiring_default.role,
            interview_types=["technical", "behavioral", "system_design", "coding", "cloud", "database", "cybersecurity"],
            realtime=True,
            candidates=[
                SmartInterviewCandidateInput(
                    **candidates_by_id["cand-ava"].model_dump(),
                    answers=[
                        InterviewAnswerInput(
                            question_id="q-api-reliability",
                            interview_type="system_design",
                            question="Design a reliable API gateway for enterprise AI inference.",
                            answer=(
                                "I would clarify traffic patterns and failure modes, use load balancing, rate limiting, idempotent APIs, "
                                "JWT validation, circuit breakers, observability, tracing, canary deployment, rollback, Postgres read replicas, "
                                "Redis caching, SLOs, and incident runbooks. I would test p95 latency and document tradeoffs."
                            ),
                            response_time_seconds=265,
                        ),
                        InterviewAnswerInput(
                            question_id="q-behavior",
                            interview_type="behavioral",
                            question="Describe a production incident you owned.",
                            answer=(
                                "I coordinated the incident room, communicated customer impact, delegated investigation, protected a junior engineer, "
                                "rolled back safely, and ran a blameless postmortem with follow-up owners."
                            ),
                            response_time_seconds=150,
                        ),
                    ],
                    voice_metrics=VoiceMetricsInput(words_per_minute=138, hesitation_count=2, pitch_variance=0.24, pause_ratio=0.11, volume_stability=0.82),
                    monitoring_events=[],
                ),
                SmartInterviewCandidateInput(
                    **candidates_by_id["cand-liam"].model_dump(),
                    answers=[
                        InterviewAnswerInput(
                            question_id="q-api-reliability",
                            interview_type="technical",
                            question="How would you debug elevated API latency?",
                            answer=(
                                "I would inspect logs, query timing, database indexes, worker saturation, cache hit rate, and add metrics. "
                                "I would ask for help on Kubernetes details and write tests around the bottleneck."
                            ),
                            response_time_seconds=205,
                        ),
                        InterviewAnswerInput(
                            question_id="q-behavior",
                            interview_type="behavioral",
                            question="How do you handle a blocker?",
                            answer="I communicate early, pair with senior engineers, break down the problem, and document what I learn.",
                            response_time_seconds=95,
                        ),
                    ],
                    voice_metrics=VoiceMetricsInput(words_per_minute=124, hesitation_count=5, pitch_variance=0.34, pause_ratio=0.19, volume_stability=0.69),
                    monitoring_events=[CheatingEventInput(event_type="tab_switch", timestamp_offset_seconds=412, severity_weight=0.18, details="Single documentation lookup during system design answer.")],
                ),
                SmartInterviewCandidateInput(
                    **candidates_by_id["cand-noor"].model_dump(),
                    answers=[
                        InterviewAnswerInput(
                            question_id="q-backend",
                            interview_type="technical",
                            question="Explain API reliability for model-serving systems.",
                            answer="I know REST basics and would use monitoring. I need mentorship on Kubernetes, Redis, and incident response.",
                            response_time_seconds=110,
                        )
                    ],
                    voice_metrics=VoiceMetricsInput(words_per_minute=116, hesitation_count=9, pitch_variance=0.41, pause_ratio=0.28, volume_stability=0.61),
                    monitoring_events=[],
                ),
                SmartInterviewCandidateInput(
                    **candidates_by_id["cand-risk"].model_dump(),
                    answers=[
                        InterviewAnswerInput(
                            question_id="q-api-reliability",
                            interview_type="system_design",
                            question="Design a reliable API gateway for enterprise AI inference.",
                            answer=(
                                "I have mastered all cloud and architecture. The obvious solution is to use everything perfectly. "
                                "No reviews or postmortems are required because I already know the answer."
                            ),
                            response_time_seconds=14,
                        ),
                        InterviewAnswerInput(
                            question_id="q-security",
                            interview_type="cybersecurity",
                            question="How would you secure candidate data?",
                            answer="Use security and encryption. I would decide alone and move fast.",
                            response_time_seconds=16,
                        ),
                    ],
                    voice_metrics=VoiceMetricsInput(words_per_minute=242, hesitation_count=0, pitch_variance=0.67, pause_ratio=0.02, volume_stability=0.44),
                    monitoring_events=[
                        CheatingEventInput(event_type="copy_paste", timestamp_offset_seconds=22, severity_weight=0.78, details="Large pasted answer appeared in less than fifteen seconds."),
                        CheatingEventInput(event_type="suspicious_speed", timestamp_offset_seconds=26, severity_weight=0.72, details="Answer speed exceeded realistic typing and speaking threshold."),
                        CheatingEventInput(event_type="external_assistance", timestamp_offset_seconds=48, severity_weight=0.64, details="Focus left interview tab during security question."),
                    ],
                ),
            ],
        )

    def _run_uncached(self, payload: SmartInterviewRequest) -> SmartInterviewerResponse:
        request = payload if payload.candidates else self.default_request()
        role = request.role
        questions = self._generate_questions(role, request.interview_types)
        hiring_response = hiring_intelligence_service.analyze(
            HiringAnalyzeRequest(
                role=role,
                candidates=[self._to_hiring_candidate(candidate) for candidate in request.candidates],
                realtime=request.realtime,
            )
        )
        hiring_by_id = {item.candidate_id: item for item in hiring_response.rankings}
        rankings = [
            self._candidate_ranking(candidate, role, hiring_by_id.get(candidate.candidate_id), questions)
            for candidate in request.candidates
        ]
        rankings = sorted(rankings, key=lambda item: item.overall_score, reverse=True)
        ranked = [item.model_copy(update={"rank": index}) for index, item in enumerate(rankings, start=1)]
        response = SmartInterviewerResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            role_title=role.title,
            summary=self._summary(ranked),
            generated_questions=questions,
            candidate_rankings=ranked,
            recommendations=[item.recommendation for item in ranked[:5]],
            supported_questions=self.supported_questions,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def _candidate_ranking(
        self,
        candidate: SmartInterviewCandidateInput,
        role: HiringRoleInput,
        hiring_ranking,
        questions: list[GeneratedInterviewQuestion],
    ) -> CandidateInterviewRanking:
        resume = self._resume_analysis(candidate, role)
        technical = self._technical_evaluation(candidate, role, questions)
        behavioral = self._behavioral_evaluation(candidate)
        voice = self._voice_analysis(candidate)
        cheating = self._cheating_report(candidate)
        skill_scores = self._skill_scores(candidate, role, technical, behavioral, hiring_ranking)
        skill_match = hiring_ranking.skill_match_score if hiring_ranking else mean([item.score for item in skill_scores]) if skill_scores else 0
        experience = hiring_ranking.experience_quality_score if hiring_ranking else self._experience_score(candidate, role)
        semantic = hiring_ranking.semantic_match_score if hiring_ranking else 55
        resume_quality = hiring_ranking.resume_quality_score if hiring_ranking else resume.resume_quality_score
        technical_score = technical.score
        behavioral_score = behavioral.overall_score
        communication = max(voice.communication_score * 0.55 + behavioral.communication_score * 0.45, 0)
        base = (
            technical_score * 0.27
            + behavioral_score * 0.16
            + communication * 0.14
            + skill_match * 0.17
            + experience * 0.09
            + resume_quality * 0.07
            + semantic * 0.07
            + voice.confidence_score * 0.03
        )
        overall = round(_clamp(base - cheating.cheating_risk_score * 0.23), 2)
        recommendation = self._recommendation(candidate, overall, technical, behavioral, voice, cheating, skill_scores)
        model_scores = {
            "technical_nlp_coverage": technical_score,
            "behavioral_nlp_score": behavioral_score,
            "voice_confidence_model": voice.confidence_score,
            "cheating_anomaly_score": cheating.cheating_risk_score,
            "smart_hiring_ranker_score": hiring_ranking.compatibility_score if hiring_ranking else overall,
            "interview_confidence": round(_clamp(0.58 + overall / 250 - cheating.cheating_risk_score / 450, 0.52, 0.97), 3),
        }
        report = self._write_report(candidate, role, overall, recommendation, technical, behavioral, voice, cheating, skill_scores)
        return CandidateInterviewRanking(
            rank=1,
            candidate_id=candidate.candidate_id,
            candidate_name=candidate.candidate_name,
            overall_score=overall,
            technical_score=round(technical_score, 2),
            behavioral_score=round(behavioral_score, 2),
            communication_score=round(communication, 2),
            voice_confidence_score=round(voice.confidence_score, 2),
            skill_match_score=round(skill_match, 2),
            experience_relevance_score=round(experience, 2),
            cheating_risk_score=round(cheating.cheating_risk_score, 2),
            recommendation=recommendation,
            skill_scores=skill_scores,
            resume_analysis=resume,
            technical_evaluation=technical,
            behavioral_evaluation=behavioral,
            voice_analysis=voice,
            cheating_report=cheating,
            report=report,
            model_scores=model_scores,
        )

    def _generate_questions(self, role: HiringRoleInput, interview_types: list[InterviewType]) -> list[GeneratedInterviewQuestion]:
        unique_types = list(dict.fromkeys(interview_types or ["technical", "behavioral", "system_design"]))
        difficulty = role.seniority
        skill_focus = role.required_skills[:4] or ["system design", "reliability", "security"]
        templates: dict[str, str] = {
            "technical": f"Explain how you would debug and stabilize a production {skill_focus[0]} issue under customer impact.",
            "behavioral": "Describe a high-pressure incident where you showed ownership, collaboration, and clear communication.",
            "system_design": f"Design a secure, observable, and scalable {role.title} workflow for enterprise AI workloads.",
            "coding": "Implement the core algorithm for rate-limited task processing and explain complexity, tests, and failure cases.",
            "ai_ml": "Explain how you would monitor an ML inference service for drift, latency, quality, and rollback safety.",
            "cloud": "Design a Kubernetes deployment strategy with canaries, rollback, secrets, autoscaling, and observability.",
            "database": "Diagnose a slow PostgreSQL workload and describe indexing, query planning, replication, and cache tradeoffs.",
            "cybersecurity": "How would you protect sensitive interview and employee data across APIs, storage, access control, and audit logs?",
        }
        rubrics: dict[str, list[str]] = {
            "technical": ["Root-cause isolation", "Observability", "Failure-mode handling", "Customer-impact communication"],
            "behavioral": ["Ownership", "Collaboration", "Conflict handling", "Learning loop"],
            "system_design": ["Scalability", "Security", "Tradeoffs", "Operational readiness"],
            "coding": ["Correctness", "Complexity", "Edge cases", "Testing discipline"],
            "ai_ml": ["Model quality", "Drift monitoring", "Inference reliability", "Rollback safety"],
            "cloud": ["Kubernetes operations", "Secrets", "Autoscaling", "Deployment safety"],
            "database": ["Indexing", "Query planning", "Replication", "Caching tradeoffs"],
            "cybersecurity": ["Threat model", "Least privilege", "Encryption", "Auditability"],
        }
        questions = []
        for index, interview_type in enumerate(unique_types, start=1):
            target = skill_focus if interview_type in {"technical", "system_design", "coding"} else [interview_type.replace("_", " ")]
            questions.append(
                GeneratedInterviewQuestion(
                    question_id=f"sq-{index:02d}-{interview_type}",
                    interview_type=interview_type,
                    difficulty=difficulty,
                    question=templates[interview_type],
                    target_skills=target,
                    follow_up_questions=[
                        "What tradeoff would you make if latency and cost conflict?",
                        "How would you verify this works in production?",
                    ],
                    evaluation_rubric=rubrics[interview_type],
                )
            )
        return questions

    def _resume_analysis(self, candidate: SmartInterviewCandidateInput, role: HiringRoleInput) -> ResumeAnalysis:
        text = self._candidate_text(candidate)
        skills = hiring_intelligence_engine.extract_skills(text, candidate.declared_skills)
        education = self._extract_phrases(candidate.resume_text, ["bachelor", "master", "phd", "university", "degree", "coursework"])
        projects = self._extract_phrases(candidate.resume_text + " " + candidate.portfolio_summary, ["built", "led", "architected", "migrated", "optimized", "created"])
        missing = [skill for skill in role.required_skills if self._normalize(skill) not in {self._normalize(item) for item in skills}]
        summary = (
            f"{candidate.candidate_name} has {candidate.years_experience:g} years of experience with evidence in "
            f"{', '.join(skills[:6]) or 'general software delivery'}."
        )
        quality = _clamp(
            22
            + min(len(candidate.resume_text) / 900, 1) * 20
            + min(len(skills) / 9, 1) * 24
            + min(len(projects) / 4, 1) * 18
            + min(len(candidate.certifications) / 2, 1) * 10
            + min(candidate.years_experience / 10, 1) * 6
        )
        return ResumeAnalysis(
            candidate_id=candidate.candidate_id,
            candidate_name=candidate.candidate_name,
            extracted_skills=skills,
            education=education[:5],
            certifications=candidate.certifications,
            experience_years=candidate.years_experience,
            projects=projects[:6],
            summary=summary,
            skill_gap_analysis=[f"Validate {skill} depth with a practical exercise." for skill in missing] or ["No critical role skill gap detected."],
            resume_quality_score=round(quality, 2),
        )

    def _technical_evaluation(
        self,
        candidate: SmartInterviewCandidateInput,
        role: HiringRoleInput,
        questions: list[GeneratedInterviewQuestion],
    ) -> TechnicalEvaluation:
        technical_answers = [answer for answer in candidate.answers if answer.interview_type != "behavioral"]
        answer_text = " ".join(answer.answer for answer in technical_answers) or candidate.interview_transcript or candidate.resume_text
        lower = answer_text.lower()
        dimensions = {
            "scalability": ["scale", "autoscal", "load balancing", "replica", "throughput"],
            "security": ["jwt", "security", "encrypt", "least privilege", "auth", "audit"],
            "observability": ["observability", "tracing", "metrics", "logs", "monitoring", "slo"],
            "failure modes": ["failure", "rollback", "circuit", "incident", "postmortem", "recovery"],
            "data reliability": ["postgres", "index", "replica", "transaction", "cache", "redis"],
            "testing": ["test", "edge", "canary", "verify", "quality gate"],
            "tradeoffs": ["tradeoff", "latency", "cost", "consistency", "risk"],
        }
        covered = [dimension for dimension, tokens in dimensions.items() if any(token in lower for token in tokens)]
        missing = [dimension for dimension in dimensions if dimension not in covered]
        role_hits = sum(1 for skill in role.required_skills + role.preferred_skills if self._normalize(skill) in lower)
        quantified = len(re.findall(r"\d+%|\d+x|p\d+|\d+m|\d+k|\d+ monthly", lower))
        weak_signals = sum(1 for token in ["mastered all", "obvious solution", "already know", "use everything", "decide alone"] if token in lower)
        score = _clamp(38 + len(covered) * 7.4 + min(role_hits, 8) * 3.2 + min(quantified, 3) * 3.5 - weak_signals * 12)
        follow_ups = [
            f"Go deeper on {dimension} with concrete production checks."
            for dimension in missing[:3]
        ] or ["Walk through rollback and validation steps with metrics."]
        strengths = [f"Covers {dimension} in the answer." for dimension in covered[:4]] or ["Shows basic technical awareness."]
        weaknesses = [f"Missing depth in {dimension}." for dimension in missing[:4]]
        evidence = [
            f"Technical answer covered {len(covered)}/{len(dimensions)} production engineering dimensions.",
            f"Role-skill mentions detected: {role_hits}.",
        ]
        return TechnicalEvaluation(
            candidate_id=candidate.candidate_id,
            score=round(score, 2),
            strengths=strengths,
            weaknesses=weaknesses,
            follow_up_questions=follow_ups,
            answer_evidence=evidence,
        )

    def _behavioral_evaluation(self, candidate: SmartInterviewCandidateInput) -> BehavioralEvaluation:
        behavioral_answers = " ".join(answer.answer for answer in candidate.answers if answer.interview_type == "behavioral")
        text = f"{candidate.interview_transcript} {behavioral_answers} {candidate.resume_text}".lower()
        scores = {
            "leadership_score": self._signal_score(text, ["led", "lead", "mentor", "delegate", "roadmap", "decision"], ["alone", "no reviews"]),
            "communication_score": self._signal_score(text, ["communicate", "clarify", "handoff", "document", "customer impact", "feedback"], ["already know", "do not need"]),
            "teamwork_score": self._signal_score(text, ["collaborat", "pair", "team", "blameless", "support", "postmortem"], ["work alone", "decide alone"]),
            "problem_solving_score": self._signal_score(text, ["root cause", "debug", "isolate", "tradeoff", "incident", "rollback"], ["obvious solution"]),
            "adaptability_score": self._signal_score(text, ["learn", "migrated", "adopted", "course", "feedback", "new"], ["already know"]),
            "ownership_score": self._signal_score(text, ["owned", "ownership", "responsible", "follow-up", "runbook", "postmortem"], ["no process"]),
        }
        overall = mean(scores.values())
        evidence = [
            "Behavioral NLP scored ownership, communication, collaboration, adaptability, and incident maturity.",
            f"Positive collaboration terms={sum(text.count(token) for token in ['team', 'mentor', 'communicate', 'collaborat', 'postmortem'])}.",
        ]
        return BehavioralEvaluation(
            candidate_id=candidate.candidate_id,
            overall_score=round(overall, 2),
            evidence=evidence,
            **{key: round(value, 2) for key, value in scores.items()},
        )

    def _voice_analysis(self, candidate: SmartInterviewCandidateInput) -> VoiceConfidenceAnalysis:
        metrics = candidate.voice_metrics or self._voice_metrics_from_text(candidate)
        if candidate.audio_signal:
            avg = mean(candidate.audio_signal)
            variance = mean((item - avg) ** 2 for item in candidate.audio_signal)
            stability = _clamp(100 - math.sqrt(variance) * 160)
        else:
            stability = _clamp(metrics.volume_stability * 100 - metrics.pitch_variance * 18)
        pace_score = _clamp(100 - abs(metrics.words_per_minute - 140) * 0.55)
        hesitation_score = _clamp(100 - metrics.hesitation_count * 4.8 - metrics.pause_ratio * 38)
        confidence = _clamp(pace_score * 0.32 + hesitation_score * 0.34 + stability * 0.34)
        clarity = _clamp(pace_score * 0.45 + hesitation_score * 0.25 + stability * 0.3)
        communication = _clamp(confidence * 0.46 + clarity * 0.42 + (100 - metrics.pause_ratio * 100) * 0.12)
        return VoiceConfidenceAnalysis(
            candidate_id=candidate.candidate_id,
            confidence_score=round(confidence, 2),
            communication_score=round(communication, 2),
            clarity_score=round(clarity, 2),
            hesitation_frequency=round(metrics.hesitation_count / max(len(candidate.answers), 1), 2),
            speaking_speed_wpm=round(metrics.words_per_minute, 2),
            voice_stability=round(stability, 2),
            evidence=[
                f"Voice model used {round(metrics.words_per_minute)} WPM, {metrics.hesitation_count} hesitations, and {round(metrics.pause_ratio, 2)} pause ratio.",
                "Fallback text-derived confidence is used when raw audio is unavailable.",
            ],
        )

    def _cheating_report(self, candidate: SmartInterviewCandidateInput) -> CheatingDetectionReport:
        weights = {
            "copy_paste": 34,
            "tab_switch": 18,
            "suspicious_speed": 30,
            "external_assistance": 38,
            "repeated_similarity": 24,
            "identity_mismatch": 46,
        }
        suspicious_events = [
            f"{event.event_type}: {event.details or 'monitoring signal detected'}"
            for event in candidate.monitoring_events
        ]
        event_score = sum(weights[event.event_type] * event.severity_weight for event in candidate.monitoring_events)
        speed_flags = 0
        for answer in candidate.answers:
            words = len(answer.answer.split())
            if words >= 28 and answer.response_time_seconds <= max(18, words / 4):
                speed_flags += 1
        if speed_flags:
            event_score += min(30, speed_flags * 14)
            suspicious_events.append(f"suspicious_speed: {speed_flags} answer(s) completed faster than realistic response thresholds.")
        similarity = self._answer_similarity(candidate.answers)
        if similarity >= 68:
            event_score += 18
            suspicious_events.append(f"repeated_similarity: maximum repeated-answer similarity is {round(similarity)}.")
        score = _clamp(event_score)
        level = self._risk_level(score)
        recommendation = (
            "Continue interview normally."
            if score < 30
            else "Require live follow-up questions and evidence verification."
            if score < 60
            else "Escalate to recruiter review before hiring decision."
        )
        return CheatingDetectionReport(
            candidate_id=candidate.candidate_id,
            cheating_risk_score=round(score, 2),
            risk_level=level,
            suspicious_events=suspicious_events,
            copy_paste_events=sum(1 for event in candidate.monitoring_events if event.event_type == "copy_paste"),
            tab_switch_events=sum(1 for event in candidate.monitoring_events if event.event_type == "tab_switch"),
            external_assistance_signals=sum(1 for event in candidate.monitoring_events if event.event_type == "external_assistance"),
            repeated_similarity_score=round(similarity, 2),
            recommendation=recommendation,
        )

    def _skill_scores(
        self,
        candidate: SmartInterviewCandidateInput,
        role: HiringRoleInput,
        technical: TechnicalEvaluation,
        behavioral: BehavioralEvaluation,
        hiring_ranking,
    ) -> list[SkillProficiencyScore]:
        text = self._candidate_text(candidate).lower()
        base_match = hiring_ranking.skill_match_score if hiring_ranking else 55
        scores = [
            ("Programming", _clamp(technical.score * 0.62 + self._token_bonus(text, ["python", "api", "fastapi", "code", "algorithm"], 8) + 18), "Programming evidence from coding/API answers and resume skills."),
            ("Problem Solving", _clamp(technical.score * 0.48 + behavioral.problem_solving_score * 0.37 + 12), "Root-cause, rollback, and tradeoff language in interview answers."),
            ("System Design", _clamp(technical.score * 0.56 + self._token_bonus(text, ["scale", "kubernetes", "gateway", "observability", "replica"], 7) + 15), "System design score based on architecture, failure-mode, and observability coverage."),
            ("Communication", _clamp(behavioral.communication_score * 0.62 + 0.38 * self._voice_metrics_from_text(candidate).volume_stability * 100), "Communication evidence from transcript structure and voice clarity signals."),
            ("Leadership", _clamp(behavioral.leadership_score * 0.7 + self._token_bonus(text, ["mentor", "led", "delegate", "roadmap"], 6)), "Leadership evidence from ownership, mentoring, and incident coordination."),
            ("Technical Depth", _clamp(base_match * 0.43 + technical.score * 0.47 + len(role.required_skills) * 1.2), "Required-skill coverage combined with technical answer depth."),
        ]
        return [SkillProficiencyScore(skill=skill, score=round(score, 2), evidence=evidence) for skill, score, evidence in scores]

    def _recommendation(
        self,
        candidate: SmartInterviewCandidateInput,
        overall: float,
        technical: TechnicalEvaluation,
        behavioral: BehavioralEvaluation,
        voice: VoiceConfidenceAnalysis,
        cheating: CheatingDetectionReport,
        skill_scores: list[SkillProficiencyScore],
    ) -> HiringRecommendation:
        if overall >= 84 and cheating.cheating_risk_score < 32:
            decision: HiringDecision = "strong_hire"
        elif overall >= 70 and cheating.cheating_risk_score < 52:
            decision = "hire"
        elif overall >= 52 and cheating.cheating_risk_score < 72:
            decision = "consider"
        else:
            decision = "reject"
        strengths = [
            *technical.strengths[:2],
            f"Behavioral score is {round(behavioral.overall_score)}.",
            f"Voice confidence score is {round(voice.confidence_score)}.",
        ]
        weaknesses = technical.weaknesses[:3] or ["No major technical weakness detected."]
        risks = cheating.suspicious_events[:3] or ([f"Cheating risk is {round(cheating.cheating_risk_score)}."] if cheating.cheating_risk_score >= 30 else ["Low interview integrity risk."])
        development = [
            f"Deepen {item.skill} through targeted onboarding." for item in sorted(skill_scores, key=lambda item: item.score)[:2]
        ]
        rationale = (
            f"{candidate.candidate_name} reached {round(overall)} overall after technical, behavioral, voice, resume, "
            f"skill, and integrity scoring."
        )
        confidence = _clamp(0.58 + overall / 250 - cheating.cheating_risk_score / 500, 0.52, 0.97)
        return HiringRecommendation(
            decision=decision,
            strengths=strengths,
            weaknesses=weaknesses,
            risks=risks,
            development_areas=development,
            rationale=rationale,
            confidence=round(confidence, 3),
        )

    def _write_report(
        self,
        candidate: SmartInterviewCandidateInput,
        role: HiringRoleInput,
        overall: float,
        recommendation: HiringRecommendation,
        technical: TechnicalEvaluation,
        behavioral: BehavioralEvaluation,
        voice: VoiceConfidenceAnalysis,
        cheating: CheatingDetectionReport,
        skill_scores: list[SkillProficiencyScore],
    ) -> InterviewReportArtifact:
        generated_at = datetime.now(timezone.utc)
        slug = self._slug(f"{candidate.candidate_id}-{generated_at.strftime('%Y%m%d%H%M%S')}")
        pdf_path = REPORT_DIR / f"{slug}.pdf"
        docx_path = REPORT_DIR / f"{slug}.docx"
        lines = [
            f"AI Smart Interview Report: {candidate.candidate_name}",
            f"Role: {role.title}",
            f"Overall Score: {round(overall, 2)}",
            f"Recommendation: {recommendation.decision.replace('_', ' ').title()}",
            f"Technical Score: {technical.score}",
            f"Behavioral Score: {behavioral.overall_score}",
            f"Voice Confidence: {voice.confidence_score}",
            f"Cheating Risk: {cheating.cheating_risk_score}",
            "Strengths: " + "; ".join(recommendation.strengths),
            "Weaknesses: " + "; ".join(recommendation.weaknesses),
            "Risks: " + "; ".join(recommendation.risks),
            "Skill Breakdown: " + "; ".join(f"{item.skill}={round(item.score)}" for item in skill_scores),
        ]
        self._write_pdf(pdf_path, lines)
        self._write_docx(docx_path, lines)
        return InterviewReportArtifact(
            candidate_id=candidate.candidate_id,
            title=f"{candidate.candidate_name} Interview Report",
            pdf_path=str(pdf_path),
            docx_path=str(docx_path),
            sections=[
                "Candidate Overview",
                "Resume Summary",
                "Technical Evaluation",
                "Behavioral Evaluation",
                "Communication Analysis",
                "Skill Breakdown",
                "Final Recommendation",
            ],
            generated_at=generated_at,
        )

    @staticmethod
    def _write_pdf(path: Path, lines: list[str]) -> None:
        safe_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:110] for line in lines[:42]]
        stream_lines = ["BT", "/F1 10 Tf", "50 770 Td", "14 TL"]
        for line in safe_lines:
            stream_lines.append(f"({line}) Tj")
            stream_lines.append("T*")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1", errors="replace")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        chunks = [b"%PDF-1.4\n"]
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(sum(len(chunk) for chunk in chunks))
            chunks.append(f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
        xref_offset = sum(len(chunk) for chunk in chunks)
        xref = [b"xref\n0 6\n", b"0000000000 65535 f \n"]
        xref.extend(f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets[1:])
        trailer = b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_offset).encode("ascii") + b"\n%%EOF\n"
        path.write_bytes(b"".join(chunks + xref + [trailer]))

    @staticmethod
    def _write_docx(path: Path, lines: list[str]) -> None:
        document = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
            + "".join(f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>" for line in lines)
            + "<w:sectPr><w:pgSz w:w=\"12240\" w:h=\"15840\"/><w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\"/></w:sectPr>"
            + "</w:body></w:document>"
        )
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            archive.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            archive.writestr("word/document.xml", document)

    def _summary(self, rankings: list[CandidateInterviewRanking]) -> SmartInterviewerSummary:
        top = rankings[0] if rankings else None
        return SmartInterviewerSummary(
            active_interviews=len(rankings),
            top_candidate=top.candidate_name if top else "n/a",
            average_overall_score=round(mean(item.overall_score for item in rankings), 2) if rankings else 0,
            strong_hire_count=sum(1 for item in rankings if item.recommendation.decision == "strong_hire"),
            high_risk_candidates=sum(1 for item in rankings if item.cheating_risk_score >= 55),
            report_count=len(rankings),
        )

    @staticmethod
    def _to_hiring_candidate(candidate: SmartInterviewCandidateInput) -> HiringCandidateInput:
        return HiringCandidateInput(
            candidate_id=candidate.candidate_id,
            candidate_name=candidate.candidate_name,
            resume_text=candidate.resume_text,
            interview_transcript=" ".join([candidate.interview_transcript, *[answer.answer for answer in candidate.answers]]),
            portfolio_summary=candidate.portfolio_summary,
            years_experience=candidate.years_experience,
            expected_salary=candidate.expected_salary,
            location=candidate.location,
            current_title=candidate.current_title,
            certifications=candidate.certifications,
            declared_skills=candidate.declared_skills,
        )

    @staticmethod
    def _candidate_text(candidate: SmartInterviewCandidateInput) -> str:
        return " ".join(
            [
                candidate.current_title,
                candidate.resume_text,
                candidate.interview_transcript,
                candidate.portfolio_summary,
                " ".join(candidate.certifications),
                " ".join(candidate.declared_skills),
                " ".join(answer.answer for answer in candidate.answers),
            ]
        )

    @staticmethod
    def _extract_phrases(text: str, triggers: list[str]) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [sentence.strip()[:220] for sentence in sentences if any(trigger in sentence.lower() for trigger in triggers)]

    @staticmethod
    def _signal_score(text: str, positive: list[str], negative: list[str]) -> float:
        hits = sum(text.count(token) for token in positive)
        weak = sum(text.count(token) for token in negative)
        return _clamp(46 + min(hits, 8) * 7.2 - min(weak, 5) * 13.5 + min(len(text) / 900, 1) * 8)

    @staticmethod
    def _voice_metrics_from_text(candidate: SmartInterviewCandidateInput) -> VoiceMetricsInput:
        text = " ".join([candidate.interview_transcript, *[answer.answer for answer in candidate.answers]]).lower()
        words = max(len(text.split()), 1)
        hesitations = sum(text.count(token) for token in [" um ", " uh ", "maybe", "not sure", "i think"])
        speed = _clamp(118 + words / max(len(candidate.answers), 1) * 0.2, 80, 180)
        return VoiceMetricsInput(
            words_per_minute=speed,
            hesitation_count=hesitations,
            pitch_variance=0.32 if hesitations < 5 else 0.48,
            pause_ratio=_clamp(0.12 + hesitations * 0.025, 0.05, 0.45),
            volume_stability=_clamp(0.74 - hesitations * 0.025, 0.38, 0.88),
        )

    @staticmethod
    def _answer_similarity(answers: list[InterviewAnswerInput]) -> float:
        if len(answers) < 2:
            return 0
        token_sets = [set(re.findall(r"[a-z0-9]+", answer.answer.lower())) for answer in answers if answer.answer.strip()]
        best = 0.0
        for index, left in enumerate(token_sets):
            for right in token_sets[index + 1 :]:
                if not left or not right:
                    continue
                best = max(best, len(left & right) / len(left | right) * 100)
        return best

    @staticmethod
    def _experience_score(candidate: SmartInterviewCandidateInput, role: HiringRoleInput) -> float:
        target = {"junior": 1.5, "mid": 3, "senior": 6, "staff": 8, "principal": 10}[role.seniority]
        return _clamp(40 + min(candidate.years_experience / target, 1.35) * 42)

    @staticmethod
    def _token_bonus(text: str, tokens: list[str], weight: float) -> float:
        return min(sum(1 for token in tokens if token in text.lower()) * weight, 30)

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 82:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 35:
            return "medium"
        return "low"

    @staticmethod
    def _intent(question: str) -> str:
        if any(token in question for token in ["top candidate", "best candidate", "strongest candidate", "show top"]):
            return "top_candidate"
        if any(token in question for token in ["start", "question", "technical interview"]):
            return "start_interview"
        if any(token in question for token in ["report", "pdf", "docx"]):
            return "report"
        if any(token in question for token in ["compare", "rank", "ranking"]):
            return "compare"
        if any(token in question for token in ["evaluate", "score", "candidate"]):
            return "evaluate"
        return "top_candidate"

    @staticmethod
    def _selected_candidate(rankings: list[CandidateInterviewRanking], candidate_id: str | None) -> CandidateInterviewRanking | None:
        if not candidate_id:
            return None
        return next((item for item in rankings if item.candidate_id == candidate_id), None)

    @staticmethod
    def _scenario_variant(base: SmartInterviewRequest, title_suffix: str, interview_types: list[InterviewType]) -> SmartInterviewRequest:
        role = base.role.model_copy(update={"title": f"{base.role.title} - {title_suffix}"})
        return base.model_copy(update={"role": role, "interview_types": interview_types})

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-").lower()[:120]

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, float(value)))


smart_interviewer_service = SmartInterviewerService()

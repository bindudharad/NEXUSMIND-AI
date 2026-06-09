from __future__ import annotations

import asyncio
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np
import httpx

from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator
from app.ai.genai_hr_assistant_engine import GenAIKnowledgeDocument, genai_hr_assistant_engine
from app.schemas.genai_hr_assistant import (
    GenAIContextSource,
    GenAIConversationMemory,
    GenAIHRAssistantRequest,
    GenAIHRAssistantResponse,
    GenAIHRIntent,
    GenAIReportSection,
    GenAIToolCall,
)
from app.schemas.enterprise_knowledge import EnterpriseKnowledgeAskRequest
from app.services.alert_service import alert_service
from app.services.attrition_service import attrition_prediction_service
from app.services.company_health_service import company_health_service
from app.services.hiring_service import hiring_intelligence_service
from app.services.enterprise_knowledge_service import enterprise_knowledge_service
from app.services.knowledge_loss_service import knowledge_loss_service
from app.services.productivity_service import productivity_leakage_service
from app.services.project_failure_service import project_failure_service
from app.services.roi_service import roi_intelligence_service
from app.services.suggestion_service import smart_suggestion_service
from app.services.wellness_service import wellness_intelligence_service
from app.services.work_life_balance_service import work_life_balance_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ASSISTANT_HISTORY_PATH = DATA_DIR / "genai_hr_assistant_history.jsonl"
ASSISTANT_MEMORY_PATH = DATA_DIR / "genai_hr_assistant_memory.jsonl"


class GenAIHRAssistantService:
    model_name = genai_hr_assistant_engine.model_name
    source_systems = [
        "local_enterprise_llm_adapter",
        "openai_compatible_llm_api_adapter",
        "rag_vector_retrieval",
        "conversation_memory_jsonl",
        "attrition_prediction_ai",
        "wellness_intelligence_ai",
        "productivity_leakage_ai",
        "project_failure_prediction_ai",
        "smart_hiring_ai",
        "company_health_dashboard",
        "financial_roi_intelligence",
        "company_digital_twin",
        "enterprise_knowledge_company_brain",
        "knowledge_loss_graph_ai",
        "work_life_balance_optimizer",
        "ai_alert_correlator",
        "smart_suggestion_engine",
    ]

    def __init__(self) -> None:
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> GenAIHRAssistantResponse:
        return self.ask(GenAIHRAssistantRequest(question="Generate executive workforce report."))

    def ask(self, request: GenAIHRAssistantRequest) -> GenAIHRAssistantResponse:
        started = time.perf_counter()
        prior_memory = self._session_memory(request.session_id)
        memory_summary = prior_memory.memory_summary if prior_memory else ""
        intent = self._resolve_intent(request.question, memory_summary)
        tool_payloads, tool_calls = self._collect_tool_context(intent, include_realtime=request.include_realtime)
        documents = self._documents_from_tools(tool_payloads)
        history_documents = self._documents_from_history(request)
        retrieved_hits, vector_index = genai_hr_assistant_engine.retrieve(
            self._retrieval_query(request, memory_summary, intent),
            [*documents, *history_documents],
            top_k=8,
        )
        context_sources = [
            GenAIContextSource(
                citation_id=f"C{index}",
                system=hit.document.system,
                title=hit.document.title,
                snippet=hit.document.content[:650],
                confidence=round(float(np.clip(0.56 + hit.score * 0.42, 0.56, 0.98)), 3),
                metadata=hit.document.metadata,
            )
            for index, hit in enumerate(retrieved_hits, start=1)
        ]
        report_sections = self._report_sections(tool_payloads, context_sources)
        recommended_actions = self._recommended_actions(tool_payloads, report_sections, intent)
        local_answer = self._generate_answer(request.question, intent, report_sections, context_sources, recommended_actions, tool_payloads)
        provider_answer = self._external_llm_answer(request.question, intent, report_sections, context_sources, recommended_actions, local_answer)
        answer = provider_answer or local_answer
        executive_summary = self._executive_summary(intent, report_sections, tool_payloads)
        response_mode = self._response_mode(request.question, intent)
        memory = self._build_memory(request, intent, answer, prior_memory)
        confidence = self._confidence(context_sources, tool_calls, started)
        response = GenAIHRAssistantResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            session_id=request.session_id,
            question=request.question,
            intent=intent,
            response_mode=response_mode,
            answer=answer,
            executive_summary=executive_summary,
            recommended_actions=recommended_actions,
            retrieved_context=context_sources,
            tool_calls=tool_calls,
            report_sections=report_sections,
            conversation_memory=memory,
            reasoning_trace=[
                f"Classified natural-language HR query as {intent}.",
                f"Executed {len([call for call in tool_calls if call.status == 'success'])} analytics tool call(s) against live platform services.",
                f"Built {len(documents)} RAG documents from workforce analytics and retrieved {len(context_sources)} ranked context source(s).",
                "Synthesized answer using retrieved context, current tool outputs, conversation memory, and executive reporting policy.",
                f"Generation mode: {'external LLM API' if provider_answer else 'local retrieval-grounded fallback'}.",
            ],
            confidence=confidence,
            source_systems=self.source_systems,
            llm_provider=genai_hr_assistant_engine.llm_provider,
            rag_pipeline=genai_hr_assistant_engine.rag_pipeline,
            vector_database=genai_hr_assistant_engine.vector_database,
            storage=str(ASSISTANT_HISTORY_PATH),
            vector_index=vector_index,
        )
        self._append_jsonl(ASSISTANT_HISTORY_PATH, response.model_dump(mode="json"))
        self._append_jsonl(
            ASSISTANT_MEMORY_PATH,
            {
                "session_id": request.session_id,
                "created_at": response.generated_at.isoformat(),
                "user_id": request.user_id,
                "question": request.question,
                "intent": intent,
                "answer": answer,
                "entities": memory.remembered_entities,
            },
        )
        return response

    async def stream(self, request: GenAIHRAssistantRequest):
        response = self.ask(request)
        sequence = 1
        for token in self._tokenize_for_stream(response.answer):
            data = {
                "session_id": response.session_id,
                "type": "token",
                "token": token,
                "intent": response.intent,
                "sequence": sequence,
            }
            yield f"event: genai_hr_token\ndata: {json.dumps(data)}\n\n"
            sequence += 1
            await asyncio.sleep(0.025)
        payload = response.model_dump(mode="json")
        payload["stream_sequence"] = sequence
        yield f"event: genai_hr_complete\ndata: {json.dumps(payload)}\n\n"

    def _resolve_intent(self, question: str, memory_summary: str) -> GenAIHRIntent:
        normalized = question.strip().lower()
        if normalized in {"why", "why?", "explain", "explain why", "show trend", "show last 3 months trend"}:
            last = self._last_intent_from_memory(memory_summary)
            if last:
                return last
        scenario_tokens = [
            "simulate",
            "digital twin",
            "what happens if",
            "what if",
            "workforce reduction",
            "hiring freeze",
            "hiring freezes",
            "slips by",
            "budget cut",
            "meetings reduced",
            "meeting reduction",
            "team merge",
            "two teams merge",
            "lose engineers",
            "losing engineers",
            "finish in",
            "can we finish",
            "predict next quarter",
        ]
        if any(token in normalized for token in scenario_tokens):
            return "digital_twin"
        if "report" in normalized or "board" in normalized:
            return "report"
        if "resign" in normalized or "attrition" in normalized or "leave" in normalized:
            return "attrition"
        if "burnout" in normalized or "morale" in normalized or "wellness" in normalized or "stress" in normalized:
            return "burnout"
        if "productivity" in normalized or "focus" in normalized or "deep work" in normalized:
            return "productivity"
        if "project" in normalized and ("fail" in normalized or "risk" in normalized or "sprint" in normalized):
            return "project_risk"
        if "hiring" in normalized or "staff" in normalized or "hire" in normalized or "recruit" in normalized:
            return "hiring"
        if any(
            token in normalized
            for token in [
                "financial",
                "finance",
                "roi",
                "revenue",
                "cost",
                "costs",
                "budget",
                "profit",
                "profitability",
                "margin",
                "savings",
                "payback",
            ]
        ):
            return "financial"
        if "knowledge" in normalized or "sop" in normalized or "expertise" in normalized:
            return "knowledge"
        if "company health" in normalized or "summarize company" in normalized or "restructure" in normalized:
            return "company_health"
        return genai_hr_assistant_engine.classify_intent(question, memory_summary)

    def _collect_tool_context(self, intent: GenAIHRIntent, include_realtime: bool) -> tuple[dict[str, dict[str, object]], list[GenAIToolCall]]:
        tool_specs = [
            ("company_health", company_health_service.analyze, "Company health, team risk, executive KPI, workforce stability"),
            ("attrition", attrition_prediction_service.analyze, "Employee resignation forecasting and retention risk"),
            ("wellness", wellness_intelligence_service.analyze, "Burnout, stress, emotional exhaustion, wellness recommendations"),
            ("productivity", productivity_leakage_service.analyze, "Productivity leakage, focus windows, deep-work disruption"),
            ("project_failure", project_failure_service.analyze, "Project failure, deadline, budget, and sprint risk"),
        ]
        if intent in {"hiring", "report", "general"}:
            tool_specs.append(("hiring", hiring_intelligence_service.analyze, "Recruiting demand, candidate ranking, hiring recommendations"))
        if intent in {"financial", "report", "general"}:
            tool_specs.append(("roi", roi_intelligence_service.analyze, "Financial ROI, revenue exposure, payback, and budget optimization"))
        if intent in {"digital_twin", "report", "general"}:
            tool_specs.append(("digital_twin", self._digital_twin_payload, "Company Digital Twin simulation, graph snapshot, and risk propagation"))
        if intent in {"knowledge", "report", "general"}:
            tool_specs.append(("enterprise_knowledge", enterprise_knowledge_service.default, "Company Brain RAG, semantic search, expertise graph, organizational memory"))
            tool_specs.append(("knowledge_loss", knowledge_loss_service.analyze, "Knowledge graph, SOP generation, expertise-loss prevention"))
        if intent in {"burnout", "productivity", "report", "general"}:
            tool_specs.append(("work_life_balance", work_life_balance_service.optimize, "Work-life optimization, meeting reduction, task redistribution"))
        if include_realtime:
            tool_specs.extend(
                [
                    ("alerts", alert_service.feed, "Realtime AI alert correlation"),
                    ("suggestions", smart_suggestion_service.generate, "Smart AI recommendation engine"),
                ]
            )
        payloads: dict[str, dict[str, object]] = {}
        calls: list[GenAIToolCall] = []
        for name, func, purpose in tool_specs:
            started = time.perf_counter()
            try:
                result = func()
                data = result.model_dump(mode="json") if hasattr(result, "model_dump") else dict(result)
                payloads[name] = data
                calls.append(
                    GenAIToolCall(
                        name=name,
                        status="success",
                        latency_ms=round((time.perf_counter() - started) * 1000),
                        summary=purpose,
                        evidence=self._tool_evidence(name, data),
                    )
                )
            except Exception as error:
                calls.append(
                    GenAIToolCall(
                        name=name,
                        status="error",
                        latency_ms=round((time.perf_counter() - started) * 1000),
                        summary=f"{purpose} failed during assistant orchestration.",
                        evidence=[str(error)[:240]],
                    )
                )
        return payloads, calls

    def _documents_from_tools(self, payloads: dict[str, dict[str, object]]) -> list[GenAIKnowledgeDocument]:
        documents: list[GenAIKnowledgeDocument] = []
        if company := payloads.get("company_health"):
            summary = company.get("summary", {})
            top_team = self._first(company.get("team_scores", []))
            documents.append(
                self._doc(
                    "company-health-summary",
                    "company_health",
                    "Realtime Company Health Summary",
                    (
                        f"Company health score is {self._number(summary, 'company_health_score')} with "
                        f"burnout risk {self._number(summary, 'burnout_risk')}, attrition risk {self._number(summary, 'attrition_risk')}, "
                        f"productivity {self._number(summary, 'productivity_score')}, and {summary.get('high_risk_teams', 0)} high-risk team(s). "
                        f"Highest visible team context: {top_team.get('team_name', 'unknown')} has risk {top_team.get('risk_score', 'n/a')} and recommendation {top_team.get('recommendation', 'n/a')}."
                    ),
                    {"health": self._number(summary, "company_health_score"), "burnout": self._number(summary, "burnout_risk")},
                )
            )
        if attrition := payloads.get("attrition"):
            summary = attrition.get("summary", {})
            top = self._first(attrition.get("predictions", []))
            documents.append(
                self._doc(
                    "attrition-risk",
                    "attrition_prediction_ai",
                    "Employee Attrition Forecast",
                    (
                        f"{summary.get('high_risk_employees', 0)} high-risk employee(s), {summary.get('critical_risk_employees', 0)} critical employee(s), "
                        f"average resignation probability {self._number(summary, 'average_resignation_probability')} and workforce stability {self._number(summary, 'workforce_stability_score')}. "
                        f"Top risk: {top.get('employee_name', summary.get('top_risk_employee', 'unknown'))} at {top.get('resignation_probability', 'n/a')} probability with reasons {', '.join(top.get('primary_reasons', [])[:3])}."
                    ),
                    {"high_risk": summary.get("high_risk_employees", 0), "avg_attrition": self._number(summary, "average_resignation_probability")},
                )
            )
        if wellness := payloads.get("wellness"):
            summary = wellness.get("summary", {})
            alert = self._first(wellness.get("risk_alerts", []))
            documents.append(
                self._doc(
                    "wellness-burnout",
                    "wellness_intelligence_ai",
                    "Burnout And Mental Wellness Forecast",
                    (
                        f"Wellness score {self._number(summary, 'wellness_score')}, stress {self._number(summary, 'stress_score')}, burnout probability {self._number(summary, 'burnout_probability')}, "
                        f"emotional exhaustion {self._number(summary, 'emotional_exhaustion_probability')}, high-risk teams {summary.get('high_risk_team_count', 0)}. "
                        f"Top alert: {alert.get('message', 'No severe alert')} with recommendation {alert.get('recommendation', 'maintain monitoring')}."
                    ),
                    {"burnout": self._number(summary, "burnout_probability"), "stress": self._number(summary, "stress_score")},
                )
            )
        if productivity := payloads.get("productivity"):
            summary = productivity.get("summary", {})
            documents.append(
                self._doc(
                    "productivity-forecast",
                    "productivity_leakage_ai",
                    "Productivity And Focus Forecast",
                    (
                        f"Productivity score {self._number(summary, 'productivity_score')}, focus score {self._number(summary, 'focus_score')}, efficiency {self._number(summary, 'efficiency_score')}, "
                        f"leakage {self._number(summary, 'leakage_percent')} percent, lost hours {summary.get('lost_productive_hours', 0)}, "
                        f"tool-switching overload {self._number(summary, 'tool_switching_overload')} and deep-work stability {self._number(summary, 'deep_work_stability')}."
                    ),
                    {"productivity": self._number(summary, "productivity_score"), "leakage": self._number(summary, "leakage_percent")},
                )
            )
        if project := payloads.get("project_failure"):
            summary = project.get("summary", {})
            top = self._first(project.get("predictions", []))
            documents.append(
                self._doc(
                    "project-risk",
                    "project_failure_prediction_ai",
                    "Project Failure Forecast",
                    (
                        f"{summary.get('critical_projects', 0)} critical project(s), average failure probability {self._number(summary, 'average_failure_probability')}, "
                        f"average delay probability {self._number(summary, 'average_delay_probability')}, highest risk project {summary.get('highest_risk_project', 'unknown')}. "
                        f"Top project {top.get('project_name', 'unknown')} has failure probability {top.get('failure_probability', 'n/a')} and deadline miss {top.get('deadline_miss_probability', 'n/a')}."
                    ),
                    {"failure": self._number(summary, "average_failure_probability"), "delay": self._number(summary, "average_delay_probability")},
                )
            )
        if twin := payloads.get("digital_twin"):
            stress = twin.get("stress_case", {})
            baseline = twin.get("baseline", {})
            suite = twin.get("scenario_suite", {}) if isinstance(twin, dict) else {}
            scenarios = suite.get("scenarios", []) if isinstance(suite, dict) else []
            top_scenario = self._first(scenarios)
            documents.append(
                self._doc(
                    "company-digital-twin",
                    "company_digital_twin",
                    "Company Digital Twin Scenario Model",
                    (
                        f"Digital Twin tracks {twin.get('employees', 0)} employee twin(s), {twin.get('teams', 0)} team twin(s), "
                        f"{twin.get('projects', 0)} project twin(s), {twin.get('resources', 0)} resource twin(s), and {twin.get('operations', 0)} operation twin(s). "
                        f"Stress case delay is {self._number(stress, 'delay_probability')} percent, team collapse is "
                        f"{self._number(stress, 'team_collapse_probability')} percent, revenue impact is "
                        f"{self._number(stress, 'revenue_impact_percent')} percent, and affected departments are "
                        f"{', '.join(stress.get('affected_departments', [])[:3]) if isinstance(stress, dict) else 'unknown'}. "
                        f"Baseline stability is {self._number(baseline, 'stability_score')}. "
                        f"The enterprise scenario decision engine covers employee resignation, project completion, hiring freeze, team restructure, budget cut, and productivity change. "
                        f"Top suite scenario {top_scenario.get('scenario_type', 'unknown')} has success probability {top_scenario.get('success_probability', 'n/a')} and risk level {top_scenario.get('risk_level', 'n/a')}."
                    ),
                    {
                        "stress_delay": self._number(stress, "delay_probability"),
                        "stress_collapse": self._number(stress, "team_collapse_probability"),
                        "baseline_stability": self._number(baseline, "stability_score"),
                    },
                )
            )
        if hiring := payloads.get("hiring"):
            summary = hiring.get("summary", {})
            documents.append(
                self._doc(
                    "hiring-demand",
                    "smart_hiring_ai",
                    "Strategic Hiring Demand",
                    (
                        f"Hiring analysis reviewed {summary.get('candidates_analyzed', 0)} candidate(s), top candidate {summary.get('top_candidate', 'unknown')}, "
                        f"average compatibility {self._number(summary, 'average_compatibility')}, skill gaps {summary.get('skill_gap_count', 0)}, and fraud risks {summary.get('fraud_risk_count', 0)}."
                    ),
                    {"skill_gaps": summary.get("skill_gap_count", 0), "strong_hires": summary.get("strong_hire_count", 0)},
                )
            )
        if roi := payloads.get("roi"):
            summary = roi.get("summary", {})
            forecast = self._first(roi.get("forecast", []))
            recommendation = self._first(roi.get("recommendations", []))
            documents.append(
                self._doc(
                    "financial-roi-intelligence",
                    "financial_roi_intelligence",
                    "Financial ROI And Budget Forecast",
                    (
                        f"Baseline annual loss is ${round(self._number(summary, 'baseline_annual_loss')):,}, optimized annual loss is "
                        f"${round(self._number(summary, 'optimized_annual_loss')):,}, net savings are ${round(self._number(summary, 'net_savings')):,}, "
                        f"ROI is {self._number(summary, 'roi_percent')} percent, and payback is {self._number(summary, 'payback_months')} months. "
                        f"Replacement exposure is ${round(self._number(summary, 'replacement_cost_exposure')):,}, productivity-loss exposure is "
                        f"${round(self._number(summary, 'productivity_loss_exposure')):,}, project-delay exposure is ${round(self._number(summary, 'project_delay_exposure')):,}. "
                        f"Forecast month {forecast.get('month', 'n/a')} cumulative savings are ${round(self._number(forecast, 'cumulative_savings')):,}. "
                        f"Top budget action: {recommendation.get('action', 'prioritize highest ROI intervention')}."
                    ),
                    {
                        "roi_percent": self._number(summary, "roi_percent"),
                        "net_savings": self._number(summary, "net_savings"),
                        "payback_months": self._number(summary, "payback_months"),
                    },
                )
            )
        if knowledge := payloads.get("knowledge_loss"):
            summary = knowledge.get("summary", {})
            documents.append(
                self._doc(
                    "knowledge-loss",
                    "knowledge_loss_graph_ai",
                    "Organizational Knowledge Risk",
                    (
                        f"Knowledge graph has {summary.get('graph_nodes', 0)} nodes and {summary.get('graph_edges', 0)} edges, "
                        f"{summary.get('high_risk_dependencies', 0)} high-risk dependencies, top owner {summary.get('top_risk_owner', 'unknown')}, "
                        f"knowledge-loss risk {self._number(summary, 'knowledge_loss_risk')} and documentation coverage {self._number(summary, 'average_documentation_coverage')}."
                    ),
                    {"knowledge_loss": self._number(summary, "knowledge_loss_risk"), "docs": self._number(summary, "average_documentation_coverage")},
                )
            )
        if brain := payloads.get("enterprise_knowledge"):
            summary = brain.get("summary", {})
            top_experts = brain.get("top_experts", []) if isinstance(brain, dict) else []
            top_expert = self._first(top_experts)
            incident_memory = brain.get("incident_memory", []) if isinstance(brain, dict) else []
            incident = self._first(incident_memory)
            documents.append(
                self._doc(
                    "enterprise-knowledge-brain",
                    "enterprise_knowledge_company_brain",
                    "Company Brain Knowledge Memory",
                    (
                        f"Company Brain indexed {summary.get('documents_indexed', 0)} document(s), {summary.get('chunks_indexed', 0)} chunk(s), "
                        f"{summary.get('graph_nodes', 0)} graph node(s), and {summary.get('graph_edges', 0)} graph edge(s). "
                        f"Top expert is {top_expert.get('employee_name', 'unknown')} for {top_expert.get('skill', 'enterprise knowledge')} at {top_expert.get('score', 'n/a')}. "
                        f"Incident memory example: {incident.get('title', 'none')} with detail {incident.get('detail', 'none')}."
                    ),
                    {
                        "documents": summary.get("documents_indexed", 0) if isinstance(summary, dict) else 0,
                        "graph_nodes": summary.get("graph_nodes", 0) if isinstance(summary, dict) else 0,
                        "experts": summary.get("experts_detected", 0) if isinstance(summary, dict) else 0,
                    },
                )
            )
        if worklife := payloads.get("work_life_balance"):
            summary = worklife.get("summary", {})
            documents.append(
                self._doc(
                    "work-life-balance",
                    "work_life_balance_optimizer",
                    "Work-Life Balance Optimization",
                    (
                        f"Work-life optimizer analyzed {summary.get('employees_analyzed', 0)} employees with wellness {self._number(summary, 'wellness_score')}, "
                        f"burnout risk {self._number(summary, 'burnout_risk')}, meeting reduction {self._number(summary, 'meeting_reduction_percent')} percent, "
                        f"focus gain {summary.get('focus_time_gain_hours', 0)} hours, and redistribution {summary.get('task_redistribution_hours', 0)} hours."
                    ),
                    {"meeting_reduction": self._number(summary, "meeting_reduction_percent"), "focus_gain": self._number(summary, "focus_time_gain_hours")},
                )
            )
        if alerts := payloads.get("alerts"):
            summary = alerts.get("summary", {})
            top = self._first(alerts.get("alerts", []))
            documents.append(
                self._doc(
                    "realtime-alerts",
                    "ai_alert_correlator",
                    "Realtime AI Alert Context",
                    (
                        f"Alert feed has {summary.get('total', 0)} event(s), {summary.get('critical', 0)} critical, {summary.get('high', 0)} high, average risk {summary.get('average_risk', 0)}. "
                        f"Top alert {top.get('title', 'none')} says {top.get('message', 'No active severe alert')}."
                    ),
                    {"critical": summary.get("critical", 0), "average_risk": summary.get("average_risk", 0)},
                )
            )
        if suggestions := payloads.get("suggestions"):
            summary = suggestions.get("summary", {})
            top = self._first(suggestions.get("suggestions", []))
            documents.append(
                self._doc(
                    "smart-suggestions",
                    "smart_suggestion_engine",
                    "AI Recommended Intervention",
                    (
                        f"Suggestion engine generated {summary.get('total', 0)} action(s), average impact {summary.get('average_impact', 0)}, "
                        f"average confidence {summary.get('average_confidence', 0)}. Top action: {top.get('action', 'maintain monitoring')}."
                    ),
                    {"actions": summary.get("total", 0), "impact": summary.get("average_impact", 0)},
                )
            )
        return documents

    def _documents_from_history(self, request: GenAIHRAssistantRequest) -> list[GenAIKnowledgeDocument]:
        documents = []
        for index, message in enumerate(request.history[-6:], start=1):
            documents.append(
                self._doc(
                    f"history-{index}",
                    "conversation_memory",
                    f"Conversation {message.role}",
                    message.content,
                    {"turn": index},
                )
            )
        previous = self._last_memory_entries(request.session_id, limit=4)
        for index, item in enumerate(previous, start=1):
            documents.append(
                self._doc(
                    f"session-memory-{index}",
                    "conversation_memory",
                    f"Previous {item.get('intent', 'general')} discussion",
                    f"Question: {item.get('question', '')}. Answer: {item.get('answer', '')}",
                    {"turn": index},
                )
            )
        return documents

    def _report_sections(self, payloads: dict[str, dict[str, object]], sources: list[GenAIContextSource]) -> list[GenAIReportSection]:
        company = payloads.get("company_health", {}).get("summary", {})
        attrition = payloads.get("attrition", {}).get("summary", {})
        wellness = payloads.get("wellness", {}).get("summary", {})
        productivity = payloads.get("productivity", {}).get("summary", {})
        project = payloads.get("project_failure", {}).get("summary", {})
        twin = payloads.get("digital_twin", {})
        twin_stress = twin.get("stress_case", {}) if isinstance(twin, dict) else {}
        suite = twin.get("scenario_suite", {}) if isinstance(twin, dict) else {}
        scenario_count = len(suite.get("scenarios", [])) if isinstance(suite, dict) and isinstance(suite.get("scenarios", []), list) else 0
        hiring = payloads.get("hiring", {}).get("summary", {})
        roi = payloads.get("roi", {}).get("summary", {})
        knowledge = payloads.get("knowledge_loss", {}).get("summary", {})
        company_brain = payloads.get("enterprise_knowledge", {}).get("summary", {})
        company_brain_expert = self._first(payloads.get("enterprise_knowledge", {}).get("top_experts", []))
        suggestions = payloads.get("suggestions", {}).get("suggestions", [])
        sections = [
            GenAIReportSection(
                title="Executive Workforce Health",
                summary=(
                    f"Company health is {self._number(company, 'company_health_score')} with burnout risk {self._number(company, 'burnout_risk')} "
                    f"and attrition risk {self._number(company, 'attrition_risk')}."
                ),
                metrics={
                    "company_health_score": self._number(company, "company_health_score"),
                    "employee_happiness_score": self._number(company, "employee_happiness_score"),
                    "high_risk_teams": company.get("high_risk_teams", 0) if isinstance(company, dict) else 0,
                },
                evidence=[source.title for source in sources[:3]],
                recommendations=[self._first(suggestions).get("action", "Prioritize highest-risk workforce interventions.")],
            ),
            GenAIReportSection(
                title="Retention And Burnout Risk",
                summary=(
                    f"Attrition model reports {attrition.get('high_risk_employees', 0) if isinstance(attrition, dict) else 0} high-risk employee(s). "
                    f"Wellness model estimates burnout probability {self._number(wellness, 'burnout_probability')} and stress {self._number(wellness, 'stress_score')}."
                ),
                metrics={
                    "average_resignation_probability": self._number(attrition, "average_resignation_probability"),
                    "critical_risk_employees": attrition.get("critical_risk_employees", 0) if isinstance(attrition, dict) else 0,
                    "burnout_probability": self._number(wellness, "burnout_probability"),
                },
                evidence=["Attrition model probabilities", "Wellness NLP and behavioral analytics"],
                recommendations=["Run retention interventions for top attrition employees and reduce workload for high-burnout teams."],
            ),
            GenAIReportSection(
                title="Productivity And Delivery Forecast",
                summary=(
                    f"Productivity score is {self._number(productivity, 'productivity_score')} with leakage {self._number(productivity, 'leakage_percent')} percent. "
                    f"Project portfolio average failure probability is {self._number(project, 'average_failure_probability')} and delay probability {self._number(project, 'average_delay_probability')}."
                ),
                metrics={
                    "productivity_score": self._number(productivity, "productivity_score"),
                    "lost_productive_hours": productivity.get("lost_productive_hours", 0) if isinstance(productivity, dict) else 0,
                    "critical_projects": project.get("critical_projects", 0) if isinstance(project, dict) else 0,
                },
                evidence=["Productivity leakage engine", "Project failure forecasting engine"],
                recommendations=["Protect deep-work windows and stabilize highest-risk sprint delivery paths."],
            ),
            GenAIReportSection(
                title="Hiring And Knowledge Continuity",
                summary=(
                    f"Hiring analysis reports {hiring.get('skill_gap_count', 0) if isinstance(hiring, dict) else 0} skill gap(s). "
                    f"Knowledge graph reports top risk owner {knowledge.get('top_risk_owner', 'unknown') if isinstance(knowledge, dict) else 'unknown'}, "
                    f"and Company Brain top expert {company_brain_expert.get('employee_name', 'unknown')} for {company_brain_expert.get('skill', 'enterprise knowledge')}."
                ),
                metrics={
                    "skill_gap_count": hiring.get("skill_gap_count", 0) if isinstance(hiring, dict) else 0,
                    "knowledge_loss_risk": self._number(knowledge, "knowledge_loss_risk"),
                    "generated_documents": knowledge.get("generated_documents", 0) if isinstance(knowledge, dict) else 0,
                    "company_brain_documents": company_brain.get("documents_indexed", 0) if isinstance(company_brain, dict) else 0,
                    "company_brain_graph_nodes": company_brain.get("graph_nodes", 0) if isinstance(company_brain, dict) else 0,
                },
                evidence=["Smart hiring ranking", "Knowledge graph and generated SOP engine", "Company Brain semantic RAG and expertise graph"],
                recommendations=["Prioritize hiring for bottleneck skills, complete SOP transfer, and keep Company Brain citations current."],
            ),
        ]
        if isinstance(roi, dict) and roi:
            sections.insert(
                3,
                GenAIReportSection(
                    title="Financial Intelligence",
                    summary=(
                        f"ROI engine models ${round(self._number(roi, 'net_savings')):,} net savings, "
                        f"{self._number(roi, 'roi_percent')} percent ROI, and {self._number(roi, 'payback_months')} month payback."
                    ),
                    metrics={
                        "baseline_annual_loss": self._number(roi, "baseline_annual_loss"),
                        "net_savings": self._number(roi, "net_savings"),
                        "roi_percent": self._number(roi, "roi_percent"),
                        "project_delay_exposure": self._number(roi, "project_delay_exposure"),
                    },
                    evidence=["ROI intelligence engine", "Revenue exposure forecast", "Workforce cost model"],
                    recommendations=["Fund interventions where ROI, delay-risk reduction, and retention exposure produce measurable payback."],
                ),
            )
        if isinstance(twin_stress, dict) and twin_stress:
            sections.insert(
                3,
                GenAIReportSection(
                    title="Company Digital Twin",
                    summary=(
                        f"Stress simulation predicts {self._number(twin_stress, 'delay_probability')} percent delay risk, "
                        f"{self._number(twin_stress, 'team_collapse_probability')} percent team-collapse probability, and "
                        f"{self._number(twin_stress, 'revenue_impact_percent')} percent revenue impact. "
                        f"The enterprise decision suite evaluates {scenario_count} scenario contract(s) across workforce, project, hiring, budget, restructuring, and productivity decisions."
                    ),
                    metrics={
                        "delay_probability": self._number(twin_stress, "delay_probability"),
                        "team_collapse_probability": self._number(twin_stress, "team_collapse_probability"),
                        "productivity_loss_percent": self._number(twin_stress, "productivity_loss_percent"),
                        "stability_score": self._number(twin_stress, "stability_score"),
                    },
                    evidence=["Employee, team, project, resource, workflow, and operation twin graph", "Monte Carlo simulation", "Risk propagation path", "Scenario decision suite"],
                    recommendations=["Use the Digital Twin decision suite before approving workforce reduction, hiring freeze, project, budget, productivity, or restructuring decisions."],
                ),
            )
        return sections

    def _recommended_actions(self, payloads: dict[str, dict[str, object]], sections: list[GenAIReportSection], intent: GenAIHRIntent) -> list[str]:
        actions: list[str] = []
        for key in ["suggestions", "company_health", "attrition", "wellness", "project_failure", "digital_twin", "roi", "work_life_balance"]:
            data = payloads.get(key, {})
            for item_key in ["suggestions", "recommendations", "portfolio_recommendations"]:
                items = data.get(item_key, [])
                if isinstance(items, list):
                    for item in items[:2]:
                        if isinstance(item, dict):
                            action = item.get("action") or item.get("recommendation") or item.get("title")
                            if action:
                                actions.append(str(action))
        for section in sections:
            actions.extend(section.recommendations)
        if intent == "hiring":
            actions.insert(0, "Open a targeted hiring plan for backend platform, reliability, or bottleneck roles with validated skill-gap evidence.")
        if intent == "attrition":
            actions.insert(0, "Start manager-led retention reviews for employees with the highest resignation probability.")
        if intent == "financial":
            actions.insert(0, "Prioritize funded interventions by modeled ROI, payback period, revenue protection, and avoidable workforce cost.")
        if intent == "digital_twin":
            actions.insert(0, "Run the company Digital Twin before approving workforce, project, budget, overtime, or hiring-freeze decisions.")
        unique: list[str] = []
        for action in actions:
            if action not in unique:
                unique.append(action)
        return unique[:8]

    def _generate_answer(
        self,
        question: str,
        intent: GenAIHRIntent,
        sections: list[GenAIReportSection],
        sources: list[GenAIContextSource],
        actions: list[str],
        payloads: dict[str, dict[str, object]],
    ) -> str:
        citations = ", ".join(source.citation_id for source in sources[:4]) or "C1"
        if intent == "report":
            section_lines = " ".join(f"{section.title}: {section.summary}" for section in sections)
            return (
                f"Generated executive HR report successfully. {section_lines} "
                f"Primary action: {actions[0] if actions else 'Prioritize the highest-risk workforce intervention.'} "
                f"Grounding: {citations}."
            )
        if intent == "attrition":
            attrition = payloads.get("attrition", {})
            summary = attrition.get("summary", {})
            top = self._first(attrition.get("predictions", []))
            return (
                f"The highest attrition concern is {top.get('employee_name', summary.get('top_risk_employee', 'unknown'))} at "
                f"{top.get('resignation_probability', self._number(summary, 'average_resignation_probability'))}% resignation probability. "
                f"The likely drivers are {', '.join(top.get('primary_reasons', [])[:3]) or 'burnout, workload, and engagement pressure'}. "
                f"Recommended intervention: {actions[0] if actions else 'Run retention review and workload reset.'} Grounding: {citations}."
            )
        if intent == "burnout":
            wellness = payloads.get("wellness", {}).get("summary", {})
            company = payloads.get("company_health", {}).get("summary", {})
            return (
                f"The strongest burnout signal is company burnout risk {self._number(company, 'burnout_risk')} and employee burnout probability "
                f"{self._number(wellness, 'burnout_probability')}. Stress is {self._number(wellness, 'stress_score')}, with emotional exhaustion "
                f"{self._number(wellness, 'emotional_exhaustion_probability')}. Recommended intervention: {actions[0] if actions else 'Reduce meeting load and rebalance workload.'} Grounding: {citations}."
            )
        if intent == "productivity":
            productivity = payloads.get("productivity", {}).get("summary", {})
            return (
                f"Next productivity risk is concentrated in leakage {self._number(productivity, 'leakage_percent')}%, focus score {self._number(productivity, 'focus_score')}, "
                f"and tool-switching overload {self._number(productivity, 'tool_switching_overload')}. The likely next-month productivity movement is negative if focus protection is not enforced. "
                f"Recommended action: {actions[0] if actions else 'Protect deep-work windows and reduce notification load.'} Grounding: {citations}."
            )
        if intent == "project_risk":
            project = payloads.get("project_failure", {})
            summary = project.get("summary", {})
            top = self._first(project.get("predictions", []))
            return (
                f"{top.get('project_name', summary.get('highest_risk_project', 'unknown'))} is the project most likely to fail next sprint, with failure probability "
                f"{top.get('failure_probability', self._number(summary, 'average_failure_probability'))}% and deadline miss probability {top.get('deadline_miss_probability', self._number(summary, 'average_delay_probability'))}%. "
                f"Recommended action: {actions[0] if actions else 'Stabilize dependencies and reduce scope pressure.'} Grounding: {citations}."
            )
        if intent == "hiring":
            hiring = payloads.get("hiring", {}).get("summary", {})
            company = payloads.get("company_health", {}).get("summary", {})
            return (
                f"The urgent hiring signal is tied to {hiring.get('skill_gap_count', 0) if isinstance(hiring, dict) else 0} detected skill gap(s), "
                f"company operational risk {self._number(company, 'operational_risk')}, and high-risk teams {company.get('high_risk_teams', 0) if isinstance(company, dict) else 0}. "
                f"Recommended action: {actions[0] if actions else 'Open targeted hiring for bottleneck skills.'} Grounding: {citations}."
            )
        if intent == "financial":
            roi = payloads.get("roi", {})
            summary = roi.get("summary", {})
            top = self._first(roi.get("recommendations", []))
            return (
                f"Financial intelligence models ${round(self._number(summary, 'net_savings')):,} net savings, "
                f"{self._number(summary, 'roi_percent')}% ROI, and {self._number(summary, 'payback_months')} month payback. "
                f"Baseline annual loss is ${round(self._number(summary, 'baseline_annual_loss')):,}, with "
                f"${round(self._number(summary, 'replacement_cost_exposure')):,} replacement exposure, "
                f"${round(self._number(summary, 'productivity_loss_exposure')):,} productivity-loss exposure, and "
                f"${round(self._number(summary, 'project_delay_exposure')):,} project-delay exposure. "
                f"Recommended budget action: {top.get('action', actions[0] if actions else 'Fund the highest ROI intervention first.')} Grounding: {citations}."
            )
        if intent == "digital_twin":
            twin = payloads.get("digital_twin", {})
            stress = twin.get("stress_case", {})
            affected = stress.get("affected_departments", []) if isinstance(stress, dict) else []
            suite = twin.get("scenario_suite", {}) if isinstance(twin, dict) else {}
            scenarios = suite.get("scenarios", []) if isinstance(suite, dict) else []
            selected = self._select_scenario(question, scenarios if isinstance(scenarios, list) else [])
            if selected:
                recommendations = selected.get("recommendations", [])
                recommendation = recommendations[0] if isinstance(recommendations, list) and recommendations else actions[0] if actions else "Run scenario-specific mitigation before committing the decision."
                return (
                    f"The Company Digital Twin scenario engine says {selected.get('scenario_summary', 'scenario simulation')} returns {selected.get('success_probability', 0)}% success probability, "
                    f"{selected.get('failure_probability', 0)}% failure probability, {selected.get('delivery_delay_probability', 0)}% delivery-delay risk, "
                    f"{selected.get('productivity_impact_percent', 0)}% productivity impact, {selected.get('revenue_impact_percent', 0)}% revenue impact, "
                    f"and {selected.get('risk_level', 'unknown')} risk. Required engineers: {selected.get('required_engineers', 0)}; required budget: "
                    f"${round(self._number(selected, 'required_budget')):,}. Recommendation: {recommendation} Grounding: {citations}."
                )
            return (
                f"The Company Digital Twin simulates employee, team, project, department, resource, workflow, and operation impact. "
                f"In the stress scenario, delay risk is {self._number(stress, 'delay_probability')}%, team-collapse probability is "
                f"{self._number(stress, 'team_collapse_probability')}%, productivity loss is {self._number(stress, 'productivity_loss_percent')}%, "
                f"revenue impact is {self._number(stress, 'revenue_impact_percent')}%, and stability is {self._number(stress, 'stability_score')}%. "
                f"Affected departments: {', '.join(affected[:3]) if isinstance(affected, list) and affected else 'not detected'}. "
                f"Recommended action: {actions[0] if actions else 'Run a scenario-specific simulation before committing the decision.'} Grounding: {citations}."
            )
        if intent == "knowledge":
            try:
                brain_answer = enterprise_knowledge_service.ask(
                    EnterpriseKnowledgeAskRequest(question=question, top_k=6, session_id="genai-hr")
                )
                brain_citations = ", ".join(citation.citation_id for citation in brain_answer.citations[:4]) or citations
                return (
                    f"{brain_answer.answer} Company Brain confidence is {round(brain_answer.confidence * 100)}%. "
                    f"Recommended action: {brain_answer.recommended_follow_up_actions[0] if brain_answer.recommended_follow_up_actions else actions[0] if actions else 'Keep knowledge transfer and SOP updates active.'} "
                    f"Grounding: {brain_citations}."
                )
            except Exception:
                pass
            knowledge = payloads.get("knowledge_loss", {}).get("summary", {})
            return (
                f"The highest knowledge continuity concern is {knowledge.get('top_risk_owner', 'unknown') if isinstance(knowledge, dict) else 'unknown'}, "
                f"with knowledge-loss risk {self._number(knowledge, 'knowledge_loss_risk')} and documentation coverage {self._number(knowledge, 'average_documentation_coverage')}. "
                f"Recommended action: {actions[0] if actions else 'Generate SOPs and assign backup owners.'} Grounding: {citations}."
            )
        company = payloads.get("company_health", {}).get("summary", {})
        return (
            f"NEXUSMIND AI sees company health {self._number(company, 'company_health_score')}, burnout risk {self._number(company, 'burnout_risk')}, "
            f"attrition risk {self._number(company, 'attrition_risk')}, and productivity {self._number(company, 'productivity_score')}. "
            f"Recommended action: {actions[0] if actions else 'Prioritize the highest confidence workforce intervention.'} Grounding: {citations}."
        )

    def _external_llm_answer(
        self,
        question: str,
        intent: GenAIHRIntent,
        sections: list[GenAIReportSection],
        sources: list[GenAIContextSource],
        actions: list[str],
        fallback_answer: str,
    ) -> str | None:
        if os.getenv("NEXUSMIND_ENABLE_EXTERNAL_LLM", "").lower() not in {"1", "true", "yes"}:
            return None
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
        model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        context = "\n".join(f"{source.citation_id} {source.title}: {source.snippet}" for source in sources[:6])
        report = "\n".join(f"{section.title}: {section.summary}" for section in sections)
        action_text = "\n".join(f"- {action}" for action in actions[:6])
        try:
            response = httpx.post(
                api_url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0.2,
                    "max_tokens": 520,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are NEXUSMIND AI's enterprise HR assistant. Answer only from supplied analytics context, "
                                "cite source ids inline, preserve numeric metrics, and return concise executive guidance."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Question: {question}\nIntent: {intent}\n\nRAG context:\n{context}\n\nReport sections:\n{report}\n\n"
                                f"Recommended actions:\n{action_text}\n\nFallback synthesis:\n{fallback_answer}"
                            ),
                        },
                    ],
                },
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()[:4000]
        except Exception:
            return None
        return None

    def _digital_twin_payload(self) -> dict[str, object]:
        snapshot = digital_twin_simulator.snapshot()
        scenario = TwinScenarioInput(
            resignation_count=20,
            workload_delta_percent=30,
            budget_delta_percent=-10,
            security_incident=True,
        )
        stress = digital_twin_simulator.simulate_extended(scenario)
        monte_carlo = digital_twin_simulator.simulate_monte_carlo(scenario)
        scenario_suite = digital_twin_simulator.scenario_decision_suite()
        return {
            "employees": len(snapshot["employees"]),
            "teams": len(snapshot["teams"]),
            "departments": len(snapshot["departments"]),
            "projects": len(snapshot["projects"]),
            "resources": len(snapshot["resources"]),
            "workflows": len(snapshot["workflows"]),
            "operations": len(snapshot["operations"]),
            "graph_edges": len(snapshot["graph_edges"]),
            "forecast_models": snapshot["forecast_models"],
            "supported_scenarios": snapshot["supported_scenarios"],
            "baseline": snapshot["baseline"],
            "stress_case": {
                "delay_probability": stress.delay_probability,
                "burnout_delta": stress.burnout_delta,
                "revenue_impact_percent": stress.revenue_impact_percent,
                "stability_score": stress.stability_score,
                "productivity_loss_percent": stress.productivity_loss_percent,
                "team_collapse_probability": stress.team_collapse_probability,
                "affected_departments": stress.affected_departments,
                "workflow_impacts": stress.workflow_impacts,
                "recovery_actions": stress.recovery_actions,
            },
            "monte_carlo": {
                "runs": monte_carlo.runs,
                "success_probability": monte_carlo.success_probability,
                "delay_probability_p90": monte_carlo.delay_probability_p90,
                "team_collapse_p90": monte_carlo.team_collapse_p90,
                "confidence": monte_carlo.confidence,
            },
            "scenario_suite": scenario_suite,
            "recommendations": [
                {"action": stress.recovery_actions[0]},
                *[{"action": item} for item in scenario_suite.get("executive_recommendations", [])[:2]],
            ],
        }

    def _executive_summary(self, intent: GenAIHRIntent, sections: list[GenAIReportSection], payloads: dict[str, dict[str, object]]) -> str:
        company = payloads.get("company_health", {}).get("summary", {})
        health = self._number(company, "company_health_score")
        risk = self._number(company, "operational_risk")
        return f"Intent {intent}: enterprise workforce health is {health}, operational risk is {risk}, and {len(sections)} executive report section(s) were generated from live analytics."

    def _build_memory(
        self,
        request: GenAIHRAssistantRequest,
        intent: GenAIHRIntent,
        answer: str,
        prior: GenAIConversationMemory | None,
    ) -> GenAIConversationMemory:
        entities = self._extract_entities(f"{request.question} {answer}")
        if prior:
            entities = sorted(set([*prior.remembered_entities, *entities]))[:16]
            turns = prior.turns + 1
        else:
            turns = 1
        return GenAIConversationMemory(
            session_id=request.session_id,
            turns=turns,
            last_intent=intent,
            remembered_entities=entities,
            memory_summary=f"Last intent: {intent}. Entities: {', '.join(entities[:8]) or 'none'}. Turns: {turns}.",
        )

    def _session_memory(self, session_id: str) -> GenAIConversationMemory | None:
        entries = self._last_memory_entries(session_id, limit=8)
        if not entries:
            return None
        last = entries[-1]
        entities = sorted({entity for entry in entries for entity in entry.get("entities", []) if isinstance(entity, str)})
        intent = last.get("intent", "general")
        if intent not in genai_hr_assistant_engine._intent_labels():
            intent = "general"
        return GenAIConversationMemory(
            session_id=session_id,
            turns=len(entries),
            last_intent=intent,  # type: ignore[arg-type]
            remembered_entities=entities[:16],
            memory_summary=f"Last intent: {intent}. Entities: {', '.join(entities[:8]) or 'none'}. Turns: {len(entries)}.",
        )

    def _last_memory_entries(self, session_id: str, limit: int) -> list[dict[str, object]]:
        if not ASSISTANT_MEMORY_PATH.exists():
            return []
        rows = []
        try:
            with ASSISTANT_MEMORY_PATH.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    if item.get("session_id") == session_id:
                        rows.append(item)
        except (OSError, json.JSONDecodeError):
            return []
        return rows[-limit:]

    @staticmethod
    def _retrieval_query(request: GenAIHRAssistantRequest, memory_summary: str, intent: GenAIHRIntent) -> str:
        history = " ".join(message.content for message in request.history[-4:])
        return f"{intent} {request.question} {history} {memory_summary}"

    @staticmethod
    def _response_mode(question: str, intent: GenAIHRIntent) -> str:
        normalized = question.lower()
        if intent == "report" or "report" in normalized:
            return "report"
        if intent == "digital_twin":
            return "forecast"
        if "forecast" in normalized or "predict" in normalized or "next month" in normalized:
            return "forecast"
        if "compare" in normalized:
            return "comparison"
        return "answer"

    @staticmethod
    def _confidence(sources: list[GenAIContextSource], calls: list[GenAIToolCall], started: float) -> float:
        successful = sum(1 for call in calls if call.status == "success")
        source_score = mean([source.confidence for source in sources]) if sources else 0.55
        latency_penalty = min(0.08, max(0, (time.perf_counter() - started) - 8) * 0.01)
        return round(float(np.clip(0.58 + successful * 0.025 + source_score * 0.24 - latency_penalty, 0.62, 0.97)), 3)

    @staticmethod
    def _tool_evidence(name: str, data: dict[str, object]) -> list[str]:
        summary = data.get("summary")
        if isinstance(summary, dict):
            return [f"{key}={value}" for key, value in list(summary.items())[:5]]
        return [f"{name} returned {len(data)} top-level fields"]

    @staticmethod
    def _first(value: object) -> dict[str, object]:
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]
        return {}

    @staticmethod
    def _number(data: object, key: str) -> float:
        if isinstance(data, dict):
            try:
                return round(float(data.get(key, 0)), 2)
            except (TypeError, ValueError):
                return 0
        return 0

    @staticmethod
    def _doc(doc_id: str, system: str, title: str, content: str, metadata: dict[str, str | float | int]) -> GenAIKnowledgeDocument:
        return GenAIKnowledgeDocument(doc_id=doc_id, system=system, title=title, content=content, metadata=metadata)

    @staticmethod
    def _extract_entities(text: str) -> list[str]:
        matches = re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}|[A-Z]{2,})\b", text)
        ignored = {"Generated", "Grounding", "Recommended", "NEXUSMIND", "AI"}
        entities = [match for match in matches if match not in ignored and len(match) > 2]
        return sorted(set(entities))[:16]

    @staticmethod
    def _last_intent_from_memory(memory_summary: str) -> GenAIHRIntent | None:
        match = re.search(r"Last intent:\s*([a-z_]+)", memory_summary)
        if not match:
            return None
        value = match.group(1)
        return value if value in genai_hr_assistant_engine._intent_labels() else None  # type: ignore[return-value]

    @staticmethod
    def _select_scenario(question: str, scenarios: list[object]) -> dict[str, object]:
        normalized = question.lower()
        if "finish" in normalized or "complete" in normalized or "project" in normalized:
            preferred = "project_completion"
        elif "hiring freeze" in normalized or "hiring freezes" in normalized or "freeze" in normalized:
            preferred = "hiring_freeze"
        elif "budget" in normalized or "cost cut" in normalized:
            preferred = "budget_cut"
        elif "meeting" in normalized or "productivity" in normalized or "workload" in normalized:
            preferred = "productivity_change"
        elif "merge" in normalized or "restructure" in normalized or "team" in normalized:
            preferred = "team_restructure"
        elif "resign" in normalized or "lose" in normalized or "losing" in normalized or "engineer" in normalized:
            preferred = "employee_resignation"
        else:
            preferred = ""
        for scenario in scenarios:
            if isinstance(scenario, dict) and scenario.get("scenario_type") == preferred:
                return scenario
        first = scenarios[0] if scenarios else {}
        return first if isinstance(first, dict) else {}

    @staticmethod
    def _tokenize_for_stream(answer: str) -> list[str]:
        tokens = re.findall(r"\S+\s*", answer)
        return tokens or [answer]

    def _append_jsonl(self, path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


genai_hr_assistant_service = GenAIHRAssistantService()

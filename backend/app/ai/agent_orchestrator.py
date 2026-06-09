from app.schemas.intelligence import AgentCouncilResponse, AgentTurn


class AgentOrchestrator:
    def run_council(self, topic: str, risk_score: int, revenue_impact: float) -> AgentCouncilResponse:
        risk_band = "critical" if risk_score >= 82 else "high" if risk_score >= 68 else "elevated" if risk_score >= 50 else "controlled"
        margin_pressure = abs(revenue_impact)
        intervention_window = 48 if risk_score >= 82 else 72 if risk_score >= 68 else 120
        overload_delta = max(0, risk_score - 55)
        security_pressure = min(100, round(risk_score * 0.42 + margin_pressure * 2.1))
        shared_memory = [
            f"Topic under review: {topic}",
            f"Current risk score: {risk_score}",
            f"Revenue impact estimate: {revenue_impact}%",
            f"Risk band: {risk_band}",
            f"Intervention window: {intervention_window} hours",
        ]
        turns = [
            AgentTurn(
                agent="HR Agent",
                observation=f"Burnout pressure is {risk_band}; retention risk rises when risk score stays above {max(60, risk_score - 8)} for two review cycles.",
                recommendation=f"Start retention and wellness reviews for the top overloaded cohort within {intervention_window} hours.",
                confidence=min(97, 74 + round(risk_score * 0.22)),
                memory_keys=["burnout_forecast", "attrition_risk", "retention_history"],
                tool_calls=["attrition_prediction.analyze", "wellness.analyze"],
                workflow_trigger="open_retention_intervention",
            ),
            AgentTurn(
                agent="Wellness Agent",
                observation=f"Workload stress is {risk_band}; emotional recovery capacity is the limiting factor before delivery throughput improves.",
                recommendation="Reduce after-hours ownership, assign protected focus blocks, and schedule a manager wellness intervention for the highest-risk owners.",
                confidence=min(96, 76 + round(risk_score * 0.18)),
                memory_keys=["voice_stress_history", "wellness_analysis", "work_life_balance_plan"],
                tool_calls=["voice.analyze", "wellness.analyze", "work_life_balance.optimize"],
                workflow_trigger="schedule_wellness_recovery",
            ),
            AgentTurn(
                agent="Hiring Agent",
                observation=f"The capacity gap needs a hiring or internal-marketplace response if risk remains {risk_band} beyond {intervention_window} hours.",
                recommendation="Open a focused hiring lane for platform reliability and match internal mentors to overloaded delivery teams.",
                confidence=min(94, 72 + round(overload_delta * 0.24)),
                memory_keys=["hiring_rankings", "skill_gap_analysis", "internal_marketplace_matches"],
                tool_calls=["hiring.analyze", "strategic.internal_marketplace"],
                workflow_trigger="launch_capacity_hiring_lane",
            ),
            AgentTurn(
                agent="Finance Agent",
                observation=f"Projected operating margin exposure is {margin_pressure:.1f}% with a risk-adjusted contractor payback threshold near {round(18 + overload_delta * 0.4)} days.",
                recommendation="Fund short-term specialist capacity only where it lowers delivery delay and protects renewal revenue.",
                confidence=min(94, 72 + round(margin_pressure * 1.8)),
                memory_keys=["roi_model", "revenue_at_risk", "contractor_payback"],
                tool_calls=["roi.analyze", "client_risk.predict"],
                workflow_trigger="approve_targeted_capacity_budget",
            ),
            AgentTurn(
                agent="Security Agent",
                observation=f"Stress-linked access risk is scoring {security_pressure}/100 because fatigued privileged users are operating under incident pressure.",
                recommendation="Apply adaptive authentication, export throttling, and session replay to high-risk admin workflows.",
                confidence=min(96, 76 + round(security_pressure * 0.16)),
                memory_keys=["security_alerts", "anomaly_events", "privileged_access_sessions"],
                tool_calls=["security.analyze", "anomalies.detect", "alerts.feed"],
                workflow_trigger="tighten_privileged_access_controls",
            ),
            AgentTurn(
                agent="Productivity Agent",
                observation=f"Meeting drag and context switching are likely consuming {round(8 + overload_delta * 0.18, 1)} execution hours per critical owner each week.",
                recommendation="Convert low-signal recurring meetings into async updates and create two protected focus blocks per owner.",
                confidence=min(96, 78 + round(overload_delta * 0.18)),
                memory_keys=["productivity_leakage", "meeting_waste", "focus_windows"],
                tool_calls=["productivity.analyze", "meetings.analyze"],
                workflow_trigger="convert_recurring_meetings_to_async",
            ),
            AgentTurn(
                agent="Operations Agent",
                observation=f"Workflow stability will recover fastest if dependency ownership is centralized for the next {intervention_window} hours.",
                recommendation="Create a recovery room for dependency clearing, scope freeze decisions, and capacity rebalancing.",
                confidence=min(95, 75 + round(risk_score * 0.18)),
                memory_keys=["workflow_bottlenecks", "resource_allocation", "realtime_events"],
                tool_calls=["workflow.optimize", "resources.optimize"],
                workflow_trigger="open_recovery_room",
            ),
            AgentTurn(
                agent="Knowledge Agent",
                observation="Critical recovery knowledge must stay attached to people, projects, incidents, SOPs, and expertise maps.",
                recommendation="Refresh the Kubernetes, incident-response, and renewal-risk runbooks and assign backup owners for every overloaded expert.",
                confidence=min(96, 78 + round(risk_score * 0.15)),
                memory_keys=["knowledge_graph", "sop_generation_queue", "expertise_map", "outage_history"],
                tool_calls=["knowledge.query", "knowledge_loss.analyze", "genai.hr.ask"],
                workflow_trigger="refresh_enterprise_knowledge_runbooks",
            ),
            AgentTurn(
                agent="Executive Agent",
                observation=(
                    f"The executive command layer should coordinate financial, workforce, security, and delivery decisions "
                    f"under the {risk_band} risk posture."
                ),
                recommendation="Issue one integrated CEO-level decision brief with owner, cost, revenue, people-risk, and deadline impact for each intervention.",
                confidence=min(97, 79 + round(risk_score * 0.15) + round(margin_pressure * 0.32)),
                memory_keys=["ceo_command_brief", "financial_roi_model", "strategic_priorities", "enterprise_recovery_plan"],
                tool_calls=["genai.hr.ask", "roi.analyze", "platform.operating_system", "strategic.enterprise"],
                workflow_trigger="publish_ceo_decision_brief",
            ),
            AgentTurn(
                agent="Executive Decision Agent",
                observation=(
                    f"Enterprise operating posture is {risk_band}; the board-level tradeoff is protecting renewal revenue "
                    f"while reducing people-risk within {intervention_window} hours."
                ),
                recommendation=(
                    "Authorize the integrated recovery plan, track ROI impact daily, and escalate only decisions that change delivery, "
                    "retention, or security risk."
                ),
                confidence=min(96, 77 + round(risk_score * 0.16) + round(margin_pressure * 0.35)),
                memory_keys=["agent_shared_memory", "boardroom_kpis", "digital_twin_scenario"],
                tool_calls=["platform.operating_system", "digital_twin.simulate"],
                workflow_trigger="authorize_enterprise_recovery_protocol",
            ),
            AgentTurn(
                agent="Project Agent",
                observation=f"Scope volatility is amplifying delivery uncertainty under a {risk_band} risk posture.",
                recommendation="Freeze non-essential scope until the digital twin delay probability drops below 45%.",
                confidence=min(94, 76 + round(risk_score * 0.14)),
                memory_keys=["project_failure_forecast", "delivery_delay_probability", "scope_volatility"],
                tool_calls=["projects.failure.predict", "digital_twin.simulate"],
                workflow_trigger="freeze_nonessential_scope",
            ),
        ]
        decision = (
            f"Launch a {intervention_window}-hour recovery protocol: rebalance workload, protect execution time, "
            "harden privileged sessions, and freeze non-essential scope until risk stabilizes."
        )
        workflow_triggers = [turn.workflow_trigger for turn in turns if turn.workflow_trigger]
        return AgentCouncilResponse(
            topic=topic,
            shared_memory=shared_memory,
            turns=turns,
            decision=decision,
            workflow_triggers=workflow_triggers,
            coordination_score=min(100, 82 + round(risk_score * 0.14) + min(8, round(margin_pressure * 0.3))),
        )


agent_orchestrator = AgentOrchestrator()

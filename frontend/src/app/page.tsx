import {
  Building2,
  CircleDollarSign,
  Gauge,
  Network,
  Radio,
  Rocket,
  Sparkles,
  TimerReset,
} from "lucide-react";
import type React from "react";

import { AgentFeed } from "@/components/dashboard/AgentFeed";
import { AdvancedFeaturePanel } from "@/components/dashboard/AdvancedFeaturePanel";
import { AdvancedPowerFeaturesPanel } from "@/components/dashboard/AdvancedPowerFeaturesPanel";
import { AIAlertCenterPanel } from "@/components/dashboard/AIAlertCenterPanel";
import { AICompanyTimeMachinePanel } from "@/components/dashboard/AICompanyTimeMachinePanel";
import { AIShadowCompanyPanel } from "@/components/dashboard/AIShadowCompanyPanel";
import { AnomalyDetectionPanel } from "@/components/dashboard/AnomalyDetectionPanel";
import { AttritionPredictionPanel } from "@/components/dashboard/AttritionPredictionPanel";
import { AutonomyPanel } from "@/components/dashboard/AutonomyPanel";
import { AutonomousWorkflowPanel } from "@/components/dashboard/AutonomousWorkflowPanel";
import { BurnoutHeatmap } from "@/components/dashboard/BurnoutHeatmap";
import { BenchmarkingPanel } from "@/components/dashboard/BenchmarkingPanel";
import { BoardroomDashboardPanel } from "@/components/dashboard/BoardroomDashboardPanel";
import { BusinessPredictionPanel } from "@/components/dashboard/BusinessPredictionPanel";
import { CompanyHealthPanel } from "@/components/dashboard/CompanyHealthPanel";
import { CompletePlatformPanel } from "@/components/dashboard/CompletePlatformPanel";
import { CommunicationQualityPanel } from "@/components/dashboard/CommunicationQualityPanel";
import { ClientSatisfactionPanel } from "@/components/dashboard/ClientSatisfactionPanel";
import { CinematicCommandCenter } from "@/components/dashboard/CinematicCommandCenter";
import { CinematicExecutiveDemoPanel } from "@/components/dashboard/CinematicExecutiveDemoPanel";
import { CompanyEmotionMapPanel } from "@/components/dashboard/CompanyEmotionMapPanel";
import { CompanySimulationLabPanel } from "@/components/dashboard/CompanySimulationLabPanel";
import { CompetitiveIntelligencePanel } from "@/components/dashboard/CompetitiveIntelligencePanel";
import { CrisisCommandCenterPanel } from "@/components/dashboard/CrisisCommandCenterPanel";
import { CybersecurityPanel } from "@/components/dashboard/CybersecurityPanel";
import { DecisionAssistantPanel } from "@/components/dashboard/DecisionAssistantPanel";
import { DepartmentMatrix } from "@/components/dashboard/DepartmentMatrix";
import { DigitalTwinDashboardPanel } from "@/components/dashboard/DigitalTwinDashboardPanel";
import { EmployeeDashboardPanel } from "@/components/dashboard/EmployeeDashboardPanel";
import { EnterpriseOSVerificationPanel } from "@/components/dashboard/EnterpriseOSVerificationPanel";
import { EnterpriseMetaverseControlRoomPanel } from "@/components/dashboard/EnterpriseMetaverseControlRoomPanel";
import { EnterpriseTwinScene } from "@/components/dashboard/EnterpriseTwinScene";
import { ExecutiveAssistantPanel } from "@/components/dashboard/ExecutiveAssistantPanel";
import { FeatureCoveragePanel } from "@/components/dashboard/FeatureCoveragePanel";
import { ForecastChart } from "@/components/dashboard/ForecastChart";
import { GenAIHRAssistantPanel } from "@/components/dashboard/GenAIHRAssistantPanel";
import { GlobalRiskScannerPanel } from "@/components/dashboard/GlobalRiskScannerPanel";
import { HiddenLeaderDetectionPanel } from "@/components/dashboard/HiddenLeaderDetectionPanel";
import { InnovationScoringPanel } from "@/components/dashboard/InnovationScoringPanel";
import { EnterpriseKnowledgeBrainPanel } from "@/components/dashboard/EnterpriseKnowledgeBrainPanel";
import { JudgeDemoModePanel } from "@/components/dashboard/JudgeDemoModePanel";
import { JudgeImpactValidationPanel } from "@/components/dashboard/JudgeImpactValidationPanel";
import { JudgeStorytellingEnginePanel } from "@/components/dashboard/JudgeStorytellingEnginePanel";
import { JudgeWinningInnovationStackPanel } from "@/components/dashboard/JudgeWinningInnovationStackPanel";
import { KnowledgeLossPanel } from "@/components/dashboard/KnowledgeLossPanel";
import { LazyPanel } from "@/components/dashboard/LazyPanel";
import { ManagerDashboardPanel } from "@/components/dashboard/ManagerDashboardPanel";
import { MeetingAnalyzerPanel } from "@/components/dashboard/MeetingAnalyzerPanel";
import { MentalWellnessPanel } from "@/components/dashboard/MentalWellnessPanel";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { ModelValidationPanel } from "@/components/dashboard/ModelValidationPanel";
import { MultiAgentWorkforcePanel } from "@/components/dashboard/MultiAgentWorkforcePanel";
import { NlpSentimentPanel } from "@/components/dashboard/NlpSentimentPanel";
import { OrganizationalBrainPanel } from "@/components/dashboard/OrganizationalBrainPanel";
import { OrganizationalOptimizerPanel } from "@/components/dashboard/OrganizationalOptimizerPanel";
import { ProductivityLeakagePanel } from "@/components/dashboard/ProductivityLeakagePanel";
import { ProjectFailurePanel } from "@/components/dashboard/ProjectFailurePanel";
import { LearningRecommendationPanel } from "@/components/dashboard/LearningRecommendationPanel";
import { LivingCompanyBrainPanel } from "@/components/dashboard/LivingCompanyBrainPanel";
import { RecommendationAIPanel } from "@/components/dashboard/RecommendationAIPanel";
import { RecruiterImpressionPanel } from "@/components/dashboard/RecruiterImpressionPanel";
import { ResearchGradePlatformPanel } from "@/components/dashboard/ResearchGradePlatformPanel";
import { ResourceAllocationPanel } from "@/components/dashboard/ResourceAllocationPanel";
import { RiskPanel } from "@/components/dashboard/RiskPanel";
import { RoiIntelligencePanel } from "@/components/dashboard/RoiIntelligencePanel";
import { SalaryRecommendationPanel } from "@/components/dashboard/SalaryRecommendationPanel";
import { ScenarioDecisionEnginePanel } from "@/components/dashboard/ScenarioDecisionEnginePanel";
import { SelfLearningCompanyAIPanel } from "@/components/dashboard/SelfLearningCompanyAIPanel";
import { SimulationConsole } from "@/components/dashboard/SimulationConsole";
import { SmartSuggestionPanel } from "@/components/dashboard/SmartSuggestionPanel";
import { SmartHiringPanel } from "@/components/dashboard/SmartHiringPanel";
import { SmartInterviewerPanel } from "@/components/dashboard/SmartInterviewerPanel";
import { StrategicIntelligencePanel } from "@/components/dashboard/StrategicIntelligencePanel";
import { StrategicDecisionIntelligencePanel } from "@/components/dashboard/StrategicDecisionIntelligencePanel";
import { TalentMarketplacePanel } from "@/components/dashboard/TalentMarketplacePanel";
import { TeamBuilderPanel } from "@/components/dashboard/TeamBuilderPanel";
import { TechnologyStackPanel } from "@/components/dashboard/TechnologyStackPanel";
import { TeamCompatibilityPanel } from "@/components/dashboard/TeamCompatibilityPanel";
import { UltimateFeatureCoverageAuditPanel } from "@/components/dashboard/UltimateFeatureCoverageAuditPanel";
import { UltimatePlatformPanel } from "@/components/dashboard/UltimatePlatformPanel";
import { VoiceEnterpriseCopilotPanel } from "@/components/dashboard/VoiceEnterpriseCopilotPanel";
import { VirtualEmployeeGeneratorPanel } from "@/components/dashboard/VirtualEmployeeGeneratorPanel";
import { VoiceStressPanel } from "@/components/dashboard/VoiceStressPanel";
import { UnifiedEnterpriseSystemPanel } from "@/components/dashboard/UnifiedEnterpriseSystemPanel";
import { VirtualEnterpriseUniversePanel } from "@/components/dashboard/VirtualEnterpriseUniversePanel";
import { WorkLifeBalancePanel } from "@/components/dashboard/WorkLifeBalancePanel";
import { WhatIfDecisionEnginePanel } from "@/components/dashboard/WhatIfDecisionEnginePanel";
import { WorkloadForecastPanel } from "@/components/dashboard/WorkloadForecastPanel";
import { AppShell } from "@/components/layout/AppShell";
import { getCommandCenterData, getEnterpriseImpactData } from "@/lib/api";
import type { EnterpriseImpactResponse } from "@/types/impact";

export default async function Home() {
  const [{ dashboard, intelligence, modelValidation }, impact] = await Promise.all([
    getCommandCenterData(),
    getEnterpriseImpactData(),
  ]);

  return (
    <AppShell>
      <JudgeStorytellingEnginePanel dashboard={dashboard} impact={impact} />

      <CinematicCommandCenter dashboard={dashboard} impact={impact} />

      <CinematicExecutiveDemoPanel dashboard={dashboard} impact={impact} />

      <section id="judge-demo-mode-panel" className="mb-4">
        <JudgeDemoModePanel />
      </section>

      <section id="self-learning-company-ai-panel" className="mb-4">
        <SelfLearningCompanyAIPanel />
      </section>

      <section id="living-company-brain-panel" className="mb-4">
        <LivingCompanyBrainPanel />
      </section>

      <section id="ultimate-feature-coverage-audit-panel" className="mb-4">
        <UltimateFeatureCoverageAuditPanel />
      </section>

      <section id="judge-winning-innovation-stack-panel" className="mb-4">
        <JudgeWinningInnovationStackPanel />
      </section>

      <section id="virtual-enterprise-universe-panel" className="mb-4">
        <VirtualEnterpriseUniversePanel />
      </section>

      <EnterpriseImpactBrief impact={impact} />

      <section className="mb-4">
        <VoiceEnterpriseCopilotPanel />
      </section>

      <section id="organizational-brain-panel" className="mb-4">
        <OrganizationalBrainPanel />
      </section>

      <section id="boardroom-dashboard-panel" className="mb-4">
        <BoardroomDashboardPanel />
      </section>

      <section id="ai-shadow-company-panel" className="mb-4">
        <AIShadowCompanyPanel />
      </section>

      <section id="strategic-decision-intelligence-panel" className="mb-4">
        <StrategicDecisionIntelligencePanel />
      </section>

      <section id="ai-company-time-machine-panel" className="mb-4">
        <AICompanyTimeMachinePanel />
      </section>

      <section className="mb-4">
        <WhatIfDecisionEnginePanel />
      </section>

      <section id="virtual-employee-generator-panel" className="mb-4">
        <VirtualEmployeeGeneratorPanel />
      </section>

      <section id="crisis-command-center-panel" className="mb-4">
        <CrisisCommandCenterPanel />
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        {dashboard.metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <ExecutiveAssistantPanel directives={intelligence.executiveDirectives} />
        <EnterpriseTwinScene nodes={intelligence.orgBrain.nodes} />
      </section>

      <section id="enterprise-metaverse-control-room-panel" className="mt-4">
        <LazyPanel label="Enterprise Metaverse Control Room" minHeight={760}>
          <EnterpriseMetaverseControlRoomPanel />
        </LazyPanel>
      </section>

      <section className="mt-4">
        <DigitalTwinDashboardPanel />
      </section>

      <section className="mt-4">
        <ScenarioDecisionEnginePanel />
      </section>

      <section className="mt-4">
        <CompanyEmotionMapPanel />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <BurnoutHeatmap signals={intelligence.burnoutSignals} />
        <RiskPanel risks={dashboard.riskSignals} />
      </section>

      <section className="mt-4">
        <ModelValidationPanel validation={modelValidation} />
      </section>

      <section className="mt-4">
        <TechnologyStackPanel />
      </section>

      <section className="mt-4">
        <FeatureCoveragePanel />
      </section>

      <section className="mt-4">
        <AdvancedFeaturePanel />
      </section>

      <section className="mt-4">
        <EnterpriseOSVerificationPanel />
      </section>

      <section className="mt-4">
        <CompletePlatformPanel />
      </section>

      <section className="mt-4">
        <UltimatePlatformPanel />
      </section>

      <section className="mt-4">
        <ResearchGradePlatformPanel />
      </section>

      <section className="mt-4">
        <LazyPanel label="Unified Enterprise System" minHeight={520}>
          <UnifiedEnterpriseSystemPanel />
        </LazyPanel>
      </section>

      <section id="business-prediction-panel" className="mt-4">
        <LazyPanel label="Business Prediction" minHeight={520}>
          <BusinessPredictionPanel />
        </LazyPanel>
      </section>

      <section id="company-simulation-lab-panel" className="mt-4">
        <LazyPanel label="Company Simulation Lab" minHeight={520}>
          <CompanySimulationLabPanel />
        </LazyPanel>
      </section>

      <section className="mt-4">
        <LazyPanel label="Autonomous Workflow" minHeight={520}>
          <AutonomousWorkflowPanel />
        </LazyPanel>
      </section>

      <section id="multi-agent-workforce-panel" className="mt-4">
        <LazyPanel label="Autonomous AI Managers" minHeight={520}>
          <MultiAgentWorkforcePanel />
        </LazyPanel>
      </section>

      <section id="company-health-panel" className="mt-4">
        <CompanyHealthPanel />
      </section>

      <section className="mt-4">
        <DecisionAssistantPanel />
      </section>

      <section id="client-satisfaction-panel" className="mt-4">
        <ClientSatisfactionPanel />
      </section>

      <section id="enterprise-knowledge-brain-panel" className="mt-4">
        <EnterpriseKnowledgeBrainPanel />
      </section>

      <section className="mt-4">
        <KnowledgeLossPanel />
      </section>

      <section className="mt-4">
        <BenchmarkingPanel />
      </section>

      <section className="mt-4">
        <WorkLifeBalancePanel />
      </section>

      <section className="mt-4">
        <GenAIHRAssistantPanel />
      </section>

      <section className="mt-4">
        <AdvancedPowerFeaturesPanel />
      </section>

      <section className="mt-4">
        <RecruiterImpressionPanel />
      </section>

      <section className="mt-4">
        <JudgeImpactValidationPanel />
      </section>

      <section className="mt-4">
        <EmployeeDashboardPanel />
      </section>

      <section className="mt-4">
        <AttritionPredictionPanel />
      </section>

      <section className="mt-4">
        <SmartHiringPanel />
      </section>

      <section className="mt-4">
        <SmartInterviewerPanel />
      </section>

      <section id="competitive-intelligence-panel" className="mt-4">
        <CompetitiveIntelligencePanel />
      </section>

      <section id="global-risk-scanner-panel" className="mt-4">
        <LazyPanel label="Real-Time Global Risk Scanner" minHeight={620} rootMargin="250px">
          <GlobalRiskScannerPanel />
        </LazyPanel>
      </section>

      <section className="mt-4">
        <StrategicIntelligencePanel />
      </section>

      <section id="organizational-optimizer-panel" className="mt-4">
        <OrganizationalOptimizerPanel />
      </section>

      <section className="mt-4">
        <TalentMarketplacePanel />
      </section>

      <section id="hidden-leader-detection-panel" className="mt-4">
        <HiddenLeaderDetectionPanel />
      </section>

      <section id="manager-dashboard-panel" className="mt-4">
        <ManagerDashboardPanel />
      </section>

      <section className="mt-4">
        <AIAlertCenterPanel />
      </section>

      <section className="mt-4">
        <WorkloadForecastPanel />
      </section>

      <section id="productivity-leakage-panel" className="mt-4">
        <ProductivityLeakagePanel />
      </section>

      <section className="mt-4">
        <ResourceAllocationPanel />
      </section>

      <section className="mt-4">
        <SalaryRecommendationPanel />
      </section>

      <section className="mt-4">
        <LearningRecommendationPanel />
      </section>

      <section className="mt-4">
        <CommunicationQualityPanel />
      </section>

      <section id="innovation-scoring-panel" className="mt-4">
        <InnovationScoringPanel />
      </section>

      <section className="mt-4">
        <RecommendationAIPanel />
      </section>

      <section className="mt-4">
        <SmartSuggestionPanel />
      </section>

      <section className="mt-4">
        <MeetingAnalyzerPanel />
      </section>

      <section className="mt-4">
        <MentalWellnessPanel />
      </section>

      <section className="mt-4">
        <VoiceStressPanel />
      </section>

      <section className="mt-4">
        <TeamCompatibilityPanel />
      </section>

      <section className="mt-4">
        <TeamBuilderPanel />
      </section>

      <section id="project-failure-panel" className="mt-4">
        <ProjectFailurePanel />
      </section>

      <section className="mt-4">
        <RoiIntelligencePanel />
      </section>

      <section className="mt-4">
        <AnomalyDetectionPanel />
      </section>

      <section className="mt-4">
        <NlpSentimentPanel />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <ForecastChart series={dashboard.forecastSeries} confidence={dashboard.predictionConfidence} />
        <AgentFeed messages={dashboard.agentMessages} />
      </section>

      <section id="cybersecurity-panel" className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <CybersecurityPanel events={intelligence.securityEvents} />
        <SimulationConsole simulations={intelligence.simulations} />
      </section>

      <section className="mt-4">
        <AutonomyPanel council={intelligence.agentCouncil} orgBrain={intelligence.orgBrain} />
      </section>

      <section className="mt-4">
        <DepartmentMatrix departments={dashboard.departments} />
      </section>
    </AppShell>
  );
}

function EnterpriseImpactBrief({ impact }: { impact: EnterpriseImpactResponse | null }) {
  const impactSummary = impact?.summary;
  const strongestSignal =
    impact?.strongestSignal ?? "Enterprise operating risk is tied to workforce, revenue, delivery, client, and security decisions.";
  const capabilities = impactSummary ? `${impactSummary.capabilitiesReady}/${impactSummary.capabilitiesTotal}` : "verifying";

  return (
    <section className="mb-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
      <article className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 text-xs uppercase text-cyan">
              <Rocket className="size-4" />
              <span>Enterprise impact brief</span>
            </div>
            <h2 className="mt-2 text-2xl font-semibold text-white">Business-critical proof for an enterprise AI operating system</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              {impact?.topBusinessInsight ?? "The platform connects workforce risk, delivery risk, client exposure, security posture, and AI recommendations into one operating workflow."}
            </p>
          </div>
          <div className="grid min-w-56 gap-2 text-right">
            <span className="text-xs uppercase text-slate-500">Recruiter-grade proof</span>
            <strong className="text-3xl font-semibold text-mint">{score(impactSummary?.recruiterScore)}</strong>
            <span className="text-xs text-slate-500">{impactSummary?.residualRiskLevel ?? "verifying"} residual risk</span>
          </div>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <ImpactCallout
            icon={CircleDollarSign}
            label="Annual loss avoided"
            value={formatMoney(impactSummary?.netSavings)}
            detail={`${formatMoney(impactSummary?.baselineAnnualLoss)} baseline exposure modeled`}
          />
          <ImpactCallout
            icon={TimerReset}
            label="Payback window"
            value={impactSummary ? `${impactSummary.paybackMonths.toFixed(1)} mo` : "verifying"}
            detail={impactSummary ? `${Math.round(impactSummary.roiPercent)}% modeled ROI` : "verifying modeled ROI"}
          />
          <ImpactCallout
            icon={Network}
            label="Operating scope"
            value={capabilities}
            detail={
              impactSummary
                ? `${impactSummary.realtimeStreams} realtime streams, ${Math.round(impactSummary.platformScore)} platform score`
                : "verifying realtime streams"
            }
          />
        </div>
      </article>

      <article className="border border-line/70 bg-panel2/65 p-5 shadow-control backdrop-blur">
        <div className="flex items-center gap-2 text-xs uppercase text-mint">
          <Building2 className="size-4" />
          <span>Why it reads enterprise</span>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-300">{strongestSignal}</p>
        <div className="mt-4 grid gap-2">
          <ProofRow icon={Gauge} label="Platform score" value={score(impactSummary?.platformScore)} />
          <ProofRow icon={Radio} label="Realtime streams" value={String(impactSummary?.realtimeStreams ?? "verifying")} />
          <ProofRow icon={Sparkles} label="Judge wow score" value={score(impactSummary?.judgeWowScore)} />
        </div>
      </article>
    </section>
  );
}

function ImpactCallout({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="border border-line/70 bg-void/40 p-3">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block text-2xl font-semibold text-white">{value}</strong>
      <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p>
    </div>
  );
}

function ProofRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border border-line/60 bg-panel/60 px-3 py-2">
      <span className="inline-flex items-center gap-2 text-sm text-slate-400">
        <Icon className="size-4 text-cyan" />
        {label}
      </span>
      <strong className="text-sm text-white">{value}</strong>
    </div>
  );
}

function formatMoney(value?: number) {
  if (typeof value !== "number") return "verifying";
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}

function score(value?: number) {
  return typeof value === "number" ? `${Math.round(value)}` : "verifying";
}

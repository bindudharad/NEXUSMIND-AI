export type WorkflowPriority = "low" | "medium" | "high" | "critical";
export type WorkflowStatus = "queued" | "in_progress" | "approved" | "rejected" | "scheduled" | "escalated" | "completed";
export type ApprovalDecisionValue = "approved" | "rejected" | "needs_review";
export type OperationsMode = "default" | "pressure" | "crisis";

export interface TaskAssignmentDecision {
  taskId: string;
  taskTitle: string;
  assignedEmployeeId: string;
  assignedEmployeeName: string;
  team: string;
  assignmentScore: number;
  confidence: number;
  skillMatchScore: number;
  utilizationAfter: number;
  deliverySuccessProbability: number;
  workflowStatus: WorkflowStatus;
  rationale: string;
  alternatives: string[];
  sourceSystems: string[];
}

export interface ApprovalDecision {
  requestId: string;
  requestType: "leave" | "budget" | "purchase" | "access" | "training";
  requesterName: string;
  decision: ApprovalDecisionValue;
  confidence: number;
  policyScore: number;
  capacityImpact: number;
  riskScore: number;
  workflowStatus: WorkflowStatus;
  rationale: string;
  nextSteps: string[];
  sourceSystems: string[];
}

export interface MeetingScheduleDecision {
  meetingId: string;
  title: string;
  scheduledTime: string;
  durationMinutes: number;
  attendees: string[];
  conflictScore: number;
  priorityScore: number;
  workflowStatus: WorkflowStatus;
  rationale: string;
  sourceSystems: string[];
}

export interface ReminderEvent {
  reminderId: string;
  title: string;
  recipient: string;
  dueInHours: number;
  urgency: WorkflowPriority;
  channel: string;
  message: string;
  sourceWorkflow: string;
}

export interface WorkloadBalanceAction {
  actionId: string;
  fromEmployee: string;
  toEmployee: string;
  taskTitle: string;
  hours: number;
  utilizationDelta: number;
  burnoutRiskReduction: number;
  status: WorkflowStatus;
  rationale: string;
  sourceSystems: string[];
}

export interface WorkflowAutomationEvent {
  eventId: string;
  trigger: string;
  condition: string;
  action: string;
  affectedEntities: string[];
  severity: WorkflowPriority;
  confidence: number;
  workflowStatus: WorkflowStatus;
  sourceSystems: string[];
}

export interface AgentWorkflowAction {
  agent: string;
  observation: string;
  action: string;
  sharedContextKeys: string[];
  triggeredWorkflows: string[];
  confidence: number;
}

export interface EscalationEvent {
  escalationId: string;
  category: string;
  title: string;
  severity: WorkflowPriority;
  owner: string;
  routing: string[];
  rationale: string;
  slaHours: number;
  status: WorkflowStatus;
}

export interface OperationsRecommendation {
  title: string;
  category: string;
  priority: WorkflowPriority;
  action: string;
  rationale: string;
  expectedImpact: string;
  confidence: number;
}

export interface WorkflowSummary {
  activeWorkflows: number;
  pendingApprovals: number;
  scheduledMeetings: number;
  remindersCreated: number;
  escalationsOpen: number;
  automationEvents: number;
  workloadBalanceActions: number;
  operationsReadinessScore: number;
  averageAssignmentConfidence: number;
  policyAutomationRate: number;
  streamSequence: number;
}

export interface AutonomousWorkflowResponse {
  model: string;
  generatedAt: string;
  mode: OperationsMode;
  summary: WorkflowSummary;
  taskAssignments: TaskAssignmentDecision[];
  approvalDecisions: ApprovalDecision[];
  meetingSchedules: MeetingScheduleDecision[];
  reminders: ReminderEvent[];
  workloadBalancing: WorkloadBalanceAction[];
  automationEvents: WorkflowAutomationEvent[];
  agentActions: AgentWorkflowAction[];
  escalations: EscalationEvent[];
  recommendations: OperationsRecommendation[];
  supportedQuestions: string[];
  sourceSystems: string[];
  storage: string;
}

export interface OperationsAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: string;
  answer: string;
  triggeredActions: string[];
  citedWorkflows: string[];
  recommendedActions: string[];
  confidence: number;
  sourceSystems: string[];
  storage: string;
}

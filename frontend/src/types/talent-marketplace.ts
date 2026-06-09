export type TalentRiskLevel = "low" | "medium" | "high" | "critical";
export type TalentAssistantIntent = "projects" | "mentors" | "skills" | "jobs" | "experts" | "learning" | "badges" | "summary" | "search";
export type TalentBadgeLevel = "foundation" | "advanced" | "expert" | "principal" | "gold";

export interface TalentMarketplaceProfile {
  employeeId: string;
  employeeName: string;
  role: string;
  department: string;
  location: string;
  skills: string[];
  experienceYears: number;
  certifications: string[];
  projects: string[];
  achievements: string[];
  interests: string[];
  careerGoals: string[];
  learningGoals: string[];
  expertiseAreas: string[];
  offeredExpertise: string[];
  wantsMentorship: boolean;
  wantsProjects: boolean;
  wantsInternalRoles: boolean;
  capacityHours: number;
  allocatedHours: number;
  performanceScore: number;
  learningVelocity: number;
  mentorshipHours: number;
  knowledgeContributions: number;
  reputationEvents: number;
}

export interface SkillIntelligencePoint {
  employeeId: string;
  employeeName: string;
  skill: string;
  proficiencyScore: number;
  evidence: string[];
  hiddenSkill: boolean;
  marketRelevance: number;
  gapToGoal: boolean;
}

export interface ProjectMatch {
  employeeId: string;
  employeeName: string;
  projectId: string;
  projectTitle: string;
  matchScore: number;
  skillCoverage: number;
  capacityFit: number;
  growthFit: number;
  missingSkills: string[];
  rationale: string;
}

export interface MentorMatch {
  mentorId: string;
  mentorName: string;
  menteeId: string;
  menteeName: string;
  topic: string;
  matchScore: number;
  rationale: string;
}

export interface InternalRoleMatch {
  employeeId: string;
  employeeName: string;
  roleId: string;
  roleTitle: string;
  matchScore: number;
  promotionReadiness: number;
  missingSkills: string[];
  rationale: string;
}

export interface LearningPathRecommendation {
  employeeId: string;
  employeeName: string;
  targetSkill: string;
  resourceId: string;
  title: string;
  durationHours: number;
  recommendationScore: number;
  estimatedWeeksToProficiency: number;
  rationale: string;
}

export interface ExpertRanking {
  skill: string;
  employeeId: string;
  employeeName: string;
  score: number;
  evidence: string[];
}

export interface ReputationScore {
  employeeId: string;
  employeeName: string;
  contributionScore: number;
  knowledgeScore: number;
  mentorshipScore: number;
  innovationScore: number;
  totalReputation: number;
}

export interface SkillBadge {
  employeeId: string;
  employeeName: string;
  badge: string;
  level: TalentBadgeLevel;
  score: number;
  evidence: string[];
}

export interface MarketplaceGraphNode {
  id: string;
  label: string;
  type: "employee" | "skill" | "project" | "role" | "mentor" | "learning" | "badge";
  score: number;
}

export interface MarketplaceGraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
}

export interface TalentRecommendation {
  title: string;
  category: "project" | "mentor" | "learning" | "role" | "reputation" | "skill_gap" | "expertise";
  priority: TalentRiskLevel;
  action: string;
  expectedImpact: string;
  evidence: string[];
}

export interface TalentMarketplaceSummary {
  profiles: number;
  skillsDetected: number;
  hiddenSkillsDetected: number;
  projectMatches: number;
  mentorMatches: number;
  internalRoleMatches: number;
  learningPaths: number;
  badgesAwarded: number;
  averageReputation: number;
  marketplaceHealthScore: number;
  topExpert: string;
  topProjectMatch: string;
  streamSequence: number;
}

export interface TalentMarketplaceResponse {
  model: string;
  generatedAt: string;
  profiles: TalentMarketplaceProfile[];
  skillIntelligence: SkillIntelligencePoint[];
  projectMatches: ProjectMatch[];
  mentorMatches: MentorMatch[];
  internalRoleMatches: InternalRoleMatch[];
  learningPaths: LearningPathRecommendation[];
  expertRankings: ExpertRanking[];
  reputationScores: ReputationScore[];
  badges: SkillBadge[];
  graphNodes: MarketplaceGraphNode[];
  graphEdges: MarketplaceGraphEdge[];
  recommendations: TalentRecommendation[];
  assistantPrompts: string[];
  summary: TalentMarketplaceSummary;
  sourceSystems: string[];
  storage: string;
}

export interface TalentSearchResult {
  entityId: string;
  entityType: "employee" | "project" | "role" | "learning" | "skill";
  title: string;
  score: number;
  matchedSkills: string[];
  summary: string;
}

export interface TalentSearchResponse {
  model: string;
  generatedAt: string;
  query: string;
  results: TalentSearchResult[];
  sourceSystems: string[];
}

export interface TalentAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: TalentAssistantIntent;
  answer: string;
  confidence: number;
  citedProfiles: string[];
  citedOpportunities: string[];
  recommendedActions: string[];
  evidence: string[];
  sourceSystems: string[];
  storage: string;
}

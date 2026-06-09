export interface EmotionScores {
  stress: number;
  frustration: number;
  motivation: number;
  toxicity: number;
  burnout: number;
  emotionalExhaustion: number;
}

export interface NLPAnalyzeResponse {
  employeeId: string;
  department: string;
  channel: string;
  sentiment: string;
  primaryEmotion: string;
  confidence: number;
  sentimentScore: number;
  emotionScores: EmotionScores;
  burnoutIndicators: string[];
  recommendation: string;
  model: string;
  tokens: string[];
}

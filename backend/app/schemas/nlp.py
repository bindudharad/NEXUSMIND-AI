from pydantic import BaseModel, Field


class NLPAnalyzeRequest(BaseModel):
    text: str = Field(min_length=2, max_length=4000)
    employee_id: str = "anonymous"
    department: str = "Unknown"
    channel: str = "chat"


class EmotionScores(BaseModel):
    stress: float = Field(ge=0, le=1)
    frustration: float = Field(ge=0, le=1)
    motivation: float = Field(ge=0, le=1)
    toxicity: float = Field(ge=0, le=1)
    burnout: float = Field(ge=0, le=1)
    emotional_exhaustion: float = Field(ge=0, le=1)


class NLPAnalyzeResponse(BaseModel):
    employee_id: str
    department: str
    channel: str
    sentiment: str
    primary_emotion: str
    confidence: float = Field(ge=0, le=1)
    sentiment_score: float = Field(ge=-1, le=1)
    emotion_scores: EmotionScores
    burnout_indicators: list[str]
    recommendation: str
    model: str
    tokens: list[str]


class NLPBatchRequest(BaseModel):
    messages: list[NLPAnalyzeRequest] = Field(min_length=1, max_length=50)


class NLPBatchResponse(BaseModel):
    results: list[NLPAnalyzeResponse]
    team_sentiment_score: float = Field(ge=-1, le=1)
    high_risk_count: int
    recommendation: str


class NLPTrendPoint(BaseModel):
    department: str
    average_sentiment: float
    stress_index: float
    toxicity_index: float
    burnout_index: float
    messages_analyzed: int


class NLPTrendsResponse(BaseModel):
    trends: list[NLPTrendPoint]
    storage: str

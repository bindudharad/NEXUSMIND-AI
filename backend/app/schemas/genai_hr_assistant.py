from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


GenAIHRIntent = Literal[
    "attrition",
    "burnout",
    "productivity",
    "project_risk",
    "hiring",
    "company_health",
    "digital_twin",
    "financial",
    "knowledge",
    "report",
    "general",
]
GenAIHRRole = Literal["user", "assistant", "system"]
GenAIHRMode = Literal["answer", "report", "forecast", "comparison"]
ToolCallStatus = Literal["success", "degraded", "error"]


class GenAIHRMessage(BaseModel):
    role: GenAIHRRole
    content: str = Field(min_length=1, max_length=6000)
    created_at: datetime | None = None


class GenAIHRAssistantRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1200)
    session_id: str = Field(default="enterprise-hr-demo", min_length=3, max_length=120)
    user_id: str = Field(default="ceo@nexusmind.ai", max_length=160)
    history: list[GenAIHRMessage] = Field(default_factory=list, max_length=20)
    include_realtime: bool = True
    report_format: Literal["executive", "operational", "board"] = "executive"

    @model_validator(mode="before")
    @classmethod
    def normalize_client_aliases(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        normalized = dict(value)
        if "question" not in normalized and "message" in normalized:
            normalized["question"] = normalized["message"]
        if "session_id" not in normalized and "conversation_id" in normalized:
            normalized["session_id"] = normalized["conversation_id"]
        return normalized


class GenAIContextSource(BaseModel):
    citation_id: str
    system: str
    title: str
    snippet: str
    confidence: float = Field(ge=0, le=1)
    metadata: dict[str, str | float | int] = Field(default_factory=dict)


class GenAIToolCall(BaseModel):
    name: str
    status: ToolCallStatus
    latency_ms: int = Field(ge=0)
    summary: str
    evidence: list[str] = Field(default_factory=list)


class GenAIReportSection(BaseModel):
    title: str
    summary: str
    metrics: dict[str, float | int | str] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class GenAIConversationMemory(BaseModel):
    session_id: str
    turns: int = Field(ge=0)
    last_intent: GenAIHRIntent
    remembered_entities: list[str] = Field(default_factory=list)
    memory_summary: str


class GenAIHRAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    session_id: str
    question: str
    intent: GenAIHRIntent
    response_mode: GenAIHRMode
    answer: str
    executive_summary: str
    recommended_actions: list[str]
    retrieved_context: list[GenAIContextSource]
    tool_calls: list[GenAIToolCall]
    report_sections: list[GenAIReportSection]
    conversation_memory: GenAIConversationMemory
    reasoning_trace: list[str]
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]
    llm_provider: str
    rag_pipeline: str
    vector_database: str
    storage: str
    vector_index: str
    stream_sequence: int = 1

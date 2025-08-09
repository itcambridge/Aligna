"""
Pydantic schemas for Coral Protocol message contracts.
Defines structured data models for agent communication.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    """Types of messages in Coral threads."""
    MESSAGE = "message"
    REQUEST = "request"
    RESPONSE = "response"
    MENTION = "mention"
    RESULT = "result"
    ERROR = "error"
    SYSTEM = "system"

class AgentCapability(str, Enum):
    """Agent capabilities for registration."""
    JOB_ANALYSIS = "job_analysis"
    CV_MATCHING = "cv_matching"
    CV_WRITING = "cv_writing"
    JOB_SEARCH = "job_search"
    INTERFACE = "interface"

# Base message structures

class ThreadMessage(BaseModel):
    """Base message structure for Coral threads."""
    thread_id: str
    message_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    content: str
    agent_name: str
    message_type: MessageType = MessageType.MESSAGE
    payload: Dict[str, Any] = Field(default_factory=dict)
    mentions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True

class AgentEnvelope(BaseModel):
    """Envelope for agent-to-agent communication."""
    thread_id: str
    from_agent: str
    to_agent: Optional[str] = None
    intent: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Job-related schemas

class JobSpec(BaseModel):
    """Job specification for search and analysis."""
    job_title: str
    location: str
    company: Optional[str] = None
    job_id: Optional[str] = None
    job_description: Optional[str] = None
    source: str = "linkedin_mcp"

class JobRequirements(BaseModel):
    """Structured job requirements from analysis."""
    skills_required: List[str] = Field(default_factory=list)
    skills_preferred: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    level: Optional[str] = None
    summary: Optional[str] = None

# CV matching schemas

class CVMatchRequest(BaseModel):
    """Request for CV matching against job requirements."""
    thread_id: str
    user_id: str
    cv_id: str
    requirements: JobRequirements
    top_k: int = 5
    similarity_threshold: float = 0.7

class CVMatchEvidence(BaseModel):
    """Evidence from CV matching."""
    text: str
    cv_id: str
    chunk_index: int
    score: float
    section: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CVMatchResult(BaseModel):
    """Result of CV matching for a specific requirement."""
    requirement: str
    requirement_type: str  # skill_required, skill_preferred, experience, qualification
    matches: List[CVMatchEvidence] = Field(default_factory=list)
    unmatched: bool = False
    match_score: float = 0.0

class CVMatchResponse(BaseModel):
    """Complete response from CV matching."""
    thread_id: str
    user_id: str
    cv_id: str
    results: List[CVMatchResult] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    total_requirements: int = 0
    matched_requirements: int = 0
    match_rate: float = 0.0

# CV generation schemas

class CVSection(BaseModel):
    """A section of the generated CV."""
    section_name: str
    content: str
    evidence: List[CVMatchEvidence] = Field(default_factory=list)
    grounded: bool = True

class CVDraft(BaseModel):
    """Generated CV draft with evidence."""
    thread_id: str
    user_id: str
    cv_id: str
    job_title: str
    sections: List[CVSection] = Field(default_factory=list)
    cv_text: str = ""
    evidence_report: str = ""
    generated_at: datetime = Field(default_factory=datetime.now)
    grounding_score: float = 0.0

# Agent registration schemas

class AgentRegistration(BaseModel):
    """Agent registration information."""
    agent_name: str
    capabilities: List[AgentCapability]
    endpoint: str
    description: Optional[str] = None
    version: str = "1.0.0"
    registered_at: datetime = Field(default_factory=datetime.now)

class AgentHandleRequest(BaseModel):
    """Request structure for agent adapters."""
    thread_id: str
    message: ThreadMessage
    payload: Dict[str, Any] = Field(default_factory=dict)

class AgentHandleResponse(BaseModel):
    """Response structure from agent adapters."""
    thread_id: str
    messages: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"
    error: Optional[str] = None

# Workflow schemas

class WorkflowRequest(BaseModel):
    """Complete workflow request."""
    user_id: str
    cv_file_path: Optional[str] = None
    cv_id: Optional[str] = None
    job_title: str
    location: str
    company: Optional[str] = None
    orchestrator: str = "coral"

class WorkflowResponse(BaseModel):
    """Complete workflow response."""
    workflow_id: str
    thread_id: str
    user_id: str
    status: str
    cv_draft: Optional[CVDraft] = None
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

# Intent-specific payloads

class JobAnalysisIntent(BaseModel):
    """Intent payload for job analysis."""
    job_spec: JobSpec

class CVMatchingIntent(BaseModel):
    """Intent payload for CV matching."""
    user_id: str
    cv_id: str
    job_requirements: JobRequirements
    top_k: int = 5

class CVWritingIntent(BaseModel):
    """Intent payload for CV writing."""
    user_id: str
    cv_id: str
    job_requirements: JobRequirements
    cv_matches: CVMatchResponse
    contact_info: Dict[str, str] = Field(default_factory=dict)

class JobSearchIntent(BaseModel):
    """Intent payload for job search."""
    job_title: str
    location: str
    company: Optional[str] = None
    limit: int = 5

# Error schemas

class CoralError(BaseModel):
    """Error response structure."""
    error_type: str
    message: str
    thread_id: Optional[str] = None
    agent_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)

# Thread management schemas

class ThreadInfo(BaseModel):
    """Thread information."""
    thread_id: str
    title: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    message_count: int = 0
    participants: List[str] = Field(default_factory=list)

class ThreadSummary(BaseModel):
    """Summary of thread activity."""
    thread_id: str
    title: str
    status: str
    participants: List[str]
    message_count: int
    last_activity: datetime
    workflow_status: Optional[str] = None

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class Skill(BaseModel):
    name: str
    level: SkillLevel
    evidence: Optional[str] = None

class SkillProfile(BaseModel):
    skills: List[Skill] = Field(default_factory=list)

class Objective(BaseModel):
    description: str
    hours_estimated: float

class GapStatus(str, Enum):
    HAS = "has"
    PARTIAL = "partial"
    MISSING = "missing"

class Gap(BaseModel):
    required_skill: str
    status: GapStatus
    priority: int = 1 # 1 is highest priority (foundation)
    objectives: List[Objective] = Field(default_factory=list)

class GapList(BaseModel):
    target_role: str
    gaps: List[Gap] = Field(default_factory=list)

class ResourceType(str, Enum):
    VIDEO = "video"
    DOCS = "docs"
    COURSE = "course"
    ARTICLE = "article"
    PRACTICE = "practice"

class Resource(BaseModel):
    title: str
    url: str
    type: ResourceType
    level: SkillLevel
    time_estimate_minutes: int

class ItemType(str, Enum):
    LEARNING = "learning"
    PRACTICE = "practice"
    PROJECT = "project"

class ItemStatus(str, Enum):
    TODO = "todo"
    DONE = "done"
    SKIPPED = "skipped"

class Rating(str, Enum):
    EASY = "easy"
    OK = "ok"
    STRUGGLED = "struggled"

class PlanItem(BaseModel):
    id: str
    objective_ref: Optional[str] = None
    skill_ref: Optional[str] = None
    item_type: ItemType
    description: str
    resources: List[Resource] = Field(default_factory=list)
    status: ItemStatus = ItemStatus.TODO
    minutes_spent: int = 0
    rating: Optional[Rating] = None
    quiz_score: Optional[float] = None

class WeeklyPlan(BaseModel):
    version: int = 1
    change_reasons: List[str] = Field(default_factory=list)
    goal_sentences: Dict[int, str] = Field(default_factory=dict) # week number -> goal
    weeks: Dict[int, List[PlanItem]] = Field(default_factory=dict) # week number -> items

class ActivityLog(BaseModel):
    item_id: str
    minutes_spent: int
    rating: Rating
    quiz_score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StruggleFlag(BaseModel):
    skill_name: str
    reason: str
    severity: str # e.g., "high", "medium"

class LearnerState(BaseModel):
    id: str
    profile: Optional[SkillProfile] = None
    gaps: Optional[GapList] = None
    plan: Optional[WeeklyPlan] = None
    activity_log: List[ActivityLog] = Field(default_factory=list)
    struggle_flags: List[StruggleFlag] = Field(default_factory=list)
    hours_per_week: float
    weeks_available: int

class ProgressStats(BaseModel):
    items_done: int = 0
    hours_spent: float = 0.0
    skills_by_status: Dict[str, int] = Field(default_factory=dict) # e.g., "acquired": 5

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Auth Schemas
class UserProfile(BaseModel):
    experience_level: str = "fresher"  # fresher, intermediate, experienced
    interests: List[str] = []

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    experience_level: str = "fresher"
    interests: List[str] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    profile: UserProfile
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

# Content Schemas
class ContentBlock(BaseModel):
    type: str  # text, code, resource_link
    value: str
    language: Optional[str] = None
    label: Optional[str] = None
    url: Optional[str] = None

class SubTopic(BaseModel):
    title: str
    content_blocks: List[Dict[str, Any]]
    difficulty: Optional[str] = None

class TopicResponse(BaseModel):
    id: str
    domain_slug: str
    slug: str
    title: str
    content_blocks: Optional[List[Dict[str, Any]]] = []
    difficulty: str
    subtopics: Optional[List[SubTopic]] = []

class DomainResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    topics: List[str] = []  # List of topic slugs or IDs

# AI Schemas
class AIRecommendRequest(BaseModel):
    topic_slug: str
    answers: Dict[str, Any]

class AIChatRequest(BaseModel):
    topic_slug: str
    message: str

class AIExplainRequest(BaseModel):
    topic_slug: str
    level: str  # fresher, intermediate, experienced

# Practice Schemas
class TestCase(BaseModel):
    input: str
    expected_output: str

class PracticeProblemResponse(BaseModel):
    id: str
    topic_slug: str
    title: str
    difficulty: str
    description: str
    starter_code: str
    # Test cases are hidden or returned depending on need. We return count or simple description, hide actual assertions if necessary, or return. Let's return them.
    test_cases: List[TestCase]

class CodeSubmitRequest(BaseModel):
    language: str
    code: str

# Progress Schemas
class ProgressUpdate(BaseModel):
    topic_slug: str
    status: str  # not_started, in_progress, completed
    ai_notes: Optional[str] = None

# Activity Log & Streak Schemas
class ActivityLog(BaseModel):
    minutes_spent: int
    activity_type: str  # lesson, playground, quiz, practice
    topic_slug: Optional[str] = None

class ActivityLogCreate(ActivityLog):
    pass

class ActivityLogResponse(BaseModel):
    id: str
    user_id: str
    date: str  # YYYY-MM-DD
    minutes_spent: int
    activity_type: str
    topic_slug: Optional[str] = None

class StreakData(BaseModel):
    current_streak: int
    longest_streak: int
    last_active_date: Optional[str] = None

class StreakResponse(StreakData):
    pass


# ===== Extended Domain Detail Schemas (Roadmap, Prep, Projects) =====
class SkillItem(BaseModel):
    name: str
    description: str
    importance: str
    level: str  # beginner, intermediate, advanced
    estimated_hours: int

class ResourceSet(BaseModel):
    documentation: Optional[str] = None
    youtube_playlist: Optional[str] = None
    articles: List[str] = []
    notes: Optional[str] = None
    practice_platform: Optional[str] = None
    cheat_sheet: Optional[str] = None

class TopicDetail(BaseModel):
    name: str
    description: str
    importance: str
    difficulty: str
    estimated_time: str
    prerequisites: List[str] = []
    resources: ResourceSet
    practice_questions: List[str] = []
    projects: List[str] = []
    interview_questions: List[str] = []

class ProjectItem(BaseModel):
    title: str
    description: str
    skills_learned: List[str] = []
    technologies_used: List[str] = []
    github_ideas: List[str] = []
    tier: str  # beginner, intermediate, advanced

class CompanyPrepGroup(BaseModel):
    group_name: str  # "Product Companies", "Service Companies"
    example_companies: List[str] = []
    focus_areas: List[str] = []

class InterviewPrep(BaseModel):
    important_topics: List[str] = []
    frequently_asked_questions: List[str] = []
    coding_questions: List[str] = []
    hr_questions: List[str] = []
    system_design_questions: List[str] = []

class RoadmapTier(BaseModel):
    tier: str  # beginner, intermediate, advanced
    items: List[str] = []

class DomainDetailResponse(BaseModel):
    domain_slug: str
    overview: str
    why_important: str
    industries_using: List[str] = []
    future_scope: str
    average_salary: Optional[str] = None
    skills_required: List[str] = []
    prerequisites: List[str] = []
    roadmap: List[RoadmapTier] = []
    topics: List[TopicDetail] = []
    skills: List[SkillItem] = []
    practice_platforms: List[str] = []
    projects: List[ProjectItem] = []
    interview_prep: InterviewPrep
    resume_tips: List[str] = []
    certifications: List[str] = []
    company_prep: List[CompanyPrepGroup] = []

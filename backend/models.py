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

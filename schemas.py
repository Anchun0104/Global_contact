from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str = ""
    role: str = ""
    display_name: str = ""


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    role: str = "user"


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class UserResetPassword(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    role: str
    is_active: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    target_type: str
    target_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWorkload(BaseModel):
    user_id: int
    username: str
    display_name: Optional[str] = None
    total_operations: int = 0
    create_count: int = 0
    update_count: int = 0
    delete_count: int = 0
    professor_count: int = 0
    conference_count: int = 0
    cooperation_count: int = 0


class ProfessorCreate(BaseModel):
    name: str
    title: Optional[str] = None
    university: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    qs_ranking: Optional[int] = None
    research_direction: Optional[str] = None
    research_keywords: Optional[str] = None
    notes: Optional[str] = None


class ProfessorUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    university: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    qs_ranking: Optional[int] = None
    research_direction: Optional[str] = None
    research_keywords: Optional[str] = None
    notes: Optional[str] = None


class ProfessorResponse(BaseModel):
    id: int
    name: str
    title: Optional[str] = None
    university: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    qs_ranking: Optional[int] = None
    research_direction: Optional[str] = None
    research_keywords: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cooperation_count: Optional[int] = None

    class Config:
        from_attributes = True


class ConferenceCreate(BaseModel):
    name: str
    year: Optional[int] = None
    location: Optional[str] = None
    field: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "planned"
    total_sessions: Optional[int] = 0
    notes: Optional[str] = None


class ConferenceUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    location: Optional[str] = None
    field: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    total_sessions: Optional[int] = None
    notes: Optional[str] = None


class ConferenceResponse(BaseModel):
    id: int
    name: str
    year: Optional[int] = None
    location: Optional[str] = None
    field: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    total_sessions: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubConferenceCreate(BaseModel):
    conference_id: int
    name: str
    description: Optional[str] = None
    field: Optional[str] = None
    status: Optional[str] = "pending"


class SubConferenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    field: Optional[str] = None
    status: Optional[str] = None


class SubConferenceResponse(BaseModel):
    id: int
    conference_id: int
    name: str
    description: Optional[str] = None
    field: Optional[str] = None
    status: Optional[str] = None
    assigned_professor: Optional["ProfessorResponse"] = None
    cooperation_type: Optional[str] = None

    class Config:
        from_attributes = True


class CooperationCreate(BaseModel):
    professor_id: int
    conference_id: int
    sub_conference_id: Optional[int] = None
    cooperation_type: str
    notes: Optional[str] = None


class CooperationUpdate(BaseModel):
    cooperation_type: Optional[str] = None
    notes: Optional[str] = None


class CooperationResponse(BaseModel):
    id: int
    professor_id: int
    conference_id: int
    sub_conference_id: Optional[int] = None
    cooperation_type: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    professor_name: Optional[str] = None
    conference_name: Optional[str] = None
    sub_conference_name: Optional[str] = None

    class Config:
        from_attributes = True


class DirectionCreate(BaseModel):
    name: str


class DirectionResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_professors: int
    total_conferences: int
    total_cooperations: int
    total_subconferences: int
    unassigned_subconferences: int
    direction_distribution: List[dict] = []
    cooperation_type_distribution: List[dict] = []
    top_professors: List[dict] = []
    conference_progress: List[dict] = []


class ImportResult(BaseModel):
    success: bool
    message: str
    imported_count: int = 0
    errors: List[str] = []

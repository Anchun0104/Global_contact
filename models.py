import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
from database import Base


class CooperationType(str, enum.Enum):
    KEYNOTE = "keynote"
    COMMITTEE = "committee"
    SESSION_CHAIR = "session_chair"
    GENERAL_CHAIR = "general_chair"
    EDITOR = "editor"
    OTHER = "other"


class ConferenceStatus(str, enum.Enum):
    PLANNED = "planned"
    ONGOING = "ongoing"
    COMPLETED = "completed"


class SubConfStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    CONFIRMED = "confirmed"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    role = Column(String(20), default="user")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())


class Professor(Base):
    __tablename__ = "professors"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    title = Column(String(100))
    university = Column(String(200), index=True)
    email = Column(String(200))
    website = Column(String(500))
    location = Column(String(200))
    qs_ranking = Column(Integer)
    research_direction = Column(String(100), index=True)
    research_keywords = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    cooperations = relationship("Cooperation", back_populates="professor", cascade="all, delete-orphan")


class Conference(Base):
    __tablename__ = "conferences"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    year = Column(Integer)
    location = Column(String(200))
    field = Column(String(100), index=True)
    description = Column(Text)
    status = Column(SQLEnum(ConferenceStatus), default=ConferenceStatus.PLANNED)
    total_sessions = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    sub_conferences = relationship("SubConference", back_populates="conference", cascade="all, delete-orphan")
    cooperations = relationship("Cooperation", back_populates="conference", cascade="all, delete-orphan")


class SubConference(Base):
    __tablename__ = "sub_conferences"
    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey("conferences.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    field = Column(String(100))
    status = Column(SQLEnum(SubConfStatus), default=SubConfStatus.PENDING)

    conference = relationship("Conference", back_populates="sub_conferences")
    cooperations = relationship("Cooperation", back_populates="sub_conference", cascade="all, delete-orphan")


class Cooperation(Base):
    __tablename__ = "cooperations"
    id = Column(Integer, primary_key=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    conference_id = Column(Integer, ForeignKey("conferences.id"), nullable=False)
    sub_conference_id = Column(Integer, ForeignKey("sub_conferences.id"), nullable=True)
    cooperation_type = Column(SQLEnum(CooperationType), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    professor = relationship("Professor", back_populates="cooperations")
    conference = relationship("Conference", back_populates="cooperations")
    sub_conference = relationship("SubConference", back_populates="cooperations")


class ResearchDirection(Base):
    __tablename__ = "research_directions"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

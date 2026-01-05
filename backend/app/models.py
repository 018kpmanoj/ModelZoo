"""Database models and Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


# SQLAlchemy ORM Models
class ChatSession(Base):
    """Chat session database model."""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=True)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Chat message database model."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=True)
    complexity_score = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)  # in seconds
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    session = relationship("ChatSession", back_populates="messages")
    suggestions = relationship("Suggestion", back_populates="message", cascade="all, delete-orphan")


class Feedback(Base):
    """User feedback database model."""
    __tablename__ = "feedbacks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    message_id = Column(String(36), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    was_helpful = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="feedbacks")


class Suggestion(Base):
    """AI-generated suggestions database model."""
    __tablename__ = "suggestions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    suggestion_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)  # 'follow_up', 'clarification', 'related_topic'
    is_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    message = relationship("Message", back_populates="suggestions")


# Pydantic Schemas for API
class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str = Field(..., min_length=1, max_length=50000)
    model: Optional[str] = Field(None, description="Specific model to use (optional)")
    session_id: Optional[str] = Field(None, description="Session ID (creates new if not provided)")
    use_rag: bool = Field(False, description="Enable RAG for context retrieval")


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    role: str
    content: str
    model_used: Optional[str] = None
    complexity_score: Optional[float] = None
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    timestamp: datetime
    suggestions: List[str] = []
    
    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    """Schema for creating a new session."""
    title: Optional[str] = "New Chat"
    user_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for session response."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int = 0
    last_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class SessionDetail(SessionResponse):
    """Detailed session with messages."""
    messages: List[MessageResponse] = []


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    session_id: str
    message_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    was_helpful: Optional[bool] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: str
    rating: int
    comment: Optional[str]
    was_helpful: Optional[bool]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelInfo(BaseModel):
    """Schema for model information."""
    id: str
    display_name: str
    description: str
    max_tokens: int
    capabilities: List[str]
    is_available: bool = True


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    model: Optional[str] = None  # If None, auto-select
    use_rag: bool = False
    stream: bool = True


class ChatResponse(BaseModel):
    """Schema for chat response."""
    session_id: str
    message: MessageResponse
    model_selected: str
    was_auto_selected: bool
    complexity_score: float


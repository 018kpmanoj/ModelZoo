"""Business logic services for chat, sessions, and feedback."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload
import uuid

from app.models import (
    ChatSession, Message, Feedback, Suggestion,
    MessageCreate, MessageResponse, SessionResponse, SessionDetail,
    FeedbackCreate, FeedbackResponse, ChatRequest, ChatResponse
)
from app.orchestrator import orchestrator
from app.azure_client import azure_client


class ChatService:
    """Service for handling chat operations."""
    
    @staticmethod
    async def create_session(
        db: AsyncSession,
        title: str = "New Chat",
        user_id: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            id=str(uuid.uuid4()),
            title=title,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: str,
        include_messages: bool = False
    ) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        if include_messages:
            query = select(ChatSession).options(
                selectinload(ChatSession.messages)
            ).where(ChatSession.id == session_id)
        else:
            query = select(ChatSession).where(ChatSession.id == session_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all chat sessions with message counts."""
        query = select(ChatSession).where(
            ChatSession.is_active == True
        ).order_by(desc(ChatSession.updated_at)).offset(offset).limit(limit)
        
        if user_id:
            query = query.where(ChatSession.user_id == user_id)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        # Get message counts
        session_data = []
        for session in sessions:
            count_query = select(func.count(Message.id)).where(
                Message.session_id == session.id
            )
            count_result = await db.execute(count_query)
            message_count = count_result.scalar() or 0
            
            # Get last message
            last_msg_query = select(Message).where(
                Message.session_id == session.id
            ).order_by(desc(Message.timestamp)).limit(1)
            last_msg_result = await db.execute(last_msg_query)
            last_message = last_msg_result.scalar_one_or_none()
            
            session_data.append({
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "is_active": session.is_active,
                "message_count": message_count,
                "last_message": last_message.content[:100] if last_message else None
            })
        
        return session_data
    
    @staticmethod
    async def delete_session(db: AsyncSession, session_id: str) -> bool:
        """Delete a chat session."""
        session = await ChatService.get_session(db, session_id)
        if not session:
            return False
        
        await db.execute(delete(ChatSession).where(ChatSession.id == session_id))
        await db.commit()
        return True
    
    @staticmethod
    async def update_session_title(
        db: AsyncSession,
        session_id: str,
        title: str
    ) -> Optional[ChatSession]:
        """Update session title."""
        await db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(title=title, updated_at=datetime.utcnow())
        )
        await db.commit()
        return await ChatService.get_session(db, session_id)
    
    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        complexity_score: Optional[float] = None,
        tokens_used: Optional[int] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Add a message to a session."""
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            model_used=model_used,
            complexity_score=complexity_score,
            tokens_used=tokens_used,
            response_time=response_time,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        db.add(message)
        
        # Update session timestamp
        await db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        
        await db.commit()
        await db.refresh(message)
        return message
    
    @staticmethod
    async def get_session_messages(
        db: AsyncSession,
        session_id: str,
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a session."""
        query = select(Message).where(
            Message.session_id == session_id
        ).order_by(Message.timestamp).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def process_chat(
        db: AsyncSession,
        request: ChatRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a chat request and return response."""
        # Get or create session
        if request.session_id:
            session = await ChatService.get_session(db, request.session_id)
            if not session:
                session = await ChatService.create_session(db, user_id=user_id)
        else:
            session = await ChatService.create_session(db, user_id=user_id)
        
        # Analyze query and select model
        selected_model, analysis = orchestrator.select_model(
            request.message,
            request.model
        )
        
        # Save user message
        user_message = await ChatService.add_message(
            db,
            session.id,
            "user",
            request.message,
            complexity_score=analysis["total_score"]
        )
        
        # Get conversation history for context
        history = await ChatService.get_session_messages(db, session.id)
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history[-10:]  # Last 10 messages for context
        ]
        
        # Add system message
        system_message = {
            "role": "system",
            "content": "You are a helpful AI assistant in ModelZoo. Provide clear, accurate, and helpful responses. Be concise but thorough."
        }
        messages.insert(0, system_message)
        
        # Get response from Azure OpenAI
        response = await azure_client.chat_completion(
            messages=messages,
            model_id=selected_model,
            stream=False
        )
        
        # Save assistant message
        assistant_message = await ChatService.add_message(
            db,
            session.id,
            "assistant",
            response["content"],
            model_used=response["model"],
            tokens_used=response.get("tokens_used"),
            response_time=response.get("response_time"),
            metadata={"analysis": analysis}
        )
        
        # Generate title if first message
        messages_count = await db.execute(
            select(func.count(Message.id)).where(Message.session_id == session.id)
        )
        if messages_count.scalar() <= 2:
            # Auto-generate title from first message
            title = request.message[:50] + ("..." if len(request.message) > 50 else "")
            await ChatService.update_session_title(db, session.id, title)
        
        return {
            "session_id": session.id,
            "message": {
                "id": assistant_message.id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "model_used": assistant_message.model_used,
                "complexity_score": analysis["total_score"],
                "tokens_used": assistant_message.tokens_used,
                "response_time": assistant_message.response_time,
                "timestamp": assistant_message.timestamp
            },
            "model_selected": selected_model,
            "was_auto_selected": analysis["was_auto_selected"],
            "complexity_score": analysis["total_score"],
            "analysis": analysis
        }


class FeedbackService:
    """Service for handling feedback operations."""
    
    @staticmethod
    async def create_feedback(
        db: AsyncSession,
        feedback: FeedbackCreate
    ) -> Feedback:
        """Create new feedback."""
        fb = Feedback(
            id=str(uuid.uuid4()),
            session_id=feedback.session_id,
            message_id=feedback.message_id,
            rating=feedback.rating,
            comment=feedback.comment,
            was_helpful=feedback.was_helpful,
            created_at=datetime.utcnow()
        )
        db.add(fb)
        await db.commit()
        await db.refresh(fb)
        return fb
    
    @staticmethod
    async def get_session_feedback(
        db: AsyncSession,
        session_id: str
    ) -> List[Feedback]:
        """Get all feedback for a session."""
        query = select(Feedback).where(
            Feedback.session_id == session_id
        ).order_by(desc(Feedback.created_at))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_feedback_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get overall feedback statistics."""
        # Average rating
        avg_query = select(func.avg(Feedback.rating))
        avg_result = await db.execute(avg_query)
        avg_rating = avg_result.scalar() or 0
        
        # Total feedback count
        count_query = select(func.count(Feedback.id))
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Helpful ratio
        helpful_query = select(func.count(Feedback.id)).where(
            Feedback.was_helpful == True
        )
        helpful_result = await db.execute(helpful_query)
        helpful_count = helpful_result.scalar() or 0
        
        return {
            "average_rating": round(avg_rating, 2),
            "total_feedback": total_count,
            "helpful_count": helpful_count,
            "helpful_ratio": round(helpful_count / total_count, 2) if total_count > 0 else 0
        }


class SuggestionService:
    """Service for generating and managing suggestions."""
    
    @staticmethod
    async def generate_suggestions(
        db: AsyncSession,
        message_id: str,
        content: str
    ) -> List[str]:
        """Generate follow-up suggestions based on response."""
        # Simple rule-based suggestions for now
        suggestions = []
        
        content_lower = content.lower()
        
        if "code" in content_lower or "```" in content:
            suggestions.append("Can you explain this code step by step?")
            suggestions.append("How can I optimize this code?")
        
        if "error" in content_lower or "exception" in content_lower:
            suggestions.append("What causes this error?")
            suggestions.append("How can I prevent this in the future?")
        
        if not suggestions:
            suggestions = [
                "Tell me more about this topic",
                "Can you provide an example?",
                "What are the best practices?"
            ]
        
        # Save suggestions to database
        for suggestion_text in suggestions[:3]:
            suggestion = Suggestion(
                id=str(uuid.uuid4()),
                message_id=message_id,
                suggestion_text=suggestion_text,
                category="follow_up",
                created_at=datetime.utcnow()
            )
            db.add(suggestion)
        
        await db.commit()
        return suggestions[:3]
    
    @staticmethod
    async def get_message_suggestions(
        db: AsyncSession,
        message_id: str
    ) -> List[str]:
        """Get suggestions for a message."""
        query = select(Suggestion).where(
            Suggestion.message_id == message_id
        )
        result = await db.execute(query)
        suggestions = result.scalars().all()
        return [s.suggestion_text for s in suggestions]


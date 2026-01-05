"""FastAPI main application for ModelZoo."""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import json
import asyncio
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, get_db, close_db
from app.azure_client import azure_client
from app.orchestrator import orchestrator
from app.services import ChatService, FeedbackService, SuggestionService
from app.models import (
    ChatRequest, ChatResponse, SessionCreate, SessionResponse, SessionDetail,
    FeedbackCreate, FeedbackResponse, ModelInfo, MessageResponse
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting ModelZoo Backend...")
    await init_db()
    azure_client.initialize()
    print("✅ ModelZoo Backend is ready!")
    yield
    # Shutdown
    print("👋 Shutting down ModelZoo Backend...")
    await close_db()


app = FastAPI(
    title="ModelZoo API",
    description="Multi-LLM Chat System with Intelligent Model Orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "service": "ModelZoo API",
        "version": "1.0.0",
        "azure_connected": azure_client.is_initialized
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "api": "up",
            "database": "up",
            "azure_openai": "connected" if azure_client.is_initialized else "mock_mode"
        }
    }


# ==================== Models ====================

@app.get("/api/models", response_model=List[ModelInfo], tags=["Models"])
async def list_models():
    """List all available AI models."""
    models = orchestrator.get_available_models()
    return [
        ModelInfo(
            id=m["id"],
            display_name=m["display_name"],
            description=m["description"],
            max_tokens=m["max_tokens"],
            capabilities=m["capabilities"],
            is_available=True
        )
        for m in models
    ]


@app.get("/api/models/{model_id}", response_model=ModelInfo, tags=["Models"])
async def get_model(model_id: str):
    """Get details for a specific model."""
    config = orchestrator.get_model_config(model_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return ModelInfo(
        id=model_id,
        display_name=config["display_name"],
        description=config["description"],
        max_tokens=config["max_tokens"],
        capabilities=config["capabilities"],
        is_available=True
    )


# ==================== Chat Sessions ====================

@app.post("/api/sessions", response_model=SessionResponse, tags=["Sessions"])
async def create_session(
    session: SessionCreate = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    title = session.title if session else "New Chat"
    user_id = session.user_id if session else None
    
    new_session = await ChatService.create_session(db, title, user_id)
    return SessionResponse(
        id=new_session.id,
        title=new_session.title,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        is_active=new_session.is_active,
        message_count=0
    )


@app.get("/api/sessions", response_model=List[SessionResponse], tags=["Sessions"])
async def list_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all chat sessions."""
    sessions = await ChatService.list_sessions(db, limit=limit, offset=offset)
    return [SessionResponse(**s) for s in sessions]


@app.get("/api/sessions/{session_id}", response_model=SessionDetail, tags=["Sessions"])
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific chat session with messages."""
    session = await ChatService.get_session(db, session_id, include_messages=True)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await ChatService.get_session_messages(db, session_id)
    
    return SessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        message_count=len(messages),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                model_used=m.model_used,
                complexity_score=m.complexity_score,
                tokens_used=m.tokens_used,
                response_time=m.response_time,
                timestamp=m.timestamp
            )
            for m in messages
        ]
    )


@app.delete("/api/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a chat session."""
    success = await ChatService.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}


@app.patch("/api/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def update_session(
    session_id: str,
    title: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Update session title."""
    session = await ChatService.update_session_title(db, session_id, title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        message_count=0
    )


# ==================== Chat ====================

@app.post("/api/chat", tags=["Chat"])
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a chat message and get a response."""
    try:
        result = await ChatService.process_chat(db, request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Stream a chat response."""
    
    async def generate():
        # Get or create session
        if request.session_id:
            session = await ChatService.get_session(db, request.session_id)
        else:
            session = await ChatService.create_session(db)
        
        # Select model
        selected_model, analysis = orchestrator.select_model(
            request.message,
            request.model
        )
        
        # Save user message
        await ChatService.add_message(db, session.id, "user", request.message)
        
        # Get history
        history = await ChatService.get_session_messages(db, session.id)
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant in ModelZoo."},
            *[{"role": m.role, "content": m.content} for m in history[-10:]]
        ]
        
        # Send initial metadata
        yield f"data: {json.dumps({'type': 'meta', 'session_id': session.id, 'model': selected_model})}\n\n"
        
        # Stream response
        full_response = ""
        async for chunk in azure_client.chat_completion_stream(messages, selected_model):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        
        # Save assistant message
        await ChatService.add_message(
            db, session.id, "assistant", full_response, model_used=selected_model
        )
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/analyze", tags=["Chat"])
async def analyze_query(message: str = Query(...)):
    """Analyze a query without sending it to a model."""
    model_id, analysis = orchestrator.select_model(message)
    return {
        "recommended_model": model_id,
        "analysis": analysis
    }


# ==================== Feedback ====================

@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def create_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback for a chat session."""
    fb = await FeedbackService.create_feedback(db, feedback)
    return FeedbackResponse(
        id=fb.id,
        rating=fb.rating,
        comment=fb.comment,
        was_helpful=fb.was_helpful,
        created_at=fb.created_at
    )


@app.get("/api/feedback/stats", tags=["Feedback"])
async def get_feedback_stats(db: AsyncSession = Depends(get_db)):
    """Get overall feedback statistics."""
    return await FeedbackService.get_feedback_stats(db)


@app.get("/api/sessions/{session_id}/feedback", tags=["Feedback"])
async def get_session_feedback(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get feedback for a specific session."""
    feedbacks = await FeedbackService.get_session_feedback(db, session_id)
    return [
        FeedbackResponse(
            id=f.id,
            rating=f.rating,
            comment=f.comment,
            was_helpful=f.was_helpful,
            created_at=f.created_at
        )
        for f in feedbacks
    ]


# ==================== Suggestions ====================

@app.get("/api/messages/{message_id}/suggestions", tags=["Suggestions"])
async def get_suggestions(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get suggestions for a message."""
    suggestions = await SuggestionService.get_message_suggestions(db, message_id)
    return {"suggestions": suggestions}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


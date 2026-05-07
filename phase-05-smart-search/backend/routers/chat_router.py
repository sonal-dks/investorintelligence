"""Chat API endpoints for Smart Search."""

from __future__ import annotations

import logging
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client, create_client

from backend.config.settings import Settings, get_settings
from backend.deps import get_current_user_id
from backend.models.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSession,
    ChatSessionListResponse,
)
from backend.services.chat_service import ChatService
from backend.services.intent_router import IntentRouter
from backend.services.llm_client import LLMClient
from backend.services.memory_service import MemoryService
from backend.services.pii_detector import PIIDetector
from backend.services.refusal_classifier import RefusalClassifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

_rag_pipeline = None


def _get_rag_pipeline():
    global _rag_pipeline
    if _rag_pipeline is not None:
        return _rag_pipeline
    try:
        phase02_path = Path(__file__).resolve().parents[3] / "phase-02-rag-pipeline"
        if str(phase02_path) not in sys.path:
            sys.path.insert(0, str(phase02_path))
        from backend.services.rag_pipeline import RAGPipeline
        _rag_pipeline = RAGPipeline()
        return _rag_pipeline
    except Exception:
        logger.warning("rag_pipeline_import_failed — retrieval will return empty results")
        return None


def _get_supabase(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    client = _get_supabase(settings)
    llm = LLMClient(
        api_key=settings.openrouter_api_key,
        primary_model=settings.openrouter_primary_model,
        fallback_model=settings.openrouter_fallback_model,
        max_tokens=settings.max_response_tokens,
    )
    memory = MemoryService(
        supabase=client,
        openrouter_api_key=settings.openrouter_api_key,
        model=settings.openrouter_fallback_model,
        update_interval=settings.memory_update_interval,
    )

    pipeline = _get_rag_pipeline()

    def retrieval_fn(query: str, corpus_filter: str | None = None):
        if pipeline is None:
            return None
        try:
            svc = pipeline.get_retrieval()
            return svc.query(query, corpus_filter=corpus_filter)
        except Exception:
            logger.exception("retrieval_query_failed")
            return None

    return ChatService(
        supabase=client,
        llm=llm,
        memory=memory,
        retrieval_fn=retrieval_fn,
        pii=PIIDetector(),
        refusal=RefusalClassifier(),
        intent_router=IntentRouter(),
        max_history=settings.max_conversation_history,
    )


@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    req: ChatMessageRequest,
    user_id: str = Depends(get_current_user_id),
    svc: ChatService = Depends(_get_chat_service),
) -> ChatMessageResponse:
    settings = get_settings()
    client = _get_supabase(settings)

    session = (
        client.table("chat_sessions")
        .select("id,user_id")
        .eq("id", req.session_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your session")

    return svc.process_message(
        session_id=req.session_id,
        user_id=user_id,
        content=req.content,
    )


@router.get("/sessions", response_model=ChatSessionListResponse)
def list_sessions(
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> ChatSessionListResponse:
    client = _get_supabase(settings)
    rows = (
        client.table("chat_sessions")
        .select("id,title,last_message_at,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    sessions = [
        ChatSession(
            id=r["id"],
            title=r.get("title") or "New Chat",
            last_message_at=r.get("last_message_at"),
            created_at=r["created_at"],
        )
        for r in rows
    ]
    return ChatSessionListResponse(sessions=sessions)


@router.post("/sessions", response_model=ChatSession, status_code=201)
def create_session(
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> ChatSession:
    client = _get_supabase(settings)
    now_iso = datetime.now(UTC).isoformat()
    row = (
        client.table("chat_sessions")
        .insert({
            "user_id": user_id,
            "title": "New Chat",
            "created_at": now_iso,
        })
        .execute()
        .data[0]
    )
    return ChatSession(
        id=row["id"],
        title=row.get("title") or "New Chat",
        last_message_at=row.get("last_message_at"),
        created_at=row["created_at"],
    )


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> None:
    client = _get_supabase(settings)
    session = (
        client.table("chat_sessions")
        .select("id,user_id")
        .eq("id", session_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your session")

    client.table("chat_messages").delete().eq("session_id", session_id).execute()
    client.table("chat_sessions").delete().eq("id", session_id).execute()


@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    client = _get_supabase(settings)
    session = (
        client.table("chat_sessions")
        .select("id,user_id")
        .eq("id", session_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your session")

    rows = (
        client.table("chat_messages")
        .select("id,role,content,citations,metadata,created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
        or []
    )
    return {"messages": rows}

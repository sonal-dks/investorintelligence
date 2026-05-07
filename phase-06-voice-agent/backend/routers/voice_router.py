"""Voice Agent API endpoints."""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from supabase import Client, create_client

from backend.config.settings import Settings, get_settings
from backend.deps import get_current_user_id
from backend.models.schemas import (
    TTSRequest,
    VoiceGreetingThemeResponse,
    VoiceMessageRequest,
    VoiceMessageResponse,
    VoiceSession,
    VoiceSessionListResponse,
)
from backend.services.pulse_theme_service import PulseThemeService
from backend.services.tts_service import TTSService
from backend.services.voice_session_service import VoiceSessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

_rag_pipeline = None
_tts_service: TTSService | None = None


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
        logger.warning("rag_pipeline_import_failed — voice retrieval will return empty results")
        return None


def _get_tts_service(settings: Settings = Depends(get_settings)) -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService(
            default_voice=settings.tts_default_voice,
            max_text_length=settings.tts_max_text_length,
        )
    return _tts_service


def _get_supabase(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _get_phase05_deps():
    """Import Phase 05 services needed by voice: LLM, memory, PII, refusal, intent."""
    phase05_path = Path(__file__).resolve().parents[3] / "phase-05-smart-search"
    if str(phase05_path) not in sys.path:
        sys.path.insert(0, str(phase05_path))
    from backend.services.intent_router import IntentRouter
    from backend.services.approval_workflow_service import ApprovalWorkflowService
    from backend.services.llm_client import LLMClient
    from backend.services.memory_service import MemoryService
    from backend.services.pii_detector import PIIDetector
    from backend.services.refusal_classifier import RefusalClassifier
    return LLMClient, MemoryService, PIIDetector, RefusalClassifier, IntentRouter, ApprovalWorkflowService


def _get_voice_service(settings: Settings = Depends(get_settings)) -> VoiceSessionService:
    client = _get_supabase(settings)

    LLMClient, MemoryService, PIIDetector, RefusalClassifier, IntentRouter, ApprovalWorkflowService = _get_phase05_deps()

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
            logger.exception("voice_retrieval_query_failed")
            return None

    return VoiceSessionService(
        supabase=client,
        llm_client=llm,
        memory_service=memory,
        retrieval_fn=retrieval_fn,
        pii_detector=PIIDetector(),
        refusal_classifier=RefusalClassifier(),
        intent_router=IntentRouter(),
        approval_workflow=ApprovalWorkflowService(client),
        max_history=settings.max_conversation_history,
    )


@router.post("/message", response_model=VoiceMessageResponse)
def send_voice_message(
    req: VoiceMessageRequest,
    user_id: str = Depends(get_current_user_id),
    svc: VoiceSessionService = Depends(_get_voice_service),
    settings: Settings = Depends(get_settings),
) -> VoiceMessageResponse:
    client = _get_supabase(settings)

    session = (
        client.table("voice_sessions")
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
        input_mode=req.input_mode,
    )


@router.post("/tts")
async def text_to_speech(
    req: TTSRequest,
    tts: TTSService = Depends(_get_tts_service),
) -> Response:
    if not tts.is_available:
        raise HTTPException(status_code=503, detail="Edge TTS not available")
    try:
        audio_bytes = await tts.generate_audio(req.text, req.voice)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=tts.mp3"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/sessions", response_model=VoiceSessionListResponse)
def list_voice_sessions(
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> VoiceSessionListResponse:
    client = _get_supabase(settings)
    rows = (
        client.table("voice_sessions")
        .select("id,title,mode,last_message_at,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    sessions = [
        VoiceSession(
            id=r["id"],
            title=r.get("title") or "Voice Chat",
            mode=r.get("mode") or "voice",
            last_message_at=r.get("last_message_at"),
            created_at=r["created_at"],
        )
        for r in rows
    ]
    return VoiceSessionListResponse(sessions=sessions)


@router.post("/sessions", response_model=VoiceSession, status_code=201)
def create_voice_session(
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> VoiceSession:
    client = _get_supabase(settings)
    now_iso = datetime.now(UTC).isoformat()
    row = (
        client.table("voice_sessions")
        .insert({
            "user_id": user_id,
            "title": "Voice Chat",
            "mode": "voice",
            "created_at": now_iso,
        })
        .execute()
        .data[0]
    )
    return VoiceSession(
        id=row["id"],
        title=row.get("title") or "Voice Chat",
        mode=row.get("mode") or "voice",
        last_message_at=row.get("last_message_at"),
        created_at=row["created_at"],
    )


@router.delete("/sessions/{session_id}", status_code=204)
def delete_voice_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> None:
    client = _get_supabase(settings)
    session = (
        client.table("voice_sessions")
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

    client.table("voice_messages").delete().eq("session_id", session_id).execute()
    client.table("voice_sessions").delete().eq("id", session_id).execute()


@router.get("/sessions/{session_id}/messages")
def get_voice_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    client = _get_supabase(settings)
    session = (
        client.table("voice_sessions")
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
        client.table("voice_messages")
        .select("id,role,content,input_mode,citations,metadata,created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
        or []
    )
    return {"messages": rows}


@router.get("/greeting-theme", response_model=VoiceGreetingThemeResponse)
def get_voice_greeting_theme(
    settings: Settings = Depends(get_settings),
) -> VoiceGreetingThemeResponse:
    client = _get_supabase(settings)
    top_theme = PulseThemeService(client).get_latest_llm_theme()
    if top_theme:
        return VoiceGreetingThemeResponse(
            greeting=f"Welcome back. This week users are discussing {top_theme}. How can I help today?",
            top_theme=top_theme,
        )
    return VoiceGreetingThemeResponse(
        greeting="Welcome back. How can I help with mutual fund information today?",
        top_theme=None,
    )

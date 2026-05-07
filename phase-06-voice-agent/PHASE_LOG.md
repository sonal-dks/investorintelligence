# Phase Log: 06 — Voice Agent

## Goal
Build a dual-mode (voice + text) AI agent with Web Speech API for STT, browser TTS + Edge TTS for response playback, session persistence, and shared RAG pipeline from Phase 05.

## Changes
- `phase-06-voice-agent/backend/*` — VoiceSessionService, TTSService, voice_router
- `phase-06-voice-agent/frontend/*` — VoiceAgentPage, MicButton, LiveTranscript, ModeToggle, hooks
- `phase-06-voice-agent/migrations/001_create_voice_tables.sql` — voice_sessions, voice_messages
- `phase-06-voice-agent/tests/*` — unit + integration tests

## Checks Run
- ruff check: PASS
- pytest phase-06-voice-agent/tests/: PASS
- tsc --noEmit: PASS
- npm run build: PASS
- Runtime: voice flow verified

## Debug Notes
- Voice mode auto-falls back to text when Speech API unavailable
- TTS uses Edge TTS (server) as primary, browser SpeechSynthesis as fallback
- Voice prompt limits responses to 3 sentences for natural spoken delivery
- Activity logged as 'voice_agent_used' per session (deduplicated)

## Result: PASS

## Next Step: Phase 07 — AI Intent Detection + Approval Center

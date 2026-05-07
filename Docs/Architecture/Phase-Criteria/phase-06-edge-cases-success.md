# Phase 06: Voice Agent — Edge Cases & Success Criteria

## Success Criteria (per HLD/LLD/PRD)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Voice recording produces accurate transcript | PASS | useSpeechRecognition hook with Web Speech API; interim + final transcript display |
| TTS reads response naturally | PASS | Edge TTS (en-IN-NeerjaNeural) as primary; browser SpeechSynthesis fallback |
| Mode toggle preserves context | PASS | Single session_id shared across mode switches; messages persist in voice_messages |
| Fallbacks work when APIs unavailable | PASS | isSupported check → auto-text; Edge TTS fail → browser TTS; both fail → text only |
| Voice sessions persist after refresh | PASS | Stored in Supabase voice_sessions + voice_messages tables |
| Voice prompt limits to 3 sentences | PASS | VOICE_SYSTEM_PROMPT includes "maximum 3 sentences for voice mode" |
| PII redaction on transcripts | PASS | PIIDetector from Phase 05 applied before storage |
| Refusal for advice requests | PASS | RefusalClassifier from Phase 05 reused |
| Activity logging (voice_agent_used) | PASS | Logged per session (deduplicated) in activity_log |

## Edge-Case Inventory

### Inputs
| Edge Case | Impact | Likelihood | Handling |
|-----------|--------|------------|----------|
| Silent recording (no speech) | Low | High | 10s timeout; "No speech detected" error; user can retry |
| Very long recording (>2min) | Low | Low | maxAlternatives=1, continuous=false limits duration |
| Background noise / garbage transcript | Low | High | Transcript shown for user review; can be edited in text mode |
| Non-English speech | Low | Medium | lang="en-IN" set; poor results surfaced as-is |
| Empty/whitespace content | Medium | Medium | Schema validation (min_length=1) rejects |
| Content >2000 chars | Low | Low | Schema validation (max_length=2000) rejects |
| Invalid input_mode value | Medium | Low | Pydantic Literal["voice","text"] rejects (422) |

### System
| Edge Case | Impact | Likelihood | Handling |
|-----------|--------|------------|----------|
| Web Speech API unavailable (Firefox/Safari) | High | High | Feature detection on mount → auto-switch to text mode with banner |
| Edge TTS server unreachable | Medium | Low | Fallback to browser SpeechSynthesis; if both fail, text-only |
| Edge TTS returns empty audio | Medium | Low | RuntimeError raised → 503 → frontend uses browser TTS |
| Audio playback interrupted (new message) | Low | Medium | stopCurrent() called before each speak() |
| Supabase write failure on message store | Medium | Low | Exception caught + logged; response still returned |

### Dependencies
| Edge Case | Impact | Likelihood | Handling |
|-----------|--------|------------|----------|
| Microphone hardware fails | High | Low | onerror handler shows user-friendly message |
| Browser permission denied | High | Medium | "Microphone permission denied" error message + instructions |
| Browser permission revoked mid-session | Medium | Low | onerror fires → stops recording → error banner |
| Phase 05 RAG pipeline unavailable | Medium | Low | retrieval_fn returns None → LLM answers without context |
| OpenRouter LLM unavailable | High | Low | Fallback model chain (Claude → Gemini → error response) |

### User Behavior
| Edge Case | Impact | Likelihood | Handling |
|-----------|--------|------------|----------|
| Press mic then immediately stop | Low | Medium | Short/empty transcript not sent (min 1 char) |
| Switch modes while response is being read | Low | Medium | stopTTS() called on mode change |
| Close browser mid-recording | Low | Low | cleanup on unmount (abort recognition) |
| Multiple rapid record/stop cycles | Low | Medium | isListening state prevents double-start |
| Send suggested query in voice mode | Low | Medium | Works — sends as voice input_mode |

### Environment
| Edge Case | Impact | Likelihood | Handling |
|-----------|--------|------------|----------|
| Slow network makes TTS audio buffer | Low | Medium | Audio.play() handles buffering natively |
| Mobile browser background-kills audio | Low | Medium | Audio restarts on next interaction |
| No speakers/headphones connected | Low | Low | Audio plays silently; text still shown |
| HTTPS required for mic access | High | High | Documented in prerequisites; local dev uses localhost |

### AI-Specific
| Edge Case | Impact | Likelihood | Handling |
|-----------|--------|------------|----------|
| LLM response too long for natural TTS | Medium | Medium | Voice system prompt limits to 3 sentences |
| Garbled transcript sent to LLM | Low | Medium | LLM handles noisy input; retrieval may return empty |
| Prompt injection via voice | Medium | Low | Same safety pipeline as Phase 05 (intent routing + refusal) |
| PII spoken aloud | Medium | Low | PIIDetector scans transcript before storage/LLM call |

## Guardrails

### Engineering Defenses
- [x] Schema validation on all API inputs (Pydantic models)
- [x] TTS text length cap (1000 chars)
- [x] Recording timeout (continuous=false limits single utterance)
- [x] Session ownership check before any operation
- [x] JWT auth on all endpoints except /health and /tts
- [x] CORS configured via environment variable

### AI Guardrails
- [x] PIIDetector applied to all voice transcripts
- [x] RefusalClassifier blocks investment advice
- [x] IntentRouter classifies safety/action intents
- [x] Voice prompt restricts response length (3 sentences)
- [x] Same grounding rules as Smart Search (answer from context only)

## Observability

| Signal | Implementation |
|--------|---------------|
| Speech API availability | Logged per session via isSupported |
| TTS method used | Logged in metadata (edge-tts vs browser) |
| Transcript length | Included in voice_messages |
| Voice vs text usage ratio | Queryable from voice_messages.input_mode |
| Session count per user | Queryable from voice_sessions |
| Activity log events | voice_agent_used entries in activity_log |
| LLM model used | Included in response metadata |
| Response time | response_time_ms in metadata |

## Pre-Launch Checklist

- [x] Empty/null inputs handled (schema validation)
- [x] Extreme values bounded (max content length, max TTS text)
- [x] Invalid/adversarial input rejected (PII detection, refusal, intent routing)
- [x] Duplicate/repeated requests idempotent (activity log dedup)
- [x] Concurrency safe (one recognition instance at a time)
- [x] State consistency (Zustand store + React Query cache)
- [x] Failure isolation (TTS failure doesn't block text response)
- [x] API timeout/failure fallback (TTS: edge → browser → text; LLM: primary → fallback)
- [x] Low-bandwidth behavior acceptable (text-only fallback)
- [x] Hallucination handling (grounded responses from RAG context only)
- [x] Prompt injection resistance (safety intent router)
- [x] Unsafe output filtering (refusal classifier)
- [x] Confidence-based fallback (dynamic-k from Phase 02 retrieval)

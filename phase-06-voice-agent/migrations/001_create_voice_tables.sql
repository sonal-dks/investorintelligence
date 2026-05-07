-- Phase 06: Voice Agent tables
-- voice_sessions and voice_messages for dual-mode voice/text agent

CREATE TABLE IF NOT EXISTS voice_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    title text DEFAULT 'Voice Chat',
    mode text DEFAULT 'voice' CHECK (mode IN ('voice', 'text')),
    last_message_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_user ON voice_sessions (user_id, created_at DESC);

ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own voice sessions"
    ON voice_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own voice sessions"
    ON voice_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own voice sessions"
    ON voice_sessions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own voice sessions"
    ON voice_sessions FOR DELETE
    USING (auth.uid() = user_id);


CREATE TABLE IF NOT EXISTS voice_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    input_mode text NOT NULL DEFAULT 'text' CHECK (input_mode IN ('voice', 'text')),
    citations jsonb DEFAULT '[]',
    metadata jsonb DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_voice_messages_session ON voice_messages (session_id, created_at ASC);

ALTER TABLE voice_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own voice messages"
    ON voice_messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM voice_sessions vs
            WHERE vs.id = voice_messages.session_id AND vs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own voice messages"
    ON voice_messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM voice_sessions vs
            WHERE vs.id = voice_messages.session_id AND vs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own voice messages"
    ON voice_messages FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM voice_sessions vs
            WHERE vs.id = voice_messages.session_id AND vs.user_id = auth.uid()
        )
    );

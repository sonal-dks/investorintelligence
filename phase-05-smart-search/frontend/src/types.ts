export type UserRole = "investor" | "admin";

export type UserProfile = {
  id: string;
  user_id: string;
  email: string | null;
  display_name: string | null;
  role: UserRole;
  first_login_complete: boolean;
  created_at: string;
  updated_at: string;
};

export type Citation = {
  text: string;
  source_url: string;
  fund: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ChatSession = {
  id: string;
  title: string;
  last_message_at: string | null;
  created_at: string;
};

export type ChatMessageResponse = {
  id: string;
  role: "assistant";
  content: string;
  citations: Citation[];
  metadata: Record<string, unknown>;
  created_at: string;
};

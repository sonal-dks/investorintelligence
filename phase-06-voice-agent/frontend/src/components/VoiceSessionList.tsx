import { Plus, Trash2, Volume2 } from "lucide-react";

import type { VoiceSession } from "../types";

type VoiceSessionListProps = {
  sessions: VoiceSession[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
};

export function VoiceSessionList({ sessions, activeSessionId, onSelect, onCreate, onDelete }: VoiceSessionListProps) {
  return (
    <div className="flex h-full flex-col border-r border-border bg-sidebar">
      <div className="flex items-center justify-between border-b border-sidebar-border p-3">
        <h2 className="text-sm font-semibold text-sidebar-foreground">Voice Sessions</h2>
        <button
          type="button"
          onClick={onCreate}
          className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-sidebar-accent transition-colors"
          aria-label="New voice session"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-4 text-center text-xs text-muted-foreground">
            No sessions yet. Start a new one!
          </div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(s.id)}
              onKeyDown={(e) => e.key === "Enter" && onSelect(s.id)}
              className={`group flex items-center gap-2 border-b border-sidebar-border px-3 py-2.5 cursor-pointer transition-colors ${
                activeSessionId === s.id
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "hover:bg-sidebar-accent/50"
              }`}
            >
              <Volume2 className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{s.title}</p>
                <p className="text-xs text-muted-foreground">
                  {s.last_message_at
                    ? new Date(s.last_message_at).toLocaleDateString()
                    : "No messages"}
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
                className="hidden group-hover:flex h-6 w-6 items-center justify-center rounded hover:bg-red-50 hover:text-red-500 transition-colors"
                aria-label="Delete session"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

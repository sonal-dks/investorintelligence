import { MessageSquarePlus, Trash2 } from "lucide-react";

import type { ChatSession } from "../types";

type Props = {
  sessions: ChatSession[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  isCreating: boolean;
};

export function SessionList({ sessions, activeId, onSelect, onNew, onDelete, isCreating }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-border">
        <button
          type="button"
          onClick={onNew}
          disabled={isCreating}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary text-primary-foreground px-3 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          <MessageSquarePlus className="w-4 h-4" />
          {isCreating ? "Creating…" : "New Chat"}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-4">No conversations yet</p>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(s.id)}
            onKeyDown={(e) => e.key === "Enter" && onSelect(s.id)}
            className={`group relative flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm cursor-pointer transition-all duration-150 ${
              activeId === s.id
                ? "bg-primary text-primary-foreground"
                : "text-foreground hover:bg-muted"
            }`}
          >
            <span className="flex-1 truncate">{s.title}</span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(s.id);
              }}
              className={`shrink-0 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity ${
                activeId === s.id
                  ? "hover:bg-white/20"
                  : "hover:bg-muted"
              }`}
              aria-label={`Delete ${s.title}`}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

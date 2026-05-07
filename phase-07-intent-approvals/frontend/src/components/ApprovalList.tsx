type ApprovalItem = {
  id: string;
  title: string;
  investor_name: string;
  status: "pending" | "approved" | "rejected";
  priority: "low" | "medium" | "high";
};

type Props = {
  items: ApprovalItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function ApprovalList({ items, selectedId, onSelect }: Props) {
  if (items.length === 0) {
    return <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">No pending approvals.</div>;
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onSelect(item.id)}
          className={`w-full rounded-lg border p-3 text-left ${selectedId === item.id ? "border-primary bg-primary/5" : "border-border"}`}
        >
          <div className="text-sm font-medium">{item.title}</div>
          <div className="mt-1 text-xs text-muted-foreground">{item.investor_name} • {item.priority}</div>
        </button>
      ))}
    </div>
  );
}

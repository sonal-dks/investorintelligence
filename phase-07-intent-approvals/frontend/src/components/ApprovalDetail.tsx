import { EmailPreview } from "./EmailPreview";

type Approval = {
  id: string;
  action_type: "calendar" | "email" | "booking" | "note" | "follow_up";
  title: string;
  description: string;
  status: "pending" | "approved" | "rejected";
  payload: Record<string, unknown>;
};

type Props = {
  approval: Approval | null;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
};

export function ApprovalDetail({ approval, onApprove, onReject }: Props) {
  if (!approval) {
    return <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">Select an item to view details.</div>;
  }

  const payloadString = JSON.stringify(approval.payload, null, 2);

  return (
    <div className="space-y-3 rounded-lg border border-border p-4">
      <div>
        <h3 className="text-base font-semibold">{approval.title}</h3>
        <p className="text-sm text-muted-foreground">{approval.description || "No additional description"}</p>
      </div>
      {approval.action_type === "email" && (
        <EmailPreview
          subject={String(approval.payload.subject ?? "Draft message")}
          body={String(approval.payload.body ?? "No body")}
        />
      )}
      <pre className="max-h-72 overflow-auto rounded bg-muted p-3 text-xs">{payloadString}</pre>
      <div className="flex gap-2">
        <button type="button" onClick={() => onApprove(approval.id)} className="rounded bg-green-600 px-3 py-2 text-sm text-white">Approve</button>
        <button type="button" onClick={() => onReject(approval.id)} className="rounded bg-red-600 px-3 py-2 text-sm text-white">Reject</button>
      </div>
    </div>
  );
}

export type Approval = {
  id: string;
  action_type: "calendar" | "email" | "booking" | "note" | "follow_up";
  title: string;
  description: string;
  investor_name: string;
  status: "pending" | "approved" | "rejected";
  priority: "low" | "medium" | "high";
  payload: Record<string, unknown>;
};

const base = () => import.meta.env.VITE_API_BASE ?? "";

export async function fetchApprovals(status: string) {
  const res = await fetch(`${base()}/api/approvals?status=${status}`);
  if (!res.ok) throw new Error("Failed to load approvals");
  return res.json() as Promise<{ items: Approval[]; pending_count: number }>;
}

export async function reviewApproval(id: string, status: "approved" | "rejected") {
  const res = await fetch(`${base()}/api/approvals/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", "x-user-role": "admin" },
    body: JSON.stringify({ status, reviewed_by: "admin-demo" }),
  });
  if (!res.ok) throw new Error("Failed to update approval");
  return res.json() as Promise<Approval>;
}

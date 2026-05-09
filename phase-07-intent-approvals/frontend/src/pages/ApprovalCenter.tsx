import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApprovalDetail } from "../components/ApprovalDetail";
import { ApprovalList } from "../components/ApprovalList";
import { fetchApprovals, reviewApproval } from "../lib/api";
import { useApprovalStore } from "../stores/approval-store";

export function ApprovalCenterPage() {
  const queryClient = useQueryClient();
  const selectedApprovalId = useApprovalStore((s) => s.selectedApprovalId);
  const activeFilter = useApprovalStore((s) => s.activeFilter);
  const setSelected = useApprovalStore((s) => s.setSelectedApprovalId);
  const setFilter = useApprovalStore((s) => s.setActiveFilter);

  const approvalsQuery = useQuery({
    queryKey: ["approvals", activeFilter],
    queryFn: () => fetchApprovals(activeFilter),
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "approved" | "rejected" }) => reviewApproval(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["approvals"] }),
  });

  const selected = useMemo(
    () => approvalsQuery.data?.items.find((i) => i.id === selectedApprovalId) ?? null,
    [approvalsQuery.data?.items, selectedApprovalId],
  );

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-5">
        <h1 className="text-xl font-semibold">Approval Center</h1>
        <p className="mt-1 text-sm text-muted-foreground">Review and approve investor-triggered actions.</p>
      </div>
      <div className="flex items-center justify-between rounded-xl border border-border bg-card p-3">
        <div className="flex gap-2">
          {(["all", "pending", "approved", "rejected"] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={`rounded px-3 py-1 text-sm ${activeFilter === f ? "bg-primary text-primary-foreground" : "bg-muted"}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 rounded-xl border border-border bg-card p-4">
        <ApprovalList items={approvalsQuery.data?.items ?? []} selectedId={selectedApprovalId} onSelect={setSelected} />
        <ApprovalDetail
          approval={selected}
          onApprove={(id) => reviewMutation.mutate({ id, status: "approved" })}
          onReject={(id) => reviewMutation.mutate({ id, status: "rejected" })}
        />
      </div>
    </div>
  );
}

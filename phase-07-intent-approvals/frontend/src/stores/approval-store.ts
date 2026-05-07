import { create } from "zustand";

type ApprovalFilter = "all" | "pending" | "approved" | "rejected";

type ApprovalStore = {
  selectedApprovalId: string | null;
  activeFilter: ApprovalFilter;
  setSelectedApprovalId: (id: string | null) => void;
  setActiveFilter: (filter: ApprovalFilter) => void;
};

export const useApprovalStore = create<ApprovalStore>((set) => ({
  selectedApprovalId: null,
  activeFilter: "pending",
  setSelectedApprovalId: (selectedApprovalId) => set({ selectedApprovalId }),
  setActiveFilter: (activeFilter) => set({ activeFilter }),
}));

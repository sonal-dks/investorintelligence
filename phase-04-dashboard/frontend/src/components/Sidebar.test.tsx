import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { Sidebar } from "./Sidebar";

vi.mock("../providers/AuthProvider", () => ({
  useAuthActions: () => ({ signOut: vi.fn() }),
}));

describe("Sidebar", () => {
  it("hides admin-only nav for investor", () => {
    render(
      <MemoryRouter>
        <Sidebar role="investor" />
      </MemoryRouter>,
    );
    expect(screen.queryByText("Approval Center")).not.toBeInTheDocument();
  });

  it("shows admin-only nav for admin", () => {
    render(
      <MemoryRouter>
        <Sidebar role="admin" />
      </MemoryRouter>,
    );
    expect(screen.getByText("Approval Center")).toBeInTheDocument();
  });
});

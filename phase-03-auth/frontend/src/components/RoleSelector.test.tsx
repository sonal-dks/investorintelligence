import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import type { UserRole } from "../types";
import { RoleSelector } from "./RoleSelector";

function Harness({ initial = "investor" as UserRole }) {
  const [role, setRole] = useState<UserRole>(initial);
  return <RoleSelector value={role} onChange={setRole} />;
}

describe("RoleSelector", () => {
  it("calls onChange when a role card is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<RoleSelector value="investor" onChange={onChange} />);
    await user.click(screen.getByRole("radio", { name: /Investor/i }));
    expect(onChange).toHaveBeenCalledWith("investor");
    await user.click(screen.getByRole("radio", { name: /Admin/i }));
    expect(onChange).toHaveBeenCalledWith("admin");
  });

  it("moves selection with arrow keys", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const investor = screen.getByRole("radio", { name: /Investor/i });
    investor.focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("radio", { name: /Admin/i })).toHaveAttribute("aria-checked", "true");
    await user.keyboard("{ArrowLeft}");
    expect(screen.getByRole("radio", { name: /Investor/i })).toHaveAttribute("aria-checked", "true");
  });
});

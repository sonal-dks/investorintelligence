import { render, screen } from "@testing-library/react";

import { KPICard } from "./KPICard";

describe("KPICard", () => {
  it("renders label and value", () => {
    render(
      <KPICard
        label="Login Sessions"
        data={{ value: 12, trend_pct: 20, trend_direction: "up" }}
        icon={<span>i</span>}
        iconClass="bg-blue-50 text-blue-600"
      />,
    );
    expect(screen.getByText("Login Sessions")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("+20.0%")).toBeInTheDocument();
  });
});

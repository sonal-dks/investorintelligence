import type { UserRole } from "../types";

type Props = {
  value: UserRole;
  onChange: (r: UserRole) => void;
  disabled?: boolean;
};

export function RoleSelector({ value, onChange, disabled }: Props) {
  return (
    <div
      className="grid grid-cols-1 gap-3 sm:grid-cols-2"
      role="radiogroup"
      aria-label="Choose your role"
    >
      {(
        [
          ["investor", "Investor", "Personal metrics and standard navigation."],
          ["admin", "Admin", "Platform-wide visibility and approvals (demo)."],
        ] as const
      ).map(([id, title, desc]) => {
        const selected = value === id;
        return (
          <button
            key={id}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            onClick={() => onChange(id)}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight" || e.key === "ArrowDown") {
                e.preventDefault();
                if (value === "investor") onChange("admin");
              }
              if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
                e.preventDefault();
                if (value === "admin") onChange("investor");
              }
            }}
            className={
              "rounded-xl border px-4 py-4 text-left transition focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 " +
              (selected
                ? "border-sky-500 bg-sky-950/40"
                : "border-neutral-700 bg-neutral-900/50 hover:border-neutral-500") +
              (disabled ? " opacity-50" : "")
            }
          >
            <div className="text-lg font-semibold text-neutral-100">{title}</div>
            <p className="mt-1 text-sm text-neutral-400">{desc}</p>
          </button>
        );
      })}
    </div>
  );
}

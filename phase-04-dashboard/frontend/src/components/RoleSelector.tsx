import type { UserRole } from "../types";

type Props = {
  value: UserRole;
  onChange: (v: UserRole) => void;
  disabled?: boolean;
};

export function RoleSelector({ value, onChange, disabled = false }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Role">
      {(["investor", "admin"] as const).map((role) => {
        const active = value === role;
        return (
          <button
            key={role}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={disabled}
            onClick={() => onChange(role)}
            className={`rounded-lg border px-4 py-3 text-sm font-medium ${
              active ? "bg-primary text-primary-foreground border-primary" : "border-border bg-background"
            }`}
          >
            {role === "admin" ? "Admin" : "Investor"}
          </button>
        );
      })}
    </div>
  );
}

import { useEffect } from "react";

import { useAuthStore as useDashboardAuth } from "../stores/auth-store";
import { useAuthStore as usePhase05Auth } from "@phase05/stores/auth-store";
import { useAuthStore as usePhase06Auth } from "@phase06/stores/auth-store";

type Target = "phase05" | "phase06";

type Props = {
  target: Target;
};

/** Mirror dashboard Supabase session into embedded phase SPAs (separate Zustand stores). */
export function PhaseAuthSync({ target }: Props) {
  const session = useDashboardAuth((s) => s.session);
  const profile = useDashboardAuth((s) => s.profile);

  const set05Session = usePhase05Auth((s) => s.setFromSession);
  const set05Profile = usePhase05Auth((s) => s.setProfile);
  const set06Session = usePhase06Auth((s) => s.setFromSession);
  const set06Profile = usePhase06Auth((s) => s.setProfile);

  useEffect(() => {
    if (target === "phase05") {
      set05Session(session);
      set05Profile(profile);
    } else {
      set06Session(session);
      set06Profile(profile);
    }
  }, [target, session, profile, set05Session, set05Profile, set06Session, set06Profile]);

  return null;
}

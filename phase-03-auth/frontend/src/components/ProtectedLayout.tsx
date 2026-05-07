import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";

import { useAuthActions } from "../providers/AuthProvider";
import { useAuthStore } from "../stores/auth-store";
import { upsertProfile } from "../lib/api";
import { EmailCaptureModal } from "./EmailCaptureModal";

export function ProtectedLayout() {
  const session = useAuthStore((s) => s.session);
  const profile = useAuthStore((s) => s.profile);
  const isLoading = useAuthStore((s) => s.isLoading);
  const { refreshProfile } = useAuthActions();
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (profile && !profile.first_login_complete) setModalOpen(true);
    else setModalOpen(false);
  }, [profile]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-neutral-400">
        Loading session…
      </div>
    );
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (!profile) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
        <p className="text-neutral-300">Profile could not be loaded.</p>
        <a href="/login" className="text-sky-400 hover:underline">
          Back to login
        </a>
      </div>
    );
  }

  async function onModalSubmit(email: string, displayName: string) {
    const sess = useAuthStore.getState().session;
    if (!sess) return;
    const token = sess.access_token;
    const { res } = await upsertProfile(token, {
      email,
      display_name: displayName || null,
      first_login_complete: true,
    });
    if (!res.ok) throw new Error("save failed");
    await refreshProfile();
    setModalOpen(false);
  }

  return (
    <>
      <EmailCaptureModal
        open={modalOpen}
        defaultEmail={profile.email ?? ""}
        defaultDisplayName={profile.display_name ?? ""}
        onSubmit={onModalSubmit}
        onCloseBlocked
      />
      <Outlet />
    </>
  );
}

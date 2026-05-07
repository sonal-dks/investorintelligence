import { useEffect, useId, useState } from "react";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

type Props = {
  open: boolean;
  defaultEmail: string;
  defaultDisplayName: string;
  onSubmit: (email: string, displayName: string) => Promise<void>;
  onCloseBlocked?: boolean;
};

export function EmailCaptureModal({
  open,
  defaultEmail,
  defaultDisplayName,
  onSubmit,
  onCloseBlocked = true,
}: Props) {
  const id = useId();
  const [email, setEmail] = useState(defaultEmail);
  const [displayName, setDisplayName] = useState(defaultDisplayName);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open) {
      setEmail(defaultEmail);
      setDisplayName(defaultDisplayName);
      setError(null);
    }
  }, [open, defaultEmail, defaultDisplayName]);

  if (!open) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!EMAIL_RE.test(email.trim())) {
      setError("Enter a valid email address.");
      return;
    }
    if (displayName.trim().length > 255) {
      setError("Display name is too long.");
      return;
    }
    setBusy(true);
    try {
      await onSubmit(email.trim(), displayName.trim());
    } catch {
      setError("Could not save. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={`${id}-title`}
    >
      <div className="w-full max-w-md rounded-2xl border border-neutral-700 bg-neutral-950 p-6 shadow-xl">
        <h2 id={`${id}-title`} className="text-xl font-semibold text-neutral-50">
          Confirm your profile
        </h2>
        <p className="mt-2 text-sm text-neutral-400">
          First login — confirm email and how we should display your name. This step runs once.
        </p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor={`${id}-email`} className="block text-sm font-medium text-neutral-300">
              Email
            </label>
            <input
              id={`${id}-email`}
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-600 bg-neutral-900 px-3 py-2 text-neutral-100 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              required
            />
          </div>
          <div>
            <label htmlFor={`${id}-name`} className="block text-sm font-medium text-neutral-300">
              Display name
            </label>
            <input
              id={`${id}-name`}
              type="text"
              autoComplete="name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-600 bg-neutral-900 px-3 py-2 text-neutral-100 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
          {error ? <p className="text-sm text-red-400">{error}</p> : null}
          <div className="flex justify-end gap-2 pt-2">
            {!onCloseBlocked ? (
              <button
                type="button"
                className="rounded-lg px-3 py-2 text-sm text-neutral-400 hover:text-neutral-200"
              >
                Cancel
              </button>
            ) : null}
            <button
              type="submit"
              disabled={busy}
              className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
            >
              {busy ? "Saving…" : "Continue"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

import { useState } from "react";

type Props = {
  disabled: boolean;
  disabledReason: string;
  onSend: () => Promise<void>;
};

export function SendBookingEmailButton({ disabled, disabledReason, onSend }: Props) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function confirmSend() {
    setBusy(true);
    setMsg(null);
    try {
      await onSend();
      setMsg("Sent.");
      setOpen(false);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Send failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span>
      <button type="button" disabled={disabled || busy} title={disabled ? disabledReason : ""} onClick={() => setOpen(true)}>
        Send Email
      </button>
      {open && (
        <div
          role="dialog"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15,23,42,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
          }}
        >
          <div style={{ background: "#fff", padding: 20, borderRadius: 12, maxWidth: 420 }}>
            <h3 style={{ marginTop: 0 }}>Send booking email</h3>
            <p style={{ fontSize: "0.9rem", color: "#475569" }}>
              Sends confirmation to the investor (from auth) and advisor ({`ADVISOR_EMAIL`}). Includes Weekly Pulse when
              available.
            </p>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 16 }}>
              <button type="button" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button type="button" className="primary" disabled={busy} onClick={confirmSend}>
                {busy ? "Sending…" : "Confirm send"}
              </button>
            </div>
            {msg && <p style={{ color: msg === "Sent." ? "#15803d" : "#b91c1c" }}>{msg}</p>}
          </div>
        </div>
      )}
    </span>
  );
}

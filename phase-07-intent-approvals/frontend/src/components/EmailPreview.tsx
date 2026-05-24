type Props = {
  subject: string;
  body: string;
};

export function EmailPreview({ subject, body }: Props) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">Newsletter Draft</div>
      <div className="mt-2 rounded-md bg-muted px-3 py-2 text-sm font-semibold">Subject: {subject}</div>
      <div className="mt-3 text-xs text-muted-foreground">
        Includes booking update + Weekly Pulse + fee explanation.
      </div>
      <pre className="mt-3 max-h-[420px] overflow-auto whitespace-pre-wrap text-sm text-foreground">{body}</pre>
    </div>
  );
}

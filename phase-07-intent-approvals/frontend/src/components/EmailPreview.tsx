type Props = {
  subject: string;
  body: string;
};

export function EmailPreview({ subject, body }: Props) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">Email Draft</div>
      <div className="mt-2 text-sm font-semibold">Subject: {subject}</div>
      <pre className="mt-3 whitespace-pre-wrap text-sm text-foreground">{body}</pre>
    </div>
  );
}

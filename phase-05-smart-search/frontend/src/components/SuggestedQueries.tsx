import { Lightbulb } from "lucide-react";

const SUGGESTIONS = [
  "What is the exit load of Mirae Asset Large Cap Fund?",
  "Compare expense ratios of Large Cap vs Flexi Cap funds",
  "What are the tax implications for ELSS funds?",
  "Tell me about Mirae Asset Small Cap Fund returns",
  "What is the minimum SIP amount for Mirae Asset Flexi Cap?",
  "Explain the difference between direct and regular plans",
];

type Props = {
  onSelect: (query: string) => void;
};

export function SuggestedQueries({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12">
      <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
        <Lightbulb className="w-6 h-6 text-primary" />
      </div>
      <h2 className="text-lg font-semibold text-foreground mb-1">Smart Search</h2>
      <p className="text-sm text-muted-foreground mb-6 text-center max-w-md">
        Ask questions about mutual funds, fees, returns, and more. Answers are grounded in real fund data.
      </p>
      <div className="grid gap-2 w-full max-w-lg">
        {SUGGESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onSelect(q)}
            className="text-left rounded-xl border border-border px-4 py-3 text-sm text-foreground hover:bg-muted transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

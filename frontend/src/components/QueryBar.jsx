import { useState } from "react";

const EXAMPLES = [
  "Should we be long or short on Nvidia going into next quarter?",
  "Is Apple's management tone improving or deteriorating?",
  "Compare Meta and Alphabet's recent filing language",
  "What does Microsoft's latest 10-K signal about their outlook?",
  "Which is a better buy: JPMorgan or Goldman Sachs?",
];

export default function QueryBar({ onSubmit, loading }) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query.trim());
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about any public company's SEC filings..."
          disabled={loading}
          className="flex-1 bg-navy-light border border-border rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-terminal/50 font-sans text-sm transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="bg-terminal/20 text-terminal border border-terminal/30 px-6 py-3 rounded-lg font-mono text-sm font-semibold hover:bg-terminal/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-terminal/30 border-t-terminal rounded-full animate-spin" />
              Analyzing
            </span>
          ) : (
            "Analyze"
          )}
        </button>
      </form>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2 mt-3">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => {
              setQuery(ex);
              if (!loading) onSubmit(ex);
            }}
            disabled={loading}
            className="text-xs text-gray-500 bg-navy-light border border-border rounded-full px-3 py-1 hover:border-terminal/30 hover:text-terminal/70 transition-colors disabled:opacity-40"
          >
            {ex.length > 50 ? ex.slice(0, 50) + "..." : ex}
          </button>
        ))}
      </div>
    </div>
  );
}

import ReactMarkdown from "react-markdown";

export default function EvidencePanel({ result }) {
  const handleDownload = () => {
    const blob = new Blob([result.full_memo || ""], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.company}_analysis.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Key Evidence */}
      {result.key_evidence && result.key_evidence.length > 0 && (
        <div className="bg-navy-light border border-border rounded-xl p-5">
          <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
            Key Evidence
          </h3>
          <ul className="space-y-2">
            {result.key_evidence.map((point, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-300">
                <span className="text-terminal flex-shrink-0 mt-0.5">
                  &#9654;
                </span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Historical Context */}
      {result.historical_context && (
        <div className="bg-navy-light border border-border rounded-xl p-5">
          <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
            Historical Context
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            {result.historical_context}
          </p>
        </div>
      )}

      {/* Competitor Comparison */}
      {result.competitor_comparison && (
        <div className="bg-navy-light border border-border rounded-xl p-5">
          <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
            Competitor Comparison
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            {result.competitor_comparison}
          </p>
        </div>
      )}

      {/* Full Memo */}
      {result.full_memo && (
        <div className="bg-navy-light border border-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider">
              Full Research Memo
            </h3>
            <button
              onClick={handleDownload}
              className="text-xs text-terminal/70 hover:text-terminal border border-terminal/20 rounded px-3 py-1 font-mono transition-colors"
            >
              Download .md
            </button>
          </div>
          <div className="prose prose-sm prose-invert max-w-none text-gray-300 leading-relaxed">
            <ReactMarkdown>{result.full_memo}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

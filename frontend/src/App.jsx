import { useState } from "react";
import QueryBar from "./components/QueryBar";
import AgentSteps from "./components/AgentSteps";
import SignalCard from "./components/SignalCard";
import EvidencePanel from "./components/EvidencePanel";
import ChartView from "./components/ChartView";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [steps, setSteps] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQuery = async (question) => {
    setLoading(true);
    setSteps([]);
    setResult(null);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);
            if (event.type === "step") {
              setSteps((prev) => [...prev, event]);
            } else if (event.type === "error") {
              setError(event.message);
              setLoading(false);
            } else if (event.type === "result") {
              setResult(event.data);
              setLoading(false);
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy text-white font-sans">
      {/* Header */}
      <header className="border-b border-border px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-terminal font-mono text-xl font-bold">
            FilingLens
          </span>
          <span className="text-gray-500 text-sm">
            SEC Intelligence Platform
          </span>
        </div>
        <span className="text-gray-600 text-xs font-mono">
          EDGAR &middot; Yahoo Finance &middot; OpenAI
        </span>
      </header>

      {/* Query Bar */}
      <div className="px-8 py-6 border-b border-border">
        <QueryBar onSubmit={handleQuery} loading={loading} />
      </div>

      {/* Main content */}
      <div className="flex h-[calc(100vh-160px)]">
        {/* Left: Agent reasoning steps */}
        <div className="w-80 border-r border-border overflow-y-auto p-4 flex-shrink-0">
          <AgentSteps steps={steps} loading={loading} />
        </div>

        {/* Right: Results */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-danger/10 border border-danger/30 rounded-lg p-4 text-danger">
              {error}
            </div>
          )}
          {result && (
            <>
              <SignalCard result={result} />
              <ChartView chartBase64={result.chart_base64} />
              <EvidencePanel result={result} />
            </>
          )}
          {!result && !loading && !error && (
            <div className="flex items-center justify-center h-full text-gray-600">
              <div className="text-center">
                <p className="font-mono text-lg mb-2">
                  Ask a question to begin analysis
                </p>
                <p className="text-sm text-gray-700">
                  Example: &ldquo;Should we be long or short on Nvidia going
                  into next quarter?&rdquo;
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

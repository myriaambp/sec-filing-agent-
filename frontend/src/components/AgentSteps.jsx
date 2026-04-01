const AGENT_ICONS = {
  Orchestrator: "\u2699\uFE0F",
  FilingNLPAgent: "\uD83D\uDD0D",
  MarketSignalAgent: "\uD83D\uDCC8",
  AnalystAgent: "\u270D\uFE0F",
};

const AGENT_COLORS = {
  Orchestrator: "text-blue-400",
  FilingNLPAgent: "text-purple-400",
  MarketSignalAgent: "text-yellow-400",
  AnalystAgent: "text-terminal",
};

export default function AgentSteps({ steps, loading }) {
  return (
    <div>
      <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4">
        Agent Activity
      </h3>

      {steps.length === 0 && !loading && (
        <p className="text-gray-700 text-sm">
          Agent reasoning will appear here...
        </p>
      )}

      <div className="space-y-3">
        {steps.map((step, i) => {
          const icon = AGENT_ICONS[step.agent] || "\u25CF";
          const color = AGENT_COLORS[step.agent] || "text-gray-400";
          const isLatest = i === steps.length - 1 && loading;

          return (
            <div
              key={i}
              className={`flex gap-2 text-sm ${isLatest ? "opacity-100" : "opacity-70"}`}
            >
              <span className="text-base flex-shrink-0 mt-0.5">{icon}</span>
              <div>
                <span
                  className={`font-mono text-xs font-semibold ${color} block`}
                >
                  {step.agent}
                </span>
                <span className="text-gray-400 text-xs leading-relaxed">
                  {step.message}
                </span>
              </div>
              {isLatest && (
                <span className="w-2 h-2 bg-terminal rounded-full mt-2 animate-pulse-dot flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>

      {loading && steps.length > 0 && (
        <div className="mt-4 flex items-center gap-2 text-xs text-gray-600">
          <span className="w-3 h-3 border-2 border-gray-700 border-t-terminal rounded-full animate-spin" />
          Processing...
        </div>
      )}
    </div>
  );
}

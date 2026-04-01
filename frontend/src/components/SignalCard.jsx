const SIGNAL_STYLES = {
  BUY: { bg: "bg-terminal/10", border: "border-terminal/30", text: "text-terminal" },
  OVERWEIGHT: { bg: "bg-terminal/10", border: "border-terminal/30", text: "text-terminal" },
  SELL: { bg: "bg-danger/10", border: "border-danger/30", text: "text-danger" },
  UNDERWEIGHT: { bg: "bg-danger/10", border: "border-danger/30", text: "text-danger" },
  HOLD: { bg: "bg-warning/10", border: "border-warning/30", text: "text-warning" },
};

const SIGNAL_LABELS = {
  BULLISH: { color: "text-terminal", icon: "\u25B2" },
  CAUTIONARY: { color: "text-warning", icon: "\u25C6" },
  BEARISH: { color: "text-danger", icon: "\u25BC" },
};

export default function SignalCard({ result }) {
  const rec = result.recommendation || "HOLD";
  const style = SIGNAL_STYLES[rec] || SIGNAL_STYLES.HOLD;
  const signalInfo = SIGNAL_LABELS[result.signal] || SIGNAL_LABELS.CAUTIONARY;
  const confidence = Math.round((result.confidence || 0) * 100);

  const trendIcon =
    result.language_trend === "deteriorating"
      ? "\u2191"
      : result.language_trend === "improving"
        ? "\u2193"
        : "\u2194";

  return (
    <div className={`${style.bg} border ${style.border} rounded-xl p-6`}>
      <div className="flex items-start justify-between">
        {/* Left: Company + Signal */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-2xl font-bold text-white">
              {result.company}
            </span>
            <span className="text-gray-400 text-sm">
              {result.company_name}
            </span>
          </div>

          {/* Signal badge */}
          <div className="flex items-center gap-4 mt-3">
            <span
              className={`${style.text} font-mono text-3xl font-bold tracking-wide`}
            >
              {rec}
            </span>
            <span className={`${signalInfo.color} text-sm font-mono`}>
              {signalInfo.icon} {result.signal}
            </span>
          </div>
        </div>

        {/* Right: Confidence + Metrics */}
        <div className="text-right space-y-2">
          <div>
            <span className="text-xs text-gray-500 font-mono block">
              CONFIDENCE
            </span>
            <span className={`font-mono text-xl font-bold ${style.text}`}>
              {confidence}%
            </span>
          </div>
          <div className="w-24 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${rec === "BUY" || rec === "OVERWEIGHT" ? "bg-terminal" : rec === "SELL" || rec === "UNDERWEIGHT" ? "bg-danger" : "bg-warning"}`}
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>
      </div>

      {/* Bottom metrics row */}
      <div className="flex gap-6 mt-5 pt-4 border-t border-white/5">
        <div>
          <span className="text-xs text-gray-500 block">Language Trend</span>
          <span className="font-mono text-sm text-white">
            {trendIcon}{" "}
            {result.language_trend
              ? result.language_trend.charAt(0).toUpperCase() +
                result.language_trend.slice(1)
              : "N/A"}
          </span>
        </div>
        <div>
          <span className="text-xs text-gray-500 block">
            Uncertainty Change
          </span>
          <span className="font-mono text-sm text-white">
            {result.uncertainty_score_change || "N/A"}
          </span>
        </div>
        {result.competitors_analyzed && result.competitors_analyzed.length > 0 && (
          <div>
            <span className="text-xs text-gray-500 block">Compared To</span>
            <div className="flex gap-1 mt-0.5">
              {result.competitors_analyzed.map((c) => (
                <span
                  key={c}
                  className="font-mono text-xs bg-white/5 border border-white/10 rounded px-1.5 py-0.5 text-gray-300"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

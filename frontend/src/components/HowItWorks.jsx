export default function HowItWorks({ compact = false }) {
  const sectionClass = compact
    ? "bg-navy-light/50 border border-border rounded-lg p-3"
    : "bg-navy-light border border-border rounded-xl p-5";

  return (
    <div className={compact ? "space-y-3" : "space-y-4 max-w-3xl mx-auto"}>
      {!compact && (
        <h2 className="text-lg font-mono text-terminal font-bold mb-4">
          How FilingLens Works
        </h2>
      )}

      {/* Pipeline overview */}
      <div className={sectionClass}>
        <h3 className="text-xs font-mono text-terminal/80 uppercase tracking-wider mb-2">
          1. Collect
        </h3>
        <p className="text-xs text-gray-400 leading-relaxed">
          When you ask a question, the system identifies the company ticker and
          fetches <strong className="text-gray-300">real SEC filings</strong>{" "}
          (10-Q quarterly or 10-K annual) from the{" "}
          <strong className="text-gray-300">EDGAR database</strong>. It also
          pulls <strong className="text-gray-300">stock price history</strong>{" "}
          from Yahoo Finance. Competitors are auto-detected based on sector.
        </p>
      </div>

      <div className={sectionClass}>
        <h3 className="text-xs font-mono text-terminal/80 uppercase tracking-wider mb-2">
          2. Explore &amp; Analyze
        </h3>
        <p className="text-xs text-gray-400 leading-relaxed mb-2">
          Two AI agents analyze the data{" "}
          <strong className="text-gray-300">in parallel</strong>:
        </p>
        <ul className="text-xs text-gray-400 space-y-1 ml-3">
          <li>
            <span className="text-purple-400 font-mono">Filing NLP Agent</span>{" "}
            &mdash; Scans the MD&amp;A and Risk Factors sections for
            uncertainty language (words like &ldquo;may,&rdquo;
            &ldquo;risk,&rdquo; &ldquo;adverse&rdquo;) and confidence language
            (&ldquo;strong,&rdquo; &ldquo;growth,&rdquo;
            &ldquo;exceeded&rdquo;). Tracks how this shifts quarter over
            quarter.
          </li>
          <li>
            <span className="text-yellow-400 font-mono">
              Market Signal Agent
            </span>{" "}
            &mdash; Checks what happened to the stock price in the 30 and 60
            days after each filing. Compares to the S&amp;P 500 to see if high
            uncertainty predicted underperformance.
          </li>
        </ul>
      </div>

      <div className={sectionClass}>
        <h3 className="text-xs font-mono text-terminal/80 uppercase tracking-wider mb-2">
          3. Hypothesize
        </h3>
        <p className="text-xs text-gray-400 leading-relaxed">
          The{" "}
          <span className="text-terminal font-mono">Analyst Agent</span>{" "}
          synthesizes everything into a research memo with a{" "}
          <strong className="text-gray-300">
            Buy / Sell / Hold recommendation
          </strong>
          . Confidence is computed from signal strength, trend magnitude, data
          consistency, and competitor comparison &mdash; not hardcoded.
        </p>
      </div>

      {/* Reading the results */}
      <div className={sectionClass}>
        <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-2">
          Understanding the Output
        </h3>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-gray-500 block mb-1">Signal Card</span>
            <p className="text-gray-400">
              Shows the recommendation (BUY/SELL/HOLD/OVERWEIGHT/UNDERWEIGHT),
              confidence %, language trend direction, and which competitors were
              analyzed.
            </p>
          </div>
          <div>
            <span className="text-gray-500 block mb-1">Chart</span>
            <p className="text-gray-400">
              Red line = filing uncertainty score over time. Green line = stock
              price. Dashed lines = competitor uncertainty. Vertical dotted
              lines mark filing dates.
            </p>
          </div>
          <div>
            <span className="text-gray-500 block mb-1">Uncertainty Score</span>
            <p className="text-gray-400">
              Ratio of hedging/risk words in filing text, scaled 0&ndash;1.
              Higher = more cautious management language. A rising score means
              management is becoming less confident.
            </p>
          </div>
          <div>
            <span className="text-gray-500 block mb-1">Confidence %</span>
            <p className="text-gray-400">
              How much the data supports the recommendation. Based on signal
              strength, trend consistency, number of filings analyzed, and
              competitor divergence. Not a price prediction.
            </p>
          </div>
        </div>
      </div>

      {!compact && (
        <p className="text-xs text-gray-600 text-center mt-4">
          All data is fetched at runtime from public sources. No financial
          advice is implied.
        </p>
      )}
    </div>
  );
}

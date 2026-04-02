function downloadCSV(filename, headers, rows) {
  const csv = [
    headers.join(","),
    ...rows.map((r) =>
      r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")
    ),
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function DataSourcesPanel({ dataSources }) {
  if (!dataSources) return null;

  const primary = dataSources.primary || {};
  const competitors = dataSources.competitors || {};
  const priceData = dataSources.price_data || {};
  const rawScores = dataSources.raw_scores || {};

  const ticker = priceData.ticker || "DATA";

  const handleDownloadFilings = () => {
    const headers = ["Ticker", "Period", "Filing Date", "Form Type", "URL"];
    const rows = [];
    for (const f of primary.filings || []) {
      rows.push([ticker, f.period, f.filing_date, f.form_type, f.url]);
    }
    for (const [comp, data] of Object.entries(competitors)) {
      for (const f of data.filings || []) {
        rows.push([comp, f.period, f.filing_date, f.form_type, f.url]);
      }
    }
    downloadCSV(`${ticker}_filing_sources.csv`, headers, rows);
  };

  const handleDownloadScores = () => {
    const headers = [
      "Ticker",
      "Period",
      "Filing Date",
      "Uncertainty Score",
      "Sentiment Score",
      "Uncertainty Words",
      "Total Words",
    ];
    const rows = [];
    for (const q of rawScores.primary_quarterly_scores || []) {
      rows.push([
        ticker,
        q.period,
        q.filing_date,
        q.uncertainty_score,
        q.sentiment_score,
        q.uncertainty_word_count,
        q.total_word_count,
      ]);
    }
    for (const [comp, scores] of Object.entries(
      rawScores.competitor_quarterly_scores || {}
    )) {
      for (const q of scores || []) {
        rows.push([
          comp,
          q.period,
          q.filing_date,
          q.uncertainty_score,
          q.sentiment_score,
          q.uncertainty_word_count || "",
          q.total_word_count || "",
        ]);
      }
    }
    downloadCSV(`${ticker}_analysis_scores.csv`, headers, rows);
  };

  const handleDownloadRawData = () => {
    const headers = [
      "Ticker",
      "Period",
      "Filing Date",
      "Uncertainty Score",
      "Sentiment Score",
      "Uncertainty Words",
      "Total Words",
      "Key Risk Phrases",
      "Filing URL",
    ];
    const rows = [];
    for (const q of rawScores.primary_quarterly_scores || []) {
      rows.push([
        ticker,
        q.period,
        q.filing_date,
        q.uncertainty_score,
        q.sentiment_score,
        q.uncertainty_word_count,
        q.total_word_count,
        (q.key_risk_phrases || []).join(" | "),
        q.filing_url || "",
      ]);
    }
    for (const [comp, scores] of Object.entries(
      rawScores.competitor_quarterly_scores || {}
    )) {
      for (const q of scores || []) {
        rows.push([
          comp,
          q.period,
          q.filing_date,
          q.uncertainty_score,
          q.sentiment_score,
          q.uncertainty_word_count || "",
          q.total_word_count || "",
          (q.key_risk_phrases || []).join(" | "),
          q.filing_url || "",
        ]);
      }
    }
    downloadCSV(`${ticker}_raw_data.csv`, headers, rows);
  };

  const filingCount =
    (primary.filings || []).length +
    Object.values(competitors).reduce(
      (sum, d) => sum + (d.filings || []).length,
      0
    );
  const scoreCount =
    (rawScores.primary_quarterly_scores || []).length +
    Object.values(rawScores.competitor_quarterly_scores || {}).reduce(
      (sum, s) => sum + (s || []).length,
      0
    );

  return (
    <div className="bg-navy-light border border-border rounded-xl p-5">
      <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4">
        Downloads
      </h3>
      <div className="flex flex-wrap gap-3">
        {filingCount > 0 && (
          <button
            onClick={handleDownloadFilings}
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-terminal bg-navy border border-border hover:border-terminal/30 rounded-lg px-4 py-2.5 font-mono transition-colors"
          >
            <span className="text-base">&#128196;</span>
            <div className="text-left">
              <span className="block text-gray-300">Filing Sources</span>
              <span className="text-gray-600">
                {filingCount} filings &middot; CSV
              </span>
            </div>
          </button>
        )}

        {scoreCount > 0 && (
          <button
            onClick={handleDownloadScores}
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-terminal bg-navy border border-border hover:border-terminal/30 rounded-lg px-4 py-2.5 font-mono transition-colors"
          >
            <span className="text-base">&#128202;</span>
            <div className="text-left">
              <span className="block text-gray-300">Analysis Scores</span>
              <span className="text-gray-600">
                {scoreCount} quarters &middot; CSV
              </span>
            </div>
          </button>
        )}

        {scoreCount > 0 && (
          <button
            onClick={handleDownloadRawData}
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-terminal bg-navy border border-border hover:border-terminal/30 rounded-lg px-4 py-2.5 font-mono transition-colors"
          >
            <span className="text-base">&#128451;</span>
            <div className="text-left">
              <span className="block text-gray-300">
                Raw Data + Risk Phrases
              </span>
              <span className="text-gray-600">
                Full dataset &middot; CSV
              </span>
            </div>
          </button>
        )}

        {priceData.url && (
          <a
            href={priceData.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-terminal bg-navy border border-border hover:border-terminal/30 rounded-lg px-4 py-2.5 font-mono transition-colors"
          >
            <span className="text-base">&#128200;</span>
            <div className="text-left">
              <span className="block text-gray-300">Price History</span>
              <span className="text-gray-600">
                {priceData.summary?.total_trading_days || 0} days &middot;
                Yahoo Finance &#8599;
              </span>
            </div>
          </a>
        )}

        {primary.edgar_company_page && (
          <a
            href={primary.edgar_company_page}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs text-gray-400 hover:text-terminal bg-navy border border-border hover:border-terminal/30 rounded-lg px-4 py-2.5 font-mono transition-colors"
          >
            <span className="text-base">&#127963;</span>
            <div className="text-left">
              <span className="block text-gray-300">EDGAR Filings</span>
              <span className="text-gray-600">
                Browse all filings &#8599;
              </span>
            </div>
          </a>
        )}
      </div>
    </div>
  );
}

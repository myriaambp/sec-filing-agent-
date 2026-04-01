function downloadCSV(filename, headers, rows) {
  const csv = [
    headers.join(","),
    ...rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")),
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function DownloadBtn({ onClick, children }) {
  return (
    <button
      onClick={onClick}
      className="text-xs text-terminal/60 hover:text-terminal border border-terminal/20 hover:border-terminal/40 rounded px-2 py-0.5 font-mono transition-colors"
    >
      {children}
    </button>
  );
}

export default function DataSourcesPanel({ dataSources }) {
  if (!dataSources) return null;

  const primary = dataSources.primary || {};
  const competitors = dataSources.competitors || {};
  const priceData = dataSources.price_data || {};
  const rawScores = dataSources.raw_scores || {};

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
    const ticker = priceData.ticker || "PRIMARY";
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
    downloadCSV(`${ticker}_language_scores.csv`, headers, rows);
  };

  const handleDownloadFilings = () => {
    const headers = ["Ticker", "Period", "Filing Date", "Form Type", "URL"];
    const rows = [];
    const ticker = priceData.ticker || "PRIMARY";
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

  return (
    <div className="space-y-4">
      {/* Filing Sources */}
      <div className="bg-navy-light border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider">
            Data Sources — SEC Filings
          </h3>
          {primary.filings && primary.filings.length > 0 && (
            <DownloadBtn onClick={handleDownloadFilings}>
              Download CSV
            </DownloadBtn>
          )}
        </div>

        {primary.filings && primary.filings.length > 0 && (
          <div className="mb-4">
            {primary.edgar_company_page && (
              <a
                href={primary.edgar_company_page}
                target="_blank"
                rel="noopener noreferrer"
                className="text-terminal/80 hover:text-terminal text-xs font-mono underline mb-2 block"
              >
                View all filings on EDGAR &#8599;
              </a>
            )}
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-500 border-b border-border">
                  <th className="text-left py-1 font-mono">Period</th>
                  <th className="text-left py-1 font-mono">Filed</th>
                  <th className="text-left py-1 font-mono">Type</th>
                  <th className="text-left py-1 font-mono">Link</th>
                </tr>
              </thead>
              <tbody>
                {primary.filings.map((f, i) => (
                  <tr
                    key={i}
                    className="border-b border-white/5 text-gray-400"
                  >
                    <td className="py-1.5 font-mono">{f.period}</td>
                    <td className="py-1.5 font-mono">{f.filing_date}</td>
                    <td className="py-1.5 font-mono">{f.form_type}</td>
                    <td className="py-1.5">
                      <a
                        href={f.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-terminal/70 hover:text-terminal underline"
                      >
                        View Filing &#8599;
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {Object.entries(competitors).map(([ticker, data]) => (
          <div key={ticker} className="mt-3 pt-3 border-t border-white/5">
            <span className="text-xs font-mono text-gray-500">
              {ticker} Filings
            </span>
            {data.filings && data.filings.length > 0 && (
              <div className="mt-1 space-y-0.5">
                {data.filings.map((f, i) => (
                  <div key={i} className="flex gap-3 text-xs text-gray-500">
                    <span className="font-mono">{f.period}</span>
                    <a
                      href={f.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-terminal/60 hover:text-terminal underline"
                    >
                      View &#8599;
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Price Data Source */}
      <div className="bg-navy-light border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider">
            Data Sources — Price Data ({priceData.summary?.total_trading_days || 0} trading days)
          </h3>
          {priceData.url && (
            <a
              href={priceData.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-terminal/70 hover:text-terminal text-xs font-mono underline"
            >
              Yahoo Finance &#8599;
            </a>
          )}
        </div>

        {priceData.summary && (
          <div className="grid grid-cols-4 gap-3 text-xs">
            {[
              ["Total Return", `${((priceData.summary.total_return || 0) * 100).toFixed(1)}%`],
              ["Ann. Volatility", `${((priceData.summary.annualized_volatility || 0) * 100).toFixed(1)}%`],
              ["Max Drawdown", `${((priceData.summary.max_drawdown || 0) * 100).toFixed(1)}%`],
              ["Sharpe Ratio", priceData.summary.sharpe_ratio_approx],
              ["Price Range", `$${priceData.summary.price_low} — $${priceData.summary.price_high}`],
              ["Current", `$${priceData.summary.price_end}`],
              ["Avg Volume", (priceData.summary.avg_volume || 0).toLocaleString()],
              ["Trading Days", priceData.summary.total_trading_days],
            ].map(([label, value]) => (
              <div key={label}>
                <span className="text-gray-600 block">{label}</span>
                <span className="font-mono text-gray-300">{value}</span>
              </div>
            ))}
          </div>
        )}

        {/* Competitor price summaries */}
        {priceData.competitor_summaries && Object.entries(priceData.competitor_summaries).map(([ticker, summary]) => (
          summary && (
            <div key={ticker} className="mt-3 pt-3 border-t border-white/5">
              <span className="text-xs font-mono text-gray-500 block mb-2">{ticker}</span>
              <div className="grid grid-cols-4 gap-2 text-xs">
                {[
                  ["Return", `${((summary.total_return || 0) * 100).toFixed(1)}%`],
                  ["Volatility", `${((summary.annualized_volatility || 0) * 100).toFixed(1)}%`],
                  ["Drawdown", `${((summary.max_drawdown || 0) * 100).toFixed(1)}%`],
                  ["Sharpe", summary.sharpe_ratio_approx],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span className="text-gray-600 block">{label}</span>
                    <span className="font-mono text-gray-500">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )
        ))}
      </div>

      {/* Raw Scores */}
      {rawScores.primary_quarterly_scores &&
        rawScores.primary_quarterly_scores.length > 0 && (
          <div className="bg-navy-light border border-border rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider">
                Raw Analysis Scores
              </h3>
              <DownloadBtn onClick={handleDownloadScores}>
                Download CSV
              </DownloadBtn>
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-500 border-b border-border">
                  <th className="text-left py-1 font-mono">Period</th>
                  <th className="text-right py-1 font-mono">Uncertainty</th>
                  <th className="text-right py-1 font-mono">Sentiment</th>
                  <th className="text-right py-1 font-mono">Unc. Words</th>
                  <th className="text-right py-1 font-mono">Total Words</th>
                </tr>
              </thead>
              <tbody>
                {rawScores.primary_quarterly_scores.map((q, i) => (
                  <tr
                    key={i}
                    className="border-b border-white/5 text-gray-400"
                  >
                    <td className="py-1.5 font-mono">{q.period}</td>
                    <td className="py-1.5 font-mono text-right">
                      {(q.uncertainty_score || 0).toFixed(3)}
                    </td>
                    <td className="py-1.5 font-mono text-right">
                      {(q.sentiment_score || 0).toFixed(3)}
                    </td>
                    <td className="py-1.5 font-mono text-right">
                      {q.uncertainty_word_count}
                    </td>
                    <td className="py-1.5 font-mono text-right">
                      {q.total_word_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {rawScores.competitor_quarterly_scores &&
              Object.entries(rawScores.competitor_quarterly_scores).map(
                ([ticker, scores]) =>
                  scores &&
                  scores.length > 0 && (
                    <div
                      key={ticker}
                      className="mt-3 pt-3 border-t border-white/5"
                    >
                      <span className="text-xs font-mono text-gray-500 block mb-1">
                        {ticker}
                      </span>
                      <table className="w-full text-xs">
                        <tbody>
                          {scores.map((q, i) => (
                            <tr
                              key={i}
                              className="border-b border-white/5 text-gray-500"
                            >
                              <td className="py-1 font-mono">{q.period}</td>
                              <td className="py-1 font-mono text-right">
                                {(q.uncertainty_score || 0).toFixed(3)}
                              </td>
                              <td className="py-1 font-mono text-right">
                                {(q.sentiment_score || 0).toFixed(3)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
              )}
          </div>
        )}
    </div>
  );
}

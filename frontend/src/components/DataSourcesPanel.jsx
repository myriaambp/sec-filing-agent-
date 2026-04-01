export default function DataSourcesPanel({ dataSources }) {
  if (!dataSources) return null;

  const primary = dataSources.primary || {};
  const competitors = dataSources.competitors || {};
  const priceData = dataSources.price_data || {};
  const rawScores = dataSources.raw_scores || {};

  return (
    <div className="space-y-4">
      {/* Filing Sources */}
      <div className="bg-navy-light border border-border rounded-xl p-5">
        <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
          Data Sources — SEC Filings
        </h3>

        {/* Primary company filings */}
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
                  <tr key={i} className="border-b border-white/5 text-gray-400">
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

        {/* Competitor filings */}
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
        <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
          Data Sources — Price Data
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">
            {priceData.source} — {priceData.ticker}
          </span>
          {priceData.url && (
            <a
              href={priceData.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-terminal/70 hover:text-terminal text-xs underline"
            >
              View on Yahoo Finance &#8599;
            </a>
          )}
        </div>
      </div>

      {/* Raw Scores */}
      {rawScores.primary_quarterly_scores &&
        rawScores.primary_quarterly_scores.length > 0 && (
          <div className="bg-navy-light border border-border rounded-xl p-5">
            <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
              Raw Analysis Scores
            </h3>
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

            {/* Competitor raw scores */}
            {rawScores.competitor_quarterly_scores &&
              Object.entries(rawScores.competitor_quarterly_scores).map(
                ([ticker, scores]) =>
                  scores &&
                  scores.length > 0 && (
                    <div key={ticker} className="mt-3 pt-3 border-t border-white/5">
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

import ReactMarkdown from "react-markdown";

function generateFullReportHTML(result) {
  const scores =
    result.data_sources?.raw_scores?.primary_quarterly_scores || [];
  const compScores =
    result.data_sources?.raw_scores?.competitor_quarterly_scores || {};
  const filings = result.data_sources?.primary?.filings || [];
  const priceUrl = result.data_sources?.price_data?.url || "";
  const edgarUrl = result.data_sources?.primary?.edgar_company_page || "";
  const chartSrc = result.chart_base64
    ? `data:image/png;base64,${result.chart_base64}`
    : "";

  const recColor =
    result.recommendation === "BUY" || result.recommendation === "OVERWEIGHT"
      ? "#00875a"
      : result.recommendation === "SELL" ||
          result.recommendation === "UNDERWEIGHT"
        ? "#de350b"
        : "#ff991f";

  const recBg =
    result.recommendation === "BUY" || result.recommendation === "OVERWEIGHT"
      ? "#e3fcef"
      : result.recommendation === "SELL" ||
          result.recommendation === "UNDERWEIGHT"
        ? "#ffebe6"
        : "#fffae6";

  const scoresRows = scores
    .map(
      (q) => `
    <tr>
      <td>${q.period || ""}</td>
      <td>${q.filing_date || ""}</td>
      <td style="text-align:right">${(q.uncertainty_score || 0).toFixed(4)}</td>
      <td style="text-align:right">${(q.sentiment_score || 0).toFixed(4)}</td>
      <td style="text-align:right">${q.uncertainty_word_count || 0}</td>
      <td style="text-align:right">${q.total_word_count || 0}</td>
    </tr>`
    )
    .join("");

  const compTables = Object.entries(compScores)
    .filter(([, s]) => s && s.length > 0)
    .map(
      ([ticker, cScores]) => `
    <h4>${ticker}</h4>
    <table>
      <thead><tr><th>Period</th><th>Filing Date</th><th style="text-align:right">Uncertainty</th><th style="text-align:right">Sentiment</th></tr></thead>
      <tbody>
        ${cScores
          .map(
            (q) =>
              `<tr><td>${q.period || ""}</td><td>${q.filing_date || ""}</td><td style="text-align:right">${(q.uncertainty_score || 0).toFixed(4)}</td><td style="text-align:right">${(q.sentiment_score || 0).toFixed(4)}</td></tr>`
          )
          .join("")}
      </tbody>
    </table>`
    )
    .join("");

  const filingsRows = filings
    .map(
      (f) =>
        `<tr><td>${f.period || ""}</td><td>${f.filing_date || ""}</td><td>${f.form_type || ""}</td><td><a href="${f.url || "#"}" target="_blank">View on EDGAR</a></td></tr>`
    )
    .join("");

  const evidenceItems = (result.key_evidence || [])
    .map((e) => `<li>${e}</li>`)
    .join("");

  // Convert markdown memo to simple HTML
  const memoHTML = (result.full_memo || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^## (.+)$/gm, '<h2 class="memo-h2">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="memo-h3">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>");

  const date = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return `<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>${result.company_name || result.company} — FilingLens Research Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

  :root { --accent: ${recColor}; --accent-bg: ${recBg}; }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  @page { size: A4; margin: 20mm 25mm; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    color: #1e293b;
    line-height: 1.65;
    padding: 48px 64px;
    max-width: 860px;
    margin: 0 auto;
    font-size: 13px;
  }

  /* Header */
  .report-header {
    border-bottom: 3px solid var(--accent);
    padding-bottom: 24px;
    margin-bottom: 32px;
  }
  .report-header h1 {
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #0f172a;
  }
  .report-header .tagline {
    color: #64748b;
    font-size: 14px;
    margin-top: 2px;
  }
  .report-header .date {
    color: #94a3b8;
    font-size: 11px;
    font-family: 'IBM Plex Mono', monospace;
    margin-top: 8px;
  }

  /* Signal box */
  .signal-row {
    display: flex;
    align-items: center;
    gap: 32px;
    background: var(--accent-bg);
    border: 1px solid var(--accent);
    border-radius: 8px;
    padding: 20px 28px;
    margin: 24px 0 32px;
  }
  .signal-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    color: var(--accent);
  }
  .signal-meta { display: flex; gap: 28px; }
  .signal-meta-item .label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #94a3b8;
    font-weight: 500;
  }
  .signal-meta-item .value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 15px;
    font-weight: 600;
    color: #334155;
  }

  /* Section headings */
  h2 {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    margin: 36px 0 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e2e8f0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  h3, h4 {
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    margin: 20px 0 8px;
  }
  .memo-h2 {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
    margin: 28px 0 10px;
    padding-bottom: 4px;
    border-bottom: 1px solid #e2e8f0;
  }
  .memo-h3 {
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    margin: 16px 0 6px;
  }

  p { margin: 8px 0; color: #334155; }

  /* Evidence box */
  .evidence-box {
    background: #f8fafc;
    border-left: 3px solid var(--accent);
    border-radius: 0 6px 6px 0;
    padding: 16px 20px;
    margin: 16px 0;
  }
  .evidence-box li {
    margin: 6px 0;
    color: #334155;
    line-height: 1.6;
  }

  /* Methodology */
  .methodology-box {
    background: #f1f5f9;
    border-radius: 8px;
    padding: 20px 24px;
    margin: 16px 0;
  }
  .methodology-box p {
    font-size: 12px;
    color: #475569;
    margin: 6px 0;
  }
  .methodology-box strong { color: #1e293b; }

  /* Memo content */
  .memo-content {
    padding: 4px 0;
  }
  .memo-content p {
    margin: 8px 0;
    line-height: 1.7;
  }
  .memo-content ul {
    padding-left: 20px;
    margin: 8px 0;
  }
  .memo-content li {
    margin: 4px 0;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 20px;
    font-size: 11px;
    font-family: 'IBM Plex Mono', monospace;
  }
  thead th {
    text-align: left;
    padding: 8px 10px;
    background: #f1f5f9;
    border-bottom: 2px solid #cbd5e1;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
  }
  td {
    padding: 6px 10px;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
  }
  tbody tr:hover { background: #f8fafc; }

  /* Chart */
  .chart-section { margin: 24px 0; text-align: center; }
  .chart-section img {
    max-width: 100%;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .chart-caption {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 8px;
  }

  /* Links */
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* Footer */
  .report-footer {
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid #e2e8f0;
  }
  .report-footer p {
    font-size: 10px;
    color: #94a3b8;
    margin: 2px 0;
  }

  ul { padding-left: 20px; }
  li { margin: 4px 0; }

  @media print {
    body { padding: 0; }
    .signal-row { break-inside: avoid; }
    table { break-inside: avoid; }
    h2 { break-after: avoid; }
  }
</style>
</head><body>

<div class="report-header">
  <h1>${result.company_name || result.company}</h1>
  <div class="tagline">SEC Filing Language Analysis &mdash; Research Report</div>
  <div class="date">FilingLens &bull; ${date}</div>
</div>

<div class="signal-row">
  <div class="signal-badge">${result.recommendation || "HOLD"}</div>
  <div class="signal-meta">
    <div class="signal-meta-item">
      <div class="label">Signal</div>
      <div class="value">${result.signal || "N/A"}</div>
    </div>
    <div class="signal-meta-item">
      <div class="label">Confidence</div>
      <div class="value">${Math.round((result.confidence || 0) * 100)}%</div>
    </div>
    <div class="signal-meta-item">
      <div class="label">Language Trend</div>
      <div class="value">${result.language_trend || "N/A"}</div>
    </div>
    <div class="signal-meta-item">
      <div class="label">Uncertainty Change</div>
      <div class="value">${result.uncertainty_score_change || "N/A"}</div>
    </div>
    <div class="signal-meta-item">
      <div class="label">Vs. Competitors</div>
      <div class="value">${(result.competitors_analyzed || []).join(", ") || "None"}</div>
    </div>
  </div>
</div>

<h2>Key Findings</h2>
<div class="evidence-box">
  <ul>${evidenceItems || "<li>No evidence points available.</li>"}</ul>
</div>

<h2>Detailed Analysis</h2>
<div class="memo-content">
  <p>${memoHTML || "No detailed analysis available."}</p>
</div>

${chartSrc ? `
<h2>Filing Uncertainty vs. Stock Price</h2>
<div class="chart-section">
  <img src="${chartSrc}" alt="Uncertainty vs Price" />
  <div class="chart-caption">Red: uncertainty score &bull; Green: stock price &bull; Dashed: competitor uncertainty &bull; Dotted verticals: filing dates</div>
</div>
` : ""}

<h2>Historical Context</h2>
<p>${result.historical_context || "No historical context available."}</p>

<h2>Competitor Comparison</h2>
<p>${result.competitor_comparison || "No competitor comparison available."}</p>

<h2>Methodology</h2>
<div class="methodology-box">
  <p><strong>Data Collection:</strong> SEC filings (10-Q/10-K) retrieved from the EDGAR database at runtime. Stock price data sourced from Yahoo Finance (2&ndash;3 years of daily OHLCV).</p>
  <p><strong>Language Analysis:</strong> MD&amp;A and Risk Factors sections parsed via BeautifulSoup. Uncertainty score = ratio of hedging words (may, might, risk, adverse, decline, etc.) scaled to 0&ndash;1. Sentiment = net balance of confidence vs. uncertainty words, scaled -1 to +1.</p>
  <p><strong>Market Signal:</strong> 30-day and 60-day stock returns computed after each filing date and benchmarked against the S&amp;P 500 (SPY). Signal strength based on return spread and historical accuracy.</p>
  <p><strong>Confidence Computation:</strong> Six factors: signal strength (0&ndash;20%), trend magnitude (0&ndash;15%), filings analyzed (0&ndash;10%), trend consistency (0&ndash;10%), return spread (0&ndash;10%), competitor divergence (0&ndash;5%). Base: 30%.</p>
  <p><strong>Recommendation:</strong> Deteriorating language + strong signal &rarr; SELL/UNDERWEIGHT. Improving + strong &rarr; BUY/OVERWEIGHT. Mixed/weak &rarr; HOLD. Magnitude &gt;20% shifts to stronger tier.</p>
</div>

<h2>Appendix A &mdash; Quarterly Language Scores</h2>
<h3>${result.company || "Primary"}</h3>
<table>
  <thead><tr><th>Period</th><th>Filed</th><th style="text-align:right">Uncertainty</th><th style="text-align:right">Sentiment</th><th style="text-align:right">Unc. Words</th><th style="text-align:right">Total Words</th></tr></thead>
  <tbody>${scoresRows || "<tr><td colspan='6'>No data</td></tr>"}</tbody>
</table>
${compTables}

<h2>Appendix B &mdash; Filing Sources</h2>
<table>
  <thead><tr><th>Period</th><th>Filed</th><th>Form</th><th>Source</th></tr></thead>
  <tbody>${filingsRows || "<tr><td colspan='4'>No filings</td></tr>"}</tbody>
</table>
${edgarUrl ? `<p style="margin-top:8px"><a href="${edgarUrl}" target="_blank">Browse all filings on EDGAR &rarr;</a></p>` : ""}
${priceUrl ? `<p><a href="${priceUrl}" target="_blank">View price history on Yahoo Finance &rarr;</a></p>` : ""}

<div class="report-footer">
  <p><strong>FilingLens</strong> &mdash; SEC Intelligence Platform</p>
  <p>All data retrieved at runtime from SEC EDGAR and Yahoo Finance. This report is for informational and educational purposes only and does not constitute financial advice.</p>
  <p>Generated: ${date}</p>
</div>

</body></html>`;
}

function downloadReport(result) {
  const html = generateFullReportHTML(result);
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, "_blank");
  if (win) {
    win.onload = () => URL.revokeObjectURL(url);
  }
}

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

function downloadRawData(result) {
  const scores =
    result.data_sources?.raw_scores?.primary_quarterly_scores || [];
  const compScores =
    result.data_sources?.raw_scores?.competitor_quarterly_scores || {};
  const ticker = result.company || "DATA";

  const headers = [
    "Company",
    "Period",
    "Filing Date",
    "Uncertainty Score",
    "Sentiment Score",
    "Uncertainty Word Count",
    "Total Word Count",
    "Key Risk Phrases",
  ];
  const rows = [];
  for (const q of scores) {
    rows.push([
      ticker,
      q.period,
      q.filing_date,
      q.uncertainty_score,
      q.sentiment_score,
      q.uncertainty_word_count,
      q.total_word_count,
      (q.key_risk_phrases || []).join(" | "),
    ]);
  }
  for (const [comp, cScores] of Object.entries(compScores)) {
    for (const q of cScores || []) {
      rows.push([
        comp,
        q.period,
        q.filing_date,
        q.uncertainty_score,
        q.sentiment_score,
        q.uncertainty_word_count || "",
        q.total_word_count || "",
        (q.key_risk_phrases || []).join(" | "),
      ]);
    }
  }
  downloadCSV(`${ticker}_raw_analysis_data.csv`, headers, rows);
}

export default function EvidencePanel({ result }) {
  return (
    <div className="space-y-4">
      {/* Key Evidence */}
      {result.key_evidence && result.key_evidence.length > 0 && (
        <div className="bg-navy-light border border-border rounded-xl p-5">
          <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
            Key Evidence
          </h3>
          <ul className="space-y-2.5">
            {result.key_evidence.map((point, i) => (
              <li key={i} className="flex gap-3 text-sm text-gray-300">
                <span className="text-terminal flex-shrink-0 mt-1 text-xs">
                  &#9654;
                </span>
                <span className="leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Historical + Competitor side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
      </div>

      {/* Research Memo */}
      {result.full_memo && (
        <div className="bg-navy-light border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider">
              Research Memo
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => downloadRawData(result)}
                className="text-xs text-gray-500 hover:text-terminal border border-border hover:border-terminal/30 rounded px-3 py-1.5 font-mono transition-colors"
              >
                Raw Data CSV
              </button>
              <button
                onClick={() => downloadReport(result)}
                className="text-xs bg-terminal/10 text-terminal hover:bg-terminal/20 border border-terminal/30 rounded px-3 py-1.5 font-mono font-semibold transition-colors"
              >
                Full Report
              </button>
            </div>
          </div>

          <div className="memo-content space-y-4 text-sm text-gray-300 leading-relaxed">
            <ReactMarkdown
              components={{
                h2: ({ children }) => (
                  <h4 className="text-terminal/90 font-mono text-xs uppercase tracking-wider mt-6 mb-2 pb-1.5 border-b border-border">
                    {children}
                  </h4>
                ),
                h3: ({ children }) => (
                  <h5 className="text-gray-400 font-semibold text-sm mt-4 mb-1">
                    {children}
                  </h5>
                ),
                p: ({ children }) => (
                  <p className="text-gray-400 leading-relaxed mb-2">
                    {children}
                  </p>
                ),
                strong: ({ children }) => (
                  <strong className="text-gray-200 font-semibold">
                    {children}
                  </strong>
                ),
                ul: ({ children }) => (
                  <ul className="space-y-1.5 ml-3 mb-3">{children}</ul>
                ),
                li: ({ children }) => (
                  <li className="text-gray-400 flex gap-2">
                    <span className="text-gray-600 mt-1.5 text-[6px]">
                      &#9679;
                    </span>
                    <span>{children}</span>
                  </li>
                ),
              }}
            >
              {result.full_memo}
            </ReactMarkdown>
          </div>

          <div className="mt-5 pt-3 border-t border-white/5 flex items-center justify-between">
            <p className="text-xs text-gray-600">
              Full report includes methodology, appendices, and source links.
              Opens in a new tab &mdash; save as PDF via Cmd+P / Ctrl+P.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ChartView({ chartBase64 }) {
  if (!chartBase64) return null;

  return (
    <div className="bg-navy-light border border-border rounded-xl p-4">
      <h3 className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
        Sentiment vs. Price — Historical View
      </h3>
      <img
        src={`data:image/png;base64,${chartBase64}`}
        alt="Uncertainty score vs stock price chart"
        className="w-full rounded-lg"
      />
      <p className="text-xs text-gray-600 mt-2">
        Red line: filing uncertainty score | Green line: stock price | Dashed:
        competitor uncertainty
      </p>
    </div>
  );
}

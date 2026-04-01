import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import base64
import io
from datetime import datetime
from typing import List, Dict, Optional


def generate_sentiment_vs_price_chart(
    ticker: str,
    quarterly_scores: List[Dict],
    price_data: List[Dict],
    competitors: Optional[List[Dict]] = None,
) -> str:
    """
    Generate a dual-axis chart: uncertainty score vs stock price.
    Returns base64-encoded PNG.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#0f1117")
    ax1.set_facecolor("#0f1117")

    # Parse quarterly scores
    q_dates = []
    q_uncertainty = []
    for q in sorted(quarterly_scores, key=lambda x: x["filing_date"]):
        try:
            q_dates.append(datetime.strptime(q["filing_date"], "%Y-%m-%d"))
        except (ValueError, KeyError):
            continue
        q_uncertainty.append(q["uncertainty_score"])

    if not q_dates:
        plt.close()
        return ""

    # Plot uncertainty on left axis
    color_unc = "#ff4757"
    ax1.plot(
        q_dates,
        q_uncertainty,
        color=color_unc,
        marker="o",
        linewidth=2,
        markersize=8,
        label=f"{ticker} Uncertainty",
        zorder=5,
    )
    ax1.fill_between(q_dates, q_uncertainty, alpha=0.1, color=color_unc)
    ax1.set_ylabel("Uncertainty Score", color=color_unc, fontsize=12)
    ax1.tick_params(axis="y", labelcolor=color_unc)

    # Plot competitor uncertainty if available
    if competitors:
        comp_colors = ["#ffa502", "#747d8c", "#70a1ff"]
        for i, comp in enumerate(competitors):
            comp_dates = []
            comp_scores = []
            for q in sorted(comp.get("quarterly_scores", []), key=lambda x: x["filing_date"]):
                try:
                    comp_dates.append(datetime.strptime(q["filing_date"], "%Y-%m-%d"))
                except (ValueError, KeyError):
                    continue
                comp_scores.append(q["uncertainty_score"])
            if comp_dates:
                c = comp_colors[i % len(comp_colors)]
                ax1.plot(
                    comp_dates,
                    comp_scores,
                    color=c,
                    linestyle="--",
                    linewidth=1.5,
                    marker="s",
                    markersize=5,
                    label=f"{comp.get('company', '')} Uncertainty",
                    alpha=0.7,
                )

    # Plot stock price on right axis
    ax2 = ax1.twinx()
    if price_data:
        p_dates = []
        p_prices = []
        for p in price_data:
            try:
                p_dates.append(datetime.strptime(str(p["date"])[:10], "%Y-%m-%d"))
            except (ValueError, KeyError):
                continue
            p_prices.append(p["close"])

        if p_dates:
            color_price = "#00d4aa"
            ax2.plot(
                p_dates,
                p_prices,
                color=color_price,
                linewidth=1.5,
                alpha=0.8,
                label=f"{ticker} Price",
            )
            ax2.set_ylabel("Stock Price ($)", color=color_price, fontsize=12)
            ax2.tick_params(axis="y", labelcolor=color_price)

    # Filing date markers
    for d in q_dates:
        ax1.axvline(x=d, color="#2f3542", linestyle=":", linewidth=0.8, alpha=0.5)

    # Style
    ax1.set_xlabel("Date", color="#a4b0be", fontsize=12)
    ax1.set_title(
        f"{ticker} — Filing Uncertainty vs. Stock Price",
        color="white",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.tick_params(colors="#a4b0be")
    ax2.tick_params(colors="#a4b0be")

    for spine in ax1.spines.values():
        spine.set_color("#2f3542")
    for spine in ax2.spines.values():
        spine.set_color("#2f3542")

    ax1.grid(axis="y", color="#2f3542", alpha=0.3)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper left",
        facecolor="#1e2d3d",
        edgecolor="#2f3542",
        labelcolor="white",
        fontsize=9,
    )

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight", facecolor="#0f1117")
    buffer.seek(0)
    chart_b64 = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close()
    return chart_b64

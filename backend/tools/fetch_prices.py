import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def fetch_price_history(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Fetch daily price history for a ticker."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    if df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    return df[["Date", "Open", "High", "Low", "Close", "Volume"]]


def compute_returns_around_date(
    ticker: str,
    date_str: str,
    windows: Optional[List[int]] = None,
    price_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Given a filing date, compute stock returns, volatility, and volume
    for N days after. Also computes S&P 500 (SPY) for benchmarking.
    """
    if windows is None:
        windows = [30, 60]

    filing_date = pd.to_datetime(date_str)

    if price_df is None:
        price_df = fetch_price_history(ticker, period="3y")
    if price_df.empty:
        return {f"return_{w}d": 0.0 for w in windows}

    spy_df = fetch_price_history("SPY", period="3y")

    result = {}
    for w in windows:
        stock_ret = _get_return(price_df, filing_date, w)
        spy_ret = _get_return(spy_df, filing_date, w)
        result[f"return_{w}d"] = round(stock_ret, 4)
        result[f"sp500_return_{w}d"] = round(spy_ret, 4)
        result[f"outperformed_{w}d"] = bool(stock_ret > spy_ret)

    # Compute volatility around filing date (30 days before and after)
    vol_data = _compute_volatility(price_df, filing_date, window=30)
    result.update(vol_data)

    # Compute volume spike on filing date
    vol_spike = _compute_volume_spike(price_df, filing_date)
    result.update(vol_spike)

    return result


def _get_return(df: pd.DataFrame, start_date: pd.Timestamp, days: int) -> float:
    """Compute return from start_date over N trading days."""
    if df.empty:
        return 0.0

    mask_start = df["Date"] >= start_date
    if not mask_start.any():
        return 0.0

    start_idx = df.loc[mask_start].index[0]
    start_price = df.loc[start_idx, "Close"]

    end_date = start_date + timedelta(days=days)
    mask_end = df["Date"] >= end_date
    if not mask_end.any():
        end_idx = df.index[-1]
    else:
        end_idx = df.loc[mask_end].index[0]

    end_price = df.loc[end_idx, "Close"]
    if start_price == 0:
        return 0.0
    return (end_price - start_price) / start_price


def _compute_volatility(
    df: pd.DataFrame, filing_date: pd.Timestamp, window: int = 30
) -> Dict:
    """
    Compute realized volatility (annualized std of daily returns)
    for the period before and after a filing date.
    """
    if df.empty or len(df) < 20:
        return {"volatility_pre": 0.0, "volatility_post": 0.0, "volatility_change": 0.0}

    df = df.copy()
    df["daily_return"] = df["Close"].pct_change()

    pre_start = filing_date - timedelta(days=window)
    post_end = filing_date + timedelta(days=window)

    pre_mask = (df["Date"] >= pre_start) & (df["Date"] < filing_date)
    post_mask = (df["Date"] >= filing_date) & (df["Date"] <= post_end)

    pre_returns = df.loc[pre_mask, "daily_return"].dropna()
    post_returns = df.loc[post_mask, "daily_return"].dropna()

    # Annualized volatility
    pre_vol = float(pre_returns.std() * np.sqrt(252)) if len(pre_returns) > 2 else 0.0
    post_vol = float(post_returns.std() * np.sqrt(252)) if len(post_returns) > 2 else 0.0

    vol_change = 0.0
    if pre_vol > 0:
        vol_change = (post_vol - pre_vol) / pre_vol

    return {
        "volatility_pre": round(pre_vol, 4),
        "volatility_post": round(post_vol, 4),
        "volatility_change": round(vol_change, 4),
    }


def _compute_volume_spike(df: pd.DataFrame, filing_date: pd.Timestamp) -> Dict:
    """
    Check if trading volume spiked around the filing date
    compared to the 20-day average.
    """
    if df.empty or len(df) < 25:
        return {"volume_avg_20d": 0, "volume_on_filing": 0, "volume_spike_ratio": 0.0}

    mask_before = (df["Date"] < filing_date) & (
        df["Date"] >= filing_date - timedelta(days=30)
    )
    avg_vol = df.loc[mask_before, "Volume"].mean() if mask_before.any() else 0

    mask_filing = df["Date"] >= filing_date
    if not mask_filing.any():
        return {"volume_avg_20d": 0, "volume_on_filing": 0, "volume_spike_ratio": 0.0}

    filing_vol = float(df.loc[mask_filing].iloc[0]["Volume"])

    spike = filing_vol / avg_vol if avg_vol > 0 else 0.0

    return {
        "volume_avg_20d": int(avg_vol),
        "volume_on_filing": int(filing_vol),
        "volume_spike_ratio": round(spike, 2),
    }


def compute_price_summary(ticker: str, period: str = "2y") -> Dict:
    """
    Compute comprehensive price statistics for a ticker.
    Uses the full price history dataset.
    """
    df = fetch_price_history(ticker, period)
    if df.empty:
        return {}

    df["daily_return"] = df["Close"].pct_change()
    df["rolling_vol_30d"] = df["daily_return"].rolling(30).std() * np.sqrt(252)

    return {
        "ticker": ticker,
        "period": period,
        "total_trading_days": len(df),
        "price_start": round(float(df.iloc[0]["Close"]), 2),
        "price_end": round(float(df.iloc[-1]["Close"]), 2),
        "price_high": round(float(df["High"].max()), 2),
        "price_low": round(float(df["Low"].min()), 2),
        "total_return": round(
            float((df.iloc[-1]["Close"] - df.iloc[0]["Close"]) / df.iloc[0]["Close"]),
            4,
        ),
        "avg_daily_return": round(float(df["daily_return"].mean()), 6),
        "daily_return_std": round(float(df["daily_return"].std()), 6),
        "annualized_volatility": round(
            float(df["daily_return"].std() * np.sqrt(252)), 4
        ),
        "avg_volume": int(df["Volume"].mean()),
        "max_volume": int(df["Volume"].max()),
        "sharpe_ratio_approx": round(
            float(
                df["daily_return"].mean()
                / df["daily_return"].std()
                * np.sqrt(252)
            )
            if df["daily_return"].std() > 0
            else 0.0,
            2,
        ),
        "max_drawdown": round(
            float(
                (df["Close"] / df["Close"].cummax() - 1).min()
            ),
            4,
        ),
    }


def fetch_prices_for_companies(
    tickers: List[str], period: str = "2y"
) -> Dict[str, pd.DataFrame]:
    """Fetch price history for multiple tickers."""
    result = {}
    for ticker in tickers:
        result[ticker] = fetch_price_history(ticker, period)
    return result

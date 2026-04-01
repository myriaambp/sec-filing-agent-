import yfinance as yf
import pandas as pd
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
    Given a filing date, compute stock returns for N days after.
    Also computes S&P 500 (SPY) returns for the same period as benchmark.
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


def fetch_prices_for_companies(
    tickers: List[str], period: str = "2y"
) -> Dict[str, pd.DataFrame]:
    """Fetch price history for multiple tickers."""
    result = {}
    for ticker in tickers:
        result[ticker] = fetch_price_history(ticker, period)
    return result

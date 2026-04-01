import requests
import time
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "FilingLens research@filinglens.com"}


def get_cik_for_ticker(ticker: str) -> Optional[str]:
    """Look up the SEC CIK number for a stock ticker."""
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry.get("ticker", "").upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)
    return None


def fetch_recent_filings(
    ticker: str, form_type: str = "10-Q", num_filings: int = 6
) -> List[Dict]:
    """
    Fetch recent filings metadata for a company from EDGAR submissions API.
    Returns list of dicts with: period, filing_date, accession_number, primary_doc.
    """
    cik = get_cik_for_ticker(ticker)
    if not cik:
        return []

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    company_name = data.get("name", ticker)
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    periods = recent.get("reportDate", [])

    results = []
    for i, form in enumerate(forms):
        if form == form_type and len(results) < num_filings:
            results.append({
                "period": periods[i] if i < len(periods) else "",
                "filing_date": dates[i] if i < len(dates) else "",
                "accession_number": accessions[i] if i < len(accessions) else "",
                "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
                "company_name": company_name,
                "cik": cik,
            })
    return results


def fetch_filing_text(accession_number: str, cik: str, primary_doc: str) -> str:
    """
    Fetch the actual text content of a filing.
    Focuses on MD&A and Risk Factors sections.
    """
    acc_no_dashes = accession_number.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_no_dashes}/{primary_doc}"

    time.sleep(0.12)
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return ""

    soup = BeautifulSoup(resp.content, "html.parser")

    for tag in soup(["script", "style", "img"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    sections = _extract_key_sections(text)
    return sections


def _extract_key_sections(text: str) -> str:
    """
    Extract MD&A and Risk Factors sections from filing text.
    Skips table-of-contents matches by looking for the last (longest) match.
    """
    text_lower = text.lower()
    extracted = []

    def _find_section(patterns, next_item_pattern, max_len=15000):
        """Find a section, skipping TOC entries by picking the match with most content."""
        for pattern in patterns:
            matches = list(re.finditer(pattern, text_lower))
            # Try matches from last to first — the actual section body
            # tends to appear after the TOC
            for match in reversed(matches):
                start = match.start()
                next_item = re.search(next_item_pattern, text_lower[start + 200:])
                if next_item:
                    end = start + 200 + next_item.start()
                else:
                    end = start + max_len
                section = text[start : min(end, start + max_len)]
                # Skip TOC entries (very short sections)
                if len(section.strip()) > 500:
                    return section
        return None

    # Risk Factors (Item 1A)
    risk = _find_section(
        [r"item\s+1a[\.\s\-\:]+risk\s+factors", r"risk\s+factors"],
        r"\bitem\s+[1-9]\w?\b",
        15000,
    )
    if risk:
        extracted.append(risk)

    # MD&A (Item 7 for 10-K, Item 2 for 10-Q)
    mda = _find_section(
        [
            r"item\s+7[\.\s\-\:]+management.s\s+discussion",
            r"item\s+2[\.\s\-\:]+management.s\s+discussion",
            r"management.s\s+discussion\s+and\s+analysis",
        ],
        r"\bitem\s+[3-9]\b",
        20000,
    )
    if mda:
        extracted.append(mda)

    if not extracted:
        # Fallback: return a large chunk from the middle of the filing
        mid = len(text) // 4
        extracted.append(text[mid : mid + 20000])

    return "\n\n---\n\n".join(extracted)


def fetch_filings_for_companies(
    tickers: List[str], form_type: str = "10-Q", num_filings: int = 4
) -> Dict[str, List[Dict]]:
    """Fetch filings for multiple companies. Returns dict keyed by ticker."""
    result = {}
    for ticker in tickers:
        time.sleep(0.12)
        result[ticker] = fetch_recent_filings(ticker, form_type, num_filings)
    return result

"""Fetch Form 4 insider transactions for tracked individuals and update investors.json.

Form 4 reports insider transactions (buys/sells/gifts/options) by company officers,
directors, and 10%+ owners. This script extracts recent Form 4 filings for each
tracked individual and aggregates them into a holdings-like structure.

Usage:
    python scripts/fetch_form4.py

Required env:
    EDGAR_USER_AGENT   "Whale Watch <your-email@example.com>"
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[1]
INV_PATH = ROOT / "data" / "investors.json"

UA = os.environ.get("EDGAR_USER_AGENT") or "Whale Watch dev@example.com"

session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})

SEC_RATE_SLEEP = 0.15
SEC_TIMEOUT = 60
SEC_RETRIES = 3
MAX_FORM4_FETCH = 10  # max recent Form 4 filings to process per investor


def sec_get(url: str, *, timeout: int = SEC_TIMEOUT) -> requests.Response:
    last: Exception | None = None
    for attempt in range(SEC_RETRIES):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code >= 500:
                raise requests.HTTPError(f"{r.status_code}", response=r)
            r.raise_for_status()
            return r
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
            if isinstance(e, requests.HTTPError) and e.response is not None and 400 <= e.response.status_code < 500:
                raise
            last = e
            wait = 2 ** attempt
            print(f"    retry {attempt+1}/{SEC_RETRIES}: {type(e).__name__}, sleeping {wait}s", file=sys.stderr)
            time.sleep(wait)
    assert last is not None
    raise last


def _strip_ns(xml_text: str) -> str:
    """Remove XML namespaces for easier ElementTree parsing."""
    xml_text = re.sub(r'\sxmlns(:\w+)?="[^"]*"', "", xml_text)
    xml_text = re.sub(r"<(/?)\w+:", r"<\1", xml_text)
    xml_text = re.sub(r'\s\w+:(\w+)(\s*=)', r' \1\2', xml_text)
    return xml_text


def get_form4_filings(cik: str, max_count: int = MAX_FORM4_FETCH) -> list[dict]:
    """Get recent Form 4 filing metadata for a CIK from SEC submissions API."""
    cik_padded = str(int(cik)).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    try:
        r = sec_get(url)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return []
        raise

    sub = r.json()
    recent = sub.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accs = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    primary = recent.get("primaryDocument", [])

    filings = []
    cik_int = int(cik_padded)
    for i, f in enumerate(forms):
        if f == "4" and len(filings) < max_count:
            filings.append({
                "accession": accs[i],
                "filing_date": dates[i],
                "primary_doc": primary[i],
                "cik_int": cik_int,
            })
    return filings


def fetch_form4_xml(filing: dict) -> bytes | None:
    """Download the source XML for a Form 4 filing (not the HTML rendition)."""
    cik_int = filing["cik_int"]
    acc_no = filing["accession"].replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no}"

    # Get filing index to find the actual .xml file
    try:
        r = sec_get(f"{base}/index.json")
        items = r.json().get("directory", {}).get("item", [])
    except requests.RequestException:
        return None

    # Find the .xml file (not the XSL-transformed HTML version)
    xml_file = None
    for item in items:
        name = item.get("name", "")
        if name.lower().endswith(".xml") and "xsl" not in name.lower():
            xml_file = name
            break
    if not xml_file:
        return None

    try:
        r = sec_get(f"{base}/{xml_file}")
        return r.content
    except requests.RequestException:
        return None


def parse_form4_transactions(xml_bytes: bytes) -> dict:
    """Parse a Form 4 XML and return summary of transactions by ticker.
    Returns {ticker, transactions: [{date, action, shares, price, value, ...}]}."""
    if not xml_bytes:
        return {}

    text = _strip_ns(xml_bytes.decode("utf-8", errors="ignore"))
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}

    # Helper: get text from element, checking for <value> child
    def get_val(parent, path):
        el = parent.find(path)
        if el is None:
            return ""
        # Check for <value> sub-element (SEC EDGAR XML convention)
        val_el = el.find("value")
        if val_el is not None and val_el.text:
            return val_el.text.strip()
        return (el.text or "").strip()

    # Get issuer ticker
    ticker = get_val(root, "issuerTradingSymbol")
    if not ticker:
        ticker = get_val(root, "issuer/issuerTradingSymbol")
    if not ticker:
        # Derive from issuer CIK/name
        issuer_cik = get_val(root, "issuer/issuerCik")
        issuer_name = get_val(root, "issuer/issuerName")
        ticker = issuer_name.split()[0][:8].upper().replace(",", "").replace(".", "") if issuer_name else ""

    result = {"ticker": ticker, "transactions": []}

    # Process non-derivative transactions
    for tx in root.findall(".//nonDerivativeTransaction"):
        title = get_val(tx, "securityTitle")
        date = get_val(tx, "transactionDate")
        code = get_val(tx, "transactionCoding/transactionCode")
        shares_str = get_val(tx, "transactionAmounts/transactionShares")
        price_str = get_val(tx, "transactionAmounts/transactionPricePerShare")
        acq_disp = get_val(tx, "transactionAmounts/transactionAcquiredDisposedCode")
        shares_owned_str = get_val(tx, "postTransactionAmounts/sharesOwnedFollowingTransaction")

        try:
            shares = float(shares_str) if shares_str else 0
        except ValueError:
            shares = 0
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            price = 0
        try:
            shares_owned = float(shares_owned_str) if shares_owned_str else 0
        except ValueError:
            shares_owned = 0

        if shares > 0 and acq_disp in ("A", "D"):
            is_buy = acq_disp == "A"
            if code in ("M", "F"):
                continue  # skip option exercises and tax withholds
            result["transactions"].append({
                "date": date,
                "ticker": ticker,
                "security": title,
                "code": code or "?",
                "action": "buy" if is_buy else "sell",
                "shares": shares,
                "price": price,
                "value": round(shares * price, 2) if price > 0 else 0,
                "shares_owned_after": shares_owned,
            })
            if code == "A":
                result["transactions"][-1]["note"] = "award"
            if code == "P":
                result["transactions"][-1]["note"] = "open_market_purchase"

    return result


def aggregate_form4(investor: dict) -> None:
    """Fetch and aggregate Form 4 data for an investor, update in-place."""
    cik = investor.get("cik", "")
    if not cik:
        print(f"  no CIK — skipping")
        return

    filings = get_form4_filings(cik)
    if not filings:
        print(f"  no Form 4 filings found")
        return

    print(f"  found {len(filings)} recent Form 4 filings")

    # Aggregate by ticker
    ticker_data: dict[str, dict] = {}

    for filing in filings[:MAX_FORM4_FETCH]:
        time.sleep(SEC_RATE_SLEEP)
        xml = fetch_form4_xml(filing)
        parsed = parse_form4_transactions(xml)

        tkr = parsed.get("ticker", "")
        if not tkr:
            continue

        if tkr not in ticker_data:
            ticker_data[tkr] = {
                "ticker": tkr,
                "name": "",
                "cusip": "",
                "buy_shares": 0,
                "sell_shares": 0,
                "buy_value": 0,
                "sell_value": 0,
                "latest_date": "",
                "shares_owned": 0,
                "recent_tx": [],
            }

        td = ticker_data[tkr]
        for tx in parsed.get("transactions", []):
            if tx["date"] > td["latest_date"]:
                td["latest_date"] = tx["date"]
                td["shares_owned"] = tx.get("shares_owned_after", 0)
            if tx["action"] == "buy":
                td["buy_shares"] += tx["shares"]
                td["buy_value"] += tx["value"]
            else:
                td["sell_shares"] += tx["shares"]
                td["sell_value"] += tx["value"]
            if len(td["recent_tx"]) < 5:
                td["recent_tx"].append(tx)

    # Convert to holdings format
    holdings = []
    for tkr, td in ticker_data.items():
        net_shares = td["buy_shares"] - td["sell_shares"]
        net_value = td["buy_value"] - td["sell_value"]
        holdings.append({
            "cusip": "",
            "name": f"{tkr} ({investor.get('issuer_ticker', '')})",
            "ticker": tkr,
            "value_usd": round(max(0, net_value), 2),
            "shares": max(0, int(net_shares)),
            "weight": 100.0 if len(ticker_data) == 1 else round(100.0 / max(1, len(ticker_data)), 2),
            "source": "form4",
            "buy_count": td["buy_shares"],
            "sell_count": td["sell_shares"],
            "latest_filing": td["latest_date"],
        })

    investor["holdings"] = holdings
    investor["holdings_count"] = len(holdings)
    investor["total_value_usd"] = round(sum(h["value_usd"] for h in holdings), 2)
    if filings:
        investor["filing_date"] = filings[0]["filing_date"]
        investor["period_of_report"] = filings[0]["filing_date"]
    print(f"    OK  {len(holdings)} tickers parsed")


def main() -> int:
    if "@" not in UA:
        print("warning: EDGAR_USER_AGENT should include contact email", file=sys.stderr)

    inv_data = json.loads(INV_PATH.read_text(encoding="utf-8"))

    for inv in inv_data["investors"]:
        if inv.get("source") != "form4":
            continue
        print(f"→ {inv['name']} ({inv.get('fund','')}) — CIK {inv.get('cik','')}")
        try:
            aggregate_form4(inv)
        except Exception as e:
            print(f"    ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        time.sleep(SEC_RATE_SLEEP)

    INV_PATH.write_text(
        json.dumps(inv_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nwrote {INV_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

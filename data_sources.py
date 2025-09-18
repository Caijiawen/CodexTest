"""Data retrieval utilities for the crypto research dashboard."""
from __future__ import annotations

import datetime as dt
import math
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

HEADERS = {"User-Agent": USER_AGENT}


class DataFetchError(RuntimeError):
    """Raised when a remote data source cannot be retrieved."""


@dataclass
class MarketCapSnapshot:
    btc_price: float
    btc_market_cap: float
    gold_price: float
    gold_market_cap: float

    @property
    def btc_vs_gold_ratio(self) -> float:
        if not self.gold_market_cap:
            return math.nan
        return self.btc_market_cap / self.gold_market_cap

    @property
    def gold_vs_btc_upside(self) -> float:
        if not self.btc_market_cap:
            return math.nan
        return self.gold_market_cap / self.btc_market_cap


TOTAL_ABOVE_GROUND_GOLD_TONNES = 205_000  # conservative estimate
TONNES_TO_TROY_OZ = 32_150.7466


def _request_json(url: str, *, headers: Optional[Dict[str, str]] = None) -> dict:
    resp = requests.get(url, headers=headers or HEADERS, timeout=30)
    if resp.status_code != 200:
        raise DataFetchError(f"Failed to fetch {url} (status {resp.status_code})")
    try:
        return resp.json()
    except ValueError as exc:
        raise DataFetchError(f"Invalid JSON payload from {url}") from exc


def _get_text(url: str, *, headers: Optional[Dict[str, str]] = None) -> str:
    resp = requests.get(url, headers=headers or HEADERS, timeout=30)
    if resp.status_code != 200:
        raise DataFetchError(f"Failed to fetch {url} (status {resp.status_code})")
    return resp.text


def fetch_global_m2() -> pd.DataFrame:
    """Return global broad money (M2) from the World Bank API."""
    url = (
        "https://api.worldbank.org/v2/country/WLD/indicator/"
        "FM.LBL.BMNY.CN?format=json&per_page=600"
    )
    payload = _request_json(url)
    records = payload[1]
    rows: List[Dict[str, float]] = []
    for entry in records:
        value = entry.get("value")
        year = entry.get("date")
        if value is None or year is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        rows.append({"year": int(year), "value": numeric})
    df = pd.DataFrame(rows)
    if df.empty:
        raise DataFetchError("World Bank M2 dataset returned no usable data")
    df.sort_values("year", inplace=True)
    df["value_trillion"] = df["value"] / 1e12
    return df


def fetch_market_caps() -> MarketCapSnapshot:
    """Return the latest BTC and gold market capitalisation figures."""
    btc_url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd&include_market_cap=true"
    )
    btc_payload = _request_json(btc_url)
    btc_data = btc_payload.get("bitcoin")
    if not btc_data:
        raise DataFetchError("CoinGecko response missing bitcoin data")
    btc_price = float(btc_data["usd"])
    btc_cap = float(btc_data["usd_market_cap"])

    gold_payload = _request_json("https://data-asg.goldprice.org/dbXRates/USD")
    items = gold_payload.get("items")
    if not items:
        raise DataFetchError("Gold price feed missing items list")
    gold_price = float(items[0]["xauPrice"])  # price per troy ounce in USD
    total_oz = TOTAL_ABOVE_GROUND_GOLD_TONNES * TONNES_TO_TROY_OZ
    gold_cap = gold_price * total_oz

    return MarketCapSnapshot(
        btc_price=btc_price,
        btc_market_cap=btc_cap,
        gold_price=gold_price,
        gold_market_cap=gold_cap,
    )


def _paginate_coinmetrics(base_url: str) -> Iterable[dict]:
    next_token: Optional[str] = None
    while True:
        url = base_url
        if next_token:
            url += f"&next_page_token={next_token}"
        payload = _request_json(url)
        data = payload.get("data", [])
        for row in data:
            yield row
        next_token = payload.get("next_page_token")
        if not next_token:
            break


def fetch_mvrv_timeseries(start: dt.date) -> pd.DataFrame:
    """Fetch daily MVRV ratio, market cap and realised cap from CoinMetrics."""
    today = dt.date.today()
    base_url = (
        "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
        "?assets=btc&metrics=CapMrktCurUSD,CapRealUSD,CapMVRVCur"
        f"&frequency=1d&start_time={start.isoformat()}&end_time={today.isoformat()}"
    )
    rows: List[Dict[str, object]] = []
    for row in _paginate_coinmetrics(base_url):
        try:
            timestamp = dt.datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
        except (KeyError, ValueError) as exc:
            raise DataFetchError("Invalid timestamp in CoinMetrics payload") from exc
        rows.append(
            {
                "date": timestamp.date(),
                "cap_market_usd": float(row["CapMrktCurUSD"]),
                "cap_realized_usd": float(row["CapRealUSD"]),
                "mvrv_ratio": float(row["CapMVRVCur"]),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        raise DataFetchError("CoinMetrics returned no data for MVRV")
    df.sort_values("date", inplace=True)
    return df


def fetch_ahr_timeseries() -> pd.DataFrame:
    """Scrape the AHR999 indicator from CaiZi."""
    url = "https://www.caizi.fun/trade/data/ahr"
    html = _get_text(url)
    anchor = 'name:\\"AHR999'
    anchor_idx = html.find(anchor)
    if anchor_idx == -1:
        raise DataFetchError("Unable to locate AHR999 series in CaiZi page")

    data_key = "data:["
    labels_key = "labels:["

    data_start = html.find(data_key, anchor_idx)
    labels_start = html.find(labels_key, anchor_idx)
    if data_start == -1 or labels_start == -1:
        raise DataFetchError("Missing data or labels block for AHR999")

    data_end = html.find(']', data_start)
    labels_end = html.find(']', labels_start)
    if data_end == -1 or labels_end == -1:
        raise DataFetchError("Malformed AHR999 script section")

    raw_values = [
        v.strip()
        for v in html[data_start + len(data_key) : data_end].split(',')
        if v.strip()
    ]
    raw_labels = [
        label.strip().strip('"')
        for label in html[labels_start + len(labels_key) : labels_end].split(',')
        if label.strip()
    ]
    if len(raw_values) != len(raw_labels):
        raise DataFetchError("Mismatched label/value counts in AHR data")
    dates = pd.to_datetime(raw_labels, format="%Y-%m-%d", errors="coerce")
    values = [float(v) for v in raw_values]
    df = pd.DataFrame({"date": dates, "ahr": values})
    df.dropna(inplace=True)
    df.sort_values("date", inplace=True)
    return df


def _proxied_farside_url(path: str) -> str:
    return f"https://r.jina.ai/https://farside.co.uk/{path.strip('/')}/"


def _parse_farside_daily_flows(text: str) -> pd.DataFrame:
    rows: List[Tuple[str, float]] = []
    date_pattern = re.compile(r"^\|\s*(\d{2} [A-Za-z]{3} \d{4})\s*\|")
    for line in text.splitlines():
        if not line.strip().startswith('|'):
            continue
        match = date_pattern.match(line)
        if not match:
            continue
        date_str = match.group(1)
        parts = [p.strip() for p in line.strip('|').split('|')]
        if not parts:
            continue
        total_str = parts[-1]
        value = _to_number(total_str)
        rows.append((date_str, value))
    df = pd.DataFrame(rows, columns=["date_str", "total_flow"])
    if df.empty:
        raise DataFetchError("No daily ETF flow rows found in Farside table")
    df["date"] = pd.to_datetime(df["date_str"], format="%d %b %Y", errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["total_flow"] = df["total_flow"].astype(float)
    return df


def fetch_btc_etf_flows() -> pd.DataFrame:
    text = _get_text(_proxied_farside_url("btc"))
    return _parse_farside_daily_flows(text)


def fetch_eth_etf_flows() -> pd.DataFrame:
    text = _get_text(_proxied_farside_url("eth"))
    return _parse_farside_daily_flows(text)


def _to_number(value: str) -> float:
    value = value.strip()
    if not value or value == '-':
        return float("nan")
    negative = value.startswith('(') and value.endswith(')')
    cleaned = value.strip('()').replace(',', '').replace('$', '')
    cleaned = cleaned.replace('+', '').replace('SOL', '').replace('ETH', '').replace('BTC', '')
    cleaned = cleaned.replace('%', '')
    multipliers = {"m": 1e6, "b": 1e9}
    suffix = cleaned[-1].lower() if cleaned[-1].lower() in multipliers else ''
    if suffix:
        cleaned_num = cleaned[:-1]
    else:
        cleaned_num = cleaned
    try:
        number = float(cleaned_num)
    except ValueError:
        return float("nan")
    if suffix:
        number *= multipliers[suffix]
    if negative:
        number = -number
    return number


def fetch_btc_treasury_holdings(top_n: int = 15) -> pd.DataFrame:
    text = _get_text(_proxied_farside_url("bitcoin-treasury-companies"))
    rows: List[List[str]] = []
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        parts = [p.strip() for p in line.strip('|').split('|')]
        if len(parts) < 9 or parts[0] in {"Ticker", ""}:
            continue
        rows.append(parts[:9])
    if not rows:
        raise DataFetchError("No BTC treasury rows parsed")
    df = pd.DataFrame(
        rows,
        columns=[
            "Ticker",
            "Name",
            "Type",
            "Country",
            "Currency",
            "Price",
            "Day Change",
            "Market Cap (m)",
            "BTC Holdings",
        ],
    )
    df["BTC Holdings"] = df["BTC Holdings"].apply(_to_number)
    df.sort_values("BTC Holdings", ascending=False, inplace=True)
    return df.head(top_n)


def fetch_eth_treasury_holdings(top_n: int = 15) -> pd.DataFrame:
    text = _get_text("https://r.jina.ai/https://ethereumtreasuries.net/")
    rows: List[List[str]] = []
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        parts = [p.strip() for p in line.strip('|').split('|')]
        if len(parts) < 8 or parts[0] == "Company Name":
            continue
        rows.append(parts[:8])
    if not rows:
        raise DataFetchError("No Ethereum treasury data parsed")
    df = pd.DataFrame(
        rows,
        columns=[
            "Company",
            "Ticker",
            "Flag",
            "ETH Held",
            "Value (USD)",
            "Last Update",
            "Chart",
            "Description",
        ],
    )
    df["ETH Held"] = df["ETH Held"].apply(_to_number)
    df.sort_values("ETH Held", ascending=False, inplace=True)
    return df.head(top_n)


def fetch_sol_treasury_holdings(top_n: int = 15) -> pd.DataFrame:
    text = _get_text("https://r.jina.ai/https://www.coingecko.com/en/treasuries/solana")
    rows: List[List[str]] = []
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        parts = [p.strip() for p in line.strip('|').split('|')]
        if len(parts) < 8 or parts[0] == "Company":
            continue
        # Some rows include rank numbers at index 0
        if parts[0].isdigit():
            parts = parts[1:]
        if len(parts) < 7:
            continue
        rows.append(parts[:7])
    if not rows:
        raise DataFetchError("No Solana treasury table detected")
    df = pd.DataFrame(
        rows,
        columns=[
            "Company",
            "Type",
            "Change",
            "SOL Held",
            "Value (USD)",
            "Share of Supply",
            "Links",
        ],
    )
    df["SOL Held"] = df["SOL Held"].apply(_to_number)
    df.sort_values("SOL Held", ascending=False, inplace=True)
    return df.head(top_n)


__all__ = [
    "DataFetchError",
    "MarketCapSnapshot",
    "fetch_global_m2",
    "fetch_market_caps",
    "fetch_mvrv_timeseries",
    "fetch_ahr_timeseries",
    "fetch_btc_etf_flows",
    "fetch_eth_etf_flows",
    "fetch_btc_treasury_holdings",
    "fetch_eth_treasury_holdings",
    "fetch_sol_treasury_holdings",
]

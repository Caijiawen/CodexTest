import datetime as dt
from typing import Tuple

import altair as alt
import pandas as pd
import streamlit as st

from data_sources import (
    DataFetchError,
    MarketCapSnapshot,
    fetch_ahr_timeseries,
    fetch_btc_etf_flows,
    fetch_btc_treasury_holdings,
    fetch_eth_etf_flows,
    fetch_eth_treasury_holdings,
    fetch_global_m2,
    fetch_market_caps,
    fetch_mvrv_timeseries,
    fetch_sol_treasury_holdings,
)

st.set_page_config(
    page_title="Crypto Macro Dashboard",
    layout="wide",
    page_icon="📈",
)


st.title("📊 Crypto Macro & ETF Dashboard")
st.markdown(
    "该仪表盘聚合全球宏观流动性、比特币估值、ETF 资金流以及数字资产公司持仓数据，帮助快速洞察市场趋势。"
)


@st.cache_data(ttl=3600)
def load_global_m2() -> pd.DataFrame:
    return fetch_global_m2()


@st.cache_data(ttl=1800)
def load_market_caps() -> MarketCapSnapshot:
    return fetch_market_caps()


@st.cache_data(ttl=1800)
def load_mvrv() -> pd.DataFrame:
    start = dt.date(2013, 1, 1)
    return fetch_mvrv_timeseries(start)


@st.cache_data(ttl=1800)
def load_ahr() -> pd.DataFrame:
    return fetch_ahr_timeseries()


@st.cache_data(ttl=900)
def load_btc_etf_flows() -> pd.DataFrame:
    return fetch_btc_etf_flows()


@st.cache_data(ttl=900)
def load_eth_etf_flows() -> pd.DataFrame:
    return fetch_eth_etf_flows()


@st.cache_data(ttl=3600)
def load_btc_treasuries() -> pd.DataFrame:
    return fetch_btc_treasury_holdings(15)


@st.cache_data(ttl=3600)
def load_eth_treasuries() -> pd.DataFrame:
    return fetch_eth_treasury_holdings(15)


@st.cache_data(ttl=3600)
def load_sol_treasuries() -> pd.DataFrame:
    return fetch_sol_treasury_holdings(15)


def render_global_m2():
    st.subheader("1. 全球 M2（广义货币）历史走势")
    try:
        df = load_global_m2()
    except DataFetchError as exc:
        st.error(f"无法获取世界银行数据：{exc}")
        return

    chart = (
        alt.Chart(df)
        .mark_line(point=False)
        .encode(x="year:O", y=alt.Y("value_trillion", title="Broad Money (万亿美元)"))
        .properties(height=380)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("数据来源：World Bank（指标 FM.LBL.BMNY.CN，单位为当前币值的广义货币）")


def _format_number(value: float) -> str:
    if pd.isna(value):
        return "-"
    if abs(value) >= 1e12:
        return f"{value / 1e12:.2f} 万亿"
    if abs(value) >= 1e9:
        return f"{value / 1e9:.2f} 十亿"
    if abs(value) >= 1e6:
        return f"{value / 1e6:.2f} 百万"
    return f"{value:,.0f}"


def render_market_caps():
    st.subheader("2. 比特币与黄金市值对比")
    try:
        snapshot = load_market_caps()
    except DataFetchError as exc:
        st.error(f"无法获取市值数据：{exc}")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("BTC 价格 (USD)", f"${snapshot.btc_price:,.0f}")
    col2.metric("BTC 市值", _format_number(snapshot.btc_market_cap))
    col3.metric("黄金市值", _format_number(snapshot.gold_market_cap))

    ratio = snapshot.gold_vs_btc_upside
    st.markdown(
        f"**黄金市值约为比特币的 {ratio:.2f} 倍**，若比特币市值追平黄金，理论上仍有 {ratio - 1:.2f} 倍的上升空间。"
    )
    st.caption("BTC 市值来自 CoinGecko；黄金价格来自 goldprice.org，假设全球地上黄金约 20.5 万吨。")


def render_btc_valuations():
    st.subheader("3. 比特币链上估值指标")
    col1, col2 = st.columns(2)

    with col1:
        try:
            mvrv = load_mvrv()
        except DataFetchError as exc:
            st.error(f"无法获取 CoinMetrics 数据：{exc}")
        else:
            mvrv_chart = (
                alt.Chart(mvrv)
                .mark_line()
                .encode(x="date:T", y=alt.Y("mvrv_ratio", title="MVRV Ratio"))
                .properties(height=320)
            )
            st.altair_chart(mvrv_chart, use_container_width=True)
            latest = mvrv.iloc[-1]
            st.write(
                f"- 最新 MVRV 为 **{latest['mvrv_ratio']:.2f}**，市场价值 / 实现价值 = {latest['cap_market_usd'] / latest['cap_realized_usd']:.2f}"
            )

    with col2:
        try:
            ahr = load_ahr()
        except DataFetchError as exc:
            st.error(f"无法获取 AHR999 指标：{exc}")
        else:
            base = alt.Chart(ahr).mark_line(color="#fd625e").encode(x="date:T", y="ahr:Q")
            lines = (
                base
                + alt.Chart(pd.DataFrame({"value": [0.45]})).mark_rule(color="#2ab57d", strokeDash=[4, 4]).encode(y="value")
                + alt.Chart(pd.DataFrame({"value": [1.2]})).mark_rule(color="#5156be", strokeDash=[4, 4]).encode(y="value")
            )
            st.altair_chart(lines.properties(height=320), use_container_width=True)
            st.write("- AHR999 < 0.45 常被视为抄底区间；0.45-1.2 适合定投；超过 1.2 需谨慎。")

    st.caption("MVRV 数据来自 CoinMetrics；AHR999 指标来自 菜籽数据。")


def render_etf_flows():
    st.subheader("4. BTC / ETH 现货 ETF 资金流向")
    tabs = st.tabs(["BTC ETF", "ETH ETF"])

    with tabs[0]:
        try:
            btc_flows = load_btc_etf_flows()
        except DataFetchError as exc:
            st.error(f"无法获取 BTC ETF 数据：{exc}")
        else:
            chart = (
                alt.Chart(btc_flows)
                .mark_bar(color="#fd625e")
                .encode(x="date:T", y=alt.Y("total_flow", title="净流入 (百万美元)"))
                .properties(height=320)
            )
            st.altair_chart(chart, use_container_width=True)
            st.dataframe(btc_flows.sort_values("date", ascending=False).head(10), use_container_width=True)
            st.caption("数据来源：Farside Investors，净流入按每日美元口径统计。")

    with tabs[1]:
        try:
            eth_flows = load_eth_etf_flows()
        except DataFetchError as exc:
            st.error(f"无法获取 ETH ETF 数据：{exc}")
        else:
            chart = (
                alt.Chart(eth_flows)
                .mark_bar(color="#2ab57d")
                .encode(x="date:T", y=alt.Y("total_flow", title="净流入 (百万美元)"))
                .properties(height=320)
            )
            st.altair_chart(chart, use_container_width=True)
            st.dataframe(eth_flows.sort_values("date", ascending=False).head(10), use_container_width=True)
            st.caption("数据来源：Farside Investors，净流入按每日美元口径统计。")


def render_treasury_tables():
    st.subheader("5. 公司层面的数字资产持仓（DAT）")
    tabs = st.tabs(["BTC", "ETH", "SOL"])

    with tabs[0]:
        try:
            btc_df = load_btc_treasuries()
        except DataFetchError as exc:
            st.error(f"无法获取 BTC 公司持仓数据：{exc}")
        else:
            st.dataframe(btc_df, use_container_width=True, hide_index=True)
            total = btc_df["BTC Holdings"].sum()
            st.write(f"样本中前 15 家公司合计持有 **{total:,.0f} BTC**。")
            st.caption("数据来源：Farside Investors Digital Asset Treasuries。")

    with tabs[1]:
        try:
            eth_df = load_eth_treasuries()
        except DataFetchError as exc:
            st.error(f"无法获取 ETH 公司持仓数据：{exc}")
        else:
            st.dataframe(eth_df, use_container_width=True, hide_index=True)
            total = eth_df["ETH Held"].sum()
            st.write(f"样本中前 15 家机构合计持有 **{total:,.0f} ETH**。")
            st.caption("数据来源：ethereumtreasuries.net。")

    with tabs[2]:
        try:
            sol_df = load_sol_treasuries()
        except DataFetchError as exc:
            st.error(f"无法获取 SOL 公司持仓数据：{exc}")
        else:
            st.dataframe(sol_df, use_container_width=True, hide_index=True)
            total = sol_df["SOL Held"].sum()
            st.write(f"样本中前 15 家机构合计持有约 **{total:,.0f} SOL**。")
            st.caption("数据来源：CoinGecko Treasuries 页面。")


render_global_m2()
st.divider()
render_market_caps()
st.divider()
render_btc_valuations()
st.divider()
render_etf_flows()
st.divider()
render_treasury_tables()

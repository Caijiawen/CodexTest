我想要做一个 crypto  投资研究仪表盘网站， 辅助我做投资决策。
我需要以下仪表盘：
1. 全球 M2 的历史数据
2. btc的市值， 黄金的市值 ， btc 相对黄金的上升空间
3. btc 的估值指标 （比如 mvrv ratio , ahr99 ratio)
4. btc , eth 的 etf 流入流出数据
5. btc , eth , sol 的币股（DAT） 公司买盘

---

## 实现说明

该仓库现在包含一个基于 Streamlit 的网页应用 `app.py`，整合了以上所列的五类数据。主要特性：

- **全球广义货币（M2）**：来自世界银行 API，按年份绘制广义货币规模。
- **比特币 vs 黄金市值**：实时获取 CoinGecko 的比特币价格与市值、goldprice 的黄金价格，并估算黄金总市值及相对估值空间。
- **链上估值指标**：使用 CoinMetrics API 获取 BTC MVRV、Realized Cap，并抓取菜籽数据的 AHR999 指标。
- **ETF 资金流**：抓取 Farside Investors 发布的 BTC / ETH 现货 ETF 每日净流入表格。
- **数字资产公司持仓（DAT）**：分别整合 Farside、EthereumTreasuries.net、CoinGecko 的 BTC / ETH / SOL 公司持仓榜。

所有数据请求均带缓存，默认缓存时长 15~60 分钟，以减少 API 调用并提升页面响应速度。

## 本地运行

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 启动应用：

```bash
streamlit run app.py
```

Streamlit 启动后会输出访问地址（默认 `http://localhost:8501`）。如在远程环境运行，可通过端口转发或 VSCode Remote 隧道访问。

> 注意：应用依赖外部公开 API，若运行环境无法联网将无法展示数据。

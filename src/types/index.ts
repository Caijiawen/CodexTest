export interface MarketCapData {
  btc_price: number;
  btc_market_cap: number;
  gold_price: number;
  gold_market_cap: number;
  gold_vs_btc_upside: number;
}

export interface GlobalM2Data {
  year: number;
  value_trillion: number;
}

export interface MVRVData {
  date: string;
  mvrv_ratio: number;
  cap_market_usd: number;
  cap_realized_usd: number;
}

export interface AHRData {
  date: string;
  ahr: number;
}

export interface ETFFlowData {
  date: string;
  total_flow: number;
}

export interface TreasuryHolding {
  company: string;
  ticker?: string;
  holdings: number;
  value_usd?: string;
  type?: string;
  country?: string;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
}
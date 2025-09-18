import { 
  MarketCapData, 
  GlobalM2Data, 
  MVRVData, 
  AHRData, 
  ETFFlowData, 
  TreasuryHolding,
  ApiResponse 
} from '../types';

const API_BASE = '/api';

// Mock data for demonstration - in production, these would call real APIs
export const mockGlobalM2Data: GlobalM2Data[] = [
  { year: 2020, value_trillion: 95.2 },
  { year: 2021, value_trillion: 108.7 },
  { year: 2022, value_trillion: 112.3 },
  { year: 2023, value_trillion: 118.9 },
  { year: 2024, value_trillion: 125.4 },
];

export const mockMarketCapData: MarketCapData = {
  btc_price: 97234,
  btc_market_cap: 1.92e12,
  gold_price: 2650,
  gold_market_cap: 17.4e12,
  gold_vs_btc_upside: 9.06
};

export const mockMVRVData: MVRVData[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  mvrv_ratio: 2.1 + Math.sin(i * 0.2) * 0.5 + Math.random() * 0.3,
  cap_market_usd: 1.9e12 + Math.random() * 0.2e12,
  cap_realized_usd: 0.9e12 + Math.random() * 0.1e12,
}));

export const mockAHRData: AHRData[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  ahr: 0.8 + Math.sin(i * 0.15) * 0.3 + Math.random() * 0.2,
}));

export const mockBTCETFData: ETFFlowData[] = Array.from({ length: 20 }, (_, i) => ({
  date: new Date(Date.now() - (19 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  total_flow: (Math.random() - 0.5) * 1000,
}));

export const mockETHETFData: ETFFlowData[] = Array.from({ length: 20 }, (_, i) => ({
  date: new Date(Date.now() - (19 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  total_flow: (Math.random() - 0.5) * 500,
}));

export const mockBTCTreasuryData: TreasuryHolding[] = [
  { company: 'MicroStrategy', ticker: 'MSTR', holdings: 331200, value_usd: '$32.2B', type: 'Software', country: 'US' },
  { company: 'Tesla', ticker: 'TSLA', holdings: 9720, value_usd: '$945M', type: 'Automotive', country: 'US' },
  { company: 'Coinbase', ticker: 'COIN', holdings: 9181, value_usd: '$893M', type: 'Exchange', country: 'US' },
  { company: 'Marathon Digital', ticker: 'MARA', holdings: 26200, value_usd: '$2.55B', type: 'Mining', country: 'US' },
  { company: 'Riot Platforms', ticker: 'RIOT', holdings: 15174, value_usd: '$1.48B', type: 'Mining', country: 'US' },
];

export const mockETHTreasuryData: TreasuryHolding[] = [
  { company: 'Ethereum Foundation', holdings: 300000, value_usd: '$1.2B', type: 'Foundation' },
  { company: 'Grayscale Ethereum Trust', holdings: 2800000, value_usd: '$11.2B', type: 'Investment Fund' },
  { company: 'Coinbase', holdings: 1200000, value_usd: '$4.8B', type: 'Exchange' },
  { company: 'Kraken', holdings: 800000, value_usd: '$3.2B', type: 'Exchange' },
  { company: 'Binance', holdings: 600000, value_usd: '$2.4B', type: 'Exchange' },
];

export const mockSOLTreasuryData: TreasuryHolding[] = [
  { company: 'Solana Foundation', holdings: 12500000, value_usd: '$3.1B', type: 'Foundation' },
  { company: 'Alameda Research', holdings: 58000000, value_usd: '$14.5B', type: 'Trading Firm' },
  { company: 'Jump Trading', holdings: 8500000, value_usd: '$2.1B', type: 'Trading Firm' },
  { company: 'Multicoin Capital', holdings: 4200000, value_usd: '$1.05B', type: 'VC Fund' },
  { company: 'Solana Labs', holdings: 3800000, value_usd: '$950M', type: 'Development' },
];

// API functions that would normally make HTTP requests
export const fetchGlobalM2 = async (): Promise<ApiResponse<GlobalM2Data[]>> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));
  return { data: mockGlobalM2Data };
};

export const fetchMarketCaps = async (): Promise<ApiResponse<MarketCapData>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return { data: mockMarketCapData };
};

export const fetchMVRVData = async (): Promise<ApiResponse<MVRVData[]>> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  return { data: mockMVRVData };
};

export const fetchAHRData = async (): Promise<ApiResponse<AHRData[]>> => {
  await new Promise(resolve => setTimeout(resolve, 400));
  return { data: mockAHRData };
};

export const fetchBTCETFFlows = async (): Promise<ApiResponse<ETFFlowData[]>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return { data: mockBTCETFData };
};

export const fetchETHETFFlows = async (): Promise<ApiResponse<ETFFlowData[]>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return { data: mockETHETFData };
};

export const fetchBTCTreasuryHoldings = async (): Promise<ApiResponse<TreasuryHolding[]>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return { data: mockBTCTreasuryData };
};

export const fetchETHTreasuryHoldings = async (): Promise<ApiResponse<TreasuryHolding[]>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return { data: mockETHTreasuryData };
};

export const fetchSOLTreasuryHoldings = async (): Promise<ApiResponse<TreasuryHolding[]>> => {
  await new Promise(resolve => setTimeout(resolve, 300));
  return { data: mockSOLTreasuryData };
};
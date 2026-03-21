import type { NextApiRequest, NextApiResponse } from "next";

interface Pair {
  chainId?: string;
  baseToken?: { symbol?: string };
  priceUsd?: string;
  priceChange?: { h24?: number };
  volume?: { h24?: number };
}

interface DexPayload {
  pairs?: Pair[];
}

function byVolume(p: Pair): number {
  return p.volume?.h24 ?? 0;
}

function pickPair(payload: DexPayload, preferChain?: string): Pair | null {
  const pairs = payload.pairs ?? [];
  if (!pairs.length) return null;
  if (preferChain) {
    const chainPairs = pairs.filter(
      (p) => (p.chainId ?? "").toLowerCase() === preferChain.toLowerCase()
    );
    if (chainPairs.length) {
      return chainPairs.sort((a, b) => byVolume(b) - byVolume(a))[0];
    }
  }
  return pairs.sort((a, b) => byVolume(b) - byVolume(a))[0];
}

function formatPrice(usd: string | undefined): string {
  if (!usd) return "n/a";
  const n = parseFloat(usd);
  if (isNaN(n)) return "n/a";
  if (n < 0.0001) return `$${n.toExponential(2)}`;
  if (n < 1) return `$${n.toFixed(6)}`;
  if (n < 1000) return `$${n.toFixed(4)}`;
  return `$${n.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

function formatVolume(vol: number | undefined): string {
  if (!vol) return "$0";
  if (vol >= 1_000_000) return `$${(vol / 1_000_000).toFixed(1)}M`;
  if (vol >= 1_000) return `$${(vol / 1_000).toFixed(1)}K`;
  return `$${vol.toFixed(0)}`;
}

function formatChange(pct: number | undefined): string {
  if (pct === undefined || pct === null) return "+/-0.00%";
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

async function fetchDex(url: string): Promise<DexPayload | null> {
  try {
    const res = await fetch(url, {
      headers: { "Accept": "application/json" },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const token = (req.query.token as string | undefined)?.trim();
  const chain = (req.query.chain as string | undefined)?.trim();

  if (!token) {
    return res.status(400).json({ error: "token param required" });
  }

  // Try direct token lookup first, fall back to search
  const baseUrl = "https://api.dexscreener.com/latest/dex";
  let payload = await fetchDex(`${baseUrl}/tokens/${encodeURIComponent(token)}`);
  if (!payload?.pairs?.length) {
    payload = await fetchDex(`${baseUrl}/search?q=${encodeURIComponent(token)}`);
  }

  const pair = pickPair(payload ?? {}, chain);
  if (!pair) {
    return res.status(404).json({ error: "no pairs found", token });
  }

  res.setHeader("Cache-Control", "s-maxage=60, stale-while-revalidate=30");
  return res.status(200).json({
    symbol: pair.baseToken?.symbol ?? token.toUpperCase(),
    price: formatPrice(pair.priceUsd),
    change24: formatChange(pair.priceChange?.h24),
    vol24: formatVolume(pair.volume?.h24),
  });
}

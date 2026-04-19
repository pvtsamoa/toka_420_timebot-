export interface TokenPrice {
  symbol: string;
  price: string;
  change24: string;
  vol24: string;
}

export async function fetchPrice(token: string, chain?: string): Promise<TokenPrice | null> {
  try {
    const params = new URLSearchParams({ token });
    if (chain) params.set("chain", chain);
    const res = await fetch(`/api/price?${params}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

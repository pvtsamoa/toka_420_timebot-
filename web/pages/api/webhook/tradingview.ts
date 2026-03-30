import type { NextApiRequest, NextApiResponse } from "next";

/**
 * TradingView HOB alert webhook receiver.
 *
 * POST /api/webhook/tradingview
 *
 * Auth: set WEBHOOK_SECRET in Vercel env vars, then configure TradingView to send:
 *   Authorization: Bearer <your-secret>
 * or
 *   X-Webhook-Secret: <your-secret>
 *
 * Body: JSON or plain text (TradingView supports both).
 * Sends a formatted Markdown message to the configured Telegram chat.
 */

interface AlertPayload {
  ticker?: string;
  symbol?: string;
  exchange?: string;
  timeframe?: string;
  interval?: string;
  action?: string;
  price?: string | number;
  close?: string | number;
  message?: string;
}

function verifySecret(req: NextApiRequest): boolean {
  const secret = process.env.WEBHOOK_SECRET;
  if (!secret) return true; // no secret configured → open

  const auth = req.headers["authorization"] ?? "";
  if (typeof auth === "string" && auth.startsWith("Bearer ")) {
    return auth.slice("Bearer ".length) === secret;
  }
  const xSecret = req.headers["x-webhook-secret"] ?? "";
  return xSecret === secret;
}

function parsePayload(req: NextApiRequest): AlertPayload {
  const ct = req.headers["content-type"] ?? "";
  if (ct.includes("application/json") && typeof req.body === "object" && req.body !== null) {
    return req.body as AlertPayload;
  }
  // Plain-text body — Next.js may have parsed it as a string
  const raw = typeof req.body === "string" ? req.body.trim() : "";
  return { message: raw };
}

function formatPrice(raw: string | number | undefined): string {
  if (raw === undefined || raw === null || raw === "") return "";
  const n = parseFloat(String(raw));
  if (isNaN(n)) return String(raw);
  if (n < 0.0001) return `$${n.toExponential(2)}`;
  if (n < 1) return `$${n.toFixed(6)}`;
  if (n < 1000) return `$${n.toFixed(4)}`;
  return `$${n.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

function buildTelegramMessage(payload: AlertPayload, receivedAt: string): string {
  const action = (payload.action ?? "").toUpperCase();
  const ticker = payload.ticker ?? payload.symbol ?? "";
  const exchange = payload.exchange ?? "";
  const timeframe = payload.timeframe ?? payload.interval ?? "";
  const priceRaw = payload.price ?? payload.close;
  const note = payload.message ?? "";

  const actionEmoji =
    action === "BUY" || action === "LONG" ? "🟢"
    : action === "SELL" || action === "SHORT" ? "🔴"
    : "🔵";

  const lines: string[] = ["📊 *TradingView Alert — HOB Signal*", ""];

  if (action && ticker) {
    let head = `${actionEmoji} *${action}*  \`${ticker}\``;
    if (timeframe) head += `  ·  ${timeframe}`;
    if (exchange) head += `  ·  ${exchange}`;
    lines.push(head);
  } else if (ticker) {
    lines.push(`\`${ticker}\`` + (exchange ? `  ·  ${exchange}` : ""));
  }

  const priceStr = formatPrice(priceRaw);
  if (priceStr) lines.push(`💰 Price: ${priceStr}`);

  if (note && note !== ticker && note !== action) {
    lines.push(`_${note}_`);
  }

  lines.push("");
  lines.push(`🕐 \`${receivedAt.slice(0, 19)} UTC\``);

  if (ticker) {
    const tag = "#" + ticker.replace(/[/\-:]/g, "");
    const hashtags = [tag];
    if (action) hashtags.push(`#${action.charAt(0) + action.slice(1).toLowerCase()}`);
    lines.push(hashtags.join(" "));
  }

  return lines.join("\n");
}

async function sendTelegram(text: string): Promise<void> {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_GLOBAL_CHAT_ID;

  if (!token || !chatId) {
    throw new Error("TELEGRAM_BOT_TOKEN or TELEGRAM_GLOBAL_CHAT_ID not configured");
  }

  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "Markdown" }),
    signal: AbortSignal.timeout(10_000),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Telegram API ${res.status}: ${body}`);
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method Not Allowed" });
  }

  if (!verifySecret(req)) {
    console.warn("[webhook] Unauthorized request from", req.headers["x-forwarded-for"] ?? "unknown");
    return res.status(401).json({ error: "Unauthorized" });
  }

  const payload = parsePayload(req);
  const receivedAt = new Date().toISOString();

  const ticker = payload.ticker ?? payload.symbol ?? null;
  const action = (payload.action ?? "").toUpperCase() || null;
  const price = payload.price ?? payload.close ?? null;

  const text = buildTelegramMessage(payload, receivedAt);

  try {
    await sendTelegram(text);
    console.log(
      `[webhook] alert sent ticker=${ticker} action=${action} price=${price} at=${receivedAt}`
    );
    return res.status(200).json({ ok: true });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[webhook] Telegram send failed: ${msg}`);
    return res.status(502).json({ error: "Telegram send failed", detail: msg });
  }
}

export const config = {
  api: {
    bodyParser: {
      sizeLimit: "16kb",
    },
  },
};

export interface Hub {
  hub: string;
  tz: string;
  region: string;
  region_emoji: string;
  display: string;
  lat: number;
  lng: number;
  cities: string[];
}

export function isAt420(tz: string): boolean {
  try {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: tz,
      hour: "numeric",
      minute: "numeric",
      hour12: false,
    }).formatToParts(new Date());
    const h = parseInt(parts.find((p) => p.type === "hour")?.value ?? "0");
    const m = parseInt(parts.find((p) => p.type === "minute")?.value ?? "0");
    return (h === 4 || h === 16) && m === 20;
  } catch {
    return false;
  }
}

/** Returns milliseconds until the next 4:20 (AM or PM) in the given timezone. */
export function msUntilNext420(tz: string): number {
  try {
    const now = new Date();
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: tz,
      hour: "numeric",
      minute: "numeric",
      second: "numeric",
      hour12: false,
    }).formatToParts(now);
    const h = parseInt(parts.find((p) => p.type === "hour")?.value ?? "0");
    const m = parseInt(parts.find((p) => p.type === "minute")?.value ?? "0");
    const s = parseInt(parts.find((p) => p.type === "second")?.value ?? "0");

    const totalSeconds = h * 3600 + m * 60 + s;
    const am420 = 4 * 3600 + 20 * 60; // 04:20:00
    const pm420 = 16 * 3600 + 20 * 60; // 16:20:00

    let diffSeconds: number;
    if (totalSeconds < am420) {
      diffSeconds = am420 - totalSeconds;
    } else if (totalSeconds < pm420) {
      diffSeconds = pm420 - totalSeconds;
    } else {
      diffSeconds = 24 * 3600 - totalSeconds + am420;
    }

    return diffSeconds * 1000;
  } catch {
    return Infinity;
  }
}

/** Find which hubs are currently at 4:20. */
export function findActive420Hubs(hubs: Hub[]): Hub[] {
  return hubs.filter((h) => isAt420(h.tz));
}

/** Find the hub with the soonest upcoming 4:20. */
export function nextHubToFire(hubs: Hub[]): Hub | null {
  if (!hubs.length) return null;
  return hubs.reduce((best, h) =>
    msUntilNext420(h.tz) < msUntilNext420(best.tz) ? h : best
  );
}

/** Day index since 2024-01-01 in the given timezone (for deterministic daily rotation). */
export function dayIndex(tz: string): number {
  try {
    const epoch = new Date("2024-01-01T00:00:00Z");
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: tz,
      year: "numeric",
      month: "numeric",
      day: "numeric",
    }).formatToParts(new Date());
    const y = parseInt(parts.find((p) => p.type === "year")?.value ?? "2024");
    const mo = parseInt(parts.find((p) => p.type === "month")?.value ?? "1");
    const d = parseInt(parts.find((p) => p.type === "day")?.value ?? "1");
    const today = new Date(y, mo - 1, d);
    return Math.floor((today.getTime() - epoch.getTime()) / 86400000);
  } catch {
    return 0;
  }
}

import Head from "next/head";
import dynamic from "next/dynamic";
import { useEffect, useRef, useState, useCallback } from "react";
import type { GlobeMethods } from "react-globe.gl";
import type { Hub } from "../lib/hubs";
import { findActive420Hubs, nextHubToFire, msUntilNext420, dayIndex } from "../lib/hubs";
import { getBlessing } from "../lib/blessing";
import { getJoke } from "../lib/joke";
import { fetchPrice, TokenPrice } from "../lib/dexscreener";

// react-globe.gl uses Three.js — must be client-only (no SSR)
const Globe = dynamic(() => import("react-globe.gl"), { ssr: false });

interface GlobePoint {
  lat: number;
  lng: number;
  label: string;
  color: string;
  altitude: number;
  hub: Hub;
}

const DEFAULT_ALTITUDE = 2.2;

function formatCountdown(ms: number): string {
  if (ms === Infinity || ms < 0) return "--:--";
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return `${h}h ${m.toString().padStart(2, "0")}m`;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function formatTime(tz: string): string {
  try {
    return new Intl.DateTimeFormat("en-US", {
      timeZone: tz,
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date());
  } catch {
    return "--:--";
  }
}

export default function Home() {
  const [hubs, setHubs] = useState<Hub[]>([]);
  const [jokes, setJokes] = useState<string[]>([]);
  const [activeHubs, setActiveHubs] = useState<Hub[]>([]);
  const [focusHub, setFocusHub] = useState<Hub | null>(null);
  const [countdown, setCountdown] = useState("--:--");
  const [weedcoin, setWeedcoin] = useState<TokenPrice | null>(null);
  const [secondary, setSecondary] = useState<TokenPrice | null>(null);
  const [globeSize, setGlobeSize] = useState(420);
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ctrlRef = useRef<any>(null);

  // Responsive globe size
  useEffect(() => {
    const update = () => {
      const w = window.innerWidth;
      setGlobeSize(w < 900 ? Math.min(w - 24, 520) : 420);
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // Load static data
  useEffect(() => {
    fetch("/hubs.json").then((r) => r.json()).then(setHubs).catch(console.error);
    fetch("/jokes.json").then((r) => r.json()).then(setJokes).catch(console.error);
  }, []);

  // Check active hubs + update countdown every 10s
  useEffect(() => {
    if (!hubs.length) return;
    const update = () => {
      const active = findActive420Hubs(hubs);
      setActiveHubs(active);
      const next = active.length ? active[0] : nextHubToFire(hubs);
      if (next) setFocusHub(next);
    };
    update();
    const id = setInterval(update, 10_000);
    return () => clearInterval(id);
  }, [hubs]);

  // Live countdown tick every second
  useEffect(() => {
    if (!focusHub) return;
    const id = setInterval(() => {
      if (activeHubs.length) {
        setCountdown("NOW");
      } else {
        setCountdown(formatCountdown(msUntilNext420(focusHub.tz)));
      }
    }, 1000);
    return () => clearInterval(id);
  }, [focusHub, activeHubs]);

  // Fetch prices on load, refresh every 60s
  const loadPrices = useCallback(async () => {
    const [w, s] = await Promise.all([
      fetchPrice("weedcoin", "solana"),
      fetchPrice("ethereum"),
    ]);
    setWeedcoin(w);
    setSecondary(s);
  }, []);

  useEffect(() => {
    loadPrices();
    const id = setInterval(loadPrices, 60_000);
    return () => clearInterval(id);
  }, [loadPrices]);

  // Pan to active hub, pause spin; resume spin when idle
  useEffect(() => {
    if (!ctrlRef.current) return;
    if (activeHubs.length) {
      ctrlRef.current.autoRotate = false;
      const h = activeHubs[0];
      globeRef.current?.pointOfView({ lat: h.lat, lng: h.lng, altitude: DEFAULT_ALTITUDE }, 1500);
    } else {
      ctrlRef.current.autoRotate = true;
    }
  }, [activeHubs]);

  const points: GlobePoint[] = hubs.map((h) => {
    const active = activeHubs.some((a) => a.hub === h.hub);
    return {
      lat: h.lat,
      lng: h.lng,
      label: `${h.region_emoji} ${h.display}`,
      color: active ? "#ffe44d" : "rgba(255,255,255,0.35)",
      altitude: active ? 0.09 : 0.015,
      hub: h,
    };
  });

  const idx = focusHub ? dayIndex(focusHub.tz) : 0;
  const blessing = getBlessing(idx);
  const joke = getJoke(jokes, idx);
  const isLive = activeHubs.length > 0;

  return (
    <>
      <Head>
        <title>Toka 420 — Global Green Hour</title>
        <meta name="description" content="Live 4:20 alerts for every timezone on Earth. Weedcoin price, blessings, and jokes." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" />
      </Head>

      <main className="page">
        <header className="header">
          <span className="logo">🌿 TOKA 420</span>
          <span className="tagline">Global Green Hour</span>
        </header>

        <div className="main-layout">

          {/* ── Left col: ritual card ── */}
          <aside className="ritual-col">
            <div className="ritual-card">
              <div className="ritual-header">
                {focusHub?.region_emoji ?? "🌿"} 4:20 — {focusHub?.display ?? "Earth"}
              </div>

              <p className="blessing">{blessing}</p>

              <div className="prices">
                <div className="price-row">
                  <span className="price-label">💰 $WEEDCOIN</span>
                  {weedcoin ? (
                    <span className="price-value">
                      <span className={weedcoin.change24.startsWith("+") ? "up" : "down"}>{weedcoin.change24}</span>
                      {" | "}{weedcoin.price}
                      {" | "}<span className="muted">vol {weedcoin.vol24}</span>
                    </span>
                  ) : <span className="price-value muted">loading…</span>}
                </div>
                <div className="price-row">
                  <span className="price-label">📈 ${secondary?.symbol ?? "ETH"}</span>
                  {secondary ? (
                    <span className="price-value">
                      <span className={secondary.change24.startsWith("+") ? "up" : "down"}>{secondary.change24}</span>
                      {" | "}{secondary.price}
                      {" | "}<span className="muted">vol {secondary.vol24}</span>
                    </span>
                  ) : <span className="price-value muted">loading…</span>}
                </div>
              </div>

              <p className="joke">{joke}</p>
            </div>
          </aside>

          {/* ── Centre col: globe ── */}
          <section className="globe-col">
            <div className="globe-wrap">
              <Globe
                ref={globeRef}
                globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
                backgroundColor="rgba(0,0,0,0)"
                pointsData={points}
                pointColor="color"
                pointAltitude="altitude"
                pointRadius={0.45}
                pointLabel="label"
                onPointClick={(p: object) => {
                  const pt = p as GlobePoint;
                  setFocusHub(pt.hub);
                  globeRef.current?.pointOfView(
                    { lat: pt.hub.lat, lng: pt.hub.lng, altitude: DEFAULT_ALTITUDE },
                    700
                  );
                }}
                onGlobeReady={() => {
                  setTimeout(() => {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    const g = globeRef.current as any;
                    if (!g || typeof g.controls !== "function") return;
                    const ctrl = g.controls();
                    ctrlRef.current = ctrl;

                    // Very slow westerly spin (negative = westward, like real Earth)
                    ctrl.autoRotate = true;
                    ctrl.autoRotateSpeed = -0.15;
                    ctrl.enableDamping = true;
                    ctrl.dampingFactor = 0.08;

                    // Lock Y axis — horizontal spin only, fixed elevation
                    // PI*0.42 ≈ 14° above equator, shows northern hemisphere naturally
                    ctrl.minPolarAngle = Math.PI * 0.42;
                    ctrl.maxPolarAngle = Math.PI * 0.42;

                    // Zoom limits (Three.js world units; globe radius ≈ 100)
                    ctrl.minDistance = 180;
                    ctrl.maxDistance = 380;

                    // Tilt camera slightly down toward northern hemisphere on load
                    g.pointOfView({ lat: 25, lng: 0, altitude: DEFAULT_ALTITUDE }, 0);

                    // Snap back to default altitude after user releases
                    ctrl.addEventListener("end", () => {
                      g.pointOfView({ altitude: DEFAULT_ALTITUDE }, 700);
                    });
                  }, 0);
                }}
                atmosphereColor="#39ff14"
                atmosphereAltitude={0.14}
                width={globeSize}
                height={globeSize}
              />
            </div>

            <div className={`status-banner ${isLive ? "live" : "waiting"}`}>
              {isLive ? (
                <>
                  <span className="pulse-dot" />
                  {"It's 4:20 in "}
                  <strong>{activeHubs.map((h) => h.display).join(" · ")}</strong>
                </>
              ) : (
                <>
                  Next 4:20 in{" "}
                  <strong className="countdown">{countdown}</strong>
                  {focusHub && <span className="next-city"> — {focusHub.display}</span>}
                </>
              )}
            </div>
          </section>

          {/* ── Right col: hub list ── */}
          <aside className="hub-col">
            <div className="hub-list">
              {hubs.map((h) => {
                const active = activeHubs.some((a) => a.hub === h.hub);
                return (
                  <div
                    key={h.hub}
                    className={`hub-item ${active ? "active" : ""}`}
                    onClick={() => {
                      setFocusHub(h);
                      globeRef.current?.pointOfView(
                        { lat: h.lat, lng: h.lng, altitude: DEFAULT_ALTITUDE },
                        700
                      );
                    }}
                  >
                    <span className="hi-emoji">{h.region_emoji}</span>
                    <span className="hi-body">
                      <span className="hi-display">{h.display}</span>
                      <span className="hi-meta">
                        <span className="hi-time">{formatTime(h.tz)}</span>
                        {active ? (
                          <span className="hi-live">🟢 NOW</span>
                        ) : (
                          <span className="hi-cd">{formatCountdown(msUntilNext420(h.tz))}</span>
                        )}
                      </span>
                    </span>
                  </div>
                );
              })}
            </div>
          </aside>

        </div>{/* end .main-layout */}

        <footer className="footer">
          <span>Powered by Weedcoin OG · Solana · Global Cannabis Culture</span>
        </footer>
      </main>
    </>
  );
}

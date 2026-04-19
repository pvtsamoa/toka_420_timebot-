'use client';

import { useEffect, useState } from 'react';
import { Pause, Play, Search, Waves } from 'lucide-react';

const sourceClasses = {
  youtube: 'border-red-400/30 bg-red-500/10 text-red-100',
  audius: 'border-neonPurple/40 bg-neonPurple/10 text-white',
  soundcloud: 'border-orange-400/30 bg-orange-500/10 text-orange-100',
};

export default function MusicPlayer() {
  const [query, setQuery] = useState('Curren$y');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTrack, setActiveTrack] = useState(null);
  const [playerVisible, setPlayerVisible] = useState(false);
  const [playerKey, setPlayerKey] = useState(0);

  useEffect(() => {
    const trimmedQuery = query.trim();

    if (trimmedQuery.length < 2) {
      setResults([]);
      setLoading(false);
      setError('');
      return undefined;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setError('');

      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(trimmedQuery)}`, {
          signal: controller.signal,
          cache: 'no-store',
        });

        const payload = await response.json();

        if (!response.ok) {
          throw new Error(payload.error || 'Search failed.');
        }

        setResults(payload.results || []);
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setResults([]);
          setError(requestError.message);
        }
      } finally {
        setLoading(false);
      }
    }, 350);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query]);

  const handleTrackSelect = (track) => {
    setActiveTrack(track);
    setPlayerVisible(true);
    setPlayerKey((currentValue) => currentValue + 1);
  };

  const togglePlayback = () => {
    if (!activeTrack) {
      return;
    }

    if (playerVisible) {
      setPlayerVisible(false);
      return;
    }

    setPlayerVisible(true);
    setPlayerKey((currentValue) => currentValue + 1);
  };

  return (
    <div className="glass-panel trippy-border rounded-[30px] p-5 shadow-neon">
      <p className="text-xs uppercase tracking-[0.34em] text-neonBlue">Music</p>
      <div className="mt-2 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black text-white">Cross-source player</h2>
          <p className="mt-2 text-sm leading-6 text-white/70">
            Search once and pull tracks from YouTube, Audius, and SoundCloud at the same time.
          </p>
        </div>
        <div className="rounded-full border border-neonYellow/30 bg-neonYellow/10 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-neonYellow">
          3 sources
        </div>
      </div>

      <div className="mt-5 rounded-[24px] border border-white/10 bg-black/30 p-3">
        <label className="flex min-h-[60px] items-center gap-3 rounded-[20px] border border-white/10 bg-white/5 px-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.03)]">
          <Search className="h-5 w-5 text-neonBlue" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search any song or artist"
            className="w-full bg-transparent text-base text-white outline-none placeholder:text-white/35"
          />
        </label>

        {activeTrack ? (
          <div className="mt-4 rounded-[22px] border border-white/10 bg-white/5 p-3">
            <div className="flex gap-3">
              <img
                src={activeTrack.artwork || 'https://placehold.co/144x144/0a0a0a/FFFFFF?text=Leao'}
                alt={activeTrack.title}
                className="h-20 w-20 rounded-[18px] object-cover"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-white/55">Now loaded</p>
                    <h3 className="mt-2 line-clamp-2 text-lg font-black text-white">{activeTrack.title}</h3>
                    <p className="mt-1 text-sm text-white/65">{activeTrack.artist}</p>
                  </div>
                  <span className={`rounded-full border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] ${sourceClasses[activeTrack.source] || sourceClasses.audius}`}>
                    {activeTrack.source}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={togglePlayback}
                  className="mt-4 flex min-h-[52px] items-center justify-center gap-2 rounded-[16px] bg-gradient-to-r from-neonBlue to-neonPurple px-4 text-sm font-black uppercase tracking-[0.24em] text-black shadow-neon transition duration-300 hover:scale-[1.01]"
                >
                  {playerVisible ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  {playerVisible ? 'Pause' : 'Play'}
                </button>
              </div>
            </div>

            <div className="mt-4 overflow-hidden rounded-[22px] border border-white/10 bg-black/40">
              {playerVisible ? (
                <iframe
                  key={playerKey}
                  src={activeTrack.embedUrl}
                  title={activeTrack.title}
                  className="h-[220px] w-full border-0"
                  allow="autoplay; encrypted-media; picture-in-picture"
                  loading="lazy"
                />
              ) : (
                <div className="flex h-[220px] flex-col items-center justify-center gap-3 px-6 text-center text-white/65">
                  <Waves className="h-8 w-8 text-neonGreen" />
                  <p className="max-w-[24ch] text-sm leading-6">
                    Playback is paused. Tap play to remount the selected embed and start the track again.
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : null}

        <div className="mt-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs uppercase tracking-[0.26em] text-white/45">Results</p>
            {loading ? <p className="text-xs uppercase tracking-[0.26em] text-neonGreen">Searching...</p> : null}
          </div>

          {error ? <p className="rounded-[18px] border border-red-400/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</p> : null}

          {!error && !loading && results.length === 0 ? (
            <div className="rounded-[20px] border border-white/10 bg-white/5 px-4 py-6 text-sm text-white/65">
              Start typing to load music results from all three sources.
            </div>
          ) : null}

          <div className="scrollbar-thin max-h-[360px] space-y-3 overflow-y-auto pr-1">
            {results.map((track) => (
              <button
                key={`${track.source}-${track.id}`}
                type="button"
                onClick={() => handleTrackSelect(track)}
                className="flex w-full items-center gap-3 rounded-[22px] border border-white/10 bg-white/5 p-3 text-left transition duration-300 hover:-translate-y-0.5 hover:bg-white/10"
              >
                <img
                  src={track.artwork || 'https://placehold.co/120x120/0a0a0a/FFFFFF?text=Track'}
                  alt={track.title}
                  className="h-16 w-16 rounded-[16px] object-cover"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-black text-white">{track.title}</p>
                      <p className="mt-1 truncate text-sm text-white/60">{track.artist}</p>
                    </div>
                    <span className={`rounded-full border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] ${sourceClasses[track.source] || sourceClasses.audius}`}>
                      {track.source}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
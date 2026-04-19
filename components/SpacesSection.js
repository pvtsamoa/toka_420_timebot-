'use client';

import { useEffect, useState } from 'react';
import { signIn, signOut, useSession } from 'next-auth/react';
import { ExternalLink, LogOut, RefreshCcw, Users } from 'lucide-react';

function formatListeners(count) {
  if (!count) {
    return 'Live now';
  }

  return `${new Intl.NumberFormat('en-US').format(count)} listening`;
}

export default function SpacesSection() {
  const { data: session, status } = useSession();
  const [spaces, setSpaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadSpaces = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/spaces?query=music', { cache: 'no-store' });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || 'Unable to load live Spaces.');
      }

      setSpaces(payload.spaces || []);
    } catch (requestError) {
      setSpaces([]);
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (status === 'authenticated') {
      loadSpaces();
    }
  }, [status]);

  return (
    <div className="glass-panel trippy-border rounded-[30px] p-5 shadow-neon">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.34em] text-neonGreen">Spaces</p>
          <h2 className="mt-2 text-2xl font-black text-white">Live on X right now</h2>
        </div>
        {session ? (
          <button
            type="button"
            onClick={() => signOut()}
            className="flex min-h-[44px] items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 text-xs font-semibold uppercase tracking-[0.24em] text-white/80 transition hover:bg-white/10"
          >
            <LogOut className="h-4 w-4" />
            Exit
          </button>
        ) : null}
      </div>

      <p className="mt-3 text-sm leading-6 text-white/70">
        Connect your X account to pull live Spaces from the API and jump straight into the room.
      </p>

      {status !== 'authenticated' ? (
        <div className="mt-5 rounded-[24px] border border-neonPurple/35 bg-neonPurple/10 p-4 shadow-neon">
          <p className="text-sm text-white/75">OAuth is required before the app can fetch live Spaces.</p>
          <button
            type="button"
            onClick={() => signIn('twitter')}
            className="mt-4 flex min-h-[60px] w-full items-center justify-center rounded-[20px] bg-gradient-to-r from-neonPurple via-neonBlue to-neonGreen px-4 text-sm font-black uppercase tracking-[0.28em] text-black shadow-neon transition duration-300 hover:scale-[1.01]"
          >
            Log in with X
          </button>
          <p className="mt-3 text-xs leading-5 text-white/55">
            Add your X OAuth client values to `.env.local` first if sign-in is not configured yet.
          </p>
        </div>
      ) : (
        <div className="mt-5 space-y-3">
          <div className="flex items-center justify-between rounded-[20px] border border-white/10 bg-black/25 px-4 py-3">
            <div>
              <p className="text-xs uppercase tracking-[0.26em] text-neonBlue">Signed in</p>
              <p className="mt-1 text-sm text-white/80">{session.user?.name || session.user?.email || 'X listener'}</p>
            </div>
            <button
              type="button"
              onClick={loadSpaces}
              className="flex min-h-[44px] items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 text-xs font-semibold uppercase tracking-[0.22em] text-white/80 transition hover:bg-white/10"
            >
              <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {error ? <p className="rounded-[18px] border border-red-400/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</p> : null}

          {loading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((item) => (
                <div key={item} className="animate-pulse rounded-[24px] border border-white/10 bg-white/5 p-4">
                  <div className="h-4 w-24 rounded-full bg-white/10" />
                  <div className="mt-3 h-6 w-4/5 rounded-full bg-white/10" />
                  <div className="mt-3 h-4 w-1/2 rounded-full bg-white/10" />
                </div>
              ))}
            </div>
          ) : null}

          {!loading && !error && spaces.length === 0 ? (
            <div className="rounded-[24px] border border-white/10 bg-white/5 p-4 text-sm text-white/70">
              No live Spaces came back for the current query. Try again after logging in with an account that has API access.
            </div>
          ) : null}

          {!loading && spaces.length > 0 ? (
            <div className="space-y-3">
              {spaces.map((space) => (
                <article key={space.id} className="rounded-[24px] border border-white/10 bg-black/30 p-4 shadow-[0_0_24px_rgba(0,0,0,0.18)]">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-neonYellow">{space.hostName || 'Unknown host'}</p>
                      <h3 className="mt-2 text-lg font-black text-white">{space.title}</h3>
                    </div>
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-white/70">
                      {space.statusLabel}
                    </span>
                  </div>

                  <div className="mt-4 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm text-white/70">
                      <Users className="h-4 w-4 text-neonGreen" />
                      <span>{formatListeners(space.listenerCount)}</span>
                    </div>
                    <a
                      href={space.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex min-h-[60px] items-center gap-2 rounded-[18px] bg-gradient-to-r from-neonGreen to-neonYellow px-5 text-sm font-black uppercase tracking-[0.24em] text-black shadow-lime transition duration-300 hover:scale-[1.01]"
                    >
                      Join Space
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const RESULTS_PER_SOURCE = 6;

async function searchYouTube(query) {
  const apiKey = process.env.YOUTUBE_API_KEY;

  if (!apiKey) {
    return [];
  }

  const endpoint = new URL('https://www.googleapis.com/youtube/v3/search');

  endpoint.searchParams.set('part', 'snippet');
  endpoint.searchParams.set('type', 'video');
  endpoint.searchParams.set('maxResults', String(RESULTS_PER_SOURCE));
  endpoint.searchParams.set('q', query);
  endpoint.searchParams.set('key', apiKey);

  const response = await fetch(endpoint, { next: { revalidate: 0 } });

  if (!response.ok) {
    return [];
  }

  const payload = await response.json();

  return (payload.items || []).map((item) => ({
    id: item.id.videoId,
    source: 'youtube',
    title: item.snippet.title,
    artist: item.snippet.channelTitle,
    artwork: item.snippet.thumbnails?.high?.url || item.snippet.thumbnails?.medium?.url || '',
    embedUrl: `https://www.youtube.com/embed/${item.id.videoId}?autoplay=1&playsinline=1&rel=0`,
  }));
}

async function searchAudius(query) {
  const endpoint = new URL('https://discoveryprovider.audius.co/v1/tracks/search');

  endpoint.searchParams.set('query', query);
  endpoint.searchParams.set('limit', String(RESULTS_PER_SOURCE));

  const response = await fetch(endpoint, { next: { revalidate: 0 } });

  if (!response.ok) {
    return [];
  }

  const payload = await response.json();

  return (payload.data || []).map((track) => ({
    id: String(track.id),
    source: 'audius',
    title: track.title,
    artist: track.user?.name || 'Audius Artist',
    artwork: track.artwork?.['480x480'] || track.artwork?.['150x150'] || '',
    embedUrl: `https://audius.co/embed/track/${track.id}?flavor=compact`,
  }));
}

async function searchSoundCloud(query) {
  const clientId = process.env.SOUNDCLOUD_CLIENT_ID;

  if (!clientId) {
    return [];
  }

  const endpoint = new URL('https://api-v2.soundcloud.com/search/tracks');

  endpoint.searchParams.set('q', query);
  endpoint.searchParams.set('client_id', clientId);
  endpoint.searchParams.set('limit', String(RESULTS_PER_SOURCE));

  const response = await fetch(endpoint, { next: { revalidate: 0 } });

  if (!response.ok) {
    return [];
  }

  const payload = await response.json();

  return (payload.collection || []).map((track) => ({
    id: String(track.id),
    source: 'soundcloud',
    title: track.title,
    artist: track.user?.username || 'SoundCloud Artist',
    artwork: track.artwork_url || track.user?.avatar_url || '',
    embedUrl: `https://w.soundcloud.com/player/?url=${encodeURIComponent(track.permalink_url)}&auto_play=true&visual=true&show_comments=false`,
  }));
}

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q')?.trim();

  if (!query || query.length < 2) {
    return NextResponse.json({ error: 'Provide at least 2 characters to search.' }, { status: 400 });
  }

  try {
    const [youtube, audius, soundcloud] = await Promise.all([
      searchYouTube(query),
      searchAudius(query),
      searchSoundCloud(query),
    ]);

    return NextResponse.json({
      results: [...youtube, ...audius, ...soundcloud],
    });
  } catch {
    return NextResponse.json({ error: 'Music search failed.' }, { status: 500 });
  }
}
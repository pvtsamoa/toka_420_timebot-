import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';

import { authOptions } from '@/lib/auth';

export const dynamic = 'force-dynamic';

export async function GET(request) {
  const session = await getServerSession(authOptions);
  const accessToken = session?.accessToken;

  if (!accessToken) {
    return NextResponse.json({ error: 'Sign in with X before requesting live Spaces.' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const query = searchParams.get('query')?.trim() || 'music';
  const endpoint = new URL('https://api.x.com/2/spaces/search');

  endpoint.searchParams.set('query', query);
  endpoint.searchParams.set('state', 'live');
  endpoint.searchParams.set('space.fields', 'title,participant_count,started_at,host_ids,creator_id');
  endpoint.searchParams.set('expansions', 'host_ids,creator_id');
  endpoint.searchParams.set('user.fields', 'name,username');

  const response = await fetch(endpoint, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const message = await response.text();

    return NextResponse.json(
      {
        error: message || 'X Spaces lookup failed.',
      },
      { status: response.status },
    );
  }

  const payload = await response.json();
  const users = Object.fromEntries((payload.includes?.users || []).map((user) => [user.id, user]));
  const spaces = (payload.data || []).map((space) => {
    const hostId = space.host_ids?.[0] || space.creator_id;
    const host = users[hostId] || null;

    return {
      id: space.id,
      title: space.title || 'Untitled Space',
      hostName: host?.name || host?.username || 'Unknown host',
      listenerCount: space.participant_count || 0,
      statusLabel: 'Live',
      url: `https://x.com/i/spaces/${space.id}`,
    };
  });

  return NextResponse.json({ spaces });
}
# Leao Sessions

Leao Sessions is a mobile-first Next.js app for browsing live X Spaces, searching tracks across YouTube, Audius, and SoundCloud, and triggering layered smoke-session sound effects with Howler.

## Stack

- Next.js 14 App Router
- Tailwind CSS
- NextAuth.js with X OAuth 2.0
- Howler.js
- YouTube Data API, Audius API, SoundCloud API

## Local setup

1. Install dependencies with `npm install`
2. Fill in `.env.local`
3. Add the 8 requested `.mp3` sound files into `public/sounds/`
4. Run `npm run dev`

## Environment variables

- `TWITTER_CLIENT_ID`
- `TWITTER_CLIENT_SECRET`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`
- `YOUTUBE_API_KEY`
- `SOUNDCLOUD_CLIENT_ID`

## Notes

- The X Spaces route requires an authenticated X session and valid X OAuth credentials.
- Audius search works without an API key.
- If SoundCloud or YouTube keys are missing, the search route returns results from the sources that are available.

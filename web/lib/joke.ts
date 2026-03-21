export function getJoke(jokes: string[], idx: number): string {
  if (!jokes.length) return "Why did the stoner cross the road? Because it was 4:20 on the other side.";
  return jokes[Math.abs(idx) % jokes.length];
}

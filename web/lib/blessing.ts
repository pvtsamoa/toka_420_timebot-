const BLESSINGS = [
  "May your session be smooth and your intentions clear. The herb opens doors; wisdom walks through them.",
  "As the clock strikes 4:20, may clarity find you and peace surround you. Light up with purpose.",
  "Green Hour blessings from every corner of the Earth. You are part of a global tribe.",
  "Roll with intention. Breathe with gratitude. The cannabis connects us across every timezone.",
  "May your highs be enlightening and your lows be lessons. 4:20 is a daily reminder to be present.",
  "The sacred hour arrives again. May your mind expand and your heart stay grounded.",
  "To every soul sparking up in their timezone — you are seen, you are celebrated.",
  "Let the smoke carry your worries upward and bring clarity back down. Happy Green Hour.",
  "Cannabis culture is global culture. From Anchorage to Auckland, we celebrate together.",
  "May the 4:20 ritual find you in good company — even if that company is just you and your thoughts.",
];

export function getBlessing(idx: number): string {
  return BLESSINGS[Math.abs(idx) % BLESSINGS.length];
}

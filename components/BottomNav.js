'use client';

import { Music2, Radio, Sparkles } from 'lucide-react';

const items = [
  {
    id: 'spaces',
    label: 'Spaces',
    icon: Radio,
  },
  {
    id: 'music',
    label: 'Music',
    icon: Music2,
  },
  {
    id: 'soundboard',
    label: 'Soundboard',
    icon: Sparkles,
  },
];

export default function BottomNav({ activeSection, onNavigate }) {
  return (
    <nav className="fixed bottom-3 left-1/2 z-50 w-[calc(100%-1.5rem)] max-w-[398px] -translate-x-1/2 rounded-[28px] border border-white/10 bg-black/70 p-2 shadow-neon backdrop-blur-xl">
      <div className="grid grid-cols-3 gap-2">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`flex min-h-[60px] flex-col items-center justify-center rounded-[22px] border transition duration-300 ${
                isActive
                  ? 'border-neonBlue/70 bg-neonBlue/15 text-white shadow-neon'
                  : 'border-white/8 bg-white/5 text-white/65'
              }`}
            >
              <Icon className={`h-5 w-5 ${isActive ? 'text-neonYellow' : 'text-white/70'}`} />
              <span className="mt-1 text-[11px] font-semibold uppercase tracking-[0.25em]">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
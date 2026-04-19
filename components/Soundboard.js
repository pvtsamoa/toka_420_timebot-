'use client';

import { useEffect, useRef, useState } from 'react';
import { Howl } from 'howler';
import { Volume2 } from 'lucide-react';

const soundConfig = [
  { id: 'bong-rip', label: 'Bong Rip', file: '/sounds/bong-rip.mp3' },
  { id: 'lighter', label: 'Lighter Flick', file: '/sounds/lighter.mp3' },
  { id: 'inhale', label: 'Inhale', file: '/sounds/inhale.mp3' },
  { id: 'exhale', label: 'Exhale', file: '/sounds/exhale.mp3' },
  { id: 'glass-tink', label: 'Glass Tink', file: '/sounds/glass-tink.mp3' },
  { id: 'snoop', label: 'Snoop Dogg', file: '/sounds/snoop.mp3' },
  { id: 'cheech-chong', label: 'Cheech & Chong', file: '/sounds/cheech-chong.mp3' },
  { id: 'willie', label: 'Willie Nelson', file: '/sounds/willie.mp3' },
];

export default function Soundboard() {
  const [activePad, setActivePad] = useState('');
  const [audioIssue, setAudioIssue] = useState('');
  const howlMap = useRef({});

  useEffect(() => {
    const nextHowls = {};

    soundConfig.forEach((sound) => {
      nextHowls[sound.id] = new Howl({
        src: [sound.file],
        html5: true,
        volume: 1,
        onloaderror: () => {
          setAudioIssue('Add the requested .mp3 files to public/sounds to enable the soundboard.');
        },
        onplayerror: () => {
          setAudioIssue('The soundboard could not start playback. Check the audio files in public/sounds.');
        },
      });
    });

    howlMap.current = nextHowls;

    return () => {
      Object.values(nextHowls).forEach((howl) => howl.unload());
    };
  }, []);

  const triggerSound = (soundId) => {
    const howl = howlMap.current[soundId];

    setActivePad(soundId);
    window.setTimeout(() => setActivePad((currentValue) => (currentValue === soundId ? '' : currentValue)), 280);

    if (!howl) {
      return;
    }

    howl.play();
  };

  return (
    <div className="glass-panel trippy-border rounded-[30px] p-5 shadow-neon">
      <p className="text-xs uppercase tracking-[0.34em] text-neonYellow">Soundboard</p>
      <div className="mt-2 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black text-white">Session drops</h2>
          <p className="mt-2 text-sm leading-6 text-white/70">
            Eight oversized pads powered by Howler so the drops can layer over the music player.
          </p>
        </div>
        <div className="rounded-full border border-neonGreen/30 bg-neonGreen/10 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-neonGreen">
          Layered audio
        </div>
      </div>

      {audioIssue ? <p className="mt-4 rounded-[18px] border border-amber-400/35 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">{audioIssue}</p> : null}

      <div className="mt-5 grid grid-cols-2 gap-3">
        {soundConfig.map((sound, index) => {
          const isActive = activePad === sound.id;

          return (
            <button
              key={sound.id}
              type="button"
              onClick={() => triggerSound(sound.id)}
              className={`flex min-h-[118px] flex-col items-start justify-between rounded-[24px] border p-4 text-left transition duration-200 ${
                isActive
                  ? 'animate-pulseRing border-neonGreen/60 bg-neonGreen/20 shadow-lime'
                  : 'border-white/10 bg-gradient-to-br from-white/10 to-white/5 shadow-[0_0_18px_rgba(176,38,255,0.18)]'
              }`}
            >
              <span className="rounded-full border border-white/10 bg-black/30 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-white/70">
                Pad {index + 1}
              </span>
              <div>
                <p className="text-lg font-black text-white">{sound.label}</p>
                <div className="mt-3 flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-white/55">
                  <Volume2 className="h-4 w-4 text-neonBlue" />
                  Tap to trigger
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
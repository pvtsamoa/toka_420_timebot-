'use client';

import { useEffect, useRef, useState } from 'react';

import BottomNav from '@/components/BottomNav';
import MusicPlayer from '@/components/MusicPlayer';
import Soundboard from '@/components/Soundboard';
import SpacesSection from '@/components/SpacesSection';

export default function HomePage() {
  const spacesRef = useRef(null);
  const musicRef = useRef(null);
  const soundboardRef = useRef(null);
  const [activeSection, setActiveSection] = useState('spaces');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

        if (visibleEntry?.target?.id) {
          setActiveSection(visibleEntry.target.id);
        }
      },
      {
        rootMargin: '-10% 0px -45% 0px',
        threshold: [0.2, 0.4, 0.65],
      },
    );

    const sections = [spacesRef.current, musicRef.current, soundboardRef.current].filter(Boolean);
    sections.forEach((section) => observer.observe(section));

    return () => {
      sections.forEach((section) => observer.unobserve(section));
      observer.disconnect();
    };
  }, []);

  const handleNavigate = (sectionId) => {
    const sectionMap = {
      spaces: spacesRef.current,
      music: musicRef.current,
      soundboard: soundboardRef.current,
    };

    const target = sectionMap[sectionId];

    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setActiveSection(sectionId);
    }
  };

  return (
    <main className="mx-auto min-h-screen w-full max-w-[430px] px-4 pb-28 pt-5 text-white">
      <div className="noise-overlay space-y-4">
        <section className="rounded-[30px] border border-white/10 bg-white/5 px-5 py-5 shadow-neon backdrop-blur-xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.38em] text-neonYellow">Leao Sessions</p>
              <h1 className="display-font mt-3 text-[2.35rem] leading-none text-white">
                Ride the vibe.
              </h1>
            </div>
            <div className="animate-float rounded-full border border-neonBlue/40 bg-neonBlue/10 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-neonBlue shadow-neon">
              Live stack
            </div>
          </div>
          <p className="mt-4 max-w-[28ch] text-sm leading-6 text-white/70">
            Jump into X Spaces, load tracks from multiple sources, and fire layered drops from the soundboard without leaving the session flow.
          </p>
        </section>

        <section id="spaces" ref={spacesRef}>
          <SpacesSection />
        </section>

        <section id="music" ref={musicRef}>
          <MusicPlayer />
        </section>

        <section id="soundboard" ref={soundboardRef}>
          <Soundboard />
        </section>
      </div>

      <BottomNav activeSection={activeSection} onNavigate={handleNavigate} />
    </main>
  );
}
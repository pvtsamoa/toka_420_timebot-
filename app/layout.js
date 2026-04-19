import './globals.css';

import { Bungee, Space_Grotesk } from 'next/font/google';

import Providers from '@/components/Providers';

const bodyFont = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-body',
});

const displayFont = Bungee({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-display',
});

export const metadata = {
  title: 'Leao Sessions',
  description: 'A stoner music and soundboard companion app for X Spaces.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${bodyFont.variable} ${displayFont.variable}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
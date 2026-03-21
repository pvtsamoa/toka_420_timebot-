/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // react-globe.gl uses Three.js which requires this for SSR
  webpack: (config) => {
    config.externals = config.externals || [];
    return config;
  },
};

module.exports = nextConfig;

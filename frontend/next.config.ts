import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: true,
  output: 'standalone',
  // Force all URL resources to use HTTPS protocol
  assetPrefix: process.env.NODE_ENV === 'production' ? 'https://' : undefined,
  // Ensure the application always uses HTTPS
  headers: async () => {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "upgrade-insecure-requests"
          }
        ]
      }
    ];
  }
};

export default nextConfig;

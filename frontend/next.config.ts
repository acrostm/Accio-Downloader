import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  // In local dev: proxy /api/* to the FastAPI backend
  // In Docker: Nginx handles the proxy, this is ignored at runtime
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/downloads/:path*',
        destination: 'http://127.0.0.1:8000/downloads/:path*',
      },
    ];
  },
};

export default nextConfig;

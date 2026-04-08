import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["recharts"],
  // Avoid Turbopack mis-detecting `src/app` as the workspace root (breaks `next dev` on some setups).
  turbopack: {
    root: path.resolve(process.cwd()),
  },
  async rewrites() {
    const backendBaseUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendBaseUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

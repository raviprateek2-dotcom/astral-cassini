import path from "node:path";
import type { NextConfig } from "next";

const isGitHubPagesBuild = process.env.GITHUB_PAGES === "true";
const repositoryName = process.env.GITHUB_REPOSITORY?.split("/")[1] ?? "";
const pagesBasePath =
  isGitHubPagesBuild && repositoryName ? `/${repositoryName}` : "";

const nextConfig: NextConfig = {
  transpilePackages: ["recharts"],
  // Avoid Turbopack mis-detecting `src/app` as the workspace root (breaks `next dev` on some setups).
  turbopack: {
    root: path.resolve(process.cwd()),
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' ws: wss: http: https:;"
          },
          {
            key: "X-Frame-Options",
            value: "DENY"
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff"
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin"
          }
        ]
      }
    ];
  },
  ...(isGitHubPagesBuild
    ? {
        output: "export",
        trailingSlash: true,
        images: { unoptimized: true },
        basePath: pagesBasePath || undefined,
        assetPrefix: pagesBasePath || undefined,
      }
    : {
        async rewrites() {
          const backendBaseUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";
          return [
            {
              source: "/api/:path*",
              destination: `${backendBaseUrl}/api/:path*`,
            },
          ];
        },
      }),
};

export default nextConfig;

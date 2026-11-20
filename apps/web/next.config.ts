import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  outputFileTracingRoot: __dirname,
  poweredByHeader: false,
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
  async redirects() {
    // Retired Company Brain routes from the previous site.
    return [
      { source: "/company-brain", destination: "/repeat", permanent: false },
      { source: "/demo", destination: "/repeat/example", permanent: false },
      { source: "/framework", destination: "/about", permanent: false },
      { source: "/papers", destination: "/about#writing", permanent: false },
      { source: "/papers/:slug*", destination: "/about#writing", permanent: false },
    ];
  },
};

export default nextConfig;

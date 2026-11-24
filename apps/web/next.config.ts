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
  async rewrites() {
    // Browsers and bookmark tools request /favicon.ico directly; serve the right icon for this deployment.
    const ico = process.env.NEXT_PUBLIC_REPEAT_STANDALONE === "1" ? "/repeat-favicon.ico" : "/favicon.png";
    return [{ source: "/favicon.ico", destination: ico }];
  },
  async redirects() {
    // Standalone Repeat on its own subdomain: the company site lives elsewhere (Lovable).
    if (process.env.NEXT_PUBLIC_REPEAT_STANDALONE === "1") {
      const company = (process.env.NEXT_PUBLIC_COMPANY_URL || "https://theauthority.company").replace(/\/$/, "");
      return [
        { source: "/", destination: "/repeat", permanent: false },
        { source: "/about", destination: `${company}/about`, permanent: false },
      ];
    }
    // Full site: retired Company Brain routes from the previous site.
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

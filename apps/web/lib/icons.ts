import type { Metadata } from "next";

/**
 * Browser-tab and home-screen icons.
 * Source: public/repeat-icon.svg. The PNG/ICO files beside it are rendered from it; re-render them if the SVG changes.
 */
export const REPEAT_ICONS: Metadata["icons"] = {
  icon: [
    { url: "/repeat-favicon.ico", sizes: "16x16 32x32 48x48" },
    { url: "/repeat-icon.svg", type: "image/svg+xml" },
    { url: "/repeat-icon-192.png", type: "image/png", sizes: "192x192" },
  ],
  apple: [{ url: "/repeat-apple-touch-icon.png", sizes: "180x180" }],
};

export const AUTHORITY_ICONS: Metadata["icons"] = { icon: "/favicon.png" };

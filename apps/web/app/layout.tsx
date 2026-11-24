import type { Metadata, Viewport } from "next";
import { Newsreader, Work_Sans } from "next/font/google";
import "./globals.css";
import { SITE_URL, STANDALONE } from "@/lib/site";
import { AUTHORITY_ICONS, REPEAT_ICONS } from "@/lib/icons";

const newsreader = Newsreader({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  style: ["normal", "italic"],
  variable: "--font-newsreader",
  display: "swap",
});
const workSans = Work_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-work-sans",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "Authority AI | Intelligence should lead to action", template: "%s | Authority AI" },
  description:
    "Authority AI builds intelligent systems that turn knowledge into execution. Our mission is to make business execution repeatable. Our first product is Repeat.",
  // On the standalone Repeat subdomain every page (Privacy too) carries the Repeat icon.
  icons: STANDALONE ? REPEAT_ICONS : AUTHORITY_ICONS,
  openGraph: {
    type: "website",
    siteName: "Authority AI",
    title: "Authority AI | Intelligence should lead to action",
    description: "Our mission is to make business execution repeatable. Meet repeat. — turn your first customers into repeatable revenue.",
    url: "/",
  },
  twitter: { card: "summary_large_image" },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f7f5f0" },
    { media: "(prefers-color-scheme: dark)", color: "#141311" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${newsreader.variable} ${workSans.variable}`}>
      <body className="min-h-dvh">
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:bg-ink focus:px-3 focus:py-2 focus:text-paper">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}

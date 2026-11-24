import type { Metadata } from "next";
import { RepeatHeader, SiteFooter } from "@/components/SiteChrome";
import { REPEAT_ICONS } from "@/lib/icons";

export const metadata: Metadata = {
  icons: REPEAT_ICONS,
  title: { default: "repeat. — Turn your first customers into repeatable revenue", template: "%s | repeat. by Authority AI" },
  description:
    "Repeat helps B2B founders understand how their first customers were won, identify patterns worth testing, and build a more structured approach to winning the next ones.",
  openGraph: {
    title: "repeat. — Turn your first customers into repeatable revenue",
    description: "You won your first customers. Now make it repeatable. A free diagnostic for early-stage B2B founders, by Authority AI.",
    url: "/repeat",
  },
};

export default function RepeatLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <RepeatHeader />
      <main id="main">{children}</main>
      <SiteFooter />
    </>
  );
}

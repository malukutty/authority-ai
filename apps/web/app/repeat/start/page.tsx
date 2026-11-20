import type { Metadata } from "next";
import { QuickStart } from "@/components/QuickStart";

export const metadata: Metadata = { title: "Analyze my revenue motion", robots: { index: false } };

export default function Start() {
  return <QuickStart />;
}

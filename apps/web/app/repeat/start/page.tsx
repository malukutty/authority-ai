import type { Metadata } from "next";
import { IntakeFlow } from "@/components/Intake";

export const metadata: Metadata = { title: "Analyze my sales motion", robots: { index: false } };

export default function Start() {
  return <IntakeFlow />;
}

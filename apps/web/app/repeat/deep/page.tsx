import type { Metadata } from "next";
import { IntakeFlow } from "@/components/Intake";

export const metadata: Metadata = { title: "Full diagnostic", robots: { index: false } };

/** The detailed, optional diagnostic (three customer wins + sales motion). Prefilled from the quick flow when available. */
export default function Deep() {
  return <IntakeFlow />;
}

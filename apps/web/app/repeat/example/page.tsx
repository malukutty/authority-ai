import type { Metadata } from "next";
import { ReportView } from "@/components/Report";
import { EXAMPLE_STORED } from "@/lib/repeat/example";

export const metadata: Metadata = {
  title: "Example report",
  description: "An illustrative Repeat Revenue Diagnostic for a fictional B2B SaaS company.",
};

export default function Example() {
  return <ReportView data={EXAMPLE_STORED} />;
}

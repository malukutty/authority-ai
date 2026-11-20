import type { QuickInput, QuickReport } from "./quick-schema";

/** Development only (REPEAT_MOCK=1): a clearly labelled placeholder, never shown in production. */
export function mockQuickReport(input: QuickInput, name: string): QuickReport {
  const answered = Object.values(input.answers).filter((v) => v && v.trim()).length;
  const needed: QuickReport["needed"] = [
    { question_id: "lead_sources" as const, item: "Where recent customers came from", why_it_matters: "MOCK" },
    { question_id: "trigger" as const, item: "What made customers buy now", why_it_matters: "MOCK" },
    { question_id: "why_chose" as const, item: "Why customers chose you", why_it_matters: "MOCK" },
  ].filter((n) => !input.answers[n.question_id]);
  return {
    headline: `[MOCK — no model was called] Placeholder report for ${name}. ${answered} optional answer(s) received.`,
    company: {
      name,
      sells: { text: "MOCK: what the website says the company sells.", basis: "website" },
      serves: { text: "MOCK: who the website appears to serve.", basis: "website" },
      value_prop: { text: "MOCK: the stated value proposition.", basis: "website" },
    },
    icp: {
      statement: "MOCK: draft ICP hypothesis.",
      traits: [{ statement: "MOCK trait", basis: "inferred", evidence: "none" }],
    },
    obstacles: [1, 2, 3].map((n) => ({
      title: `MOCK obstacle ${n}`,
      why_likely: "MOCK reasoning.",
      basis: "inferred" as const,
      evidence: "none",
      how_to_check: "MOCK check.",
    })),
    experiment: {
      name: "MOCK experiment",
      hypothesis: "MOCK hypothesis.",
      target: "MOCK target.",
      steps: ["MOCK step 1", "MOCK step 2"],
      success_metric: "MOCK: 3 of 20 reply within 10 days.",
      timeframe: "2 weeks",
      why: "MOCK why.",
    },
    needed,
    changes: input.previousHeadline ? [`MOCK: updated with ${answered} answer(s).`] : [],
    confidence: { level: answered ? "medium" : "low", note: "MOCK confidence note." },
  };
}

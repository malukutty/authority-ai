import { z } from "zod";
import Anthropic from "@anthropic-ai/sdk";
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import { ReportSchema, type Intake, type Report } from "./schema";
import { SYSTEM_PROMPT, buildUserMessage } from "./prompt";

export const DEFAULT_MODEL = "claude-opus-5-5";

export class AnalysisError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
  ) {
    super(message);
  }
}

export function analysisModel() {
  return process.env.REPEAT_MODEL?.trim() || DEFAULT_MODEL;
}

let client: Anthropic | null = null;
function getClient() {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new AnalysisError("Analysis is not configured on this server yet.", 503, "not_configured");
  }
  // 100s per attempt, one retry for transient (429/5xx/connection) failures.
  client ??= new Anthropic({ timeout: 100_000, maxRetries: 1 });
  return client;
}

/** Remove source labels that do not exist in the input, so the report cannot cite phantom evidence. */
export function sanitizeReport(report: Report, intake: Intake): Report {
  const valid = new Set(["Company profile", "Sales motion", ...intake.wins.map((_, i) => `Win ${i + 1}`)]);
  const clean = (s: string[]) => s.filter((x) => valid.has(x.trim()));
  const fix = <T extends { sources: string[] }>(arr: T[]) => arr.map((f) => ({ ...f, sources: clean(f.sources) }));
  return {
    ...report,
    current_motion: { ...report.current_motion, observations: fix(report.current_motion.observations) },
    icp: { ...report.icp, traits: fix(report.icp.traits), exclusions: fix(report.icp.exclusions) },
    triggers: fix(report.triggers),
    process: { ...report.process, steps: fix(report.process.steps) },
    plan: [...report.plan].sort((a, b) => a.week - b.week),
  };
}

type Key = keyof Report;
const blank = (s: string) => !s || !s.trim();

/** Per-section completeness rules. Schema validity alone doesn't catch blank strings or empty lists. */
const CHECKS: Record<Key, (r: Report) => string[]> = {
  headline: (r) => (blank(r.headline) ? ["headline"] : []),
  data_quality: (r) => (blank(r.data_quality.note) ? ["data_quality.note"] : []),
  current_motion: (r) => (blank(r.current_motion.summary) ? ["current_motion.summary"] : []),
  icp: (r) => (blank(r.icp.statement) ? ["icp.statement"] : []),
  triggers: () => [], // may legitimately be empty; the report explains it
  process: (r) => [
    ...(r.process.steps.length === 0 ? ["process.steps"] : []),
    ...(blank(r.process.typical_cycle) ? ["process.typical_cycle"] : []),
  ],
  gaps: (r) => (r.gaps.length === 0 ? ["gaps"] : []),
  next_ten: (r) => Object.entries(r.next_ten).filter(([, v]) => blank(v)).map(([k]) => `next_ten.${k}`),
  plan: (r) => [
    ...(r.plan.length < 4 ? ["plan (needs 4 weeks)"] : []),
    ...(r.plan.some((p) => p.actions.length === 0 || blank(p.success_metric)) ? ["plan actions / success metrics"] : []),
  ],
  confidence: (r) => [
    ...(r.confidence.observed.length === 0 && r.confidence.hypotheses.length === 0 ? ["confidence.observed / hypotheses"] : []),
    ...(r.confidence.missing.length === 0 ? ["confidence.missing"] : []),
  ],
};

export function incompleteSections(r: Report, keys: Key[] = Object.keys(CHECKS) as Key[]): string[] {
  return keys.flatMap((k) => CHECKS[k](r));
}

/*
 * The report is generated in two halves, in parallel. Asked for all eight sections at once at medium
 * effort, the model reliably wrote the first half and stubbed the rest with empty values (seen in 3 of
 * 5 real runs); high effort fixed that but took ~100s. Two half-size calls finish in ~40s and complete.
 */
const PARTS: { keys: Key[]; label: string }[] = [
  { keys: ["current_motion", "icp", "triggers", "process"], label: "A. current revenue motion, B. initial ICP, C. buying triggers, D. sales process" },
  { keys: ["headline", "data_quality", "gaps", "next_ten", "plan", "confidence"], label: "headline and data quality, E. repeatability gaps, F. next 10 customers, G. 30-day plan, H. evidence and confidence" },
];

const pick = (keys: Key[]) => ReportSchema.pick(Object.fromEntries(keys.map((k) => [k, true])) as { [K in Key]?: true });

async function runPart(intake: Intake, part: (typeof PARTS)[number]) {
  const schema = pick(part.keys);
  const scope = `For this request, write only these sections of the diagnostic: ${part.label}. The other sections are written separately from the same input under the same rules, so stay strictly grounded in the evidence.`;
  const first = await callModel(intake, schema, scope);
  const gaps = incompleteSections(first.data as Report, part.keys);
  if (gaps.length === 0) return first;

  // One corrective retry. If it is still incomplete, fail rather than show a half-empty report.
  console.warn("[repeat] incomplete section(s), retrying:", gaps.join(", "));
  const second = await callModel(
    intake,
    schema,
    `${scope}

A previous attempt left these empty: ${gaps.join(", ")}. Fill every one. Where evidence is thin, recommend how to collect it rather than leaving the field blank.`,
  );
  const still = incompleteSections(second.data as Report, part.keys);
  if (still.length > 0) {
    console.error("[repeat] still incomplete after retry:", still.join(", "));
    throw new AnalysisError(
      "We couldn't produce a complete diagnostic from these answers. Adding more detail to your wins usually helps — then try again.",
      502,
      "incomplete_output",
    );
  }
  return second;
}

export async function runAnalysis(intake: Intake): Promise<{ report: Report; model: string }> {
  const [a, b] = await Promise.all(PARTS.map((p) => runPart(intake, p)));
  const check = ReportSchema.safeParse({ ...a.data, ...b.data });
  if (!check.success) {
    console.error("[repeat] merged report failed validation", check.error.issues.slice(0, 5));
    throw new AnalysisError("The analysis came back in an unexpected format. Please try again.", 502, "invalid_output");
  }
  return { report: sanitizeReport(check.data, intake), model: a.model };
}

async function callModel(
  intake: Intake,
  schema: ReturnType<typeof pick>,
  instruction: string,
): Promise<{ data: Partial<Report>; model: string }> {
  const out = await structuredCall(schema, SYSTEM_PROMPT, `${buildUserMessage(intake)}

${instruction}`);
  return { data: out.data as Partial<Report>, model: out.model };
}

/**
 * One Claude call with structured output, validated against `schema`.
 * Maps every failure (rate limit, timeout, auth, refusal, truncation, bad output) to an AnalysisError.
 */
export async function structuredCall<S extends z.ZodType>(
  schema: S,
  system: string,
  user: string,
  effort: "low" | "medium" | "high" = "medium",
): Promise<{ data: z.infer<S>; model: string }> {
  const anthropic = getClient();
  const model = analysisModel();
  const started = Date.now();
  let response;
  try {
    response = await anthropic.beta.messages.parse({
      model,
      max_tokens: 16000,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      output_config: { effort, format: betaZodOutputFormat(schema) },
      system,
      messages: [{ role: "user", content: user }],
    });
  } catch (err) {
    if (err instanceof Anthropic.RateLimitError) {
      throw new AnalysisError("The analysis service is busy. Please try again in a minute.", 503, "upstream_busy");
    }
    if (err instanceof Anthropic.APIConnectionTimeoutError) {
      throw new AnalysisError("The analysis took too long. Please try again.", 504, "timeout");
    }
    if (err instanceof Anthropic.AuthenticationError || err instanceof Anthropic.PermissionDeniedError) {
      console.error("[repeat] model auth error", err.status);
      throw new AnalysisError("Analysis is temporarily unavailable.", 503, "not_configured");
    }
    if (err instanceof Anthropic.APIError) {
      console.error("[repeat] model API error", err.status, err.message);
      throw new AnalysisError("The analysis service returned an error. Please try again.", 502, "upstream_error");
    }
    // Zod / JSON parse failure from .parse(), or anything unexpected.
    console.error("[repeat] analysis failed", err);
    throw new AnalysisError("The analysis came back in an unexpected format. Please try again.", 502, "invalid_output");
  }

  if (response.stop_reason === "refusal") {
    throw new AnalysisError("The model declined to analyze this input. Try rephrasing your answers.", 422, "refused");
  }
  if (response.stop_reason === "max_tokens") {
    throw new AnalysisError("The analysis was cut short. Please try again.", 502, "truncated");
  }
  console.info(
    `[repeat] model call ${((Date.now() - started) / 1000).toFixed(1)}s, ${response.usage.output_tokens} output tokens, effort=${effort}, stop=${response.stop_reason}`,
  );
  const check = schema.safeParse(response.parsed_output);
  if (!check.success) {
    console.error("[repeat] schema validation failed", check.error.issues.slice(0, 5));
    throw new AnalysisError("The analysis came back in an unexpected format. Please try again.", 502, "invalid_output");
  }
  return { data: check.data, model: response.model ?? model };
}

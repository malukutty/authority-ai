import { NextResponse, type NextRequest } from "next/server";
import { randomUUID } from "node:crypto";
import { IntakeSchema, checkReadiness, type Intake } from "@/lib/repeat/schema";
import { AnalysisError, analysisModel, runAnalysis } from "@/lib/repeat/analyze";
import { EXAMPLE_REPORT } from "@/lib/repeat/example";
import { burstLimited, clientIp, dailyLimitReached, hashIp, sameOrigin } from "@/lib/guard";
import { recordUsage } from "@/lib/store";

export const runtime = "nodejs";
export const maxDuration = 300;

const err = (message: string, status: number, code: string) => NextResponse.json({ error: message, code }, { status });

export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return err("Forbidden.", 403, "forbidden");

  const len = Number(req.headers.get("content-length") ?? 0);
  if (len > 64_000) return err("Your answers are too long. Please shorten them.", 413, "too_large");

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return err("Invalid request.", 400, "bad_json");
  }
  const parsed = IntakeSchema.safeParse(body);
  if (!parsed.success) {
    const first = parsed.error.issues[0];
    const tooLong = first?.code === "too_big";
    return err(
      tooLong ? "One of your answers is too long. Please keep each answer under 1,200 characters." : "Please check your answers and try again.",
      400,
      "invalid_input",
    );
  }
  const intake: Intake = parsed.data;
  const ready = checkReadiness(intake);
  if (!ready.ok) return err(ready.reason, 422, "insufficient_input");

  const ipHash = hashIp(clientIp(req));
  const mock = process.env.REPEAT_MOCK === "1" && process.env.NODE_ENV !== "production";

  if (mock) {
    await recordUsage({ ipHash, status: "mock", model: "mock", latencyMs: 0 });
    return NextResponse.json({
      id: randomUUID(),
      createdAt: new Date().toISOString(),
      model: "mock",
      mock: true,
      intake,
      report: { ...EXAMPLE_REPORT, headline: `[MOCK — no model was called] ${EXAMPLE_REPORT.headline}` },
    });
  }

  if (burstLimited(ipHash, 2, 60_000)) {
    return err("Please wait a minute before running another analysis.", 429, "rate_limited");
  }
  const limited = await dailyLimitReached(ipHash).catch((e) => {
    console.error("[repeat] usage check failed", e);
    return null; // fail open on storage errors; burst limit + upstream limits still apply
  });
  if (limited) return err(limited, 429, "daily_limit");

  const started = Date.now();
  try {
    const { report, model } = await runAnalysis(intake);
    await recordUsage({ ipHash, status: "ok", model, latencyMs: Date.now() - started }).catch((e) =>
      console.error("[repeat] usage log failed", e),
    );
    return NextResponse.json({ id: randomUUID(), createdAt: new Date().toISOString(), model, intake, report });
  } catch (e) {
    // A missing server key is our fault, not the founder's: don't count it against their daily limit.
    if (!(e instanceof AnalysisError && e.code === "not_configured")) {
      await recordUsage({ ipHash, status: "error", model: analysisModel(), latencyMs: Date.now() - started }).catch(() => {});
    }
    if (e instanceof AnalysisError) return err(e.message, e.status, e.code);
    console.error("[repeat] unexpected", e);
    return err("Something went wrong. Please try again.", 500, "internal");
  }
}

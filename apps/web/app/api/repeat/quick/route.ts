import { NextResponse, type NextRequest } from "next/server";
import { ExtractError, readWebsite, type SiteRead } from "@/lib/extract";
import { burstLimited, clientIp, dailyLimitReached, hashIp, sameOrigin } from "@/lib/guard";
import { AnalysisError, analysisModel } from "@/lib/repeat/analyze";
import { runQuick } from "@/lib/repeat/quick";
import { mockQuickReport } from "@/lib/repeat/quick-mock";
import { MIN_READABLE_CHARS, QuickInputSchema } from "@/lib/repeat/quick-schema";
import { recordUsage } from "@/lib/store";

export const runtime = "nodejs";
export const maxDuration = 120;

const err = (message: string, status: number, code: string) => NextResponse.json({ error: message, code }, { status });

/**
 * Website-first report. Called once for the first report, then again after each optional answer
 * (same inputs plus the accumulated answers) to update the report in place.
 */
export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return err("Forbidden.", 403, "forbidden");
  if (Number(req.headers.get("content-length") ?? 0) > 32_000) return err("Your answers are too long.", 413, "too_large");

  const parsed = QuickInputSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    const issue = parsed.error.issues[0];
    const msg = issue?.code === "too_big" ? "That answer is too long. Please keep it under 1,000 characters." : issue?.message || "Please check the form.";
    return err(msg, 400, "invalid_input");
  }
  const input = parsed.data;

  // Read the website server-side every time (about 1s) rather than trusting page text sent by the browser.
  let site: SiteRead | null = null;
  if (input.url) {
    try {
      site = await readWebsite(input.url);
    } catch (e) {
      if (!input.manual?.sells) {
        return err(e instanceof ExtractError ? e.message : "We couldn't read that website.", 422, "site_unreadable");
      }
    }
    if (site && site.chars < MIN_READABLE_CHARS) {
      if (!input.manual?.sells) return err("We couldn't find enough readable text on that website.", 422, "site_unreadable");
      site = null; // too thin to use: rely on the founder's description, and don't claim we analyzed the site
    }
  }

  const ipHash = hashIp(clientIp(req));
  const siteOut = site ? { url: site.url, title: site.title, pagesRead: site.pages.length } : null;

  if (process.env.REPEAT_MOCK === "1" && process.env.NODE_ENV !== "production") {
    const name = site?.title?.split(/[|–—]/)[0]?.trim() || input.url || "Your company";
    await recordUsage({ ipHash, status: "mock", model: "mock", latencyMs: 0, kind: "quick" });
    return NextResponse.json({ report: mockQuickReport(input, name), model: "mock", mock: true, site: siteOut });
  }

  if (burstLimited("q:" + ipHash, 6, 60_000)) return err("Please wait a moment before updating again.", 429, "rate_limited");
  const limited = await dailyLimitReached(ipHash, "quick").catch((e) => {
    console.error("[repeat] usage check failed", e);
    return null; // fail open on storage errors; burst limit still applies
  });
  if (limited) return err(limited, 429, "daily_limit");

  const started = Date.now();
  try {
    const { report, model } = await runQuick(input, site);
    await recordUsage({ ipHash, status: "ok", model, latencyMs: Date.now() - started, kind: "quick" }).catch((e) =>
      console.error("[repeat] usage log failed", e),
    );
    return NextResponse.json({ report, model, site: siteOut });
  } catch (e) {
    if (!(e instanceof AnalysisError && e.code === "not_configured")) {
      await recordUsage({ ipHash, status: "error", model: analysisModel(), latencyMs: Date.now() - started, kind: "quick" }).catch(() => {});
    }
    if (e instanceof AnalysisError) return err(e.message, e.status, e.code);
    console.error("[repeat] quick unexpected", e);
    return err("Something went wrong. Please try again.", 500, "internal");
  }
}

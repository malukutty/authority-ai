import type { NextRequest } from "next/server";
import { countUsage, hashIp, type UsageKind } from "./store";

export function clientIp(req: NextRequest) {
  const fwd = req.headers.get("x-forwarded-for");
  return (fwd?.split(",")[0] || req.headers.get("x-real-ip") || "unknown").trim();
}

/** Reject cross-site POSTs. Browsers always send Origin on fetch POSTs. */
export function sameOrigin(req: NextRequest) {
  const origin = req.headers.get("origin");
  if (!origin) return false;
  try {
    return new URL(origin).host === req.headers.get("host");
  } catch {
    return false;
  }
}

// Per-instance short-window throttle (in memory). Durable daily limits are checked in the store.
const recent = new Map<string, number[]>();
export function burstLimited(key: string, max: number, windowMs: number) {
  const now = Date.now();
  const hits = (recent.get(key) ?? []).filter((t) => now - t < windowMs);
  if (hits.length >= max) {
    recent.set(key, hits);
    return true;
  }
  hits.push(now);
  recent.set(key, hits);
  if (recent.size > 5000) recent.clear();
  return false;
}

const num = (v: string | undefined, d: number) => {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : d;
};

export async function dailyLimitReached(ipHash: string, kind: UsageKind = "full"): Promise<string | null> {
  const perIp =
    kind === "quick"
      ? num(process.env.REPEAT_MAX_QUICK_PER_IP_PER_DAY, 25)
      : num(process.env.REPEAT_MAX_ANALYSES_PER_IP_PER_DAY, 5);
  const global =
    kind === "quick" ? num(process.env.REPEAT_MAX_QUICK_PER_DAY, 600) : num(process.env.REPEAT_MAX_ANALYSES_PER_DAY, 200);
  const [mine, all] = await Promise.all([countUsage(ipHash, kind), countUsage(undefined, kind)]);
  if (mine >= perIp) return `You've reached today's limit of ${perIp} analyses. Please come back tomorrow.`;
  if (all >= global) return "Repeat has reached its daily analysis capacity. Please try again tomorrow.";
  return null;
}

export { hashIp };

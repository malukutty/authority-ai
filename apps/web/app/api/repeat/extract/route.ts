import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";
import { ExtractError, extractWebsite } from "@/lib/extract";
import { burstLimited, clientIp, hashIp, sameOrigin } from "@/lib/guard";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return NextResponse.json({ error: "Forbidden." }, { status: 403 });
  if (burstLimited("x:" + hashIp(clientIp(req)), 6, 60_000)) {
    return NextResponse.json({ error: "Too many lookups. Please wait a minute." }, { status: 429 });
  }
  const body = z.object({ url: z.string().max(300) }).safeParse(await req.json().catch(() => null));
  if (!body.success) return NextResponse.json({ error: "Enter a website address." }, { status: 400 });
  try {
    return NextResponse.json(await extractWebsite(body.data.url));
  } catch (e) {
    const msg = e instanceof ExtractError ? e.message : "We couldn't read that website.";
    if (!(e instanceof ExtractError)) console.error("[repeat] extract failed", e);
    return NextResponse.json({ error: msg }, { status: 422 });
  }
}

import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";
import { ExtractError, readWebsite } from "@/lib/extract";
import { burstLimited, clientIp, hashIp, sameOrigin } from "@/lib/guard";
import { MIN_READABLE_CHARS } from "@/lib/repeat/quick-schema";

export const runtime = "nodejs";

/** Step 1 of the quick flow: read the public website (no model call) and say whether there's enough to analyze. */
export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return NextResponse.json({ error: "Forbidden." }, { status: 403 });
  if (burstLimited("s:" + hashIp(clientIp(req)), 10, 60_000)) {
    return NextResponse.json({ error: "Too many lookups. Please wait a minute." }, { status: 429 });
  }
  const body = z.object({ url: z.string().max(300) }).safeParse(await req.json().catch(() => null));
  if (!body.success || !body.data.url.trim()) {
    return NextResponse.json({ error: "Enter your website address." }, { status: 400 });
  }
  try {
    const site = await readWebsite(body.data.url);
    return NextResponse.json({
      url: site.url,
      title: site.title,
      description: site.description,
      pagesRead: site.pages.length,
      readable: site.chars >= MIN_READABLE_CHARS,
    });
  } catch (e) {
    const msg = e instanceof ExtractError ? e.message : "We couldn't read that website.";
    if (!(e instanceof ExtractError)) console.error("[repeat] site read failed", e);
    return NextResponse.json({ error: msg, code: "site_unreadable" }, { status: 422 });
  }
}

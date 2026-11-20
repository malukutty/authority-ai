import { NextResponse, type NextRequest } from "next/server";
import { FeedbackSchema } from "@/lib/repeat/schema";
import { burstLimited, clientIp, hashIp, sameOrigin } from "@/lib/guard";
import { saveFeedback } from "@/lib/store";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  if (!sameOrigin(req)) return NextResponse.json({ error: "Forbidden." }, { status: 403 });
  if (burstLimited("f:" + hashIp(clientIp(req)), 5, 10 * 60_000)) {
    return NextResponse.json({ error: "Too many submissions. Please try again later." }, { status: 429 });
  }
  const parsed = FeedbackSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? "Please check the form." }, { status: 400 });
  }
  const f = parsed.data;
  if (f.hp) return NextResponse.json({ ok: true }); // bot: pretend success, store nothing
  if (!f.useful && !f.mostValuable && !f.missing && !f.useAgain && !f.email) {
    return NextResponse.json({ error: "Please answer at least one question." }, { status: 400 });
  }
  if (f.email && !f.consent) {
    return NextResponse.json({ error: "Please tick the consent box if you'd like us to keep your email." }, { status: 400 });
  }
  try {
    await saveFeedback(f);
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("[repeat] feedback save failed", e);
    return NextResponse.json({ error: "We couldn't save your feedback. Please try again." }, { status: 500 });
  }
}

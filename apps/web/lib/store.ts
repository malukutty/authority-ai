import { createHash, randomUUID } from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";
import postgres from "postgres";
import type { Feedback } from "./repeat/schema";

/**
 * Minimal persistence.
 * - DATABASE_URL set  → Postgres (tables are created on first use; see sql/schema.sql).
 * - otherwise         → JSON files under ./.data (local development only).
 *
 * We store: feedback the founder chooses to send, and a usage log (hashed IP, status, latency)
 * for abuse limits. Founder intake and reports are NOT stored unless the founder opts in
 * when sending feedback.
 */

export type UsageEvent = { ipHash: string; status: "ok" | "error" | "mock"; model: string; latencyMs: number };

export function hashIp(ip: string) {
  const salt = process.env.IP_HASH_SALT || "dev-salt";
  return createHash("sha256").update(`${salt}:${ip}`).digest("hex").slice(0, 32);
}

let sql: ReturnType<typeof postgres> | null = null;
let ready: Promise<void> | null = null;

function db() {
  const url = process.env.DATABASE_URL;
  if (!url) return null;
  sql ??= postgres(url, { max: 3, idle_timeout: 20, prepare: false });
  ready ??= (async () => {
    await sql!`create table if not exists repeat_usage (
      id bigserial primary key,
      created_at timestamptz not null default now(),
      ip_hash text not null,
      status text not null,
      model text not null,
      latency_ms integer not null
    )`;
    await sql!`create index if not exists repeat_usage_created_idx on repeat_usage (created_at)`;
    await sql!`create table if not exists repeat_feedback (
      id uuid primary key,
      created_at timestamptz not null default now(),
      report_id text,
      example boolean not null default false,
      useful text,
      most_valuable text,
      missing text,
      use_again text,
      interview boolean not null default false,
      email text,
      consent boolean not null default false,
      intake jsonb
    )`;
  })();
  return sql;
}

const DATA_DIR = path.join(process.cwd(), ".data");

async function appendJsonl(file: string, row: unknown) {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.appendFile(path.join(DATA_DIR, file), JSON.stringify(row) + "\n", "utf8");
}

async function readJsonl<T>(file: string): Promise<T[]> {
  try {
    const raw = await fs.readFile(path.join(DATA_DIR, file), "utf8");
    return raw
      .split("\n")
      .filter(Boolean)
      .map((l) => JSON.parse(l) as T);
  } catch {
    return [];
  }
}

export async function recordUsage(e: UsageEvent) {
  const s = db();
  if (s) {
    await ready;
    await s`insert into repeat_usage (ip_hash, status, model, latency_ms) values (${e.ipHash}, ${e.status}, ${e.model}, ${e.latencyMs})`;
    return;
  }
  await appendJsonl("usage.jsonl", { ...e, createdAt: new Date().toISOString() });
}

/** Counts successful + failed analyses (not mocks) in the last 24h, optionally for one IP. */
export async function countUsage(ipHash?: string): Promise<number> {
  const since = new Date(Date.now() - 24 * 60 * 60 * 1000);
  const s = db();
  if (s) {
    await ready;
    const rows = ipHash
      ? await s`select count(*)::int as n from repeat_usage where created_at > ${since} and status <> 'mock' and ip_hash = ${ipHash}`
      : await s`select count(*)::int as n from repeat_usage where created_at > ${since} and status <> 'mock'`;
    return rows[0]?.n ?? 0;
  }
  const rows = await readJsonl<UsageEvent & { createdAt: string }>("usage.jsonl");
  return rows.filter(
    (r) => r.status !== "mock" && new Date(r.createdAt) > since && (!ipHash || r.ipHash === ipHash),
  ).length;
}

export async function saveFeedback(f: Feedback) {
  const id = randomUUID();
  // Email is only kept when the founder ticked the consent box.
  const email = f.consent && f.email ? f.email : null;
  const intake = f.shareInputs && f.intake ? f.intake : null;
  const s = db();
  if (s) {
    await ready;
    await s`insert into repeat_feedback
      (id, report_id, example, useful, most_valuable, missing, use_again, interview, email, consent, intake)
      values (${id}, ${f.reportId || null}, ${f.example}, ${f.useful || null}, ${f.mostValuable || null},
              ${f.missing || null}, ${f.useAgain || null}, ${f.interview && !!email}, ${email}, ${!!email},
              ${intake ? s.json(intake as never) : null})`;
    return id;
  }
  await appendJsonl("feedback.jsonl", {
    id,
    createdAt: new Date().toISOString(),
    reportId: f.reportId,
    example: f.example,
    useful: f.useful,
    mostValuable: f.mostValuable,
    missing: f.missing,
    useAgain: f.useAgain,
    interview: f.interview && !!email,
    email,
    intake,
  });
  return id;
}

export function storageMode() {
  return process.env.DATABASE_URL ? "postgres" : "local-file";
}

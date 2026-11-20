# Authority AI website + Repeat MVP

Next.js 15 (App Router) · TypeScript · Tailwind v4 · Anthropic SDK · Zod · optional Postgres.

The design tokens (paper/ink palette, square corners, Newsreader + Work Sans) were taken from the live
theauthority.company stylesheet. The previous site's frontend was built in Lovable and its source is not in this
repository, so this is a new codebase that keeps that visual identity.

## Run locally

```bash
cd apps/web
npm install
cp .env.example .env.local      # add ANTHROPIC_API_KEY for real analyses
npm run dev                     # http://localhost:3000
npm test                        # unit tests
npm run build                   # production build + type check
```

No API key? Set `REPEAT_MOCK=1` in `.env.local` to click through the full flow. Mock mode returns the fictional
example report with a red "no model was called" banner, and is ignored when `NODE_ENV=production`.

## Routes

| Route | What it is |
|---|---|
| `/` | Authority AI homepage: philosophy, mission, first product |
| `/about` | Company story; archive of earlier essay titles |
| `/privacy` | Plain-language privacy notice |
| `/repeat` | Repeat product page |
| `/repeat/start` | 4-step founder intake (company → wins → sales motion → review) |
| `/repeat/report` | The founder's diagnostic (read from this browser's local storage) |
| `/repeat/example` | Illustrative report for a fictional company ("Dockett") |
| `POST /api/repeat/analyze` | Validates intake, applies limits, calls Claude, validates and sanitizes output |
| `POST /api/repeat/extract` | Server-side read of a public homepage (title, description, headings only) |
| `POST /api/repeat/feedback` | Stores feedback; email only with consent |

Old routes redirect: `/company-brain` → `/repeat`, `/demo` → `/repeat/example`, `/framework` → `/about`,
`/papers` → `/about#writing`.

## How analysis works

1. `IntakeSchema` (Zod) validates input: every field optional, 1,200-char cap, at most 5 wins.
   `checkReadiness` requires "what you sell" plus at least one win with three or more details.
2. `lib/repeat/prompt.ts` sends the input with explicit `(not provided)` markers inside `<founder_input>` tags,
   along with grounding rules: never invent, mark every finding `observed` or `hypothesis`, cite the win.
3. `lib/repeat/analyze.ts` generates the report in **two halves in parallel** with `client.beta.messages.parse`
   and structured output: sections A–D, then the headline plus E–H. Settings: model `claude-opus-5-5`, effort
   `medium`, 100s timeout, 1 retry, server-side refusal fallback on.
   - Why two halves: asked for all eight sections at once at medium effort, the model often filled the first
     half and left the rest blank. High effort fixed that but took ~100s.
   - Two half-size calls take ~40s and came back complete in every test.
4. Each half is checked for blank sections (`incompleteSections`). A half with blanks is retried once with a
   correction; if it is still incomplete, the founder gets an error instead of a half-empty report.
5. The merged output is validated again with Zod. `sanitizeReport` then removes any cited source that doesn't
   exist in the input (for example "Win 3" when only two wins were given).
5. Refusals, truncation, timeouts, rate limits, auth errors and schema failures each map to a clear user-facing error.

Report sections: A current motion · B ICP · C triggers · D process · E gaps · F next 10 customers · G 30-day
plan · H evidence & confidence.

## Data & privacy

- Intake answers and reports live in the founder's browser (`localStorage`). They're sent to the server and
  Anthropic only to generate a report, and are **not stored server-side** unless the founder ticks "include my
  answers" when sending feedback.
- Server storage: `repeat_usage` (hashed IP, status, latency; used for limits) and `repeat_feedback`.
  See `sql/schema.sql`. With `DATABASE_URL` set, this is Postgres (tables auto-created). Without it, data goes to
  JSONL files in `./.data`, which is **local development only**: serverless hosts don't persist those files.

## Abuse limits

Same-origin check on all POSTs · 64 KB body cap · 2 analyses/min per IP (in-memory, per instance) ·
`REPEAT_MAX_ANALYSES_PER_IP_PER_DAY` (default 5) · `REPEAT_MAX_ANALYSES_PER_DAY` global (default 200) ·
feedback honeypot. The extractor allows http(s) on ports 80/443 only, blocks private, loopback and link-local
addresses (rechecked on every redirect), times out after 8s and caps pages at 1.5 MB.

## Environment variables

| Name | Required | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes (for live analysis) | Server-only. |
| `DATABASE_URL` | yes in production | Postgres (Neon, Supabase, Vercel Postgres). |
| `IP_HASH_SALT` | yes in production | Long random string. |
| `REPEAT_MODEL` | no | Default `claude-opus-5-5`. |
| `REPEAT_MAX_ANALYSES_PER_IP_PER_DAY` / `REPEAT_MAX_ANALYSES_PER_DAY` | no | Defaults 5 / 200. |
| `NEXT_PUBLIC_SITE_URL` | no | This deployment's public URL. |
| `NEXT_PUBLIC_REPEAT_STANDALONE` | no | `1` = Repeat on its own subdomain; company links go to `NEXT_PUBLIC_COMPANY_URL`. |
| `NEXT_PUBLIC_COMPANY_URL` | no | Default `https://theauthority.company`. |
| `REPEAT_MOCK` | dev only | `1` = canned report, no model call. |

## Deploy

**Current plan:** theauthority.company stays on Lovable, and Repeat runs on Vercel at
`repeat.theauthority.company` in standalone mode (`NEXT_PUBLIC_REPEAT_STANDALONE=1`). The step-by-step guide,
including the Name.com DNS record, is in `docs/DEPLOY_REPEAT_SUBDOMAIN.md`. The matching Lovable homepage update
is in `docs/LOVABLE_HOMEPAGE_UPDATE.md`.

**Later option:** to move the whole site off Lovable, deploy without standalone mode and point the domain at
Vercel. That replaces the Lovable site.

**Check your Anthropic rate limits before sharing widely.** Each analysis makes two parallel Opus calls of
~4–5k output tokens each. On a newly funded account, three analyses started at once slowed to ~9 minutes each,
against ~40s for one on its own. Check your tier in the Anthropic Console, and lower
`REPEAT_MAX_ANALYSES_PER_DAY` if needed.

`/api/repeat/analyze` sets `maxDuration = 300`. On Vercel's Hobby plan the effective limit may be lower, so check
your plan's function duration.

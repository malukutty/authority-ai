# Deploying Repeat to repeat.theauthority.company

**Setup:** theauthority.company stays on Lovable. Repeat (`apps/web` in standalone mode) runs on Vercel at
`repeat.theauthority.company`. DNS for the domain is managed at **Name.com**.

The apex domain points to Lovable (`185.158.133.1`), and these steps don't change it.

## 1. Vercel project (about 10 minutes)

1. vercel.com → **Add New → Project** → import `malukutty/authority-ai`.
2. **Root Directory:** `apps/web`. Vercel detects the Next.js framework automatically.
3. **Environment Variables** (Production and Preview):

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_REPEAT_STANDALONE` | `1` |
   | `NEXT_PUBLIC_SITE_URL` | `https://repeat.theauthority.company` |
   | `NEXT_PUBLIC_COMPANY_URL` | `https://theauthority.company` |
   | `ANTHROPIC_API_KEY` | your key |
   | `IP_HASH_SALT` | any long random string |
   | `DATABASE_URL` | set automatically in step 2 |

4. Deploy, then open the `*.vercel.app` URL and run one analysis end to end.

## 2. Database (about 5 minutes)

In the Vercel project, go to **Storage → Create Database → Neon (Postgres)** and connect it to the project.
That sets `DATABASE_URL`. The tables are created the first time they're used; the schema is in
`apps/web/sql/schema.sql`. Redeploy afterwards so the variable takes effect.

Without `DATABASE_URL`, feedback and daily usage limits **are not saved** on Vercel.

## 3. Subdomain (about 5 minutes, plus DNS propagation)

1. In Vercel, go to **Project → Settings → Domains** and add `repeat.theauthority.company`. Vercel then shows
   the DNS record to create, normally a CNAME pointing to `cname.vercel-dns.com`. **Use the exact value Vercel
   shows.**
2. In Name.com, open **My Domains → theauthority.company → Manage DNS Records** and add:

   | Type | Host | Answer | TTL |
   |---|---|---|---|
   | CNAME | `repeat` | value from Vercel (e.g. `cname.vercel-dns.com`) | 300 |

   Don't change the existing `A` records for `theauthority.company` or `www`; they serve the Lovable site.
3. Wait for Vercel to show the domain as **Valid**. HTTPS is issued automatically.

## 4. Before sharing

- Check your Anthropic rate-limit tier. Each analysis makes two parallel calls, and on a new account several
  founders at once slowed to minutes per report.
- Confirm the contact email on `/privacy` (`hello@theauthority.company`) receives mail.
- Update the Lovable homepage: see `docs/LOVABLE_HOMEPAGE_UPDATE.md`.

## How standalone mode behaves

- `/` redirects to `/repeat`, and `/about` redirects to `https://theauthority.company/about`.
- The Authority AI logo, "by authority ai", About, Philosophy and Products links all go to the Lovable site.
- The sitemap lists only the Repeat pages, and social previews use the subdomain URL.
- The company pages in `apps/web` (`/`, `/about`) aren't used in this mode; they're kept for a possible later
  move off Lovable.

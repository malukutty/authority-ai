import { lookup } from "node:dns/promises";
import net from "node:net";

/**
 * Fetches public web pages server-side and returns only text that is literally on them
 * (title, meta description, headings, readable body text). No inference, no summarisation.
 * Guards against SSRF: http(s) only, standard ports, no private/loopback/link-local targets,
 * redirects re-validated, 8s timeout, 1.5 MB cap per page.
 */

export type Extracted = {
  url: string;
  title: string;
  description: string;
  headings: string[];
  /** Visible paragraph / list / heading text, de-duplicated and capped. */
  text: string;
  /** Same-site links whose path suggests about / pricing / customers / product pages. */
  keyLinks: string[];
};

/** Everything Repeat read from a company's public site, for the quick analysis. */
export type SiteRead = {
  url: string;
  title: string;
  description: string;
  headings: string[];
  pages: { url: string; text: string }[];
  /** Characters of readable text found. A low number usually means the site renders in the browser. */
  chars: number;
};

export class ExtractError extends Error {}

function isPrivateIp(ip: string) {
  if (net.isIPv4(ip)) {
    const [a, b] = ip.split(".").map(Number);
    return (
      a === 0 || a === 10 || a === 127 || a >= 224 ||
      (a === 100 && b >= 64 && b <= 127) ||
      (a === 169 && b === 254) ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 192 && b === 168) ||
      (a === 198 && (b === 18 || b === 19))
    );
  }
  const v = ip.toLowerCase();
  if (v.startsWith("::ffff:")) return isPrivateIp(v.slice(7));
  return v === "::" || v === "::1" || v.startsWith("fc") || v.startsWith("fd") || v.startsWith("fe8") || v.startsWith("fe9") || v.startsWith("fea") || v.startsWith("feb");
}

export function normalizeUrl(input: string): URL {
  let raw = input.trim();
  if (!raw) throw new ExtractError("Enter a website address.");
  if (!/^https?:\/\//i.test(raw)) raw = `https://${raw}`;
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new ExtractError("That doesn't look like a valid website address.");
  }
  if (!["http:", "https:"].includes(url.protocol)) throw new ExtractError("Only http and https websites are supported.");
  if (url.port && !["80", "443"].includes(url.port)) throw new ExtractError("Only standard web ports are supported.");
  if (url.username || url.password) throw new ExtractError("That doesn't look like a valid website address.");
  if (!url.hostname.includes(".") || url.hostname.endsWith(".local") || url.hostname.endsWith(".internal")) {
    throw new ExtractError("Enter a public website address.");
  }
  return url;
}

async function assertPublic(url: URL) {
  const host = url.hostname.replace(/^\[|\]$/g, "");
  const addrs = net.isIP(host) ? [{ address: host }] : await lookup(host, { all: true }).catch(() => []);
  if (addrs.length === 0) throw new ExtractError("We couldn't find that website.");
  if (addrs.some((a) => isPrivateIp(a.address))) throw new ExtractError("Enter a public website address.");
}

const decode = (s: string) =>
  s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#x27;|&#39;|&apos;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
    .replace(/\s+/g, " ")
    .trim();

const strip = (s: string) => decode(s.replace(/<[^>]+>/g, " "));

function meta(html: string, key: string) {
  const re = new RegExp(`<meta[^>]+(?:name|property)=["']${key}["'][^>]*>`, "i");
  const tag = html.match(re)?.[0];
  return tag ? decode(tag.match(/content=["']([^"']*)["']/i)?.[1] ?? "") : "";
}

const KEY_PATH = /\/(about|company|pricing|plans|customers|case-studies|solutions|product|platform|features|how-it-works|use-cases)(\/|$)/i;

export function parseHtml(html: string, url: string): Extracted {
  const body = html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<noscript[\s\S]*?<\/noscript>|<svg[\s\S]*?<\/svg>/gi, "");
  const title = meta(body, "og:title") || strip(body.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] ?? "");
  const description = meta(body, "description") || meta(body, "og:description");
  const headings = [...body.matchAll(/<h[12][^>]*>([\s\S]*?)<\/h[12]>/gi)]
    .map((m) => strip(m[1]))
    .filter((h) => h.length > 2 && h.length < 200);

  // Readable text blocks in page order, skipping navigation, headers and footers.
  const content = body.replace(/<(nav|footer|header)\b[\s\S]*?<\/\1>/gi, " ");
  const seen = new Set<string>();
  const blocks: string[] = [];
  for (const m of content.matchAll(/<(h[1-4]|p|li|blockquote|td|figcaption)\b[^>]*>([\s\S]*?)<\/\1>/gi)) {
    const t = strip(m[2]);
    if (t.length < 3 || t.length > 1200 || seen.has(t)) continue;
    seen.add(t);
    blocks.push(t);
  }

  const base = new URL(url);
  const keyLinks = new Set<string>();
  for (const m of body.matchAll(/<a[^>]+href=["']([^"'#]+)["']/gi)) {
    try {
      const u = new URL(decode(m[1]), base);
      if (u.host === base.host && KEY_PATH.test(u.pathname) && u.pathname !== base.pathname) {
        keyLinks.add(`${u.origin}${u.pathname}`);
      }
    } catch {
      /* ignore malformed hrefs */
    }
  }

  return {
    url,
    title: title.slice(0, 200),
    description: description.slice(0, 500),
    headings: [...new Set(headings)].slice(0, 6),
    text: blocks.join("\n").slice(0, 6000),
    keyLinks: [...keyLinks].slice(0, 12),
  };
}

async function fetchHtml(input: string, timeoutMs = 8000): Promise<{ html: string; url: URL }> {
  let url = normalizeUrl(input);
  for (let hop = 0; hop < 4; hop++) {
    await assertPublic(url);
    const res = await fetch(url, {
      redirect: "manual",
      signal: AbortSignal.timeout(timeoutMs),
      headers: { "user-agent": "RepeatBot/1.0 (+https://theauthority.company/privacy)", accept: "text/html" },
    }).catch(() => {
      throw new ExtractError("We couldn't reach that website.");
    });
    if (res.status >= 300 && res.status < 400 && res.headers.get("location")) {
      url = normalizeUrl(new URL(res.headers.get("location")!, url).toString());
      continue;
    }
    if (!res.ok) throw new ExtractError(`The website responded with an error (${res.status}).`);
    if (!(res.headers.get("content-type") ?? "").includes("html")) throw new ExtractError("That address isn't a web page.");
    const reader = res.body?.getReader();
    if (!reader) throw new ExtractError("The website returned an empty page.");
    let html = "";
    const dec = new TextDecoder();
    while (html.length < 1_500_000) {
      const { done, value } = await reader.read();
      if (done) break;
      html += dec.decode(value, { stream: true });
    }
    reader.cancel().catch(() => {});
    return { html, url };
  }
  throw new ExtractError("That website redirected too many times.");
}

/** Homepage summary only (title, description, headings). Used by the detailed intake's "Read my website". */
export async function extractWebsite(input: string): Promise<Extracted> {
  const { html, url } = await fetchHtml(input);
  const out = parseHtml(html, url.toString());
  if (!out.title && !out.description && out.headings.length === 0) {
    throw new ExtractError("We couldn't find readable text on that page. It may be rendered in the browser.");
  }
  return out;
}

/** Pick up to `n` subpages, preferring those most useful for understanding who a company serves. */
export function pickSubpages(links: string[], n = 2) {
  const rank = (u: string) => {
    const p = new URL(u).pathname.toLowerCase();
    if (/customers|case-studies/.test(p)) return 0;
    if (/about|company/.test(p)) return 1;
    if (/pricing|plans/.test(p)) return 2;
    if (/solutions|use-cases|how-it-works/.test(p)) return 3;
    return 4;
  };
  return [...links].sort((a, b) => rank(a) - rank(b)).slice(0, n);
}

/**
 * Reads a company's homepage plus up to two key subpages (in parallel, best effort).
 * Throws ExtractError only when the homepage itself can't be read.
 */
export async function readWebsite(input: string): Promise<SiteRead> {
  const { html, url } = await fetchHtml(input);
  const home = parseHtml(html, url.toString());
  const subs = await Promise.all(
    pickSubpages(home.keyLinks).map(async (link) => {
      try {
        const page = await fetchHtml(link, 6000);
        return { url: page.url.toString(), text: parseHtml(page.html, page.url.toString()).text.slice(0, 3000) };
      } catch {
        return null; // a missing subpage is never a reason to fail
      }
    }),
  );
  const pages = [
    { url: home.url, text: home.text },
    ...subs.filter((p): p is { url: string; text: string } => !!p && p.text.length > 0),
  ];
  return {
    url: home.url,
    title: home.title,
    description: home.description,
    headings: home.headings,
    pages,
    chars: pages.reduce((n, p) => n + p.text.length, 0) + home.description.length,
  };
}

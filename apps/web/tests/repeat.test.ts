import { test } from "node:test";
import assert from "node:assert/strict";
import { IntakeSchema, ReportSchema, FeedbackSchema, checkReadiness, usableWins } from "../lib/repeat/schema";
import { EXAMPLE_INTAKE, EXAMPLE_REPORT } from "../lib/repeat/example";
import { sanitizeReport, incompleteSections } from "../lib/repeat/analyze";
import { buildUserMessage, SYSTEM_PROMPT } from "../lib/repeat/prompt";
import { normalizeUrl, parseHtml, extractWebsite } from "../lib/extract";

const blank = () => IntakeSchema.parse({ company: {}, wins: [{}, {}, {}], motion: {} });

test("example report satisfies the report schema", () => {
  assert.equal(ReportSchema.safeParse(EXAMPLE_REPORT).success, true);
  assert.equal(IntakeSchema.safeParse(EXAMPLE_INTAKE).success, true);
});

test("blank intake is not ready, with a helpful reason", () => {
  const r = checkReadiness(blank());
  assert.equal(r.ok, false);
});

test("needs what-you-sell plus one win with 3+ details", () => {
  const i = blank();
  i.company.sells = "Payroll software";
  assert.equal(checkReadiness(i).ok, false);
  i.wins[0] = { ...i.wins[0], problem: "x", trigger: "y" };
  assert.equal(checkReadiness(i).ok, false);
  i.wins[0].whyChose = "z";
  assert.equal(checkReadiness(i).ok, true);
  assert.equal(usableWins(i).length, 1);
});

test("intake rejects oversized fields and more than 5 wins", () => {
  assert.equal(IntakeSchema.safeParse({ company: { sells: "x".repeat(1201) }, wins: [], motion: {} }).success, false);
  assert.equal(IntakeSchema.safeParse({ company: {}, wins: Array(6).fill({}), motion: {} }).success, false);
});

test("sanitizeReport strips sources that don't exist in the input and sorts the plan", () => {
  const twoWins = { ...EXAMPLE_INTAKE, wins: EXAMPLE_INTAKE.wins.slice(0, 2) };
  const r = sanitizeReport(
    { ...EXAMPLE_REPORT, plan: [...EXAMPLE_REPORT.plan].reverse() },
    twoWins,
  );
  const all = [
    ...r.current_motion.observations, ...r.icp.traits, ...r.icp.exclusions, ...r.triggers, ...r.process.steps,
  ].flatMap((f) => f.sources);
  assert.ok(!all.includes("Win 3"), "Win 3 should be removed when only 2 wins exist");
  assert.ok(all.includes("Win 1"));
  assert.deepEqual(r.plan.map((p) => p.week), [1, 2, 3, 4]);
});

test("prompt marks blanks explicitly and fences founder input as data", () => {
  const i = blank();
  i.company.sells = "Payroll software";
  const msg = buildUserMessage(i);
  assert.match(msg, /<founder_input>[\s\S]*<\/founder_input>/);
  assert.match(msg, /Buying trigger: \(not provided\)/);
  assert.match(msg, /"Win 1", "Win 2", "Win 3"/);
  assert.match(SYSTEM_PROMPT, /Never invent/);
});

test("feedback: email must be valid; honeypot is accepted (route drops it)", () => {
  assert.equal(FeedbackSchema.safeParse({ email: "nope" }).success, false);
  assert.equal(FeedbackSchema.safeParse({ email: "a@b.co", consent: true }).success, true);
  assert.equal(FeedbackSchema.safeParse({ hp: "bot" }).success, true);
});

test("url normalisation and SSRF guards", async () => {
  assert.equal(normalizeUrl("example.com").toString(), "https://example.com/");
  assert.throws(() => normalizeUrl("ftp://example.com"));
  assert.throws(() => normalizeUrl("http://localhost"));
  assert.throws(() => normalizeUrl("https://example.com:8080"));
  await assert.rejects(extractWebsite("http://127.0.0.1"), /public website/);
  await assert.rejects(extractWebsite("http://169.254.169.254/latest"), /public website/);
  await assert.rejects(extractWebsite("http://10.0.0.5"), /public website/);
});

test("parseHtml extracts only literal page text", () => {
  const out = parseHtml(
    `<html><head><title>Acme &amp; Co</title><meta name="description" content="We sell widgets."><script>var h1="<h1>no</h1>"</script></head>
     <body><h1>Better widgets</h1><h2>For teams</h2></body></html>`,
    "https://acme.test/",
  );
  assert.equal(out.title, "Acme & Co");
  assert.equal(out.description, "We sell widgets.");
  assert.deepEqual(out.headings, ["Better widgets", "For teams"]);
});

test("incompleteSections flags blank sections that the schema allows", () => {
  assert.deepEqual(incompleteSections(EXAMPLE_REPORT), []);
  const blanked = {
    ...EXAMPLE_REPORT,
    process: { steps: [], typical_cycle: "" },
    next_ten: { ...EXAMPLE_REPORT.next_ten, hypothesis: "" },
    plan: [],
    confidence: { observed: [], hypotheses: [], missing: [] },
  };
  const gaps = incompleteSections(blanked);
  for (const k of ["process.steps", "process.typical_cycle", "next_ten.hypothesis", "plan (needs 4 weeks)", "confidence.missing"]) {
    assert.ok(gaps.includes(k), `expected ${k} to be flagged`);
  }
});

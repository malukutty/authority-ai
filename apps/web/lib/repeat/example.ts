import type { Intake, Report, StoredReport } from "./schema";

/**
 * ILLUSTRATIVE EXAMPLE — fictional company, fictional customers.
 * "Dockett" is not a real Repeat user. Every detail below is invented to demonstrate the report format.
 */

export const EXAMPLE_INTAKE: Intake = {
  company: {
    name: "Dockett (fictional)",
    website: "",
    sells:
      "Software that tracks subcontractor insurance certificates (COIs) and lien waivers for general contractors. Subs upload documents by replying to an email; no login needed.",
    targetCustomer: "Regional general contractors, roughly 50–300 employees",
    payingCustomers: "9",
    dealSize: "About $14k ACV",
    salesCycle: "5–8 weeks usually",
    channels: "My network from my previous construction-tech job, a talk I gave at a state contractors' association event, some inbound from LinkedIn posts",
  },
  wins: [
    {
      label: "Texas commercial GC",
      segment: "Commercial general contractor, Texas",
      companySize: "~120 employees",
      discovery: "Came up to me after my talk at the state contractors' association chapter meeting",
      problem: "A project manager was spending about 6 hours a week chasing expired certificates from subs",
      trigger: "An uninsured sub's worker got hurt on one of their sites last spring and the claim landed on their own policy",
      buyers: "CFO signed. Risk manager drove it. One PM sat in on the demo.",
      objection: "'Our PMs won't log into another tool'",
      whyChose: "Subs upload by email, nobody on their side needs a login",
      timeToClose: "6 weeks",
    },
    {
      label: "Arizona multifamily GC",
      segment: "Multifamily general contractor, Arizona",
      companySize: "~80 employees",
      discovery: "Referred by the Texas GC's risk manager — they use the same insurance broker",
      problem: "Lender and owner audits require proof that every sub is insured and every lien waiver is in",
      trigger: "A lender draw was held up for two weeks because of missing lien waivers",
      buyers: "Controller and the owner",
      objection: "Price versus a spreadsheet and a part-time admin",
      whyChose: "Lien waiver tracking is tied to each draw, so they could see what was blocking payment",
      timeToClose: "4 weeks",
    },
    {
      label: "Colorado healthcare GC",
      segment: "General contractor focused on hospital and clinic projects, Colorado",
      companySize: "~250 employees",
      discovery: "Inbound from my LinkedIn post about COI audits",
      problem: "Hospital clients require proof of sub insurance at every project phase",
      trigger: "They hired a new risk manager whose mandate was to clean up sub compliance",
      buyers: "Risk manager, CFO, IT, and procurement ran a security review",
      objection: "Security questionnaire — they asked about SOC 2, which we don't have",
      whyChose: "I ran the demo using their actual sub list, so they saw their own gaps",
      timeToClose: "11 weeks",
    },
  ],
  motion: {
    leadSources: "Mostly my network and referrals through insurance brokers. A few inbound from LinkedIn.",
    qualification: "Gut feel. If they have a risk manager or a CFO who has been burned by a claim or an audit, I pursue it.",
    firstCallToClose: "Intro call, then a demo with their real sub list, then a 2-week pilot on one project, then a proposal",
    stalls: "After the pilot, when PMs have to change how they work. Also security reviews at bigger GCs.",
    founderDependent: "All demos, pilot setup, and pricing. Nobody else has run a demo.",
    biggestObstacle: "I don't know how to find more GCs who have just had a claim or a failed audit without a warm intro",
  },
};

export const EXAMPLE_REPORT: Report = {
  headline:
    "Your wins share one thing: each customer bought shortly after a specific loss event (an injury claim, a held lender draw, a new risk mandate). Treat that event as your qualification rule and find it through insurance brokers, not cold outreach.",
  data_quality: {
    level: "partial",
    note: "Three well-described wins is enough to form hypotheses, not to confirm patterns. Deal sizes per win and pilot-to-close rates were not provided.",
  },
  current_motion: {
    summary:
      "Customers come from the founder's network, one association talk, and a broker referral. The founder qualifies on instinct, demos with the prospect's real subcontractor list, runs a two-week single-project pilot, and prices each deal personally.",
    observations: [
      {
        statement: "Warm channels produced every win; no win came from cold outreach.",
        support: "observed",
        evidence: "Win 1: association talk. Win 2: broker referral. Win 3: inbound from a LinkedIn post.",
        sources: ["Win 1", "Win 2", "Win 3", "Company profile"],
      },
      {
        statement: "The demo built on the prospect's own sub list appears to be the moment of conviction.",
        support: "hypothesis",
        evidence: "Win 3: 'I ran the demo using their actual sub list, so they saw their own gaps.' Sales motion lists it as a standard step, but only Win 3 names it as the reason they chose you.",
        sources: ["Win 3", "Sales motion"],
      },
      {
        statement: "An insurance broker connected two of your customers.",
        support: "observed",
        evidence: "Win 2: 'Referred by the Texas GC's risk manager — they use the same insurance broker.' Sales motion: 'referrals through insurance brokers.'",
        sources: ["Win 2", "Sales motion"],
      },
    ],
  },
  icp: {
    statement:
      "Hypothesis: regional GCs with 80–250 employees that have a named risk owner (risk manager, CFO or controller) and have had a recent, costly compliance failure.",
    traits: [
      {
        statement: "A finance or risk leader owns the decision; PMs are users, not buyers.",
        support: "observed",
        evidence: "Win 1: CFO signed, risk manager drove. Win 2: controller and owner. Win 3: risk manager and CFO.",
        sources: ["Win 1", "Win 2", "Win 3"],
      },
      {
        statement: "A recent, concrete loss or mandate preceded the purchase.",
        support: "observed",
        evidence: "Win 1: injury claim on their policy. Win 2: lender draw held two weeks. Win 3: new risk manager with a cleanup mandate.",
        sources: ["Win 1", "Win 2", "Win 3"],
      },
      {
        statement: "Company size of 80–250 employees.",
        support: "hypothesis",
        evidence: "Wins were ~120, ~80 and ~250 employees. Three data points; the stated 50–300 range is untested at either end.",
        sources: ["Win 1", "Win 2", "Win 3", "Company profile"],
      },
      {
        statement: "Projects where a third party (lender, hospital owner) demands compliance proof.",
        support: "hypothesis",
        evidence: "Win 2 (lender audits) and Win 3 (hospital clients) — present in two wins, but different kinds of third party.",
        sources: ["Win 2", "Win 3"],
      },
    ],
    exclusions: [
      {
        statement: "GCs that require SOC 2 before purchase may stall or fall out of a short cycle.",
        support: "hypothesis",
        evidence: "Win 3 asked about SOC 2 and took 11 weeks, versus 4–6 weeks for the others. Sales motion: security reviews cause stalls.",
        sources: ["Win 3", "Sales motion"],
      },
    ],
  },
  triggers: [
    {
      statement: "A loss event: an insurance claim, a held payment, or a failed audit.",
      support: "observed",
      evidence: "Win 1: uninsured sub's injury claim. Win 2: lender draw held for missing lien waivers.",
      sources: ["Win 1", "Win 2"],
    },
    {
      statement: "A new risk or finance leader arrives with a mandate to clean up.",
      support: "hypothesis",
      evidence: "Win 3: 'They hired a new risk manager whose mandate was to clean up sub compliance.' Seen once.",
      sources: ["Win 3"],
    },
  ],
  process: {
    steps: [
      { name: "Warm introduction", description: "Talk, broker referral or a LinkedIn post creates the first conversation.", support: "observed", founder_dependent: true, sources: ["Win 1", "Win 2", "Win 3"] },
      { name: "Intro call", description: "Founder qualifies on instinct: has a risk owner been burned?", support: "observed", founder_dependent: true, sources: ["Sales motion"] },
      { name: "Demo on their sub list", description: "Founder loads the prospect's real subcontractors and shows their current gaps.", support: "observed", founder_dependent: true, sources: ["Win 3", "Sales motion"] },
      { name: "Two-week pilot", description: "One project. Founder sets it up. PM adoption is tested here.", support: "observed", founder_dependent: true, sources: ["Sales motion"] },
      { name: "Security review (larger GCs)", description: "Questionnaire; SOC 2 questions extend the cycle.", support: "observed", founder_dependent: false, sources: ["Win 3", "Sales motion"] },
      { name: "Proposal and pricing", description: "Founder prices each deal; price objection is answered against a spreadsheet plus admin cost.", support: "observed", founder_dependent: true, sources: ["Win 2", "Sales motion"] },
    ],
    typical_cycle: "4–11 weeks across the three wins (6, 4 and 11). Your stated typical is 5–8 weeks.",
  },
  gaps: [
    {
      category: "qualification",
      gap: "The qualifying question ('has a risk owner been burned?') is applied by gut feel and not written down.",
      consequence: "Nobody else can qualify a lead, and you can't measure whether the rule predicts closes.",
      evidence: "Sales motion: 'Gut feel. If they have a risk manager or a CFO who has been burned…'",
    },
    {
      category: "founder_dependency",
      gap: "Every demo, pilot setup and price is done by the founder.",
      consequence: "Pipeline capacity is capped by your calendar; the next 10 customers compete with the first 9 for your time.",
      evidence: "Sales motion: 'All demos, pilot setup, and pricing. Nobody else has run a demo.'",
    },
    {
      category: "handoff",
      gap: "No defined plan for moving from a successful pilot to PM adoption across projects.",
      consequence: "Deals stall exactly where the buyer (CFO/risk) hands off to the users (PMs).",
      evidence: "Sales motion: stalls 'after the pilot, when PMs have to change how they work.' Win 1 objection: PMs won't log in.",
    },
    {
      category: "undocumented_step",
      gap: "The 'demo on their own sub list' is not a repeatable asset — it depends on you preparing data by hand.",
      consequence: "Your most persuasive step is also your most time-consuming one.",
      evidence: "Win 3: demo used their actual sub list. Sales motion: demo with their real sub list.",
    },
    {
      category: "measurement",
      gap: "Pilot-to-close rate and source of each lead aren't tracked.",
      consequence: "You can't tell whether brokers, talks or LinkedIn produce better customers.",
      evidence: "Not mentioned anywhere in the input.",
    },
  ],
  next_ten: {
    hypothesis:
      "Insurance brokers who serve regional GCs are the most efficient route to GCs that just had a loss event, because brokers see claims and audits first.",
    who: "Risk managers, CFOs or controllers at 80–250 person GCs in TX, AZ and CO that had a claim, held draw or failed audit in the last 6 months.",
    trigger_to_watch: "A recent claim, a payment held over missing paperwork, or a new risk leader hire.",
    channel: "Construction-focused insurance brokers (start with the broker shared by Wins 1 and 2), plus new risk-manager hires visible on LinkedIn.",
    opening_angle: "'Your client just had a claim from an uninsured sub. Here's what their sub list looks like today.' Offer the sub-list gap check as the first step.",
    rationale:
      "Two of three wins followed a loss event (Win 1, Win 2), two of three were reached through warm channels connected to risk (Win 2 via broker), and your stated obstacle is finding GCs at the moment of pain without a warm intro. Brokers sit exactly at that moment.",
    how_to_test:
      "Ask 5 brokers for introductions to GCs with a recent loss event. Run the sub-list gap check for each introduced GC. Track intros → gap checks → pilots.",
    disconfirming_signal:
      "Fewer than 2 of 5 brokers make an introduction within 3 weeks, or introduced GCs convert to pilot no better than your current leads.",
  },
  plan: [
    {
      week: 1,
      title: "Write down the qualification rule",
      owner: "Founder",
      actions: [
        "Turn 'has a risk owner been burned?' into 3 yes/no questions: named risk owner? loss event in last 6 months? third party demanding proof?",
        "Score your 9 current customers and any lost deals against them.",
      ],
      success_metric: "At least 7 of 9 current customers pass all 3 questions; if not, revise the rule before using it.",
      rationale: "Your qualification is currently gut feel (Sales motion). You need a written rule before anyone else can use it or before you can test it.",
    },
    {
      week: 2,
      title: "Broker introduction test",
      owner: "Founder",
      actions: [
        "Ask the broker shared by Wins 1 and 2 for a 20-minute call: which of their GC clients had a claim or held draw this year?",
        "Reach out to 4 more construction-focused brokers with the same ask.",
      ],
      success_metric: "3 qualified introductions from 5 brokers within 14 days.",
      rationale: "Win 2 came through a broker; your obstacle is finding loss events without warm intros.",
    },
    {
      week: 3,
      title: "Productize the sub-list gap check",
      owner: "Founder, then a contractor or first hire",
      actions: [
        "Build a template that turns a GC's sub list into a one-page gap report (expired, missing, expiring in 30 days).",
        "Time how long it takes; aim for someone other than you to produce one.",
      ],
      success_metric: "Gap report produced in under 45 minutes by someone other than the founder.",
      rationale: "The demo on their own data is your strongest step (Win 3) and fully founder-dependent (Sales motion).",
    },
    {
      week: 4,
      title: "Pilot exit plan for PMs",
      owner: "Founder with the customer's risk owner",
      actions: [
        "Define pilot success up front with the buyer: % of subs current at day 14, PM hours saved.",
        "Add a 30-minute PM handoff session at the end of each pilot.",
      ],
      success_metric: "Next 2 pilots end with a signed proposal within 10 days of pilot end.",
      rationale: "Deals stall after the pilot when PMs must change behaviour (Sales motion); Win 1's objection was PM adoption.",
    },
  ],
  confidence: {
    observed: [
      "All three wins involved a finance or risk leader as the decision owner.",
      "All three wins were preceded by a specific loss event or mandate.",
      "All demos, pilots and pricing currently depend on the founder.",
      "Deals stall after pilots and during security reviews.",
    ],
    hypotheses: [
      "Brokers are a scalable source of GCs at the moment of pain.",
      "80–250 employees is the right size band.",
      "SOC 2 requirements predict long cycles.",
      "The own-data demo is the main reason customers choose Dockett.",
    ],
    missing: [
      { item: "Deal size for each win", why_it_matters: "Shows whether any segment pays meaningfully more." },
      { item: "Lost or stalled deals", why_it_matters: "Without losses, the ICP can't be tested against counter-examples." },
      { item: "Pilot-to-close rate", why_it_matters: "Tells you whether the pilot or the demo is doing the selling." },
      { item: "The other 6 customers", why_it_matters: "Six more wins would show whether these patterns hold." },
    ],
  },
};

export const EXAMPLE_STORED: StoredReport = {
  id: "example",
  createdAt: "2026-11-01T00:00:00.000Z",
  model: "illustrative",
  example: true,
  intake: EXAMPLE_INTAKE,
  report: EXAMPLE_REPORT,
};

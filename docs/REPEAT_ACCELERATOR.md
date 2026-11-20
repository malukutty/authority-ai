# Repeat — accelerator notes

## Customer
Early-stage B2B SaaS founders with roughly 5–20 paying customers. They have shown they can sell, but they don't
yet have a consistent, documented sales motion.

## Problem
First customers are won through the founder's network, instinct and effort. The founder knows why customers buy,
but that knowledge isn't written down as qualification rules, triggers or a process, so the next 10 customers
still depend on the founder.

## Product hypothesis (unvalidated)
A founder can describe three recent wins in about 15 minutes, and from that alone get a diagnostic specific enough
to change what they do over the next 30 days: an ICP draft, buying triggers, a reconstructed process,
repeatability gaps, one acquisition hypothesis, and four measurable weekly experiments.

What makes it different from a generic "AI GTM consultant":
- Every finding cites the win it came from and is labeled observed or hypothesis.
- Repeat says what data is missing instead of filling the gaps.
- The output is a test plan with disconfirming signals, not a strategy deck.

## What is built (working today)
- Repositioned Authority AI site and a Repeat product page.
- Website-first start: a website and a customer band, then a first read in about 25 seconds. No account, email
  or confidential data.
- Optional one-at-a-time questions that update the report in place, and an optional detailed diagnostic
  (three customer wins), prefilled from the answers.
- Server-side Claude analysis with structured, schema-validated output and source sanitization.
- Report with copy-plan, print/PDF, edit answers and regenerate.
- Feedback capture: usefulness, most valuable recommendation, what was missing, reuse intent, interview opt-in,
  optional consented email.
- Fictional example report for demos.
- Abuse limits, privacy page, mobile layout.

## What is still hypothetical
- Whether founders find the diagnostic useful. Nobody has used it yet: there are no users, customers or
  testimonials.
- Whether the plans lead to more customers.
- Willingness to pay, pricing and business model.
- Whether three wins is enough input, or whether CRM or call data is needed.

## Validation plan (proposal)
1. Recruit 15–20 founders in the target band from personal networks and founder communities.
2. Each completes Repeat. Count the share who rate it "very useful" and opt in to an interview.
3. Interview 8–10 of them. Which recommendation did they act on? What was wrong or generic?
4. Follow up at 30 days: did they run the experiments, and what happened?
5. Early signal to look for: at least 40% "very useful", and at least a third ran one or more experiments.
   These thresholds are a starting proposal; adjust them before starting.

## Two-minute demo script
1. **(0:00) `/`** "Authority AI's thesis: intelligence should lead to action. Our first product is Repeat."
2. **(0:15) `/repeat`** "For founders with 5–20 customers who sold the first ones themselves." Read the hero.
3. **(0:30) `/repeat/start`** Two inputs only: website and customer band. Submit a real website live; it takes
   about 25 seconds. While it runs: "No account, no email, nothing confidential; it reads only the public site."
   Show the first read: three obstacles and one experiment, each labelled website / from you / inferred.
   Answer one optional question ("Where did your last three customers come from?") and show "Updated with your
   answer".
4. **(0:50) `/repeat/example`** The banner is fictional on purpose. Walk through:
   - Headline.
   - ICP traits, with the Observed / Hypothesis labels and the cited wins.
   - The process, with its "Founder only" steps.
   - Next 10 customers, including the "it's wrong if" line.
   - Week 1 of the plan, with its measurable success metric.
5. **(1:40) Evidence & confidence** "It tells founders what it doesn't know."
6. **(1:50)** Click "Copy action plan" and show the feedback form. "Every founder who uses it teaches us something."

For a live run, have an `ANTHROPIC_API_KEY` configured. A first read takes about 25 seconds and each answer about
the same. The full diagnostic takes 40–60 seconds, so use the fictional example for that part of the demo.

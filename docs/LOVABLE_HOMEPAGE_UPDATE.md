# Updating theauthority.company in Lovable

The company site stays on Lovable, so these changes are made in the Lovable editor. Paste the prompt below into
Lovable chat, then review its changes before publishing.

**Do this after** `https://repeat.theauthority.company` is live, so the new links don't lead to a dead page.

---

## Prompt to paste into Lovable

> Reposition the site. Keep the existing visual design exactly: typography (Newsreader + Work Sans), colors,
> spacing, square corners, and the overall editorial feel. Change content, navigation and metadata only.
>
> **1. Navigation** (all pages): Philosophy (`/#philosophy`), Products (`/#products`), About (`/about`), and a
> highlighted link "Explore Repeat" to `https://repeat.theauthority.company`. Remove "Framework", "Company
> Brain" and "Meet Your Brain" from the navigation.
>
> **2. Homepage hero:**
> - Eyebrow: AUTHORITY AI
> - Heading: Intelligence should lead to action.
> - Text: We believe the next generation of companies will operate through intelligent systems that turn
>   knowledge into execution and measurable outcomes.
> - Primary button: "Explore Repeat" → `https://repeat.theauthority.company`
> - Secondary link: "Read our philosophy" → `#philosophy`
>
> **3. Homepage section with id `philosophy`:**
> - Eyebrow: PHILOSOPHY
> - Heading: Knowing is not the bottleneck. Acting on it is.
> - Text: Most companies already hold the intelligence they need: why customers buy, where deals stall, what
>   worked last quarter. It lives in the founder's head, in scattered notes, in instinct. Very little of it
>   becomes a system someone else can run.
> - Three numbered items:
>   1. Understand: capture what actually happened, from the evidence a company already has.
>   2. Systematize: turn recurring patterns into explicit rules, steps, and owners.
>   3. Improve: run the system, measure the outcome, and learn from what changes.
> - Mission line: Make business execution repeatable.
>
> **4. Homepage section with id `products`** (on a slightly darker paper background):
> - Eyebrow: OUR FIRST PRODUCT
> - Large wordmark: "repeat." in lowercase serif, with the period in the accent color
> - Line: Turn your first customers into repeatable revenue.
> - Text: For B2B founders with their first handful of paying customers. Repeat looks at how those customers
>   were actually won, separates real patterns from hunches, and turns them into a sales motion you can test
>   over the next 30 days.
> - Button "Explore Repeat" → `https://repeat.theauthority.company`; link "See an example report" →
>   `https://repeat.theauthority.company/repeat/example`
>
> **5. Remove** the Company Brain / Decision Infrastructure sections from the homepage. Point the
> `/company-brain` and `/demo` pages to `https://repeat.theauthority.company`, or remove them. Keep `/papers`
> and the papers themselves, but put them under a heading "Writing" with the subtitle "Earlier essays on how
> companies understand themselves."
>
> **6. About page:** replace the "Meet Your Company's Brain" call to action with "Explore Repeat" →
> `https://repeat.theauthority.company`. Add a short section "What we are building first": repeat. helps
> early-stage B2B founders turn how they won their first customers into a sales motion they can test and hand
> off. It is early: a working product built to test a hypothesis, and we are learning from every founder who
> tries it.
>
> **7. Metadata:**
> - Title: "Authority AI | Intelligence should lead to action"
> - Description: "Authority AI builds intelligent systems that turn knowledge into execution. Our mission is to
>   make business execution repeatable. Our first product is Repeat."
> - Use the same title and description for Open Graph and Twitter. Regenerate the social preview image with
>   the new heading, so it no longer shows "The Brain for Companies".
>
> Do not mention any other products. Do not add testimonials, customer logos or usage numbers.

---

## After Lovable applies it, check

- [ ] No "Company Brain", "Decision Infrastructure" or "The Brain for Companies" text left in the navigation,
      homepage, About page, page titles or social preview.
- [ ] Every "Explore Repeat" link opens `https://repeat.theauthority.company`.
- [ ] `/#philosophy` and `/#products` scroll to the right sections. Repeat's header links to these anchors.
- [ ] `/about` loads. Repeat redirects its own `/about` there.
- [ ] Mobile layout still looks right.

/**
 * Two ways to run this app:
 * - Full site (default): company pages and Repeat on one domain.
 * - Standalone Repeat (NEXT_PUBLIC_REPEAT_STANDALONE=1): deployed on its own subdomain
 *   (e.g. repeat.theauthority.company) while the company site stays on Lovable.
 *   "/" goes to the Repeat page and company links point to COMPANY_URL.
 */
export const STANDALONE = process.env.NEXT_PUBLIC_REPEAT_STANDALONE === "1";
export const COMPANY_URL = (process.env.NEXT_PUBLIC_COMPANY_URL || "https://theauthority.company").replace(/\/$/, "");
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || (STANDALONE ? "https://repeat.theauthority.company" : COMPANY_URL);
export const CONTACT_EMAIL = "hello@theauthority.company";

/** A link to a company page: local in full-site mode, the company site in standalone mode. */
export function companyHref(path: string) {
  return STANDALONE ? `${COMPANY_URL}${path}` : path;
}

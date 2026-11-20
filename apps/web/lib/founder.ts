/**
 * The founder shown on the Repeat landing page. Fill these in before merging to main.
 *
 * Anything left empty is hidden in production (no "[YOUR NAME]" ever ships);
 * in local development a visible placeholder shows where it goes.
 *
 * photo: put the image in apps/web/public/ (e.g. "/founder.jpg"), square, at least 256×256.
 * calendarUrl: a booking link (Cal.com, Calendly, Google Calendar appointment page).
 */
export const FOUNDER = {
  name: "",
  /** One line, e.g. "Former Head of Revenue Operations at …" */
  background: "",
  photo: "",
  calendarUrl: "",
};

export const SHOW_PLACEHOLDERS = process.env.NODE_ENV !== "production";

/** The value, or a placeholder in development, or null (hide it) in production. */
export function founderField(value: string, placeholder: string): string | null {
  if (value.trim()) return value.trim();
  return SHOW_PLACEHOLDERS ? placeholder : null;
}

/**
 * The founder shown on the Repeat landing page.
 *
 * Anything left empty is hidden in production (no "[YOUR NAME]" ever ships);
 * in local development a visible placeholder shows where it goes.
 *
 * photo: put the image in apps/web/public/ (e.g. "/founder.jpg"), square, at least 256×256.
 * calendarUrl: a booking link (Cal.com, Calendly, Google Calendar appointment page).
 */
export const FOUNDER = {
  name: "Bhavia Velayudhan",
  title: "Founder & CEO, Authority AI",
  /** One line shown after the title. */
  background: "Making business execution repeatable.",
  photo: "",
  calendarUrl: "https://calendar.app.google/UAcpfcVr53ty1tFs7",
};

export const SHOW_PLACEHOLDERS = process.env.NODE_ENV !== "production";

/** The value, or a placeholder in development, or null (hide it) in production. */
export function founderField(value: string, placeholder: string): string | null {
  if (value.trim()) return value.trim();
  return SHOW_PLACEHOLDERS ? placeholder : null;
}

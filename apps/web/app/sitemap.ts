import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/repeat", "/repeat/example", "/about", "/privacy"].map((p) => ({ url: `${SITE_URL}${p}` }));
}

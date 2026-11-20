import type { MetadataRoute } from "next";
import { SITE_URL, STANDALONE } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const paths = STANDALONE
    ? ["/repeat", "/repeat/example", "/privacy"]
    : ["", "/repeat", "/repeat/example", "/about", "/privacy"];
  return paths.map((p) => ({ url: `${SITE_URL}${p}` }));
}

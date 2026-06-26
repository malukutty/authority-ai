from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

FETCH_TIMEOUT_SECONDS = 10.0
USER_AGENT = "AuthorityAI-WebsiteExtractor/1.0"

TITLE_SUFFIXES = (
    " | Home",
    " - Home",
    " | Company",
    " - Company",
)

LINK_PATTERNS: dict[str, tuple[str, ...]] = {
    "pricing": ("pricing",),
    "docs": ("docs", "documentation"),
    "careers": ("careers", "jobs"),
    "about": ("about",),
    "contact": ("contact",),
    "blog": ("blog",),
}


class WebsiteFetchError(Exception):
    pass


class WebsiteEmptyError(Exception):
    pass


@dataclass
class ExtractedWebsiteData:
    source_url: str
    canonical_url: str
    company_name: str
    description: str
    product: str
    industry: str
    icp: str
    pricing: str
    stage: str = "Unknown"
    employees: str = "Unknown"
    funding: str = "Unknown"
    public_links: dict[str, str] = field(default_factory=dict)
    fields_extracted: list[str] = field(default_factory=list)
    confidence: str = "low"
    page_title: str = ""
    meta_description: str = ""
    og_title: str = ""
    og_description: str = ""
    h1_text: str = ""
    h2_text: str = ""


def normalize_website_url(website_url: str) -> str:
    url = website_url.strip()
    if not url:
        raise WebsiteFetchError("Website URL is required.")

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    if not parsed.netloc:
        raise WebsiteFetchError("Website URL is invalid.")

    return url


def _clean_title(title: str) -> str:
    cleaned = title.strip()
    for suffix in TITLE_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()

    for separator in (" | ", " - "):
        if separator in cleaned:
            cleaned = cleaned.split(separator, 1)[0].strip()

    return cleaned


def _domain_company_name(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    label = host.split(".")[0]
    if not label:
        return "Unknown"

    return label.replace("-", " ").title()


def _meta_content(soup: BeautifulSoup, *keys: str) -> str:
    for key in keys:
        tag = soup.find("meta", attrs={"name": key}) or soup.find(
            "meta", attrs={"property": key}
        )
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def _visible_heading(soup: BeautifulSoup, tag_name: str) -> str:
    for tag in soup.find_all(tag_name):
        text = tag.get_text(" ", strip=True)
        if text:
            return text
    return ""


def _meaningful_paragraph(soup: BeautifulSoup) -> str:
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if len(text) >= 40 and not text.lower().startswith("cookie"):
            return text
    return ""


def _combined_text(*parts: str) -> str:
    return " ".join(part for part in parts if part).lower()


def _infer_industry(text: str) -> str:
    if any(keyword in text for keyword in ("ai", "agent", "automation", "copilot", "llm")):
        return "AI Software"
    if any(keyword in text for keyword in ("analytics", "dashboard", "metrics", "bi")):
        return "Analytics Software"
    if any(keyword in text for keyword in ("email", "deliverability", "smtp")):
        return "Developer Email Infrastructure"
    if any(
        keyword in text
        for keyword in ("developer", "api", "sdk", "infrastructure")
    ):
        return "Developer Tools"
    if any(keyword in text for keyword in ("sales", "crm", "pipeline")):
        return "Sales Software"
    return "B2B SaaS"


def _infer_icp(text: str) -> str:
    if any(
        keyword in text
        for keyword in ("developers", "engineering teams", "engineering team", "api")
    ):
        return "Developers and engineering teams"
    if any(keyword in text for keyword in ("sales", "revenue", "gtm")):
        return "Revenue and GTM teams"
    if any(keyword in text for keyword in ("founders", "startups", "startup")):
        return "Startup founders and operators"
    return "Unknown"


def _build_product(h1: str, h2: str, meta_description: str, description: str) -> str:
    for candidate in (h1, h2, meta_description, description):
        if candidate and candidate != "Unknown":
            return candidate[:500]
    return "Unknown"


def _extract_public_links(soup: BeautifulSoup, base_url: str) -> dict[str, str]:
    links: dict[str, str] = {}

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        absolute_url = urljoin(base_url, href)
        haystack = " ".join(
            [
                href.lower(),
                anchor.get_text(" ", strip=True).lower(),
            ]
        )

        for link_type, patterns in LINK_PATTERNS.items():
            if link_type in links:
                continue
            if any(pattern in haystack for pattern in patterns):
                links[link_type] = absolute_url

    return links


def _confidence_for(company_name: str, description: str, product: str) -> str:
    has_name = company_name not in {"", "Unknown"}
    has_description = description not in {"", "Unknown"}
    has_product = product not in {"", "Unknown"}

    if has_name and has_description and has_product:
        return "high"
    if has_name and (has_description or has_product):
        return "medium"
    return "low"


def _track_fields(data: ExtractedWebsiteData) -> list[str]:
    extracted: list[str] = []
    for field_name in (
        "company_name",
        "description",
        "product",
        "industry",
        "icp",
        "pricing",
        "website",
    ):
        value = getattr(data, field_name, "")
        if value and value != "Unknown":
            extracted.append(field_name)
    return extracted


def fetch_homepage_html(url: str) -> tuple[str, str]:
    try:
        with httpx.Client(
            timeout=FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise WebsiteFetchError(
            "Unable to analyze website. Please check the URL and try again."
        ) from exc

    html = response.text.strip()
    if not html:
        raise WebsiteEmptyError("Website could not be analyzed from public content.")

    final_url = str(response.url)
    return html, final_url


def extract_public_knowledge(website_url: str) -> ExtractedWebsiteData:
    normalized_url = normalize_website_url(website_url)
    html, final_url = fetch_homepage_html(normalized_url)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    page_title = soup.title.get_text(strip=True) if soup.title else ""
    meta_description = _meta_content(soup, "description")
    og_site_name = _meta_content(soup, "og:site_name")
    og_title = _meta_content(soup, "og:title")
    og_description = _meta_content(soup, "og:description")
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical_url = (
        urljoin(final_url, canonical_tag["href"].strip())
        if canonical_tag and canonical_tag.get("href")
        else final_url
    )

    h1_text = _visible_heading(soup, "h1")
    h2_text = _visible_heading(soup, "h2")
    paragraph_text = _meaningful_paragraph(soup)

    company_name = "Unknown"
    for candidate in (
        og_site_name,
        _clean_title(og_title) if og_title else "",
        _clean_title(page_title) if page_title else "",
        _domain_company_name(final_url),
    ):
        if candidate and candidate != "Unknown":
            company_name = candidate
            break

    description = "Unknown"
    for candidate in (
        meta_description,
        og_description,
        paragraph_text,
        " ".join(part for part in (h1_text, h2_text) if part).strip(),
    ):
        if candidate:
            description = candidate[:1000]
            break

    product = _build_product(h1_text, h2_text, meta_description, description)
    combined_text = _combined_text(
        page_title,
        meta_description,
        og_title,
        og_description,
        h1_text,
        h2_text,
        paragraph_text,
        description,
        product,
    )

    public_links = _extract_public_links(soup, final_url)
    pricing = "Pricing page available" if public_links.get("pricing") else "Unknown"

    if not any([page_title, meta_description, og_title, h1_text, paragraph_text]):
        raise WebsiteEmptyError("Website could not be analyzed from public content.")

    data = ExtractedWebsiteData(
        source_url=final_url,
        canonical_url=canonical_url,
        company_name=company_name,
        description=description,
        product=product,
        industry=_infer_industry(combined_text),
        icp=_infer_icp(combined_text),
        pricing=pricing,
        public_links=public_links,
        page_title=page_title,
        meta_description=meta_description,
        og_title=og_title,
        og_description=og_description,
        h1_text=h1_text,
        h2_text=h2_text,
    )
    data.confidence = _confidence_for(data.company_name, data.description, data.product)
    data.fields_extracted = _track_fields(data)
    return data

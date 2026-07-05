from __future__ import annotations

import html
import posixpath
import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
REPO_BLOB = "https://github.com/hugoii/llm-agent-audit/blob/master"


ARTICLES = [
    {
        "slug": "ap-payment-approval",
        "source": "docs/payment-approval-is-not-user-authorization.md",
        "title": "A payment approval is not user authorization",
        "eyebrow": "AP/payment case note",
        "description": "A station-readable worked case note on why a valid invoice approval does not prove that the current actor may schedule payment.",
        "type": "Worked case note",
        "scope": "Synthetic AP workflow using simulated payment tools and generated data.",
        "claim": "Read this as a worked boundary case, not as a live ERP audit, model ranking, or fraud certification.",
        "primary": {"label": "AP review page", "href": "../../payment-authorization-review/"},
    },
    {
        "slug": "multi-turn-authorization-drift",
        "source": "docs/multi-turn-authorization-drift-case-note.md",
        "title": "When an agent treats a note as authorization",
        "eyebrow": "Multi-turn case note",
        "description": "A worked multi-turn case note showing how approval-looking context can drift into a later high-impact action.",
        "type": "Worked case note",
        "scope": "Synthetic healthcare prior-authorization workflow. No PHI, no PII, no production access.",
        "claim": "This is not a benchmark or a claim that every model will fail. It shows the trace shape ActionBoundary tests.",
        "primary": {"label": "Method note", "href": "../#multi-turn-method"},
    },
    {
        "slug": "ap-poisoned-document",
        "source": "docs/ap-action-boundary-case-note.md",
        "title": "When an accounts-payable agent reads a poisoned document",
        "eyebrow": "AP/data-export case note",
        "description": "A worked AP case note showing how business documents can push an agent toward an unauthorized data export.",
        "type": "Worked case note",
        "scope": "Synthetic AP workflow using simulated tools, generated documents, and no customer data.",
        "claim": "Read this as a public method example for untrusted business context, not as a customer incident or vendor finding.",
        "primary": {"label": "AP review page", "href": "../../payment-authorization-review/"},
    },
    {
        "slug": "model-choice-authorization-layer",
        "source": "docs/model-choice-is-not-an-authorization-layer.md",
        "title": "Model choice is not an authorization layer",
        "eyebrow": "Model-behavior note",
        "description": "A public note on why model tier and refusal behavior do not replace application-layer authorization for high-impact tools.",
        "type": "Method and evidence note",
        "scope": "Synthetic public battery. Simulated tools only. No vendor production product finding.",
        "claim": "This is not a vendor ranking or global safety verdict. The useful conclusion is the need for runtime authorization checks.",
        "primary": {"label": "Evidence status", "href": "../#source-layer"},
    },
    {
        "slug": "stripe-agent-toolkit-authorization-boundary",
        "source": "docs/stripe-agent-toolkit-authorization-boundary-review.md",
        "title": "Stripe public-sample test-mode authorization review",
        "eyebrow": "Stripe L3 method note",
        "description": "A Stripe test-mode L3 slice where the official sample created unauthorized test coupons from ordinary business email, then the same write path was denied with the gate.",
        "og_image": "https://actionboundary.dev/og-stripe-test-mode.png",
        "type": "L3 method and evidence note",
        "scope": "Stripe test-mode coupon slice using the public stripe/ai repository and official sample. No live keys, production systems, customer data, payment card data, or live money movement.",
        "claim": "Read this as a bounded test-mode method demonstration, not as a Stripe engagement, endorsement, vulnerability report, production finding, or full Stripe-surface audit.",
        "primary": {"label": "Stripe MCP docs", "href": "https://docs.stripe.com/mcp"},
    },
    {
        "slug": "ap-l3-l5-control-experiment",
        "source": "docs/ap-l3-l5-control-experiment.md",
        "title": "AP Deep Payment-Control Experiment",
        "eyebrow": "AP/payment method note",
        "description": "A method note for post-approval mutation, inter-agent handoff, retry/idempotency, and benign payment controls.",
        "type": "Payment-control method note",
        "scope": "Synthetic AP/payment traces that demonstrate scorer behavior before a customer pilot.",
        "claim": "This page exposes the public evidence standard, not private customer scenarios, credentials, or production findings.",
        "primary": {"label": "AP review page", "href": "../../payment-authorization-review/"},
    },
    {
        "slug": "evidence-readiness-check",
        "source": "pilot/evidence-readiness-check.md",
        "title": "Evidence Readiness Check",
        "eyebrow": "Customer readiness",
        "description": "A pre-pilot gate for deciding whether one existing redacted trace can support a defensible authorization verdict.",
        "type": "Pre-pilot diagnostic",
        "scope": "Existing redacted trace, exported log, or one synthetic staging run.",
        "claim": "This is not a full authorization review or security assessment. It decides whether the evidence is scoreable.",
        "primary": {"label": "Pilot scope", "href": "../../index.html#pilot"},
    },
    {
        "slug": "what-we-need",
        "source": "pilot/what-we-need.md",
        "title": "What ActionBoundary needs first",
        "eyebrow": "First-contact checklist",
        "description": "The three details ActionBoundary needs before drafting the first scenario set for an agent workflow.",
        "type": "Buyer intake note",
        "scope": "Product, one action surface, and one safe trace or test path if available.",
        "claim": "Do not send credentials, production data, PHI, PII, payment data, or private traces through public channels.",
        "primary": {
            "label": "Send 3 details",
            "href": "mailto:jiahao@actionboundary.dev?subject=3%20scenarios%20for%20our%20agent",
        },
    },
    {
        "slug": "technical-handoff",
        "source": "pilot/client-handoff.md",
        "title": "Technical handoff for an Agent Authorization Review",
        "eyebrow": "Pilot handoff",
        "description": "A client-facing handoff page for safe staging paths, trace shape, data boundaries, and expected engineering work.",
        "type": "Pilot setup note",
        "scope": "Public handoff guidance for staging or sandbox reviews, redacted traces, and synthetic data.",
        "claim": "This is the safe client interface for setup, not a private implementation playbook or production-access request.",
        "primary": {"label": "Start with 3 details", "href": "../what-we-need/"},
    },
    {
        "slug": "control-alignment",
        "source": "docs/control-alignment.md",
        "title": "ActionBoundary Control Alignment",
        "eyebrow": "Review-language map",
        "description": "A public map from trace-backed authorization evidence to common AI-agent and AP/payment-control language.",
        "type": "Control-language map",
        "scope": "Reference language for review discussion; no certification, audit opinion, or legal conclusion.",
        "claim": "This page helps reviewers understand the evidence fields. It does not claim compliance certification or audit approval.",
        "primary": {"label": "Trust boundary", "href": "../../trust.html"},
    },
]

ONSITE_ARTICLES = {item["source"]: item["slug"] for item in ARTICLES}
ONSITE_PAGES = {
    "TRUST.md": "../../trust.html",
}


def repo_blob(path: str) -> str:
    return f"{REPO_BLOB}/{quote(path.replace(chr(92), '/'), safe='/#')}"


def source_github(article: dict[str, str]) -> str:
    return repo_blob(article["source"])


def normalize_href(source_path: Path, href: str, current_slug: str) -> str:
    if re.match(r"^(?:https?:|mailto:|tel:|#)", href):
        return href

    base, fragment = href, ""
    if "#" in href:
        base, fragment = href.split("#", 1)
        fragment = f"#{fragment}"

    if not base:
        return fragment

    resolved = (source_path.parent / base).resolve()
    try:
        rel = resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return href

    if rel in ONSITE_PAGES:
        return ONSITE_PAGES[rel] + fragment

    if rel in ONSITE_ARTICLES:
        slug = ONSITE_ARTICLES[rel]
        if slug == current_slug:
            return f"./{fragment}"
        return f"../{slug}/{fragment}"

    return repo_blob(rel) + fragment


def inline_html(text: str, source_path: Path, current_slug: str) -> str:
    tokens: list[str] = []

    def store(value: str) -> str:
        token = f"@@HTMLTOKEN{len(tokens)}@@"
        tokens.append(value)
        return token

    def code_repl(match: re.Match[str]) -> str:
        return store(f"<code>{html.escape(match.group(1))}</code>")

    def link_repl(match: re.Match[str]) -> str:
        label = inline_html(match.group(1), source_path, current_slug)
        href = normalize_href(source_path, match.group(2), current_slug)
        return store(f'<a href="{html.escape(href, quote=True)}">{label}</a>')

    text = re.sub(r"`([^`]+)`", code_repl, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    rendered = html.escape(text, quote=False)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", rendered)
    for idx, value in enumerate(tokens):
        rendered = rendered.replace(f"@@HTMLTOKEN{idx}@@", value)
    return rendered


def heading_id(text: str) -> str:
    raw = re.sub(r"<[^>]+>", "", text)
    raw = re.sub(r"[^a-zA-Z0-9]+", "-", raw.lower()).strip("-")
    return raw or "section"


def render_table(rows: list[str], source_path: Path, current_slug: str) -> str:
    parsed = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        parsed.append(cells)
    if len(parsed) < 2:
        return ""

    header = parsed[0]
    body = parsed[2:] if re.match(r"^:?-{3,}:?$", parsed[1][0]) else parsed[1:]
    out = ['<div class="table-wrap"><table>']
    out.append("<thead><tr>")
    for cell in header:
        out.append(f"<th>{inline_html(cell, source_path, current_slug)}</th>")
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{inline_html(cell, source_path, current_slug)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def render_markdown(markdown: str, source_path: Path, current_slug: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_type: str | None = None
    blockquote: list[str] = []
    table_lines: list[str] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    skipped_h1 = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(part.strip() for part in paragraph).strip()
            if text:
                out.append(f"<p>{inline_html(text, source_path, current_slug)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items, list_type
        if list_items:
            tag = list_type or "ul"
            out.append(f"<{tag}>")
            for item in list_items:
                out.append(f"<li>{inline_html(item, source_path, current_slug)}</li>")
            out.append(f"</{tag}>")
        list_items = []
        list_type = None

    def flush_blockquote() -> None:
        nonlocal blockquote
        if blockquote:
            text = " ".join(blockquote).strip()
            out.append(f"<blockquote><p>{inline_html(text, source_path, current_slug)}</p></blockquote>")
            blockquote = []

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            rendered = render_table(table_lines, source_path, current_slug)
            if rendered:
                out.append(rendered)
            table_lines = []

    def flush_all() -> None:
        flush_paragraph()
        flush_list()
        flush_blockquote()
        flush_table()

    for raw_line in lines:
        line = raw_line.rstrip()

        if in_code:
            if line.startswith("```"):
                out.append(
                    f'<pre><code class="language-{html.escape(code_lang)}">'
                    + html.escape("\n".join(code_lines))
                    + "</code></pre>"
                )
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                code_lines.append(raw_line)
            continue

        fence = re.match(r"^```([A-Za-z0-9_-]*)", line)
        if fence:
            flush_all()
            in_code = True
            code_lang = fence.group(1) or "text"
            code_lines = []
            continue

        if not line.strip():
            flush_paragraph()
            flush_blockquote()
            flush_table()
            continue

        if re.match(r"^\s*\|.+\|\s*$", line):
            flush_paragraph()
            flush_list()
            flush_blockquote()
            table_lines.append(line)
            continue

        flush_table()

        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_all()
            level = len(heading.group(1))
            text = inline_html(heading.group(2).strip(), source_path, current_slug)
            if level == 1 and not skipped_h1:
                skipped_h1 = True
                continue
            level = min(max(level, 2), 4)
            out.append(f'<h{level} id="{heading_id(text)}">{text}</h{level}>')
            continue

        if re.match(r"^\s*-{3,}\s*$", line):
            flush_all()
            out.append("<hr>")
            continue

        quote_match = re.match(r"^\s*>\s?(.*)$", line)
        if quote_match:
            flush_paragraph()
            flush_list()
            blockquote.append(quote_match.group(1))
            continue

        ordered = re.match(r"^\s*\d+\.\s+(.+)$", line)
        unordered = re.match(r"^\s*[-*]\s+(.+)$", line)
        if ordered or unordered:
            flush_paragraph()
            flush_blockquote()
            wanted = "ol" if ordered else "ul"
            if list_type and list_type != wanted:
                flush_list()
            list_type = wanted
            list_items.append((ordered or unordered).group(1).strip())
            continue

        continuation = re.match(r"^\s{2,}(.+)$", raw_line)
        if continuation and list_items:
            list_items[-1] = f"{list_items[-1]} {continuation.group(1).strip()}"
            continue

        flush_list()
        flush_blockquote()
        paragraph.append(line)

    if in_code:
        out.append(
            f'<pre><code class="language-{html.escape(code_lang)}">'
            + html.escape("\n".join(code_lines))
            + "</code></pre>"
        )
    flush_all()
    return "\n".join(out)


def nav_html() -> str:
    return """
<nav class="site-nav" aria-label="Primary">
  <div class="nav-inner">
    <a class="brand" href="../../index.html" aria-label="ActionBoundary home">
      <img class="brand-mark" src="../../assets/actionboundary-mark.svg" alt="" width="30" height="30" aria-hidden="true">
      <span class="brand-copy">
        <strong>ActionBoundary</strong>
        <span class="brand-subtitle">Agent Authorization Review</span>
      </span>
    </a>
    <div class="nav-links" aria-label="Site links">
      <div class="nav-dropdown">
        <a class="nav-dropdown-trigger" href="../../index.html#what" aria-haspopup="true">
          What we test <span aria-hidden="true">&#9662;</span>
        </a>
        <div class="nav-dropdown-panel" aria-label="Review paths">
          <a class="nav-path nav-path-featured" href="../../payment-authorization-review/">
            <strong>AP / payment authorization</strong>
            <span>User, approval, vendor-bank, terminal outcome.</span>
          </a>
          <a class="nav-path" href="../../index.html#intake">
            <strong>Record changes / ERP writes</strong>
            <span>Source-of-truth authority for business state changes.</span>
          </a>
          <a class="nav-path" href="../../index.html#intake">
            <strong>Data export / access grants</strong>
            <span>Actor, scope, tenant, and destination checks.</span>
          </a>
          <a class="nav-path" href="../../index.html#intake">
            <strong>Support, scheduling, operations</strong>
            <span>Agent handoffs where authority can drift.</span>
          </a>
        </div>
      </div>
      <a href="../../index.html#report">Sample report</a>
      <a href="../../index.html#pilot">Pilot</a>
      <a href="../../trust.html">Trust</a>
      <a href="../../index.html#intake">Start</a>
      <div class="nav-dropdown about-menu">
        <a class="nav-dropdown-trigger" href="../../why.html" aria-haspopup="true">
          About <span aria-hidden="true">&#9662;</span>
        </a>
        <div class="nav-dropdown-panel" aria-label="About ActionBoundary">
          <a class="nav-path nav-path-featured" href="../">
            <strong>Evidence Library</strong>
            <span>Case notes, method notes, readiness checks, and source artifacts.</span>
          </a>
          <a class="nav-path" href="../../why.html">
            <strong>Philosophy</strong>
            <span>Why ActionBoundary exists and where the review boundary comes from.</span>
          </a>
        </div>
      </div>
      <a href="../../index.html#faq">FAQ</a>
      <a class="nav-cta" href="../../index.html#intake">Get 3 scenarios</a>
    </div>
  </div>
</nav>
"""


STYLE = """
  :root {
    --ink: #161719;
    --muted: #626a75;
    --paper: #f7f8fa;
    --white: #ffffff;
    --line: #dbe1e8;
    --line-strong: #b8c1cc;
    --teal: #0f766e;
    --teal-dark: #0b4f4a;
    --teal-soft: #e7f5f3;
    --amber: #b45309;
    --amber-soft: #fff7ed;
    --charcoal: #151619;
    --charcoal-2: #202227;
    --hero-accent: #9ad7cf;
    --hero-muted: #aeb8c5;
    --lead: #3e454d;
    --body-strong: #313840;
    --footer-ink: #343b43;
    --footer-muted: #b9c2cd;
    --code-on-dark: #f5f7f8;
    --shadow-soft: 0 2px 8px rgba(16, 24, 40, 0.08);
    --ease-out-quint: cubic-bezier(0.22, 1, 0.36, 1);
    --max: 1280px;
    --readable: 820px;
  }

  * {
    box-sizing: border-box;
  }

  html {
    scroll-behavior: smooth;
    overflow-x: hidden;
  }

  body {
    margin: 0;
    color: var(--ink);
    background: var(--paper);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    overflow-wrap: anywhere;
  }

  a {
    color: var(--teal-dark);
    text-decoration-thickness: 1px;
    text-underline-offset: 3px;
  }

  a:hover {
    color: var(--teal);
  }

  a:focus-visible,
  summary:focus-visible {
    outline: 2px solid rgba(15, 118, 110, 0.42);
    outline-offset: 4px;
    border-radius: 4px;
  }

  .site-nav {
    --nav-ink: #f6f8f9;
    --nav-muted: rgba(215, 226, 229, 0.74);
    --nav-link: rgba(246, 248, 249, 0.86);
    --nav-link-hover: var(--white);
    position: fixed;
    top: 12px;
    left: 12px;
    right: 12px;
    z-index: 100;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 8px;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.055)),
      linear-gradient(180deg, rgba(18, 22, 26, 0.42), rgba(18, 22, 26, 0.30));
    box-shadow:
      0 8px 18px rgba(0, 0, 0, 0.18),
      inset 0 1px 0 rgba(255, 255, 255, 0.28),
      inset 0 -1px 0 rgba(255, 255, 255, 0.06);
    -webkit-backdrop-filter: blur(26px) saturate(170%);
    backdrop-filter: blur(26px) saturate(170%);
    transition:
      background-color 220ms var(--ease-out-quint),
      background 220ms var(--ease-out-quint),
      border-color 220ms var(--ease-out-quint),
      box-shadow 220ms var(--ease-out-quint);
  }

  .site-nav.is-over-light {
    --nav-ink: var(--ink);
    --nav-muted: var(--muted);
    --nav-link: rgba(22, 23, 25, 0.78);
    --nav-link-hover: var(--teal-dark);
    border-color: rgba(15, 118, 110, 0.18);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.68), rgba(255, 255, 255, 0.36)),
      linear-gradient(110deg, rgba(231, 245, 243, 0.26), rgba(255, 255, 255, 0.12));
    box-shadow:
      0 8px 18px rgba(16, 24, 40, 0.10),
      inset 0 1px 0 rgba(255, 255, 255, 0.72),
      inset 0 -1px 0 rgba(15, 118, 110, 0.08);
  }

  .site-nav::after {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    border-radius: inherit;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.24), transparent 46%),
      linear-gradient(100deg, transparent 8%, rgba(255, 255, 255, 0.12) 34%, transparent 58%);
    opacity: 0.76;
    transition: opacity 220ms var(--ease-out-quint), background 220ms var(--ease-out-quint);
  }

  .site-nav.is-over-light::after {
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.56), transparent 50%),
      linear-gradient(100deg, transparent 6%, rgba(255, 255, 255, 0.28) 32%, transparent 58%);
    opacity: 0.9;
  }

  .nav-inner {
    position: relative;
    z-index: 1;
    max-width: var(--max);
    margin: 0 auto;
    padding: 13px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--nav-ink);
    min-width: 0;
    transition: color 220ms var(--ease-out-quint);
  }

  .brand-mark {
    width: 30px;
    height: 30px;
    flex: 0 0 auto;
    border-radius: 8px;
  }

  .brand-copy {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .brand strong {
    font-size: 1.02rem;
    line-height: 1.1;
    letter-spacing: 0;
  }

  .brand-subtitle {
    color: var(--nav-muted);
    font-size: 0.78rem;
    line-height: 1.25;
    margin-top: 3px;
    transition: color 220ms var(--ease-out-quint);
  }

  .nav-links {
    display: flex;
    align-items: center;
    gap: 18px;
    font-size: 0.92rem;
    white-space: nowrap;
  }

  .nav-links a {
    color: var(--nav-link);
    text-decoration: none;
    transition: color 160ms var(--ease-out-quint), opacity 160ms var(--ease-out-quint);
  }

  .nav-links a:hover {
    color: var(--nav-link-hover);
  }

  .nav-dropdown {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  .nav-dropdown-trigger {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  .nav-dropdown-trigger span {
    color: rgba(154, 215, 207, 0.86);
    font-size: 0.72rem;
    line-height: 1;
  }

  .nav-dropdown-panel {
    position: absolute;
    top: calc(100% + 14px);
    left: -16px;
    z-index: 120;
    width: min(420px, calc(100vw - 32px));
    padding: 10px;
    border: 1px solid rgba(154, 215, 207, 0.24);
    border-radius: 8px;
    background:
      radial-gradient(circle at 18% 0%, rgba(73, 185, 169, 0.12), transparent 34%),
      linear-gradient(145deg, #20252b, #111317);
    box-shadow: 0 18px 34px rgba(0, 0, 0, 0.34);
    opacity: 0;
    pointer-events: none;
    transform: translateY(6px);
    visibility: hidden;
    white-space: normal;
    transition:
      opacity 160ms var(--ease-out-quint),
      transform 160ms var(--ease-out-quint),
      visibility 160ms var(--ease-out-quint);
  }

  .about-menu .nav-dropdown-panel {
    left: auto;
    right: -16px;
    width: min(360px, calc(100vw - 32px));
  }

  .nav-dropdown:hover .nav-dropdown-panel,
  .nav-dropdown:focus-within .nav-dropdown-panel {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
    visibility: visible;
  }

  .nav-dropdown-panel::before {
    content: "";
    position: absolute;
    left: 18px;
    right: 18px;
    top: -15px;
    height: 15px;
  }

  .nav-dropdown-panel .nav-path {
    display: block;
    padding: 12px;
    border-radius: 8px;
    color: var(--hero-muted);
    text-decoration: none;
  }

  .nav-dropdown-panel .nav-path:hover,
  .nav-dropdown-panel .nav-path:focus-visible {
    background: rgba(154, 215, 207, 0.10);
    color: var(--hero-muted);
  }

  .nav-path strong {
    display: block;
    color: #f7fbfb;
    font-size: 0.94rem;
    line-height: 1.2;
  }

  .nav-path span {
    display: block;
    color: var(--hero-muted);
    font-size: 0.82rem;
    line-height: 1.38;
    margin-top: 4px;
  }

  .nav-path-featured {
    border: 1px solid rgba(154, 215, 207, 0.24);
    background: rgba(15, 118, 110, 0.18);
  }

  .nav-links .nav-cta {
    border: 1px solid rgba(154, 215, 207, 0.36);
    background: rgba(11, 79, 74, 0.88);
    color: var(--white);
    padding: 8px 12px;
    border-radius: 8px;
  }

  .nav-links .nav-cta:hover {
    background: rgba(15, 118, 110, 0.96);
    border-color: rgba(154, 215, 207, 0.54);
    color: var(--white);
  }

  .hero {
    background:
      radial-gradient(circle at 10% 12%, rgba(73, 185, 169, 0.22), transparent 32%),
      linear-gradient(135deg, #111317, #1d2429 62%, #151619);
    color: var(--white);
    border-bottom: 1px solid #0f1114;
  }

  .hero-inner {
    max-width: var(--max);
    min-height: 520px;
    margin: 0 auto;
    padding: 124px 36px 56px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(290px, 0.42fr);
    gap: 38px;
    align-items: end;
  }

  .hero-panel {
    align-self: center;
    transform: translateY(-56px);
  }

  .breadcrumb {
    display: inline-flex;
    width: fit-content;
    margin-bottom: 22px;
    color: var(--hero-accent);
    font-weight: 800;
    text-decoration: none;
  }

  .eyebrow,
  .section-kicker {
    margin: 0 0 14px;
    color: var(--hero-accent);
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0;
    text-transform: uppercase;
  }

  h1,
  h2,
  h3,
  p {
    margin-top: 0;
  }

  h1 {
    max-width: 920px;
    margin-bottom: 22px;
    font-size: clamp(3rem, 5vw, 4.25rem);
    line-height: 1.02;
    letter-spacing: 0;
    text-wrap: balance;
  }

  h2,
  h3 {
    text-wrap: balance;
  }

  p,
  li {
    text-wrap: pretty;
  }

  .hero-copy {
    max-width: 760px;
    color: #d8dde5;
    font-size: 1.05rem;
    line-height: 1.6;
    margin-bottom: 28px;
  }

  .hero-actions,
  .rail-actions,
  .article-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
  }

  .button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 44px;
    padding: 11px 15px;
    border-radius: 8px;
    font-weight: 750;
    text-decoration: none;
    border: 1px solid transparent;
  }

  .button.primary {
    background: #f3f8f7;
    color: #10201f;
    border-color: #f3f8f7;
  }

  .button.primary:hover {
    background: #d8efec;
    color: #10201f;
    border-color: #d8efec;
  }

  .button.secondary {
    color: var(--white);
    border-color: rgba(255, 255, 255, 0.32);
    background: rgba(255, 255, 255, 0.08);
  }

  .button.secondary:hover {
    background: rgba(255, 255, 255, 0.14);
    color: var(--white);
  }

  .memo-card {
    border: 1px solid rgba(154, 215, 207, 0.24);
    border-radius: 8px;
    background:
      radial-gradient(circle at 12% 0%, rgba(73, 185, 169, 0.14), transparent 34%),
      linear-gradient(145deg, #20252b, #111317);
    box-shadow: 0 8px 14px rgba(0, 0, 0, 0.22);
    padding: 18px;
  }

  .memo-card b {
    display: block;
    color: #f7fbfb;
    line-height: 1.2;
    margin-bottom: 8px;
  }

  .memo-card span,
  .memo-card p {
    color: var(--hero-muted);
    font-size: 0.9rem;
  }

  .memo-card dl {
    margin: 18px 0 0;
    border-top: 1px solid rgba(215, 221, 228, 0.16);
  }

  .memo-card div {
    display: grid;
    grid-template-columns: 92px minmax(0, 1fr);
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid rgba(215, 221, 228, 0.12);
  }

  .memo-card dt {
    color: #f7fbfb;
    font-weight: 800;
  }

  .memo-card dd {
    margin: 0;
    color: var(--hero-muted);
  }

  .article-shell {
    max-width: var(--max);
    margin: 0 auto;
    padding: 66px 36px;
    display: grid;
    grid-template-columns: minmax(0, var(--readable)) minmax(280px, 0.42fr);
    gap: 28px;
    align-items: start;
  }

  .article-body {
    min-width: 0;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--white);
    box-shadow: var(--shadow-soft);
    padding: clamp(24px, 4vw, 46px);
  }

  .article-note {
    margin-bottom: 24px;
    border: 1px solid rgba(15, 118, 110, 0.18);
    border-radius: 8px;
    background: var(--teal-soft);
    padding: 14px 16px;
    color: var(--teal-dark);
    font-size: 0.93rem;
  }

  .article-body h2 {
    margin: 36px 0 12px;
    font-size: clamp(1.65rem, 2.6vw, 2.2rem);
    line-height: 1.14;
    letter-spacing: 0;
  }

  .article-body h2:first-child {
    margin-top: 0;
  }

  .article-body h3 {
    margin: 28px 0 10px;
    font-size: 1.18rem;
    line-height: 1.25;
  }

  .article-body p,
  .article-body li {
    color: var(--lead);
    font-size: 1rem;
  }

  .article-body p {
    margin-bottom: 16px;
  }

  .article-body ul,
  .article-body ol {
    margin: 0 0 18px;
    padding-left: 22px;
  }

  .article-body li + li {
    margin-top: 7px;
  }

  .article-body code {
    border: 1px solid var(--line);
    border-radius: 4px;
    background: var(--paper);
    padding: 0.08rem 0.28rem;
    color: var(--body-strong);
    font-size: 0.92em;
  }

  .article-body pre {
    overflow-x: auto;
    border: 1px solid var(--charcoal-3);
    border-radius: 8px;
    background: var(--charcoal);
    color: var(--code-on-dark);
    padding: 16px;
  }

  .article-body pre code {
    border: 0;
    background: transparent;
    padding: 0;
    color: inherit;
    font-size: 0.92rem;
  }

  .article-body blockquote {
    margin: 22px 0;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--teal-soft);
    padding: 14px 18px;
  }

  .article-body blockquote p {
    margin: 0;
  }

  .article-body hr {
    border: 0;
    border-top: 1px solid var(--line);
    margin: 34px 0;
  }

  .table-wrap {
    overflow-x: auto;
    margin: 24px 0;
    border: 1px solid var(--line);
    border-radius: 8px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    min-width: 640px;
    background: var(--white);
  }

  th,
  td {
    padding: 12px 13px;
    border-bottom: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
  }

  th {
    background: var(--teal-soft);
    color: var(--body-strong);
    font-size: 0.86rem;
  }

  td {
    color: var(--lead);
    font-size: 0.94rem;
  }

  tr:last-child td {
    border-bottom: 0;
  }

  .article-rail {
    display: grid;
    gap: 14px;
    position: sticky;
    top: 94px;
  }

  .rail-card {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--white);
    box-shadow: var(--shadow-soft);
    padding: 18px;
  }

  .rail-card h2 {
    margin-bottom: 12px;
    font-size: 1.08rem;
    line-height: 1.25;
  }

  .rail-card p,
  .rail-card dd {
    color: var(--muted);
    font-size: 0.92rem;
  }

  .rail-card dl {
    margin: 0;
    display: grid;
    gap: 11px;
  }

  .rail-card dt {
    color: var(--ink);
    font-size: 0.78rem;
    font-weight: 850;
    text-transform: uppercase;
  }

  .rail-card dd {
    margin: 3px 0 0;
  }

  .rail-actions a {
    display: inline-flex;
    width: fit-content;
    min-height: 36px;
    align-items: center;
    border: 1px solid var(--line-strong);
    border-radius: 8px;
    padding: 7px 10px;
    background: var(--white);
    color: var(--teal-dark);
    font-size: 0.86rem;
    font-weight: 800;
    text-decoration: none;
  }

  .rail-actions a:hover {
    background: var(--teal-soft);
    border-color: rgba(15, 118, 110, 0.45);
  }

  .article-nav {
    max-width: var(--max);
    margin: 0 auto;
    padding: 0 36px 70px;
  }

  .article-nav a {
    color: var(--teal-dark);
    font-weight: 800;
    text-decoration: none;
  }

  footer {
    padding: 34px 36px;
    color: var(--footer-muted);
    background: var(--footer-ink);
  }

  .footer-inner {
    max-width: var(--max);
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
    font-size: 0.9rem;
  }

  footer a {
    color: var(--white);
  }

  @media (max-width: 1040px) {
    .nav-links {
      gap: 12px;
      font-size: 0.88rem;
    }

    .hero-inner,
    .article-shell {
      grid-template-columns: 1fr;
    }

    .article-rail {
      position: static;
    }
  }

  @media (max-width: 760px) {
    .site-nav {
      left: 8px;
      right: 8px;
      top: 8px;
      overflow: hidden;
      max-width: calc(100vw - 16px);
    }

    .nav-inner {
      padding: 10px 12px;
      align-items: center;
      flex-direction: row;
      gap: 12px;
    }

    .nav-links a:not(.nav-cta) {
      display: none;
    }

    .nav-dropdown {
      display: none;
    }

    .nav-links .nav-cta {
      padding: 7px 10px;
      font-size: 0.86rem;
    }

    .brand-subtitle {
      display: none;
    }

    .hero-inner {
      min-height: 0;
      padding: 112px 22px 44px;
    }

    .hero-panel {
      transform: none;
    }

    h1 {
      font-size: 2.25rem;
      line-height: 1.05;
    }

    .article-shell {
      padding: 44px 22px;
    }

    .article-body {
      padding: 20px;
    }

    .memo-card div {
      grid-template-columns: 1fr;
      gap: 3px;
    }

    .button,
    .hero-actions .button {
      width: 100%;
    }

    .article-nav {
      padding: 0 22px 44px;
    }
  }
"""


def render_page(article: dict[str, str]) -> str:
    source_path = ROOT / article["source"]
    markdown = source_path.read_text(encoding="utf-8")
    body = render_markdown(markdown, source_path, article["slug"])
    github = source_github(article)
    description = html.escape(article["description"], quote=True)
    og_image = html.escape(article.get("og_image", "https://actionboundary.dev/og-image.png"), quote=True)
    primary = article["primary"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(article["title"])} | ActionBoundary Evidence</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://actionboundary.dev/evidence/{article["slug"]}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(article["title"])} | ActionBoundary">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://actionboundary.dev/evidence/{article["slug"]}/">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(article["title"])} | ActionBoundary">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">
<link rel="icon" type="image/svg+xml" href="../../favicon.svg">
<style>
{STYLE}
</style>
</head>
<body>
{nav_html()}
<header class="hero">
  <div class="hero-inner">
    <div class="hero-panel">
      <a class="breadcrumb" href="../">Evidence Library</a>
      <p class="eyebrow">{html.escape(article["eyebrow"])}</p>
      <h1>{html.escape(article["title"])}</h1>
      <p class="hero-copy">{html.escape(article["description"])}</p>
      <div class="hero-actions" aria-label="Evidence article actions">
        <a class="button primary" href="#article">Read article</a>
        <a class="button secondary" href="{github}">Source on GitHub</a>
      </div>
    </div>
    <aside class="memo-card" aria-label="Evidence memo summary">
      <b>Evidence memo</b>
      <span>Station-owned reading page with a source file behind it.</span>
      <dl>
        <div>
          <dt>Type</dt>
          <dd>{html.escape(article["type"])}</dd>
        </div>
        <div>
          <dt>Scope</dt>
          <dd>{html.escape(article["scope"])}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>{html.escape(article["source"])}</dd>
        </div>
      </dl>
    </aside>
  </div>
</header>
<main>
  <section class="article-shell" aria-label="Evidence article">
    <article id="article" class="article-body">
      <div class="article-note"><strong>Claim boundary.</strong> {html.escape(article["claim"])}</div>
{body}
    </article>
    <aside class="article-rail" aria-label="Article reference links">
      <section class="rail-card">
        <h2>Review boundary</h2>
        <dl>
          <div>
            <dt>Evidence type</dt>
            <dd>{html.escape(article["type"])}</dd>
          </div>
          <div>
            <dt>Public scope</dt>
            <dd>{html.escape(article["scope"])}</dd>
          </div>
          <div>
            <dt>Source file</dt>
            <dd>{html.escape(article["source"])}</dd>
          </div>
        </dl>
      </section>
      <section class="rail-card">
        <h2>Source layer</h2>
        <p>The full article is readable here. GitHub remains the audit trail for source files, raw summaries, code, and exact revisions.</p>
        <div class="rail-actions">
          <a href="{html.escape(primary["href"], quote=True)}">{html.escape(primary["label"])}</a>
          <a href="{github}">Source on GitHub</a>
          <a href="../">Evidence Library</a>
        </div>
      </section>
    </aside>
  </section>
  <nav class="article-nav" aria-label="Evidence article footer navigation">
    <a href="../">Back to Evidence Library</a>
    <a href="../../index.html#intake">Get 3 scenarios</a>
  </nav>
</main>
<footer>
  <div class="footer-inner">
    <span>ActionBoundary by JZ Software Consulting. Reviews performed and signed by <a href="../../why.html">Jiahao Zhang</a>.</span>
    <span><a href="../../index.html">Home</a> | <a href="../../why.html">About</a> | <a href="../">Evidence</a> | <a href="../../trust.html">Trust</a> | <a href="https://github.com/hugoii/llm-agent-audit">GitHub</a> | <a href="mailto:jiahao@actionboundary.dev">jiahao@actionboundary.dev</a></span>
  </div>
</footer>
<script>
  (function () {{
    var nav = document.querySelector('.site-nav');
    var hero = document.querySelector('.hero');
    if (!nav || !hero) {{
      return;
    }}
    var ticking = false;
    var updateNavGlass = function () {{
      var navBottom = nav.getBoundingClientRect().bottom;
      var heroBottom = hero.getBoundingClientRect().bottom;
      nav.classList.toggle('is-over-light', heroBottom <= navBottom + 10);
      ticking = false;
    }};
    updateNavGlass();
    window.addEventListener('scroll', function () {{
      if (!ticking) {{
        ticking = true;
        window.requestAnimationFrame(updateNavGlass);
      }}
    }}, {{ passive: true }});
    window.addEventListener('resize', updateNavGlass);
  }})();
</script>
</body>
</html>
"""


def main() -> None:
    for article in ARTICLES:
        out_dir = ROOT / "docs" / "evidence" / article["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(render_page(article), encoding="utf-8", newline="\n")
        print(f"rendered docs/evidence/{article['slug']}/index.html")


if __name__ == "__main__":
    main()

import base64
import html
import re
from pathlib import Path

BG = "#0e1b3d"
YELLOW = "#FFD23F"
WHITE = "#ffffff"
MUTED = "#c9d1e3"

_LOGO_PATH = Path(__file__).parent / "static" / "dtq-logo.png"
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)+$")
_logo_cache: str | None = None


def _logo_data_uri() -> str | None:
    global _logo_cache
    if _logo_cache is not None:
        return _logo_cache or None
    if not _LOGO_PATH.exists():
        _logo_cache = ""
        return None
    data = _LOGO_PATH.read_bytes()
    _logo_cache = f"data:image/png;base64,{base64.b64encode(data).decode('ascii')}"
    return _logo_cache


def _wrap_highlight(hook: str, highlight: str) -> str:
    safe_hook = html.escape(hook or "")
    h = (highlight or "").strip()
    if not h:
        return safe_hook
    safe_h = html.escape(h)
    pattern = re.compile(re.escape(safe_h), re.IGNORECASE)
    if not pattern.search(safe_hook):
        return safe_hook
    return pattern.sub(
        f'<span style="color:{YELLOW}">{safe_h}</span>',
        safe_hook,
        count=1,
    )


def _safe_color(value: str | None, fallback: str = "#1f2a55") -> str:
    if value and isinstance(value, str) and _HEX_RE.match(value.strip()):
        return value.strip()
    return fallback


def _badge_letter(item: dict) -> str:
    raw = (item.get("brand_letter") or item.get("title") or "?").strip()
    return html.escape(raw[:1].upper()) if raw else "?"


def _badge_html(item: dict) -> str:
    letter = _badge_letter(item)
    color = _safe_color(item.get("brand_color"), fallback="#243262")
    domain_raw = (item.get("domain") or "").strip().lower()

    fallback_letter = (
        f'<span style="position:absolute;inset:0;background:{color};color:#ffffff;'
        f'border-radius:6px;display:flex;align-items:center;justify-content:center;'
        f'font-weight:800;font-size:15px;line-height:1;">{letter}</span>'
    )

    if domain_raw and _DOMAIN_RE.match(domain_raw):
        safe_domain = html.escape(domain_raw)
        onerror_js = (
            "if(this.dataset.fb!=='1'){this.dataset.fb='1';"
            f"this.src='https://www.google.com/s2/favicons?domain={safe_domain}&sz=128';"
            "}else{this.style.display='none';}"
        )
        onerror_attr = html.escape(onerror_js, quote=True)
        logo_img = (
            f'<img src="https://logo.clearbit.com/{safe_domain}" alt="" '
            f'style="position:absolute;inset:0;width:36px;height:36px;border-radius:6px;'
            f'background:#ffffff;object-fit:contain;padding:3px;" '
            f'onerror="{onerror_attr}" />'
        )
    else:
        logo_img = ""

    return (
        f'<span style="position:relative;flex:0 0 36px;width:36px;height:36px;'
        f'display:inline-block;">{fallback_letter}{logo_img}</span>'
    )


def _render_categories(categories: list[dict]) -> str:
    blocks = []
    for cat in categories or []:
        name = html.escape((cat.get("name") or "").strip())
        items_html = []
        for item in cat.get("items") or []:
            t = html.escape((item.get("title") or "").strip())
            d = html.escape((item.get("description") or "").strip())
            if not t:
                continue
            badge = _badge_html(item)
            items_html.append(
                f'<li style="display:flex;align-items:flex-start;gap:14px;margin:0 0 14px 0;'
                f'break-inside:avoid;page-break-inside:avoid;">'
                f'{badge}'
                f'<span style="flex:1;min-width:0;">'
                f'<div style="color:{WHITE};font-weight:700;font-size:18px;line-height:1.25;">{t}</div>'
                f'<div style="color:{MUTED};font-weight:400;font-size:14px;line-height:1.4;margin-top:3px;">{d}</div>'
                f'</span>'
                f'</li>'
            )
        if not items_html:
            continue
        blocks.append(
            f'<div style="break-inside:avoid;page-break-inside:avoid;margin-bottom:22px;">'
            f'<div style="color:{YELLOW};font-size:20px;font-weight:800;'
            f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px;'
            f'padding-bottom:8px;border-bottom:2px solid rgba(255,210,63,0.25);">{name}</div>'
            f'<ul style="list-style:none;padding:0;margin:0;">'
            f'{"".join(items_html)}'
            f'</ul>'
            f'</div>'
        )
    return "".join(blocks)


def _render_logo() -> str:
    logo_uri = _logo_data_uri()
    if logo_uri:
        return (
            f'<img src="{logo_uri}" alt="DTQ" '
            f'style="height:90px;width:auto;filter:brightness(0) invert(1);"/>'
        )
    return (
        f'<div style="color:{WHITE};font-weight:900;font-size:48px;letter-spacing:4px;'
        f'line-height:1;font-family:Georgia,\'Times New Roman\',serif;">DTQ</div>'
    )


def build_card_html(data: dict) -> str:
    hook = _wrap_highlight(data.get("hook", ""), data.get("highlight", ""))
    subtitle = html.escape((data.get("subtitle") or "").strip())
    categories_html = _render_categories(data.get("categories") or [])
    logo_html = _render_logo()

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1080px;
    background: {BG};
    color: {WHITE};
    font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .card {{
    width: 1080px;
    height: 1080px;
    padding: 64px 70px 64px 70px;
    display: flex;
    flex-direction: column;
    position: relative;
  }}
  .topbar {{
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    min-height: 90px;
  }}
  .hook {{
    color: {WHITE};
    font-size: 60px;
    font-weight: 800;
    line-height: 1.08;
    margin-top: 16px;
    letter-spacing: -0.5px;
  }}
  .subtitle {{
    color: {YELLOW};
    font-size: 22px;
    font-weight: 600;
    margin-top: 18px;
    margin-bottom: 36px;
    letter-spacing: 0.3px;
  }}
  .grid {{
    column-count: 2;
    column-gap: 48px;
    flex: 1;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="topbar">{logo_html}</div>
    <div class="hook">{hook}</div>
    <div class="subtitle">{subtitle}</div>
    <div class="grid">{categories_html}</div>
  </div>
</body>
</html>"""

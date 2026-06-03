import base64
import html
import re
from pathlib import Path

WHITE = "#ffffff"
MUTED = "#c9d1e3"

_LOGO_PATH = Path(__file__).parent / "static" / "dtq-logo.png"
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)+$")
_logo_cache: str | None = None

# Curated style options exposed to the result-page customizer.
FONT_OPTIONS = {
    "sans": {"label": "Inter (Modern Sans)", "family": "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif", "google": "Inter:wght@400;600;700;800"},
    "montserrat": {"label": "Montserrat", "family": "'Montserrat', sans-serif", "google": "Montserrat:wght@400;600;800"},
    "poppins": {"label": "Poppins", "family": "'Poppins', sans-serif", "google": "Poppins:wght@400;600;800"},
    "dmsans": {"label": "DM Sans", "family": "'DM Sans', sans-serif", "google": "DM+Sans:wght@400;700"},
    "raleway": {"label": "Raleway", "family": "'Raleway', sans-serif", "google": "Raleway:wght@400;700;800"},
    "space": {"label": "Space Grotesk", "family": "'Space Grotesk', sans-serif", "google": "Space+Grotesk:wght@400;700"},
    "condensed": {"label": "Oswald (Condensed)", "family": "'Oswald', 'Arial Narrow', sans-serif", "google": "Oswald:wght@400;500;700"},
    "bebas": {"label": "Bebas Neue (Tall)", "family": "'Bebas Neue', Impact, sans-serif", "google": "Bebas+Neue"},
    "anton": {"label": "Anton (Heavy)", "family": "'Anton', Impact, sans-serif", "google": "Anton"},
    "archivo": {"label": "Archivo Black", "family": "'Archivo Black', sans-serif", "google": "Archivo+Black"},
    "serif": {"label": "Playfair Display (Serif)", "family": "'Playfair Display', Georgia, serif", "google": "Playfair+Display:wght@700;900"},
    "lora": {"label": "Lora (Serif)", "family": "'Lora', Georgia, serif", "google": "Lora:wght@400;700"},
    "merriweather": {"label": "Merriweather (Serif)", "family": "'Merriweather', Georgia, serif", "google": "Merriweather:wght@400;700"},
    "abril": {"label": "Abril Fatface (Display)", "family": "'Abril Fatface', Georgia, serif", "google": "Abril+Fatface"},
}

DEFAULT_STYLE = {
    "logo_px": 150,
    "bg_color": "#0e1b3d",
    "accent_color": "#FFD23F",
    "heading_font": "sans",
    "bg_gradient": True,
    "bg_color2": "#1a2c5b",
    "bg_angle": 150,
}

# Template registry. Each entry powers the form gallery (label/blurb), the
# main.py field-validation, and the renderer dispatch below.
TEMPLATES = {
    "catalogue": {
        "label": "Catalogue",
        "blurb": "Curated tools & frameworks, grouped into 4 categories with logos.",
        "required": ("title", "caption", "hook", "categories"),
    },
    "listicle": {
        "label": "Listicle",
        "blurb": "Top 5-7 points, big numbers. No logos — pure takeaways.",
        "required": ("title", "caption", "hook", "points"),
    },
    "news": {
        "label": "News Breakdown",
        "blurb": "A recent happening: what happened, why it matters, what to watch.",
        "required": ("title", "caption", "hook", "blocks"),
    },
    "stat": {
        "label": "Big Stat",
        "blurb": "One giant statistic with its source and supporting context.",
        "required": ("title", "caption", "stat_value"),
    },
    "quote": {
        "label": "Quote / Hot Take",
        "blurb": "A single bold point of view, set large, with one supporting line.",
        "required": ("title", "caption", "quote"),
    },
    "framework": {
        "label": "Framework",
        "blurb": "A numbered, step-by-step playbook the reader follows in order.",
        "required": ("title", "caption", "hook", "steps"),
    },
}
DEFAULT_TEMPLATE = "catalogue"


def template_required(template: str | None) -> tuple:
    return TEMPLATES.get((template or DEFAULT_TEMPLATE), TEMPLATES[DEFAULT_TEMPLATE])["required"]


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


def _hl(text: str, highlight: str) -> str:
    """Escape text and wrap the first verbatim occurrence of `highlight` in an
    accent-coloured span."""
    safe = html.escape(text or "")
    h = (highlight or "").strip()
    if not h:
        return safe
    safe_h = html.escape(h)
    pattern = re.compile(re.escape(safe_h), re.IGNORECASE)
    if not pattern.search(safe):
        return safe
    return pattern.sub('<span style="color:var(--accent)">' + safe_h + "</span>", safe, count=1)


def _safe_color(value: str | None, fallback: str) -> str:
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


# ---------------------------------------------------------------------------
# Per-template renderers. Each returns the inner content of the .card (the shell
# adds the background blobs, the logo, and the footer).
# ---------------------------------------------------------------------------

def _header_block(data: dict, hook_size: int = 50, hl_field: str = "hook") -> str:
    """Eyebrow-free hook + subtitle header used by list-style templates."""
    hook_text = data.get("hook", "")
    hook = _hl(hook_text, data.get("highlight", "")) if hl_field == "hook" else html.escape(hook_text)
    subtitle = html.escape((data.get("subtitle") or "").strip())
    sub_html = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    return (
        f'<div class="head">'
        f'<div class="hook" style="font-size:{hook_size}px;">{hook}</div>'
        f'{sub_html}'
        f'</div>'
    )


def _render_catalogue(data: dict) -> str:
    blocks = []
    for cat in data.get("categories") or []:
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
            f'<div style="color:var(--accent);font-size:20px;font-weight:800;'
            f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px;'
            f'padding-bottom:8px;border-bottom:2px solid rgba(255,255,255,0.16);">{name}</div>'
            f'<ul style="list-style:none;padding:0;margin:0;">'
            f'{"".join(items_html)}'
            f'</ul>'
            f'</div>'
        )
    categories_html = "".join(blocks)
    return (
        _header_block(data, hook_size=56)
        + f'<div class="grid">{categories_html}</div>'
    )


def _render_listicle(data: dict) -> str:
    points = [p for p in (data.get("points") or []) if (p.get("title") or "").strip()]
    points = points[:7]
    rows = []
    for i, p in enumerate(points, start=1):
        t = html.escape((p.get("title") or "").strip())
        d = html.escape((p.get("detail") or "").strip())
        detail_html = f'<div class="row-detail">{d}</div>' if d else ""
        rows.append(
            f'<div class="glass row">'
            f'<div class="numchip">{i:02d}</div>'
            f'<div class="row-text"><div class="row-title">{t}</div>{detail_html}</div>'
            f'</div>'
        )
    return _header_block(data, hook_size=46) + f'<div class="stack">{"".join(rows)}</div>'


def _render_framework(data: dict) -> str:
    steps = [s for s in (data.get("steps") or []) if (s.get("title") or "").strip()]
    steps = steps[:6]
    rows = []
    for i, s in enumerate(steps, start=1):
        t = html.escape((s.get("title") or "").strip())
        d = html.escape((s.get("detail") or "").strip())
        detail_html = f'<div class="row-detail">{d}</div>' if d else ""
        connector = '<div class="connector"></div>' if i < len(steps) else ""
        rows.append(
            f'<div class="glass row step">'
            f'<div class="step-rail"><div class="numchip">{i}</div>{connector}</div>'
            f'<div class="row-text"><div class="row-eyebrow">STEP {i}</div>'
            f'<div class="row-title">{t}</div>{detail_html}</div>'
            f'</div>'
        )
    return _header_block(data, hook_size=46) + f'<div class="stack">{"".join(rows)}</div>'


def _render_news(data: dict) -> str:
    eyebrow = html.escape((data.get("eyebrow") or "UPDATE").strip().upper())
    hook = _hl(data.get("hook", ""), data.get("highlight", ""))
    subtitle = html.escape((data.get("subtitle") or "").strip())
    sub_html = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    blocks = []
    for b in (data.get("blocks") or [])[:4]:
        label = html.escape((b.get("label") or "").strip())
        text = html.escape((b.get("text") or "").strip())
        if not text:
            continue
        blocks.append(
            f'<div class="glass news-block">'
            f'<div class="news-label">{label}</div>'
            f'<div class="news-text">{text}</div>'
            f'</div>'
        )
    head = (
        f'<div class="head">'
        f'<div class="eyebrow"><span class="dot"></span>{eyebrow}</div>'
        f'<div class="hook" style="font-size:52px;">{hook}</div>'
        f'{sub_html}'
        f'</div>'
    )
    return head + f'<div class="stack">{"".join(blocks)}</div>'


def _render_stat(data: dict) -> str:
    eyebrow = html.escape((data.get("hook") or "").strip().upper())
    value = html.escape((data.get("stat_value") or "").strip())
    label = html.escape((data.get("stat_label") or "").strip())
    source = html.escape((data.get("stat_source") or "").strip())
    subtitle = html.escape((data.get("subtitle") or "").strip())
    ctx = [html.escape((c or "").strip()) for c in (data.get("context") or []) if (c or "").strip()][:4]
    eyebrow_html = f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ""
    source_html = f'<div class="stat-source">{source}</div>' if source else ""
    sub_html = f'<div class="subtitle" style="text-align:center;">{subtitle}</div>' if subtitle else ""
    ctx_html = ""
    if ctx:
        chips = "".join(f'<div class="glass ctx-chip">{c}</div>' for c in ctx)
        ctx_html = f'<div class="ctx-wrap">{chips}</div>'
    return (
        f'<div class="stat-wrap">'
        f'<div class="stat-deco">{value}</div>'
        f'<div class="stat-main">'
        f'{eyebrow_html}'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-line"></div>'
        f'<div class="stat-label">{label}</div>'
        f'{source_html}'
        f'{sub_html}'
        f'</div>'
        f'{ctx_html}'
        f'</div>'
    )


def _render_quote(data: dict) -> str:
    kicker = html.escape((data.get("hook") or "").strip().upper())
    quote = _hl(data.get("quote", ""), data.get("highlight", ""))
    attribution = html.escape((data.get("attribution") or "DTQ").strip())
    support = html.escape((data.get("support") or "").strip())
    kicker_html = f'<div class="eyebrow">{kicker}</div>' if kicker else ""
    support_html = f'<div class="quote-support">{support}</div>' if support else ""
    return (
        f'<div class="quote-wrap">'
        f'<div class="quote-deco">&rdquo;</div>'
        f'<div class="quote-top">'
        f'{kicker_html}'
        f'<div class="quote-mark">&ldquo;</div>'
        f'</div>'
        f'<div class="quote-row">'
        f'<div class="quote-rule"></div>'
        f'<div class="quote-text">{quote}<span class="quote-close">&rdquo;</span></div>'
        f'</div>'
        f'<div class="quote-foot">'
        f'<span class="quote-dash"></span>'
        f'<div class="quote-byline"><div class="quote-attr">{attribution}</div>{support_html}</div>'
        f'</div>'
        f'</div>'
    )


_RENDERERS = {
    "catalogue": _render_catalogue,
    "listicle": _render_listicle,
    "news": _render_news,
    "stat": _render_stat,
    "quote": _render_quote,
    "framework": _render_framework,
}


# ---------------------------------------------------------------------------
# Shell: logo, background blobs, footer, stylesheet.
# ---------------------------------------------------------------------------

_LOGO_DRAG_SCRIPT = """
<script>
(function(){
  var box=document.getElementById('dtq-logo-box');
  if(!box) return;
  var img=document.getElementById('dtq-logo-img');
  var handle=box.querySelector('.resize-h');
  var dragging=false,resizing=false,sx,sy,ol,ot,oh;
  box.addEventListener('mousedown',function(e){
    sx=e.clientX; sy=e.clientY;
    if(handle && e.target===handle){ resizing=true; oh=img.offsetHeight; }
    else { dragging=true; ol=box.offsetLeft; ot=box.offsetTop; }
    e.preventDefault(); e.stopPropagation();
  });
  document.addEventListener('mousemove',function(e){
    if(dragging){
      box.style.left=(ol+(e.clientX-sx))+'px';
      box.style.top=(ot+(e.clientY-sy))+'px';
      box.style.right='auto';
    } else if(resizing){
      var nh=Math.max(40,Math.min(320,oh+(e.clientY-sy)));
      img.style.height=nh+'px';
    }
  });
  document.addEventListener('mouseup',function(){
    if(dragging||resizing){
      parent.postMessage({type:'dtq-logo',x:Math.round(box.offsetLeft),y:Math.round(box.offsetTop),size:Math.round(img.offsetHeight)},'*');
    }
    dragging=false; resizing=false;
  });
})();
</script>
"""


def _render_logo(logo_px: int, logo_x, logo_y, editable: bool) -> str:
    logo_uri = _logo_data_uri()
    if logo_uri:
        inner = (
            f'<img id="dtq-logo-img" src="{logo_uri}" alt="DTQ" draggable="false" '
            f'style="height:{logo_px}px;width:auto;display:block;filter:brightness(0) invert(1);"/>'
        )
    else:
        text_px = max(28, int(logo_px * 0.55))
        inner = (
            f'<div id="dtq-logo-img" style="color:{WHITE};font-weight:900;font-size:{text_px}px;'
            f'letter-spacing:6px;line-height:1;font-family:Georgia,\'Times New Roman\',serif;">DTQ</div>'
        )

    if logo_x is not None and logo_y is not None:
        pos = f"left:{logo_x}px;top:{logo_y}px;"
    else:
        pos = "right:70px;top:60px;"

    handle = ""
    cursor = ""
    if editable:
        cursor = "cursor:move;"
        handle = (
            '<div class="resize-h" style="position:absolute;right:-8px;bottom:-8px;width:16px;'
            'height:16px;background:#fff;border:2px solid #FFD23F;border-radius:50%;'
            'cursor:nwse-resize;"></div>'
        )

    return (
        f'<div id="dtq-logo-box" style="position:absolute;{pos}{cursor}z-index:20;">'
        f'{inner}{handle}</div>'
    )


def _render_blobs(accent: str, bg2: str) -> str:
    return (
        f'<div class="blob" style="background:{accent};top:-200px;right:-140px;"></div>'
        f'<div class="blob" style="background:{bg2};bottom:-240px;left:-180px;"></div>'
        f'<div class="blob blob-sm" style="background:{accent};bottom:80px;right:-120px;"></div>'
    )


def _render_footer() -> str:
    return (
        '<div class="footer">'
        '<span class="footer-dot"></span>'
        '<span class="footer-text">Data Trust Quotients</span>'
        '</div>'
    )


def _merge_style(style: dict | None) -> dict:
    s = dict(DEFAULT_STYLE)
    if style:
        s.update({k: v for k, v in style.items() if v not in (None, "")})
    bg = _safe_color(str(s.get("bg_color")), DEFAULT_STYLE["bg_color"])
    bg2 = _safe_color(str(s.get("bg_color2")), DEFAULT_STYLE["bg_color2"])
    accent = _safe_color(str(s.get("accent_color")), DEFAULT_STYLE["accent_color"])
    try:
        logo_px = max(40, min(320, int(s.get("logo_px"))))
    except (ValueError, TypeError):
        logo_px = DEFAULT_STYLE["logo_px"]
    try:
        bg_angle = int(s.get("bg_angle"))
    except (ValueError, TypeError):
        bg_angle = DEFAULT_STYLE["bg_angle"]
    bg_gradient = bool(s.get("bg_gradient"))
    font_key = s.get("heading_font") if s.get("heading_font") in FONT_OPTIONS else "sans"

    def _int_or_none(v):
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    return {
        "bg_color": bg, "bg_color2": bg2, "bg_angle": bg_angle, "bg_gradient": bg_gradient,
        "accent_color": accent, "logo_px": logo_px, "heading_font": font_key,
        "logo_x": _int_or_none(s.get("logo_x")), "logo_y": _int_or_none(s.get("logo_y")),
    }


def _stylesheet(accent: str, font_family: str, bg_css: str, topbar_h: int) -> str:
    return f"""
  :root {{
    --accent: {accent};
    --heading-font: {font_family};
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    width: 1080px; height: 1080px;
    background: {bg_css};
    color: {WHITE};
    font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .card {{
    width: 1080px; height: 1080px;
    padding: 60px 70px 52px 70px;
    display: flex; flex-direction: column;
    position: relative; overflow: hidden;
  }}
  .card > * {{ position: relative; z-index: 1; }}
  #dtq-logo-box {{ z-index: 20; }}

  /* Background blobs ("clouds") */
  .blob {{
    position: absolute; width: 560px; height: 560px; border-radius: 50%;
    filter: blur(130px); opacity: 0.30; z-index: 0; pointer-events: none;
  }}
  .blob-sm {{ width: 360px; height: 360px; filter: blur(110px); opacity: 0.22; }}

  .topbar {{ min-height: {topbar_h}px; flex: 0 0 auto; }}

  /* Shared header */
  .head {{ flex: 0 0 auto; margin-bottom: 26px; }}
  .eyebrow {{
    display: inline-flex; align-items: center; gap: 10px;
    color: var(--accent); font-family: var(--heading-font);
    font-size: 22px; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; margin-bottom: 16px;
  }}
  .eyebrow .dot {{
    width: 12px; height: 12px; border-radius: 50%; background: var(--accent);
    box-shadow: 0 0 0 5px rgba(255,210,63,0.18);
  }}
  .hook {{
    color: {WHITE}; font-family: var(--heading-font);
    font-weight: 800; line-height: 1.06; letter-spacing: -0.5px;
  }}
  .subtitle {{
    color: var(--accent); font-family: var(--heading-font);
    font-size: 23px; font-weight: 600; margin-top: 16px; letter-spacing: 0.3px;
  }}

  /* Catalogue grid (legacy layout) */
  .grid {{ column-count: 2; column-gap: 48px; flex: 1; }}

  /* Glass containers ("cloud cards") */
  .glass {{
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 24px;
    box-shadow: 0 10px 34px rgba(0,0,0,0.20);
  }}

  /* Vertical stack used by listicle / framework / news */
  .stack {{ flex: 1; display: flex; flex-direction: column; gap: 16px; min-height: 0; }}
  .row {{
    flex: 1 1 0; min-height: 0; overflow: hidden;
    display: flex; align-items: center; gap: 26px; padding: 18px 28px;
  }}
  .numchip {{
    flex: 0 0 auto; width: 70px; height: 70px; border-radius: 18px;
    background: var(--accent); color: #0e1b3d;
    font-family: var(--heading-font); font-weight: 800; font-size: 32px;
    display: flex; align-items: center; justify-content: center; line-height: 1;
  }}
  .row-text {{ flex: 1; min-width: 0; }}
  .row-eyebrow {{
    color: var(--accent); font-size: 14px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px;
  }}
  .row-title {{
    color: {WHITE}; font-family: var(--heading-font);
    font-weight: 700; font-size: 28px; line-height: 1.18;
  }}
  .row-detail {{ color: {MUTED}; font-size: 18px; line-height: 1.4; margin-top: 6px; }}

  /* Framework step rail with connector */
  .step {{ align-items: stretch; }}
  .step-rail {{ display: flex; flex-direction: column; align-items: center; flex: 0 0 auto; }}
  .step-rail .numchip {{ width: 58px; height: 58px; border-radius: 50%; font-size: 26px; }}
  .connector {{ flex: 1; width: 3px; background: rgba(255,255,255,0.18); margin: 8px 0 -28px; }}

  /* News blocks */
  .news-block {{ padding: 20px 28px; flex: 1 1 0; min-height: 0; overflow: hidden; }}
  .news-label {{
    color: var(--accent); font-family: var(--heading-font);
    font-size: 18px; font-weight: 800; letter-spacing: 1.5px;
    text-transform: uppercase; margin-bottom: 8px;
  }}
  .news-text {{ color: {WHITE}; font-size: 22px; line-height: 1.4; font-weight: 400; }}

  /* Big-stat layout */
  .stat-wrap {{ flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: space-between; text-align: center; position: relative; padding: 40px 0 10px; }}
  .stat-deco {{
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -58%);
    font-family: var(--heading-font); font-weight: 800; font-size: 540px; line-height: 1;
    color: var(--accent); opacity: 0.05; z-index: 0; pointer-events: none; white-space: nowrap;
  }}
  .stat-main {{ display: flex; flex-direction: column; align-items: center; flex: 1; justify-content: center; }}
  .stat-value {{
    color: var(--accent); font-family: var(--heading-font);
    font-weight: 800; font-size: 240px; line-height: 0.95; letter-spacing: -3px;
  }}
  .stat-line {{ width: 90px; height: 6px; background: var(--accent); border-radius: 3px; margin: 28px 0 24px; }}
  .stat-label {{ color: {WHITE}; font-size: 36px; font-weight: 700; line-height: 1.2; max-width: 820px; }}
  .stat-source {{ color: {MUTED}; font-size: 18px; margin-top: 16px; letter-spacing: 1px; text-transform: uppercase; }}
  .ctx-wrap {{ display: flex; flex-wrap: wrap; gap: 14px; justify-content: center; max-width: 940px; flex: 0 0 auto; }}
  .ctx-chip {{
    display: flex; align-items: center; gap: 12px; padding: 16px 24px;
    color: {WHITE}; font-size: 18px; font-weight: 500; text-align: left;
  }}
  .ctx-chip::before {{
    content: ""; flex: 0 0 auto; width: 10px; height: 10px; border-radius: 50%;
    background: var(--accent);
  }}

  /* Quote layout */
  .quote-wrap {{ flex: 1; display: flex; flex-direction: column; justify-content: space-between; position: relative; padding: 30px 0 10px; }}
  .quote-deco {{
    position: absolute; top: -150px; right: -30px;
    font-family: Georgia, 'Times New Roman', serif; font-size: 680px; line-height: 1;
    color: var(--accent); opacity: 0.07; z-index: 0; pointer-events: none;
  }}
  .quote-top {{ flex: 0 0 auto; }}
  .quote-mark {{
    color: var(--accent); font-family: Georgia, 'Times New Roman', serif;
    font-size: 180px; line-height: 0.5; height: 84px;
  }}
  .quote-row {{ display: flex; gap: 36px; align-items: stretch; flex: 0 1 auto; }}
  .quote-rule {{ flex: 0 0 6px; background: var(--accent); border-radius: 3px; }}
  .quote-text {{
    color: {WHITE}; font-family: var(--heading-font);
    font-weight: 700; font-size: 64px; line-height: 1.15; letter-spacing: -0.5px;
  }}
  .quote-close {{
    color: var(--accent); font-family: Georgia, 'Times New Roman', serif;
    font-size: 64px; line-height: 1; margin-left: 4px;
  }}
  .quote-foot {{ display: flex; align-items: flex-start; gap: 20px; }}
  .quote-dash {{ flex: 0 0 50px; height: 4px; background: var(--accent); margin-top: 18px; border-radius: 2px; }}
  .quote-attr {{ color: var(--accent); font-size: 26px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; }}
  .quote-support {{ color: {MUTED}; font-size: 22px; line-height: 1.45; margin-top: 8px; max-width: 760px; }}

  /* Footer */
  .footer {{
    flex: 0 0 auto; display: flex; align-items: center; gap: 10px;
    margin-top: 22px; padding-top: 18px;
    border-top: 1px solid rgba(255,255,255,0.10);
  }}
  .footer-dot {{ width: 10px; height: 10px; border-radius: 50%; background: var(--accent); }}
  .footer-text {{ color: {MUTED}; font-size: 16px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; }}
"""


def build_card_html(data: dict, style: dict | None = None, editable: bool = False) -> str:
    s = _merge_style(style)
    accent = s["accent_color"]
    logo_px = s["logo_px"]
    font = FONT_OPTIONS[s["heading_font"]]

    if s["bg_gradient"]:
        bg_css = f"linear-gradient({s['bg_angle']}deg, {s['bg_color']}, {s['bg_color2']})"
    else:
        bg_css = s["bg_color"]

    template = (data.get("template") or DEFAULT_TEMPLATE)
    if template not in _RENDERERS:
        template = DEFAULT_TEMPLATE
    renderer = _RENDERERS[template]
    content_html = renderer(data)

    logo_html = _render_logo(logo_px, s["logo_x"], s["logo_y"], editable)
    blobs_html = _render_blobs(accent, s["bg_color2"])
    footer_html = _render_footer()
    drag_script = _LOGO_DRAG_SCRIPT if editable else ""
    topbar_h = logo_px if (s["logo_x"] is None and s["logo_y"] is None) else 40

    google_links = "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
    google_links += (
        "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?"
        f"family={font['google']}&family=Inter:wght@400;600;700;800&display=swap'>"
    )

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
{google_links}
<style>{_stylesheet(accent, font['family'], bg_css, topbar_h)}</style>
</head>
<body>
  <div class="card">
    {blobs_html}
    {logo_html}
    <div class="topbar"></div>
    {content_html}
    {footer_html}
  </div>
  {drag_script}
</body>
</html>"""

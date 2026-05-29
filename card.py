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
    "logo_px": 160,
    "bg_color": "#0e1b3d",
    "accent_color": "#FFD23F",
    "heading_font": "sans",
    "bg_gradient": False,
    "bg_color2": "#241a3d",
    "bg_angle": 135,
}


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
        '<span style="color:var(--accent)">' + safe_h + "</span>",
        safe_hook,
        count=1,
    )


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
            f'<div style="color:var(--accent);font-size:20px;font-weight:800;'
            f'text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px;'
            f'padding-bottom:8px;border-bottom:2px solid rgba(255,255,255,0.16);">{name}</div>'
            f'<ul style="list-style:none;padding:0;margin:0;">'
            f'{"".join(items_html)}'
            f'</ul>'
            f'</div>'
        )
    return "".join(blocks)


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
        pos = "right:70px;top:64px;"

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
        f'<div id="dtq-logo-box" style="position:absolute;{pos}{cursor}z-index:10;">'
        f'{inner}{handle}</div>'
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


def build_card_html(data: dict, style: dict | None = None, editable: bool = False) -> str:
    s = _merge_style(style)
    accent = s["accent_color"]
    logo_px = s["logo_px"]
    font = FONT_OPTIONS[s["heading_font"]]

    if s["bg_gradient"]:
        bg_css = f"linear-gradient({s['bg_angle']}deg, {s['bg_color']}, {s['bg_color2']})"
    else:
        bg_css = s["bg_color"]

    hook = _wrap_highlight(data.get("hook", ""), data.get("highlight", ""))
    subtitle = html.escape((data.get("subtitle") or "").strip())
    categories_html = _render_categories(data.get("categories") or [])
    logo_html = _render_logo(logo_px, s["logo_x"], s["logo_y"], editable)
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
<style>
  :root {{
    --accent: {accent};
    --heading-font: {font['family']};
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1080px;
    background: {bg_css};
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
    min-height: {topbar_h}px;
  }}
  .hook {{
    color: {WHITE};
    font-family: var(--heading-font);
    font-size: 56px;
    font-weight: 800;
    line-height: 1.08;
    margin-top: 8px;
    letter-spacing: -0.5px;
  }}
  .subtitle {{
    color: var(--accent);
    font-family: var(--heading-font);
    font-size: 22px;
    font-weight: 600;
    margin-top: 16px;
    margin-bottom: 30px;
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
    {logo_html}
    <div class="topbar"></div>
    <div class="hook">{hook}</div>
    <div class="subtitle">{subtitle}</div>
    <div class="grid">{categories_html}</div>
  </div>
  {drag_script}
</body>
</html>"""

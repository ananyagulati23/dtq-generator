import asyncio
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from card import DEFAULT_STYLE, FONT_OPTIONS, build_card_html
from prompts import TONE_PRESETS, build_messages
from services import (
    ServiceError,
    call_groq,
    call_hcti,
    save_to_airtable,
    send_email,
    update_airtable_record,
)

load_dotenv()

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="DTQ LinkedIn Content Generator")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

TEAM_MEMBERS = ["Naman Kothari", "Piyush", "Agrima", "Kavya", "Ananya"]

# Teammate emails come from env vars (never committed). Set EMAIL_* in .env locally
# and in the Render dashboard for production. A blank value skips emailing that person.
TEAM_EMAILS = {
    "Naman Kothari": os.getenv("EMAIL_NAMAN", ""),
    "Piyush": os.getenv("EMAIL_PIYUSH", ""),
    "Agrima": os.getenv("EMAIL_AGRIMA", ""),
    "Kavya": os.getenv("EMAIL_KAVYA", ""),
    "Ananya": os.getenv("EMAIL_ANANYA", ""),
}

DEADLINE_HOURS = 12
STATUS_FLOW = ["Draft", "Ready for Review", "Approved", "Done"]
TONE_OPTIONS = [
    ("default", "Default — balanced DTQ voice"),
    ("punchy", "Punchy — short, opinionated"),
    ("thoughtful", "Thoughtful — exploratory, nuanced"),
    ("question-led", "Question-led — invites discussion"),
    ("data-led", "Data-led — anchored in a real stat"),
]

# --- Password gate (optional). Set APP_PASSWORD env var to enable. ---
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
COOKIE_NAME = "dtq_auth"
OPEN_PATHS = {"/login"}


def _expected_cookie() -> str:
    return "ok-" + hashlib.sha256(APP_PASSWORD.encode()).hexdigest()[:32]


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not APP_PASSWORD:
        return await call_next(request)
    if request.url.path in OPEN_PATHS or request.url.path.startswith("/static"):
        return await call_next(request)
    if request.cookies.get(COOKIE_NAME) == _expected_cookie():
        return await call_next(request)
    if request.url.path.startswith("/api/"):
        return JSONResponse({"ok": False, "error": "Not authenticated"}, status_code=401)
    return RedirectResponse("/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, password: str = Form(...)):
    if APP_PASSWORD and password == APP_PASSWORD:
        resp = RedirectResponse("/", status_code=302)
        resp.set_cookie(
            COOKIE_NAME,
            _expected_cookie(),
            httponly=True,
            max_age=30 * 24 * 3600,
            samesite="lax",
            secure=False,
        )
        return resp
    return templates.TemplateResponse(
        request, "login.html", {"error": "Incorrect password"}, status_code=401
    )


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp


# --- Main app ---


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "form.html",
        {"team": TEAM_MEMBERS, "tones": TONE_OPTIONS},
    )


@app.get("/download")
async def download(url: str, filename: str = "dtq-card.png"):
    if not url.startswith("https://ondemand.hcti.io/") and not url.startswith("https://hcti.io/"):
        raise HTTPException(status_code=400, detail="Invalid image host")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch image")
    safe_name = "".join(c for c in filename if c.isalnum() or c in "-_.") or "dtq-card.png"
    return Response(
        content=resp.content,
        media_type=resp.headers.get("content-type", "image/png"),
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


async def _notify_assignee(name: str, title: str, record_id: str, due_dt: datetime) -> str | None:
    """Email the assignee about a new task. Returns a warning string on failure, else None."""
    email = (TEAM_EMAILS.get(name) or "").strip()
    if not email:
        return f"No email on file for {name}; notification skipped (add it in TEAM_EMAILS)."

    base = os.getenv("AIRTABLE_BASE_ID", "")
    table = os.getenv("AIRTABLE_TABLE_ID", "")
    record_url = f"https://airtable.com/{base}/{table}/{record_id}" if base and table else "your Airtable base"

    tz_name = os.getenv("DISPLAY_TZ", "Asia/Kolkata")
    try:
        due_local = due_dt.astimezone(ZoneInfo(tz_name)).strftime("%b %d, %Y at %I:%M %p")
        tz_label = tz_name
    except Exception:
        due_local = due_dt.strftime("%b %d, %Y at %I:%M %p")
        tz_label = "UTC"

    subject = f"New DTQ post assigned to you: {title}"
    body = (
        f"Hi {name},\n\n"
        f"A new LinkedIn post has been assigned to you in the DTQ content tracker.\n\n"
        f"Post: {title}\n"
        f"Open the record: {record_url}\n\n"
        f"Please review it, post it on LI and mark it Done within {DEADLINE_HOURS} hours.\n"
        f"Deadline: {due_local} ({tz_label})\n\n"
       
        f"— DTQ Content Generator"
    )
    try:
        await asyncio.to_thread(send_email, email, subject, body)
        return None
    except Exception as e:
        return f"Assignment email to {name} failed: {e}"


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    topic: str = Form(default=""),
    custom_instructions: str = Form(default=""),
    assignee: str = Form(default=""),
    tone: str = Form(default="default"),
):
    def err(stage: str, detail: str):
        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "error": f"{stage}: {detail}",
                "caption": None,
                "image_url": None,
                "record_id": None,
                "topic": topic,
                "custom_instructions": custom_instructions,
                "tone": tone,
                "assignee": assignee or "Unassigned",
                "status": "Draft",
                "status_flow": STATUS_FLOW,
            },
            status_code=200,
        )

    try:
        messages = build_messages(topic, custom_instructions, tone=tone)
        data = await call_groq(messages)

        def _item_count(d: dict) -> int:
            return sum(len(c.get("items") or []) for c in (d.get("categories") or []))

        # Only retry on egregiously low counts to avoid blowing the Groq TPM budget.
        # Don't replay the prior response — just re-prompt with stronger emphasis.
        if _item_count(data) < 10:
            retry_messages = build_messages(topic, custom_instructions, tone=tone)
            retry_messages[0]["content"] = (
                retry_messages[0]["content"]
                + "\n\nRETRY NOTICE: A prior attempt returned too few items. "
                "You MUST return exactly 4 categories with 16-20 total items (4-5 per category). "
                "Count before responding."
            )
            try:
                retry_data = await call_groq(retry_messages)
                if _item_count(retry_data) > _item_count(data):
                    data = retry_data
            except ServiceError:
                pass  # keep the original (low-item) result rather than failing the whole request
    except ServiceError as e:
        return err("Groq generation failed", str(e))
    except Exception as e:
        return err("Unexpected error during generation", str(e))

    required = ("title", "caption", "hook", "categories")
    missing = [k for k in required if not data.get(k)]
    if missing:
        return err("Groq response missing fields", ", ".join(missing))

    try:
        card_html = build_card_html(data)
        image_url = await call_hcti(card_html)
    except ServiceError as e:
        return err("Image rendering failed", str(e))
    except Exception as e:
        return err("Unexpected error rendering card", str(e))

    airtable_warning = None
    record_id = None
    assignee_value = assignee.strip() if assignee and assignee != "Unassigned" else None
    due_dt = None
    due_iso = None
    if assignee_value:
        due_dt = datetime.now(timezone.utc) + timedelta(hours=DEADLINE_HOURS)
        due_iso = due_dt.isoformat()
    try:
        result = await save_to_airtable(
            title=data["title"],
            content=data["caption"],
            image_url=image_url,
            assignee=assignee_value,
            due_date=due_iso,
        )
        record_id = result.get("id")
    except ServiceError as e:
        airtable_warning = f"Airtable save failed: {e}"
    except Exception as e:
        airtable_warning = f"Airtable save failed: {e}"

    # Notify the assignee by email (non-fatal).
    if assignee_value and record_id:
        notice = await _notify_assignee(assignee_value, data.get("title", ""), record_id, due_dt)
        if notice:
            airtable_warning = f"{airtable_warning} | {notice}" if airtable_warning else notice

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "error": None,
            "caption": data["caption"],
            "image_url": image_url,
            "record_id": record_id,
            "topic": topic,
            "custom_instructions": custom_instructions,
            "tone": tone,
            "title": data.get("title", ""),
            "assignee": assignee_value or "Unassigned",
            "status": "Draft",
            "status_flow": STATUS_FLOW,
            "warning": airtable_warning,
            "card_data": data,
            "default_style": DEFAULT_STYLE,
            "font_options": [(k, v["label"]) for k, v in FONT_OPTIONS.items()],
        },
    )


# --- API endpoints for edits / regenerations / status changes ---


class UpdateCaptionPayload(BaseModel):
    record_id: str
    caption: str


@app.post("/api/update-caption")
async def api_update_caption(payload: UpdateCaptionPayload):
    try:
        await update_airtable_record(payload.record_id, {"Post Content": payload.caption})
    except ServiceError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=502)
    return {"ok": True}


class UpdateStatusPayload(BaseModel):
    record_id: str
    status: str


@app.post("/api/update-status")
async def api_update_status(payload: UpdateStatusPayload):
    if payload.status not in STATUS_FLOW:
        return JSONResponse({"ok": False, "error": "Invalid status"}, status_code=400)
    try:
        await update_airtable_record(payload.record_id, {"Status": payload.status})
    except ServiceError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=502)
    return {"ok": True, "status": payload.status}


class RegenPayload(BaseModel):
    record_id: str | None = None
    topic: str = ""
    custom_instructions: str = ""
    tone: str = "default"


@app.post("/api/regenerate-caption")
async def api_regenerate_caption(payload: RegenPayload):
    try:
        messages = build_messages(payload.topic, payload.custom_instructions, tone=payload.tone)
        data = await call_groq(messages)
        new_caption = (data.get("caption") or "").strip()
        if not new_caption:
            return JSONResponse({"ok": False, "error": "Groq returned no caption"}, status_code=502)
        if payload.record_id:
            await update_airtable_record(payload.record_id, {"Post Content": new_caption})
        return {"ok": True, "caption": new_caption}
    except ServiceError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=502)


@app.post("/api/regenerate-image")
async def api_regenerate_image(payload: RegenPayload):
    try:
        messages = build_messages(payload.topic, payload.custom_instructions, tone=payload.tone)
        data = await call_groq(messages)
        card_html = build_card_html(data)
        image_url = await call_hcti(card_html)
        if payload.record_id:
            await update_airtable_record(payload.record_id, {"Image URL": image_url})
        return {"ok": True, "image_url": image_url, "card_data": data}
    except ServiceError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=502)


class RestylePayload(BaseModel):
    record_id: str | None = None
    data: dict
    style: dict


@app.post("/api/card-preview", response_class=HTMLResponse)
async def api_card_preview(payload: RestylePayload):
    # Returns the live card HTML (no HCTI call) for the in-browser preview iframe.
    # editable=True injects the drag/resize handles for the logo.
    return HTMLResponse(build_card_html(payload.data, style=payload.style, editable=True))


@app.post("/api/restyle")
async def api_restyle(payload: RestylePayload):
    # Re-render the SAME content with new visual style. No Groq call, no token cost.
    try:
        card_html = build_card_html(payload.data, style=payload.style)
        image_url = await call_hcti(card_html)
        if payload.record_id:
            await update_airtable_record(payload.record_id, {"Image URL": image_url})
        return {"ok": True, "image_url": image_url}
    except ServiceError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=502)


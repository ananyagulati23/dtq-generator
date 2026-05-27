import hashlib
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from card import build_card_html
from prompts import TONE_PRESETS, build_messages
from services import (
    ServiceError,
    call_groq,
    call_hcti,
    list_airtable_records,
    save_to_airtable,
    update_airtable_record,
)

load_dotenv()

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="DTQ LinkedIn Content Generator")

TEAM_MEMBERS = ["Naman Kothari", "Piyush", "Agrima", "Kavya", "Ananya"]
STATUS_FLOW = ["Draft", "Ready for Review", "Approved", "Published"]
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
    if request.url.path in OPEN_PATHS:
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

        if _item_count(data) < 14:
            retry_messages = messages + [
                {"role": "assistant", "content": str(data)},
                {
                    "role": "user",
                    "content": (
                        "That response had too few items. Regenerate the SAME JSON object, "
                        "but ensure the categories contain a TOTAL of at least 16 items "
                        "across exactly 4 categories (4-5 items per category). Keep every "
                        "item a real named thing. Return ONLY the JSON object."
                    ),
                },
            ]
            retry_data = await call_groq(retry_messages)
            if _item_count(retry_data) > _item_count(data):
                data = retry_data
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
    try:
        result = await save_to_airtable(
            title=data["title"],
            content=data["caption"],
            image_url=image_url,
            assignee=assignee_value,
        )
        record_id = result.get("id")
    except ServiceError as e:
        airtable_warning = f"Airtable save failed: {e}"
    except Exception as e:
        airtable_warning = f"Airtable save failed: {e}"

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
        return {"ok": True, "image_url": image_url}
    except ServiceError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=502)


# --- Posts list view ---


@app.get("/posts", response_class=HTMLResponse)
async def posts(request: Request):
    try:
        raw = await list_airtable_records()
    except ServiceError as e:
        return templates.TemplateResponse(
            request,
            "posts.html",
            {"error": str(e), "records": [], "team": TEAM_MEMBERS, "statuses": STATUS_FLOW},
        )

    raw.sort(key=lambda r: r.get("createdTime", ""), reverse=True)
    records = []
    for r in raw:
        f = r.get("fields") or {}
        records.append(
            {
                "id": r.get("id", ""),
                "title": f.get("Post Title") or "(untitled)",
                "assignee": f.get("Assignee") or "Unassigned",
                "status": f.get("Status") or "Draft",
                "image_url": f.get("Image URL") or "",
                "created": (r.get("createdTime") or "")[:10],
            }
        )
    return templates.TemplateResponse(
        request,
        "posts.html",
        {"error": None, "records": records, "team": TEAM_MEMBERS, "statuses": STATUS_FLOW},
    )

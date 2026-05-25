from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from card import build_card_html
from prompts import build_messages
from services import ServiceError, call_groq, call_hcti, save_to_airtable

load_dotenv()

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="DTQ LinkedIn Content Generator")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "form.html", {})


@app.get("/download")
async def download(url: str, filename: str = "dtq-card.png"):
    # Only proxy HCTI-hosted images to avoid being used as an open proxy.
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
):
    def err(stage: str, detail: str):
        return templates.TemplateResponse(
            request,
            "result.html",
            {
                "error": f"{stage}: {detail}",
                "caption": None,
                "image_url": None,
            },
            status_code=200,
        )

    # 1. Build prompt + call Groq (with one retry if item count is too low)
    try:
        messages = build_messages(topic, custom_instructions)
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

    # 2. Sanity-check required fields from Groq
    required = ("title", "caption", "hook", "categories")
    missing = [k for k in required if not data.get(k)]
    if missing:
        return err("Groq response missing fields", ", ".join(missing))

    # 3. Build card HTML + render image
    try:
        card_html = build_card_html(data)
        image_url = await call_hcti(card_html)
    except ServiceError as e:
        return err("Image rendering failed", str(e))
    except Exception as e:
        return err("Unexpected error rendering card", str(e))

    # 4. Save to Airtable (non-fatal: still show result if Airtable fails)
    airtable_warning = None
    try:
        await save_to_airtable(
            title=data["title"],
            content=data["caption"],
            image_url=image_url,
        )
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
            "title": data.get("title", ""),
            "topic": data.get("topic", ""),
            "warning": airtable_warning,
        },
    )

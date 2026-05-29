import json
import os
import re
import smtplib
from email.message import EmailMessage

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HCTI_URL = "https://hcti.io/v1/image"
AIRTABLE_URL = "https://api.airtable.com/v0/{base}/{table}"

DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class ServiceError(Exception):
    pass


async def call_groq(messages: list[dict]) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ServiceError("GROQ_API_KEY not set")

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 6000,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Groq's JSON mode occasionally returns invalid/incomplete JSON (or wraps it
    # in code fences). It's stochastic, so retry once before giving up.
    for attempt in range(2):
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)

        if resp.status_code == 429:
            m = re.search(r"try again in ([\d.]+)s", resp.text)
            wait_hint = f" Try again in ~{m.group(1)}s." if m else ""
            raise ServiceError(f"Groq rate limit hit (free-tier TPM cap).{wait_hint}")
        if resp.status_code == 400 and "json_validate_failed" in resp.text:
            if attempt == 0:
                continue
            raise ServiceError(
                "The AI returned invalid JSON twice in a row. Please try again "
                "(a more specific topic usually helps)."
            )
        if resp.status_code >= 400:
            raise ServiceError(f"Groq error {resp.status_code}: {resp.text}")

        body = resp.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ServiceError(f"Unexpected Groq response shape: {body}") from e

        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if attempt == 0:
                continue
            raise ServiceError(f"Groq returned non-JSON content: {content[:500]}")

    raise ServiceError("Groq did not return valid JSON. Please try again.")


async def call_hcti(html: str) -> str:
    user_id = os.getenv("HCTI_USER_ID")
    api_key = os.getenv("HCTI_API_KEY")
    if not user_id or not api_key:
        raise ServiceError("HCTI_USER_ID or HCTI_API_KEY not set")

    payload = {
        "html": html,
        "viewport_width": 1080,
        "viewport_height": 1080,
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.post(HCTI_URL, json=payload, auth=(user_id, api_key))

    if resp.status_code >= 400:
        raise ServiceError(f"HCTI error {resp.status_code}: {resp.text}")

    body = resp.json()
    url = body.get("url")
    if not url:
        raise ServiceError(f"HCTI response missing 'url': {body}")
    return url


async def save_to_airtable(
    title: str,
    content: str,
    image_url: str,
    status: str = "Draft",
    assignee: str | None = None,
    due_date: str | None = None,
) -> dict:
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    if not token or not base_id or not table_id:
        raise ServiceError("AIRTABLE_TOKEN, AIRTABLE_BASE_ID, or AIRTABLE_TABLE_ID not set")

    url = AIRTABLE_URL.format(base=base_id, table=table_id)
    fields = {
        "Post Title": title,
        "Post Content": content,
        "Image URL": image_url,
        "Status": status,
    }
    if assignee:
        fields["Assignee"] = assignee
    if due_date:
        fields["Due Date"] = due_date
    payload = {"fields": fields}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.status_code >= 400:
        raise ServiceError(f"Airtable error {resp.status_code}: {resp.text}")

    return resp.json()


async def update_airtable_record(record_id: str, fields: dict) -> dict:
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    if not token or not base_id or not table_id:
        raise ServiceError("Airtable env vars not set")

    url = AIRTABLE_URL.format(base=base_id, table=table_id) + f"/{record_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.patch(url, json={"fields": fields}, headers=headers)

    if resp.status_code >= 400:
        raise ServiceError(f"Airtable update error {resp.status_code}: {resp.text}")
    return resp.json()


async def list_airtable_records(max_records: int = 100) -> list[dict]:
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    if not token or not base_id or not table_id:
        raise ServiceError("Airtable env vars not set")

    url = AIRTABLE_URL.format(base=base_id, table=table_id)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"pageSize": str(min(max_records, 100))}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url, headers=headers, params=params)

    if resp.status_code >= 400:
        raise ServiceError(f"Airtable list error {resp.status_code}: {resp.text}")
    return resp.json().get("records", [])


def send_email(to_email: str, subject: str, body: str) -> None:
    """Blocking SMTP send (call via asyncio.to_thread). Configured for Gmail by default."""
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_email = os.getenv("FROM_EMAIL") or user
    if not user or not password:
        raise ServiceError("SMTP_USER or SMTP_PASS not set")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

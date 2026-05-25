import json
import os

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
        "temperature": 0.8,
        "max_tokens": 3000,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.post(GROQ_URL, json=payload, headers=headers)

    if resp.status_code >= 400:
        raise ServiceError(f"Groq error {resp.status_code}: {resp.text}")

    body = resp.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise ServiceError(f"Unexpected Groq response shape: {body}") from e

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ServiceError(f"Groq returned non-JSON content: {content[:500]}") from e


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
) -> dict:
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    if not token or not base_id or not table_id:
        raise ServiceError("AIRTABLE_TOKEN, AIRTABLE_BASE_ID, or AIRTABLE_TABLE_ID not set")

    url = AIRTABLE_URL.format(base=base_id, table=table_id)
    payload = {
        "fields": {
            "Post Title": title,
            "Post Content": content,
            "Image URL": image_url,
            "Status": status,
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.status_code >= 400:
        raise ServiceError(f"Airtable error {resp.status_code}: {resp.text}")

    return resp.json()

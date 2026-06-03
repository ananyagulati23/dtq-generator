import asyncio
import json
import os
import re

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HCTI_URL = "https://hcti.io/v1/image"
AIRTABLE_URL = "https://api.airtable.com/v0/{base}/{table}"

DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

# Free-tier TPM is tight (~12k/min). A 429 reports how long until the window
# clears; wait it out rather than failing (a slow success beats an error). Cap
# the wait so a request can't hang indefinitely.
MAX_RATE_LIMIT_WAIT = 45.0


class ServiceError(Exception):
    pass


def _loads_lenient(text: str | None):
    """Parse JSON from a model response, tolerating code fences, leading/trailing
    prose, and truncated output (close any unterminated string/brackets). Returns
    the parsed dict, or None if nothing salvageable."""
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()

    # Isolate the first JSON object.
    start = s.find("{")
    if start == -1:
        return None
    s = s[start:]

    # Walk the text tracking string/bracket state. Record where the first
    # top-level object closes (to drop trailing prose); if it never closes the
    # output was truncated, so close the open string/brackets ourselves.
    stack = []
    in_str = False
    escaped = False
    end = None
    for i, ch in enumerate(s):
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
            if not stack:
                end = i + 1
                break

    if end is not None:
        try:
            return json.loads(s[:end])
        except json.JSONDecodeError:
            return None

    repaired = s.rstrip().rstrip(",")
    if in_str:
        repaired += '"'
    for opener in reversed(stack):
        repaired += "}" if opener == "{" else "]"

    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        return None


async def call_groq(messages: list[dict], max_tokens: int = 4500) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ServiceError("GROQ_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Groq's JSON mode is stochastic and the free tier rate-limits aggressively.
    # Retry up to 3 times: wait out 429s, salvage near-valid JSON, and give the
    # model more room (higher max_tokens) if it ran out mid-document.
    tokens = max_tokens
    last_err = "unknown error"
    for attempt in range(3):
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.6,
            "max_tokens": tokens,
        }
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)

        if resp.status_code == 429:
            m = re.search(r"try again in ([\d.]+)s", resp.text)
            wait = float(m.group(1)) if m else 5.0
            if attempt < 2 and wait <= MAX_RATE_LIMIT_WAIT:
                await asyncio.sleep(wait + 0.5)
                continue
            hint = f" Try again in ~{m.group(1)}s." if m else ""
            raise ServiceError(f"Groq rate limit hit (free-tier TPM cap).{hint}")

        if resp.status_code == 400 and "json_validate_failed" in resp.text:
            # Groq returns the partial output in error.failed_generation — try to
            # salvage it before giving up.
            try:
                fg = resp.json().get("error", {}).get("failed_generation")
            except Exception:
                fg = None
            salvaged = _loads_lenient(fg)
            if salvaged:
                return salvaged
            last_err = "model produced invalid JSON"
            if attempt < 2:
                tokens = min(tokens + 2000, 8000)  # likely truncated — give more room
                continue
            raise ServiceError(
                "The AI returned invalid JSON repeatedly. Please try again "
                "(a more specific topic usually helps)."
            )

        if resp.status_code >= 400:
            raise ServiceError(f"Groq error {resp.status_code}: {resp.text}")

        body = resp.json()
        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ServiceError(f"Unexpected Groq response shape: {body}") from e

        parsed = _loads_lenient(content)
        if parsed is not None:
            return parsed

        last_err = "non-JSON content"
        if attempt < 2:
            # finish_reason 'length' means it was cut off; otherwise just stochastic.
            if choice.get("finish_reason") == "length":
                tokens = min(tokens + 2000, 8000)
            continue
        raise ServiceError(f"Groq returned unparseable content ({last_err}).")

    raise ServiceError(f"Groq did not return valid JSON ({last_err}). Please try again.")


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
    assignee_email: str | None = None,
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
    if assignee_email:
        fields["Assignee Email"] = assignee_email
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

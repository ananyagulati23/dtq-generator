# DTQ LinkedIn Content Generator

A small FastAPI app that takes a topic (or auto-picks one), generates a LinkedIn post + an infographic card image for Data Trust Quotients (DTQ), and saves the record to Airtable.

Replaces an earlier n8n workflow with a single self-hostable Python service.

## What it does

1. User submits a topic + optional custom instructions via a form.
2. The app sends a structured prompt to Groq (`llama-3.3-70b-versatile`) asking for a JSON object: hook, subtitle, caption, and 4 categories of 4–5 real named items each.
3. It builds a 1080×1080 HTML card from the JSON, with real brand logos pulled via Clearbit → Google favicons fallback chain.
4. It sends the HTML to HTMLCSStoImage (HCTI) which returns a hosted PNG.
5. It saves the post title, caption, and image URL to Airtable as a new "Draft" record.
6. The result page shows the rendered card + the LinkedIn caption, with a download button.

## Stack

- **FastAPI** — web framework
- **Uvicorn** — ASGI server
- **httpx** — async HTTP client for all external API calls
- **Jinja2** — server-side templates
- **python-dotenv** — env var loading for local dev
- Deployed on **Render** 

## Project structure

```
dtq-generator/
├── main.py              # FastAPI routes: GET /, POST /generate, GET /download
├── prompts.py           # Groq prompt builder + topic fallback list + brand context
├── card.py              # HTML card builder (1080x1080, logos, badges)
├── services.py          # Async clients for Groq, HCTI, Airtable
├── templates/
│   ├── form.html        # Submission form (minimalist light theme)
│   └── result.html      # Generated post + card image
├── static/
│   └── dtq-logo.png     # Optional: real DTQ logo (auto-embedded as data URI if present)
├── requirements.txt     # Pinned dependencies
├── render.yaml          # Render deploy config
├── .python-version      # 3.12.7
├── .env                 # API keys (gitignored, never commit)
└── .gitignore
```

## Environment variables

Set these in `.env` for local dev, and in the Render dashboard for production.

| Variable             | Purpose                                              |
|----------------------|------------------------------------------------------|
| `GROQ_API_KEY`       | Groq chat completions                                |
| `HCTI_USER_ID`       | HTMLCSStoImage basic-auth username                   |
| `HCTI_API_KEY`       | HTMLCSStoImage basic-auth password                   |
| `AIRTABLE_TOKEN`     | Airtable personal access token                       |
| `AIRTABLE_BASE_ID`   | Airtable base ID (`app...`)                          |
| `AIRTABLE_TABLE_ID`  | Airtable table ID (`tbl...`)                         |

Airtable table must have fields named exactly: `Post Title`, `Post Content`, `Image URL`, `Status`.

## Run locally

```bash
cd dtq-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Fill in .env with your keys
python -m uvicorn main:app --reload --port 8000
```

Open http://localhost:8000.

Note: invoke uvicorn as `python -m uvicorn ...` (not bare `uvicorn`) so it picks up the venv's interpreter instead of any homebrew Python on your PATH.




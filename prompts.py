import random

DTQ_CONTEXT = """\
Data Trust Quotients (DTQ) is a strategic platform that advances and embeds
trust in data governance and management, helping organizations navigate AI
and digital transformation.

DTQ pillars:
- Forums & Engagement
- Trend Insights & Foresight
- Industry Networking
- Consultancy & Advisory
- Governance, Transparency, Resilience

Audience: CISOs, cybersecurity leaders, AI leaders, and data governance
executives at enterprises navigating AI adoption and regulatory pressure.

Voice: confident, factual, no hype, no marketing fluff. Plain English. Every
claim grounded in real frameworks, regulations, tools, vendors, or standards.
Legit information, facts only.
"""

FALLBACK_TOPICS = [
    "AI governance frameworks for enterprise adoption",
    "Data privacy regulations shaping 2026 strategy",
    "Cybersecurity in the age of generative AI",
    "Responsible AI deployment in regulated industries",
    "Third-party and supply chain risk management",
    "Zero trust architecture in hybrid cloud environments",
    "Cloud security posture management (CSPM)",
    "Data lineage, provenance, and observability",
    "AI model risk management and validation",
    "Insider threat detection and identity analytics",
    "Identity and access management for AI agents",
    "Quantum-safe cryptography and post-quantum readiness",
    "Ransomware defense and recovery strategy",
    "Generative AI security risks and mitigations",
    "Privacy-enhancing technologies (PETs)",
    "Cyber resilience and incident response maturity",
    "Regulatory compliance: EU AI Act, GDPR, DORA",
    "Data ethics, fairness, and bias mitigation",
    "Operational technology (OT) and ICS security",
    "Board-level reporting on cyber and AI risk",
]

ICON_OPTIONS = [
    "shield", "lock", "ai", "data", "scales", "search",
    "brain", "globe", "policy", "warning", "key", "chart",
    "audit", "network", "alert",
]

# Canonical template ids. Keep in sync with card.py TEMPLATES and form.html gallery.
TEMPLATE_IDS = ["catalogue", "listicle", "news", "stat", "quote", "framework"]
DEFAULT_TEMPLATE = "catalogue"

TONE_PRESETS = {
    "default": "",
    "punchy": "TONE OVERRIDE: punchy and opinionated. Short, declarative sentences. No filler. Hook is one line, blunt.",
    "thoughtful": "TONE OVERRIDE: thoughtful and exploratory. Show nuance and second-order effects. Avoid hot takes. Let the reader sit with a tension.",
    "question-led": "TONE OVERRIDE: question-led. Open with a question that names a real tension, and close with a different question that invites reply.",
    "data-led": "TONE OVERRIDE: data-led. Anchor the caption in ONE specific, real, verifiable statistic from a named source (e.g. Verizon DBIR, Gartner, IBM Cost of a Data Breach, ENISA, NIST). If you cannot name a real source, do NOT invent one.",
}


def _pick_topic() -> str:
    return random.choice(FALLBACK_TOPICS)


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------

_SYSTEM_CORE = (
    "You are a senior content strategist writing LinkedIn posts for "
    "Data Trust Quotients (DTQ). Your audience is CISOs, cybersecurity "
    "leaders, AI leaders, and data governance executives. Voice is "
    "confident, factual, plain English, zero hype, zero marketing fluff. "
    "Never invent tools, vendors, frameworks, regulations, statistics, "
    "events, dates, or quotes. Every named entity must be a real, verifiable "
    "thing. If you are not sure something is real, do not include it.\n\n"
    "HIGHEST PRIORITY: USER CUSTOM INSTRUCTIONS.\n"
    "If the user supplies custom instructions, they OUTRANK every stylistic and "
    "structural default in this prompt. If they ask for a different number of "
    "items, a specific angle, a particular emphasis, things to include or avoid, "
    "a named entity, a tone, or a wording choice, you MUST honour it. The only "
    "things custom instructions may NOT override are the accuracy, "
    "no-fabrication, and no-defamation rules below. When in doubt, do what the "
    "user asked.\n\n"
    "UNIVERSAL RELIABILITY RULES (most failures come from breaking these):\n"
    "1. COHERENCE: the headline, subtitle, and caption must describe what the "
    "card ACTUALLY contains. A reader who looks at the card must agree the "
    "headline is literally true. Do not write a claim the card content does not "
    "substantiate.\n"
    "2. EXACT REAL NAMES: use the exact product, vendor, framework, standard, "
    "person, or event name as it really exists. Never bolt a function onto a "
    "brand to invent a product (e.g. 'Mailchimp Abuse Detection' is not a real "
    "product). Fewer correct items beats padding with things that do not fit.\n"
    "3. NO DEFAMATION / NO MISLABELLING: never present a real, legitimate "
    "company, product, or person as a malicious actor, an attack/hacking tool, "
    "an illegal service, or as performing a function it does not perform. "
    "Mainstream AI vendors (OpenAI, Anthropic, Google, Microsoft, Hugging Face, "
    "Midjourney, etc.) are NOT 'phishing tools', 'hacking tools', or 'attack "
    "tools'. When a topic is about attacks or misuse, name real attack "
    "TECHNIQUES and tactics (e.g. spear phishing, credential stuffing, deepfake "
    "voice cloning, MITRE ATT&CK techniques), NOT legitimate vendor brands "
    "relabelled as weapons.\n\n" + DTQ_CONTEXT
)


def _caption_rules(card_callback: str) -> str:
    """Shared LinkedIn caption rules. card_callback describes, in plain words,
    what the accompanying card/image shows so the post can point at it."""
    return f"""\
CAPTION RULES (this is the LinkedIn post body, and it matters as much as the card, so write it with care):

Length and substance (THIS IS THE #1 PRIORITY, short captions are a failure):
- Write 220 to 320 words. This is a HARD floor of 200 words. A thin, skimpy, one-line-per-idea caption is unacceptable and will be rejected. Count your words before returning; if under 200, KEEP WRITING and add more real substance until you clear 220.
- The caption must be INFORMATIVE, not just a vibe. The reader should LEARN something concrete. Every paragraph must contain at least one specific, verifiable fact: a named framework, regulation, standard, tool, vendor, agency, or company; a real statistic with its named source; a real recent development; or a concrete worked example.
- Generic, advice-column sentences are BANNED. Do not write empty sentences like "it is essential to have a robust risk management framework in place" or "organisations must prioritise security" or "this includes conducting regular assessments". Every sentence must say something specific and true that a knowledgeable reader could not have written without knowing the topic. If a sentence would be true of almost any topic, delete it and write a concrete one.
- REFERENCE THE CARD'S ACTUAL CONTENT: name at least two or three of the specific items, points, categories, or steps that appear on THIS card, and say something real about them. This ties the post to the image and adds genuine substance.
- Aim for 5 to 7 short paragraphs (1-3 lines each), separated by blank lines. Develop the idea: set up the tension, give real context, explain the mechanism or stakes, walk through a couple of the card's specifics, and close.
- Tight but full: no repetition and no throat-clearing, but do not be terse. Depth and specificity, not padding.

NO EM-DASHES, EVER (strict, this is the most-broken rule):
- Do NOT use the em-dash (—), en-dash (–), or horizontal bar (―) anywhere. Not for asides, not for emphasis, not for ranges.
- Use a comma, period, colon, or semicolon instead. Example of what NOT to do: "Identity is the new perimeter — and most teams ignore it." Write instead: "Identity is the new perimeter, and most teams ignore it."

BANNED PHRASES AND OPENERS (do not use any of these, or close paraphrases, they are tired and overused):
- "we all know", "let's be honest", "let's face it", "here's the thing", "the truth is", "make no mistake"
- "it's no longer about X, it's about Y" and any "no longer about ..." construction
- "in today's world", "now more than ever", "gone are the days", "in an era of"
- "most CISOs we talk to", "the teams we work with", and any fake first-person-plural anecdote
- "at the end of the day", "the bottom line is", "buckle up"
Pick a FRESH, specific opener every time. Good opener styles: a real named-source statistic, a concrete recent development, a precise scenario, a counterintuitive but defensible claim, or a sharp question that names a real tension.

No hype words: "revolutionize", "game-changer", "unlock", "supercharge", "leverage", "next-gen", "cutting-edge", "harness", "empower", "transform", "seamless", "robust".

Emphasis with Unicode (this is how LinkedIn posts get visual weight without markdown):
- For 2-4 key phrases or whole sentences, use Unicode MATHEMATICAL SANS-SERIF BOLD characters (e.g. 𝗧𝗵𝗶𝘀 𝗶𝘀 𝗯𝗼𝗹𝗱). Use these on the lines that carry the most weight.
- For 1-2 softer sub-emphases, use Unicode MATHEMATICAL SANS-SERIF ITALIC characters (e.g. 𝘵𝘩𝘪𝘴 𝘪𝘴 𝘪𝘵𝘢𝘭𝘪𝘤).
- Do NOT bold or italicize every sentence. Most text is plain. Bold/italic are accents only.

Structure (follow this flow, and make the middle SUBSTANTIAL):
1. OPENER (1-2 sentences, Unicode bold): name a real tension, shift, or misconception using a fresh, specific angle (see banned openers above).
2. CONTEXT / ANCHOR (2-3 sentences): the informative core. Ground it in a real, verifiable development, regulation, framework, or statistic with a named source. This is where the reader learns something. Do not invent facts; if you cannot anchor to something real, use a concrete, well-established fact about the topic.
3. WHY IT MATTERS (1-2 sentences): the stakes or the mechanism, in concrete terms.
4. CALLBACK TO THE CARD: point at the image and name at least two or three of the specific items, points, or categories on THIS card, with a real detail about each. The card shows {card_callback}.
5. ONE OR TWO ONE-LINE INSIGHTS: short, standalone takeaways. Apply Unicode bold to the punchy half of one.
6. ENGAGEMENT QUESTION (Unicode bold): a specific closing question inviting replies, optionally followed by one italic line.

Emojis:
- Optional. AT MOST 2-3 total. Acceptable: ▶ 📌 👀 🤯. Never use emoji bullets or strings of decorative emojis.

Hashtags:
- The very last line is 5 to 8 hashtags, space-separated, each starting with a single # character. Match them to the topic and audience. Do NOT write the literal word "hashtag" before #.

Reality check:
- Every named entity (tool, vendor, framework, regulation, event, person, agency, statistic, source) must be REAL and verifiable. If unsure, omit it.
- Tie the caption substantively to the card so the reader sees the post and the image as one piece."""


def _common_keys() -> str:
    return """\
  "topic": "string - the topic in 3-8 words",
  "title": "string - short post title, 4-10 words, used as the Airtable record title",
  "hook": "string - the card headline / kicker, 5-12 words, punchy, no hype. MUST faithfully describe what the card actually contains. A reader scanning the card must agree the hook is literally accurate.",
  "highlight": "string - one or two words that appear VERBATIM inside the main display text, to be emphasised in the accent colour on the card",
  "subtitle": "string - one short line under the hook, 4-10 words. Frames the actual card contents; never introduces a claim the card does not support.",
  "caption": "string - the full LinkedIn post text, see CAPTION RULES below","""


# ---------------------------------------------------------------------------
# Per-template specs (schema body + structure rules + card callback)
# ---------------------------------------------------------------------------

def _spec_catalogue() -> dict:
    schema = f"""{{
{_common_keys()}
  "categories": [
    {{
      "name": "string - 2-5 words. Category names MUST be derived from the natural cuts WITHIN THIS SPECIFIC TOPIC, not forced into a generic taxonomy. Examples by topic: 'AI image tools' -> ['Foundation Models','Editing Tools','Specialized Generators','Open Source']; 'SEO in 2026' -> ['AI Search Engines','Content Platforms','Technical SEO','Analytics']; 'Cybersecurity stack' -> ['Threat Defence','Identity','Cloud','Resilience']. NEVER default to cybersecurity layers unless the topic is explicitly about cybersecurity. A category name is a PROMISE that EVERY item beneath it is a primary, genuine instance of that exact name.",
      "items": [
        {{
          "title": "string - the exact, real name of the thing AS IT ACTUALLY EXISTS. Do not invent product names by attaching a function to a brand. Must be a primary, genuine instance of THIS category.",
          "description": "string - 6-15 words, factual, describing what the thing ACTUALLY and PRIMARILY does, consistent with its category.",
          "icon": "string - one of: {", ".join(ICON_OPTIONS)}",
          "domain": "string - the brand's primary website domain, lowercase, no protocol/www/path (e.g. 'crowdstrike.com', 'openai.com', 'semrush.com'). For a framework/regulation/standard with no parent company (NIST AI RMF, ISO 42001, EU AI Act, OWASP LLM Top 10, GDPR), set domain to ''.",
          "brand_letter": "string - SINGLE uppercase letter, fallback if no logo loads (usually the first letter of the title)",
          "brand_color": "string - hex color like '#dc1e2c' for the fallback badge background"
        }}
      ]
    }}
  ]
}}"""
    rules = """\
STRUCTURE RULES (HARD REQUIREMENTS):
- categories: EXACTLY 4 groups (unless the user's custom instructions ask otherwise).
- total items across all categories: 16-20 (4-5 per category). COUNT before responding. Never reach the count by padding with items that do not truly belong, by inventing names, or by listing a tool under a function it does not perform.
- each item.title MUST be a REAL named thing relevant to THIS topic. NEVER invent tools. NEVER default to security vendors if the topic isn't about security.
- category names MUST reflect the topic.
- SEMANTIC FIT: every item must be a primary, genuine instance of its category name. Would an industry analyst file THIS exact product under THIS category? If it is famous for a DIFFERENT category, do not borrow it.
- HEADLINE FIT: the card is ALWAYS a set of categorised lists, never a sequence of steps. "hook"/"subtitle" must describe a catalogue/landscape/breakdown, never a "step-by-step", "how-to", "process", or "timeline".
- "highlight" must be a substring that appears verbatim inside "hook".
- icon must be one of the allowed values; if unsure, use "shield".
- brand_letter MUST be exactly ONE uppercase A-Z. brand_color a valid 6-digit hex. domain a real lowercase domain or ''."""
    return {
        "schema": schema,
        "rules": rules,
        "callback": "a curated set of real, named tools and frameworks grouped into categories",
    }


def _spec_listicle() -> dict:
    schema = f"""{{
{_common_keys()}
  "points": [
    {{
      "title": "string - the point itself, 4-10 words, a punchy standalone takeaway. This is the bold line the reader remembers.",
      "detail": "string - ONE supporting sentence, 10-20 words, that makes the point concrete with a real fact, example, or named entity."
    }}
  ]
}}"""
    rules = """\
STRUCTURE RULES (HARD REQUIREMENTS):
- points: 5 to 7 items (default 6) UNLESS the user's custom instructions specify a number, then use exactly that number.
- Each point is a distinct, non-overlapping idea. No two points may restate the same thing.
- Each "title" is a crisp, declarative takeaway (not a question, not a category label).
- Each "detail" must add a concrete, real, verifiable fact, example, statistic with a named source, or named entity. No filler, no generic advice.
- Order the points so they build a logical arc (most important or most surprising first works well).
- "hook" is the headline of the whole list (e.g. "6 shifts redefining AI governance in 2026"). "highlight" must appear verbatim inside "hook".
- Do not fabricate named tools, stats, events, or quotes inside the details."""
    return {
        "schema": schema,
        "rules": rules,
        "callback": "a numbered list of the key points, each a bold takeaway with one supporting line",
    }


def _spec_news(source_text: str | None) -> dict:
    has_source = bool((source_text or "").strip())
    schema = f"""{{
{_common_keys()}
  "eyebrow": "string - 1-3 word tag for the kind of development, UPPERCASE (e.g. 'REGULATION', 'INCIDENT', 'RELEASE', 'ENFORCEMENT', 'RULING')",
  "blocks": [
    {{
      "label": "string - 2-4 word section label. Use this exact set in this order: 'What happened', 'Why it matters', 'What to watch'. You MAY add a fourth: 'The risk' or 'For leaders'.",
      "text": "string - 1-2 tight sentences, 15-35 words, factual."
    }}
  ]
}}"""
    if has_source:
        grounding = """\
SOURCE GROUNDING (HARD REQUIREMENT, this is a real-news template):
- The user has pasted a SOURCE below. Every factual claim, name, number, date, and quote in the card and caption MUST come from that source text. Do NOT add facts from your own memory. Do NOT speculate beyond the source.
- If the source does not state something, do not assert it. It is fine for a block to be short.
- "hook" must be an accurate, non-sensational headline for what the source describes. "highlight" must appear verbatim in "hook"."""
    else:
        grounding = """\
NO SOURCE PROVIDED:
- The user did not paste a source. Only write about an event if you are HIGHLY CONFIDENT it is real and you can recall it accurately. Do NOT invent events, dates, numbers, or quotes.
- If you cannot recall a specific, real, verifiable recent development for this topic with confidence, write about a well-established, durable shift in the topic instead and keep all claims to things you are certain are true. Never fabricate a news event.
- "highlight" must appear verbatim in "hook"."""
    rules = (
        "STRUCTURE RULES (HARD REQUIREMENTS):\n"
        "- blocks: 3 to 4, in the order described in the schema.\n"
        "- Neutral, factual, newsroom tone in the card. The caption may add DTQ's point of view but must not invent facts.\n"
        "- No hype, no clickbait, no fabricated specifics.\n\n"
        + grounding
    )
    return {
        "schema": schema,
        "rules": rules,
        "callback": "a clean breakdown of a recent development: what happened, why it matters, and what to watch",
    }


def _spec_stat() -> dict:
    schema = f"""{{
{_common_keys()}
  "stat_value": "string - the headline number EXACTLY as it should read big, including unit/symbol (e.g. '$4.88M', '68%', '3.2x', '277 days'). Must be a real, verifiable figure.",
  "stat_label": "string - 4-12 words naming WHAT the number measures (e.g. 'average cost of a data breach in 2024').",
  "stat_source": "string - the real named source and year (e.g. 'IBM Cost of a Data Breach Report, 2024'). REQUIRED. If you cannot attribute the figure to a real named source, choose a different statistic you CAN attribute.",
  "context": [
    "string - a short supporting fact or implication, 6-14 words, real and verifiable"
  ]
}}"""
    rules = """\
STRUCTURE RULES (HARD REQUIREMENTS):
- stat_value, stat_label, and stat_source are all REQUIRED and must be real. Never invent a statistic or a source. If unsure of the exact figure, pick a different, well-documented statistic from a named source (IBM Cost of a Data Breach, Verizon DBIR, Gartner, ENISA, NIST, Stanford AI Index, etc.).
- context: 2 to 4 short supporting facts, each real and verifiable. Each adds something new (trend, comparison, driver, implication).
- "hook" is a short framing kicker above the number (4-8 words). "subtitle" frames it below. "highlight" must appear verbatim in "hook".
- The number is the hero. Keep all text spare so it can be set large."""
    return {
        "schema": schema,
        "rules": rules,
        "callback": "one headline statistic, its source, and a few supporting facts",
    }


def _spec_quote() -> dict:
    schema = f"""{{
{_common_keys()}
  "quote": "string - the single bold statement, 12-28 words. A sharp, defensible point of view in DTQ's voice. NOT a fabricated quote attributed to a real person.",
  "attribution": "string - who is saying it. Use 'DTQ' or a role like 'The DTQ view'. Do NOT attribute to a named real person unless it is a real, verifiable, publicly documented quote you are certain of. Otherwise use 'DTQ'.",
  "support": "string - ONE supporting line beneath the quote, 8-18 words, that grounds or sharpens it with a real fact or implication."
}}"""
    rules = """\
STRUCTURE RULES (HARD REQUIREMENTS):
- "quote" is the hero text, set large. It must be a genuine, defensible take, not hype and not a fabricated celebrity quote.
- "attribution" defaults to 'DTQ'. Only name a real person if you are quoting a real, documented statement verbatim and are certain of it.
- "support" adds one concrete, real, verifiable line.
- "hook" is a tiny kicker/eyebrow above the quote (e.g. 'THE DTQ VIEW', 2-4 words). "highlight" must appear verbatim inside the QUOTE (not the hook), so set highlight to one or two words taken from "quote"."""
    return {
        "schema": schema,
        "rules": rules,
        "callback": "a single bold point of view, set large, with one supporting line",
    }


def _spec_framework() -> dict:
    schema = f"""{{
{_common_keys()}
  "steps": [
    {{
      "title": "string - the step name, 3-8 words, action-oriented (starts with a verb where natural).",
      "detail": "string - ONE sentence, 10-20 words, on what to actually do in this step, grounded in real practice, frameworks, or named tools."
    }}
  ]
}}"""
    rules = """\
STRUCTURE RULES (HARD REQUIREMENTS):
- steps: 4 to 6 (default 5) UNLESS the user's custom instructions specify a number, then use exactly that.
- The steps are SEQUENTIAL: each follows from the last to form a real, coherent process or playbook. Order matters.
- Each "detail" must be concrete and actionable, grounded in real frameworks, standards, or practices (e.g. NIST AI RMF, ISO 42001, threat modelling). No fabricated tools or stats.
- "hook" names the framework/process (e.g. 'A 5-step playbook for AI vendor risk'). "subtitle" frames it. "highlight" must appear verbatim inside "hook".
- Because this template is explicitly a process, it is the ONE place a 'step-by-step' headline is correct."""
    return {
        "schema": schema,
        "rules": rules,
        "callback": "a numbered, step-by-step framework the reader can follow in order",
    }


def _spec_for(template: str, source_text: str | None) -> dict:
    if template == "listicle":
        return _spec_listicle()
    if template == "news":
        return _spec_news(source_text)
    if template == "stat":
        return _spec_stat()
    if template == "quote":
        return _spec_quote()
    if template == "framework":
        return _spec_framework()
    return _spec_catalogue()


_TEMPLATE_NOUN = {
    "catalogue": "categorised infographic card",
    "listicle": "numbered list card",
    "news": "news-breakdown card",
    "stat": "single-statistic card",
    "quote": "bold-quote card",
    "framework": "step-by-step framework card",
}


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_messages(
    topic: str | None,
    custom_instructions: str | None,
    tone: str | None = None,
    template: str | None = None,
    source_text: str | None = None,
) -> list[dict]:
    chosen_topic = (topic or "").strip() or _pick_topic()
    extras = (custom_instructions or "").strip()
    tone_directive = TONE_PRESETS.get((tone or "default").strip().lower(), "")
    tmpl = (template or DEFAULT_TEMPLATE).strip().lower()
    if tmpl not in TEMPLATE_IDS:
        tmpl = DEFAULT_TEMPLATE
    src = (source_text or "").strip()

    spec = _spec_for(tmpl, src)
    noun = _TEMPLATE_NOUN[tmpl]

    # Custom instructions sit at the very TOP of the user message and are repeated
    # at the end, so they are never drowned out by the structure rules.
    custom_block = ""
    if extras:
        custom_block = (
            "================ USER CUSTOM INSTRUCTIONS (HIGHEST PRIORITY) ================\n"
            f"{extras}\n"
            "These override the stylistic/structural defaults below wherever they "
            "conflict (number of items, angle, emphasis, inclusions, exclusions, "
            "wording). Honour them. They do NOT override accuracy/no-fabrication.\n"
            "=============================================================================\n\n"
        )

    source_block = ""
    if tmpl == "news" and src:
        source_block = (
            "------------------ PASTED SOURCE (summarise ONLY this) ------------------\n"
            f"{src}\n"
            "-------------------------------------------------------------------------\n\n"
        )

    user = f"""\
{custom_block}Generate ONE LinkedIn post and an accompanying {noun} on this topic:

TOPIC: {chosen_topic}

{tone_directive}

{source_block}Return a SINGLE JSON object (no markdown, no commentary) with EXACTLY these keys:

{spec['schema']}

{spec['rules']}

{_caption_rules(spec['callback'])}

FINAL SELF-CHECK BEFORE YOU RETURN:
1. Coherence: read "hook"/"subtitle", then scan the card content. Does the card deliver exactly what the headline promises? If not, fix the headline.
2. Real names: every named tool, vendor, framework, regulation, event, person, statistic, source, or quote is REAL and verifiable. Delete anything invented.
3. No defamation: no legitimate company/product/person is framed as malicious, illegal, or an attack tool.
4. Highlight: "highlight" appears verbatim inside the field specified for this template.
5. Structure: the item/section counts match the rules above (or the user's custom instructions, which win).
6. Custom instructions: re-read the user's custom instructions and confirm you followed every one.

Return ONLY the JSON object. No preface, no code fences."""

    if extras:
        user += (
            "\n\nREMINDER: the USER CUSTOM INSTRUCTIONS at the top of this message "
            "are mandatory and take precedence over the defaults wherever they conflict."
        )

    return [
        {"role": "system", "content": _SYSTEM_CORE},
        {"role": "user", "content": user},
    ]

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


def _pick_topic() -> str:
    return random.choice(FALLBACK_TOPICS)


def build_messages(topic: str | None, custom_instructions: str | None) -> list[dict]:
    chosen_topic = (topic or "").strip() or _pick_topic()
    extras = (custom_instructions or "").strip()

    system = (
        "You are a senior content strategist writing LinkedIn posts for "
        "Data Trust Quotients (DTQ). Your audience is CISOs, cybersecurity "
        "leaders, AI leaders, and data governance executives. Voice is "
        "confident, factual, plain English, zero hype, zero marketing fluff. "
        "Never invent tools, vendors, frameworks, regulations, or statistics. "
        "Every named entity must be a real, verifiable thing. If you are not "
        "sure something is real, do not include it."
        "\n\n" + DTQ_CONTEXT
    )

    user = f"""\
Generate ONE LinkedIn post and an accompanying infographic card payload on this topic:

TOPIC: {chosen_topic}

{f"ADDITIONAL INSTRUCTIONS FROM USER: {extras}" if extras else ""}

Return a SINGLE JSON object (no markdown, no commentary) with EXACTLY these keys:

{{
  "topic": "string - the topic in 3-8 words",
  "title": "string - short post title, 4-10 words, used as Airtable record title",
  "hook": "string - the card headline, 6-12 words, punchy, no hype",
  "highlight": "string - one or two words from the hook to highlight in yellow on the card",
  "subtitle": "string - one short line under the hook, 4-10 words",
  "caption": "string - the full LinkedIn post text, see CAPTION RULES below",
  "categories": [
    {{
      "name": "string - short group name, 2-5 words",
      "items": [
        {{
          "title": "string - the named real thing (framework / regulation / tool / vendor / standard)",
          "description": "string - 6-15 words, factual, what it is or does",
          "icon": "string - one of: {", ".join(ICON_OPTIONS)}",
          "domain": "string - the brand's primary website domain in lowercase, no protocol, no path, no www. Examples: 'crowdstrike.com', 'okta.com', 'paloaltonetworks.com', 'microsoft.com', 'cloudflare.com', 'wiz.io', 'snyk.io', 'sentinelone.com', 'zscaler.com', 'rubrik.com', 'druva.com', 'tenable.com', 'aikido.dev', 'vorlonsecurity.com', 'pushsecurity.com'. If the item is a framework / regulation / standard with no parent company (e.g. NIST AI RMF, ISO 42001, EU AI Act, OWASP LLM Top 10, MITRE ATLAS, SOC 2), set domain to an EMPTY STRING ''.",
          "brand_letter": "string - SINGLE uppercase letter, used as a fallback if no logo can be fetched. Usually the first letter of the title (e.g. 'C' for CrowdStrike, 'M' for Microsoft Defender)",
          "brand_color": "string - hex color like '#dc1e2c' used as the fallback badge background when no logo is shown. If the brand has a well-known color, use it (CrowdStrike red #e2231a, Okta blue #007dc1, Wiz purple #5048e5, Microsoft blue #0078d4, Cloudflare orange #f48120, Snyk purple #4c4a73, Palo Alto orange #fa582d, SentinelOne purple #6b21a8, Zscaler blue #00b1eb, Rubrik green #00b388, Druva orange #f37021, Tenable teal #00688b). For frameworks/regulations without a brand color, pick a sensible solid hex."
        }}
      ]
    }}
  ]
}}

STRUCTURE RULES (HARD REQUIREMENTS — these are non-negotiable):
- categories: EXACTLY 4 groups (not 3, not 5 — exactly 4).
- total items across all categories: AT LEAST 16, at most 20. Before you respond, COUNT your items. If the total is below 16, add more real named things until you reach 16. A response with fewer than 16 items is invalid.
- distribute items roughly evenly: 4-5 items per category.
- each item.title MUST be a REAL named thing (e.g. NIST AI RMF, ISO 42001, EU AI Act, Microsoft Purview, OpenAI, Splunk, CrowdStrike, OWASP LLM Top 10, MITRE ATLAS, SOC 2, etc.). No invented tools.
- "highlight" must be a substring that appears verbatim inside "hook".
- icon must be one of the allowed values; if unsure, use "shield".
- brand_letter MUST be exactly ONE uppercase A-Z character, normally the first letter of the title.
- brand_color MUST be a valid 6-digit hex color starting with '#'.
- domain MUST be a real, currently-resolvable public website domain in lowercase (no protocol, no www, no path). If you are not certain the brand has a real website, set it to an empty string. Never invent a domain.

CAPTION RULES (this is the LinkedIn post body — match the voice of the examples below):

Length and format:
- Length: 1100 to 1500 characters total.
- Short paragraphs separated by blank lines.
- No markdown asterisks, no headers, no bulleted lists with dashes or stars.
- NO em-dashes (—). Use commas, periods, or colons instead. This is strict.
- No hype words: "revolutionize", "game-changer", "unlock", "supercharge", "leverage", "next-gen", "cutting-edge", "harness", "empower", "transform".

Emphasis with Unicode (this is how LinkedIn posts get visual weight without markdown):
- For 2-4 key phrases or whole sentences, use Unicode MATHEMATICAL SANS-SERIF BOLD characters (e.g. 𝗧𝗵𝗶𝘀 𝗶𝘀 𝗯𝗼𝗹𝗱). Use these on lines that carry the most weight — the hook, a punchy takeaway, the closing question.
- For 1-2 softer sub-emphases (asides, follow-up lines), use Unicode MATHEMATICAL SANS-SERIF ITALIC characters (e.g. 𝘵𝘩𝘪𝘴 𝘪𝘴 𝘪𝘵𝘢𝘭𝘪𝘤).
- Do NOT bold or italicize every sentence. Most text is plain. Bold/italic are accents.

Structure (follow this rough flow):
1. CONVERSATIONAL HOOK (1-2 sentences): name a tension, a shift, or a misconception the audience will feel. Often opens with the audience ("Most CISOs we talk to...", "A lot of teams are...", "Let's be honest for a second..."). Make the hook Unicode bold.
2. A TOPICAL ANCHOR: briefly reference a current event, regulator action, recent incident, or industry shift — but ONLY if you are certain it is real and verifiable. If you cannot anchor to a real event, skip this paragraph rather than inventing one.
3. CALLBACK TO THE CARD: one short sentence that points to the image/card alongside the post. Examples: "So we put together the [N] [items] we keep seeing across [layers]." or "The card breaks them down across [N] layers."
4. ONE OR TWO ONE-LINE INSIGHTS: short, punchy, standalone takeaway sentences between paragraphs. Apply Unicode bold to the punchy part of one. Examples of the rhythm: "Identity is now where most attacks start." "Backup isn't resilience. 𝗥𝗲𝗰𝗼𝘃𝗲𝗿𝘆 𝘀𝗽𝗲𝗲𝗱 𝗶𝘀."
5. ENGAGEMENT QUESTION: a short closing question (Unicode bold) inviting replies, optionally followed by one italic line. Example: "𝗔𝗻𝘆𝘁𝗵𝗶𝗻𝗴 𝘆𝗼𝘂'𝗱 𝗮𝗱𝗱 𝗼𝗿 𝗮𝗿𝗴𝘂𝗲 𝘄𝗶𝘁𝗵? \n 𝘊𝘶𝘳𝘪𝘰𝘶𝘴 𝘸𝘩𝘦𝘳𝘦 𝘵𝘦𝘢𝘮𝘴 𝘢𝘳𝘦 𝘥𝘰𝘶𝘣𝘭𝘪𝘯𝘨 𝘥𝘰𝘸𝘯."

Emojis:
- Optional. Use AT MOST 2-3 total in the whole caption. Acceptable: ▶ 📌 👀 🤯
- Never use emoji bullets (🚀✨🔥) or strings of decorative emojis. Do not start lines with emojis as bullets.

Hashtags:
- The very last line is 5 to 8 hashtags, space-separated, each starting with a single # character.
- Do NOT write the literal word "hashtag" before # (that is a LinkedIn UI artifact, not actual text).
- Pick hashtags matched to the topic and audience: #Cybersecurity #CISO #AIGovernance #ZeroTrust #CloudSecurity #IdentitySecurity #DataPrivacy #ResponsibleAI etc.

Reality check:
- Every named entity (tool, vendor, framework, regulation, event, person, agency) must be REAL and verifiable. If you are not certain it is real, omit it.
- Tie the caption substantively to the categories/items in the card so the reader sees the post and the image as one piece.

VOICE EXAMPLES TO MATCH (do not copy text, copy the rhythm, density, and emphasis pattern):

Example A:
"𝗠𝗼𝘀𝘁 𝗖𝗜𝗦𝗢𝘀 𝘄𝗲 𝘁𝗮𝗹𝗸 𝘁𝗼 𝗮𝗿𝗲𝗻'𝘁 𝗮𝘀𝗸𝗶𝗻𝗴 𝘄𝗵𝗶𝗰𝗵 𝘁𝗼𝗼𝗹 𝗶𝘀 𝗯𝗲𝘀𝘁 𝗮𝗻𝘆𝗺𝗼𝗿𝗲.
𝘛𝘩𝘦𝘺'𝘳𝘦 𝘢𝘴𝘬𝘪𝘯𝘨 𝘸𝘩𝘪𝘤𝘩 𝘤𝘰𝘮𝘣𝘪𝘯𝘢𝘵𝘪𝘰𝘯 𝘢𝘤𝘵𝘶𝘢𝘭𝘭𝘺 𝘩𝘰𝘭𝘥𝘴 𝘶𝘱.

That question got louder this week.

So we put together the [N] platforms we keep seeing in the stacks that hold up.
Four layers ▶ 𝗧𝗵𝗿𝗲𝗮𝘁 𝗱𝗲𝗳𝗲𝗻𝗰𝗲, 𝗰𝗹𝗼𝘂𝗱, 𝗶𝗱𝗲𝗻𝘁𝗶𝘁𝘆, 𝗿𝗲𝘀𝗶𝗹𝗶𝗲𝗻𝗰𝗲.

Identity is now where most attacks start.
Backup isn't resilience. 𝗥𝗲𝗰𝗼𝘃𝗲𝗿𝘆 𝘀𝗽𝗲𝗲𝗱 𝗶𝘀.

𝗔𝗻𝘆𝘁𝗵𝗶𝗻𝗴 𝘆𝗼𝘂'𝗱 𝗮𝗱𝗱?
𝘊𝘶𝘳𝘪𝘰𝘶𝘴 𝘸𝘩𝘦𝘳𝘦 𝘵𝘦𝘢𝘮𝘴 𝘢𝘳𝘦 𝘥𝘰𝘶𝘣𝘭𝘪𝘯𝘨 𝘥𝘰𝘸𝘯.

#Cybersecurity #InfoSec #CISO #ZeroTrust #IdentitySecurity"

Example B:
"𝘓𝘦𝘵'𝘴 𝘣𝘦 𝘩𝘰𝘯𝘦𝘴𝘵 𝘧𝘰𝘳 𝘢 𝘴𝘦𝘤𝘰𝘯𝘥...
A lot of people are studying for the 𝘄𝗿𝗼𝗻𝗴 𝗰𝘆𝗯𝗲𝗿𝘀𝗲𝗰𝘂𝗿𝗶𝘁𝘆 𝗰𝗲𝗿𝘁𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗼𝗻.

Not because the cert is bad, but because it doesn't align with the career they want.

𝗧𝗵𝗲 𝗰𝗮𝗿𝗱 𝗯𝗲𝗹𝗼𝘄 𝗯𝗿𝗲𝗮𝗸𝘀 𝗱𝗼𝘄𝗻 which certifications align with which track.
📌 𝘚𝘢𝘷𝘦 𝘵𝘩𝘪𝘴 𝘣𝘦𝘧𝘰𝘳𝘦 𝘤𝘩𝘰𝘰𝘴𝘪𝘯𝘨 𝘺𝘰𝘶𝘳 𝘯𝘦𝘹𝘵 𝘤𝘦𝘳𝘵.

Which track do you think is the most underrated? 👀

#Cybersecurity #CISO #CyberCareers #SecurityCertifications"

Return ONLY the JSON object. No preface, no code fences."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

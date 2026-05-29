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

TONE_PRESETS = {
    "default": "",
    "punchy": "TONE OVERRIDE: punchy and opinionated. Short, declarative sentences. No filler. Hook is one line, blunt.",
    "thoughtful": "TONE OVERRIDE: thoughtful and exploratory. Show nuance and second-order effects. Avoid hot takes. Let the reader sit with a tension.",
    "question-led": "TONE OVERRIDE: question-led. Open with a question that names a real tension, and close with a different question that invites reply.",
    "data-led": "TONE OVERRIDE: data-led. Anchor the caption in ONE specific, real, verifiable statistic from a named source (e.g. Verizon DBIR, Gartner, IBM Cost of a Data Breach, ENISA, NIST). If you cannot name a real source, do NOT invent one — use the 'industry pulse' archetype instead.",
}


def _pick_topic() -> str:
    return random.choice(FALLBACK_TOPICS)


def build_messages(
    topic: str | None,
    custom_instructions: str | None,
    tone: str | None = None,
) -> list[dict]:
    chosen_topic = (topic or "").strip() or _pick_topic()
    extras = (custom_instructions or "").strip()
    tone_directive = TONE_PRESETS.get((tone or "default").strip().lower(), "")

    system = (
        "You are a senior content strategist writing LinkedIn posts for "
        "Data Trust Quotients (DTQ). Your audience is CISOs, cybersecurity "
        "leaders, AI leaders, and data governance executives. Voice is "
        "confident, factual, plain English, zero hype, zero marketing fluff. "
        "Never invent tools, vendors, frameworks, regulations, or statistics. "
        "Every named entity must be a real, verifiable thing. If you are not "
        "sure something is real, do not include it.\n\n"
        "FOUR NON-NEGOTIABLE RELIABILITY RULES (most failures come from breaking these):\n"
        "1. COHERENCE: the headline, subtitle, and caption must describe what the "
        "card ACTUALLY contains. The card is a curated catalogue of real named "
        "things. Do not write a news-style or attack-narrative headline that the "
        "listed items do not substantiate. A reader who looks at the items must be "
        "able to see the headline is literally true.\n"
        "2. CORRECT CATEGORISATION: a category name is a PROMISE about every item "
        "under it. Each item must be a real, PRIMARY instance of its category, not "
        "merely topic-adjacent. A general-purpose platform does not belong under a "
        "specialised function it does not actually perform. Before placing an item, "
        "ask: 'Is this thing literally and primarily a <category name>?' If not, "
        "move it or replace it.\n"
        "3. EXACT REAL NAMES: use the exact product, vendor, framework, or standard "
        "name as it really exists. Never bolt a function onto a brand to invent a "
        "product (e.g. 'Mailchimp Abuse Detection' is not a real product). Never "
        "list a tool under a job it is not actually used for. Accuracy always beats "
        "filling a quota: fewer correct items is better than padding with items "
        "that do not fit.\n"
        "4. NO DEFAMATION / NO MISLABELLING: never present a real, legitimate "
        "company, product, or person as a malicious actor, an attack/hacking tool, "
        "an illegal service, or as performing a function it does not perform. "
        "Mainstream AI vendors (OpenAI, Anthropic, Google, Microsoft, Hugging Face, "
        "Midjourney, etc.) are NOT 'phishing tools', 'hacking tools', or 'attack "
        "tools' and must never be labelled as such. Do not stretch a product into a "
        "category it does not serve (an EDR tool is not a 'phishing detector'; an "
        "MFA/identity product is not a 'phishing detector'; a cloud-posture tool is "
        "not an email-security tool). When the topic is about attacks, threats, or "
        "misuse, represent the offensive side with real, neutral, factual named "
        "things, recognised attack TECHNIQUES and tactics (e.g. spear phishing, "
        "credential stuffing, deepfake voice cloning, MITRE ATT&CK techniques) or "
        "documented threat categories, NOT legitimate vendor brands relabelled as "
        "weapons. If the only honest description is 'general-purpose tool that can "
        "be misused', name the TECHNIQUE, not the brand, or drop that category."
        "\n\n" + DTQ_CONTEXT
    )

    user = f"""\
Generate ONE LinkedIn post and an accompanying infographic card payload on this topic:

TOPIC: {chosen_topic}

{tone_directive}

{f"ADDITIONAL INSTRUCTIONS FROM USER: {extras}" if extras else ""}

Return a SINGLE JSON object (no markdown, no commentary) with EXACTLY these keys:

{{
  "topic": "string - the topic in 3-8 words",
  "title": "string - short post title, 4-10 words, used as Airtable record title",
  "hook": "string - the card headline, 6-12 words, punchy, no hype. MUST faithfully describe what the card actually contains (a curated set of real named things in this topic). It is a label for the collection, NOT a speculative news headline, attack story, or any claim the listed items do not back up. A reader scanning the items must agree the hook is literally accurate.",
  "highlight": "string - one or two words from the hook to highlight in yellow on the card",
  "subtitle": "string - one short line under the hook, 4-10 words. Reinforces or frames the actual card contents; never introduces a claim or storyline the items do not support.",
  "caption": "string - the full LinkedIn post text, see CAPTION RULES below",
  "categories": [
    {{
      "name": "string - 2-5 words. CRITICAL: category names MUST be derived from the natural cuts WITHIN THIS SPECIFIC TOPIC. Do NOT force every topic into a generic taxonomy. Different topics need totally different category names. Examples by topic: For 'AI image generation tools' use cuts like ['Foundation Models', 'Editing Tools', 'Specialized Generators', 'Open Source']. For 'SEO in 2026' use cuts like ['AI Search Engines', 'Content Platforms', 'Technical SEO', 'Analytics']. For 'AI funding 2026' use cuts like ['Top VCs', 'Accelerators', 'Grants & Programs', 'Angel Networks']. For 'AI tools for retail' use cuts like ['Personalisation', 'Inventory', 'Visual Search', 'Customer Service']. For 'Y Combinator 2026 watchlist' use cuts like ['Dev Tools', 'AI Infra', 'Fintech', 'Healthtech']. For 'Cybersecurity stack' use cuts like ['Threat Defence', 'Identity', 'Cloud', 'Resilience']. NEVER default to cybersecurity layers unless the topic is explicitly about cybersecurity. Look at the topic, ask what natural divisions exist WITHIN it, pick those. A category name is a PROMISE that EVERY item beneath it satisfies: if you cannot fill a category with at least 4 real items that are each a primary, genuine instance of that exact name, choose a different category cut. Do NOT keep a category and pad it with items that only loosely relate.",
      "items": [
        {{
          "title": "string - the exact, real name of the thing (framework / regulation / tool / vendor / standard) AS IT ACTUALLY EXISTS. Do not invent product or feature names by attaching a function to a brand (e.g. NOT 'Mailchimp Abuse Detection'). If a vendor has a real named product for this category, use that exact product name; otherwise use the plain brand/standard name. The thing MUST be a primary, genuine instance of THIS item's category, not just topic-adjacent.",
          "description": "string - 6-15 words, factual, describing what the thing ACTUALLY and PRIMARILY does. The description must be true of the real product and must be consistent with the category it sits under. If the honest description does not fit the category, the item is in the wrong place; fix it.",
          "icon": "string - one of: {", ".join(ICON_OPTIONS)}",
          "domain": "string - the brand's primary website domain in lowercase, no protocol, no path, no www. The brand MUST be a real, well-known company/tool relevant to THIS topic. Domain examples across sectors: cybersecurity -> 'crowdstrike.com', 'okta.com', 'wiz.io', 'cloudflare.com'; AI tools -> 'openai.com', 'anthropic.com', 'midjourney.com', 'stability.ai', 'huggingface.co', 'runwayml.com', 'perplexity.ai', 'mistral.ai'; SEO/content -> 'semrush.com', 'ahrefs.com', 'surferseo.com', 'clearscope.io'; VCs / funding -> 'ycombinator.com', 'a16z.com', 'sequoiacap.com', 'khoslaventures.com', 'lightspeed.com'; SaaS / productivity -> 'notion.so', 'linear.app', 'figma.com', 'slack.com'; retail/ecom -> 'shopify.com', 'klaviyo.com', 'gorgias.com'. PICK BRANDS THAT FIT THE TOPIC. If the item is a framework / regulation / standard / methodology with no parent company (e.g. NIST AI RMF, ISO 42001, EU AI Act, OWASP LLM Top 10, MITRE ATLAS, SOC 2, GDPR), set domain to an EMPTY STRING ''.",
          "brand_letter": "string - SINGLE uppercase letter, used as a fallback if no logo can be fetched. Usually the first letter of the title (e.g. 'C' for CrowdStrike, 'M' for Midjourney, 'Y' for Y Combinator)",
          "brand_color": "string - hex color like '#dc1e2c' used as the fallback badge background. Pick a color that matches the brand if you know it, otherwise any solid hex."
        }}
      ]
    }}
  ]
}}

STRUCTURE RULES (HARD REQUIREMENTS — these are non-negotiable):
- categories: EXACTLY 4 groups (not 3, not 5 — exactly 4).
- total items across all categories: AT LEAST 16, at most 20. Before you respond, COUNT your items. If the total is below 16, add more real named things THAT GENUINELY FIT THEIR CATEGORY until you reach 16. Never reach the count by padding a category with items that do not truly belong, by inventing names, or by listing a tool under a function it does not perform. If a topic cannot honestly yield 16 correctly-categorised real items, re-choose your 4 category cuts so that it can. Accuracy and correct categorisation outrank the count.
- distribute items roughly evenly: 4-5 items per category.
- each item.title MUST be a REAL named thing relevant to THIS topic. Examples across sectors so you don't anchor on one: AI tools (OpenAI, Anthropic, Midjourney, Stable Diffusion, Hugging Face, LangChain, Pinecone), security (CrowdStrike, Okta, Wiz, Splunk), frameworks (NIST AI RMF, ISO 42001, EU AI Act, OWASP LLM Top 10, SOC 2, GDPR), VCs / accelerators (Y Combinator, a16z, Sequoia, Khosla Ventures, Lightspeed), SaaS (Notion, Linear, Figma, Slack), data tools (Snowflake, Databricks, dbt, Fivetran), SEO/content (Semrush, Ahrefs, Surfer SEO). NEVER invent tools. NEVER default to security vendors if the topic isn't about security.
- category names MUST reflect the topic. Do not reuse 'Threat Defence / Identity / Cloud / Resilience' unless the topic is specifically about a cybersecurity stack.
- SEMANTIC FIT (hard requirement): every item must be a primary, genuine instance of its category name. Apply the classification test: would the vendor's own marketing, or an industry analyst (e.g. a Gartner/Forrester market category), file THIS exact product under THIS category? If it is famous for a DIFFERENT category, do not borrow it. Examples of what NOT to do: CrowdStrike Falcon (endpoint/EDR) under 'Phishing Detection'; Okta (identity/MFA) under 'Phishing Detection'; Wiz (cloud posture/CSPM) under 'Phishing Detection'. Use the genuine leaders of the EXACT category instead (for email/phishing defence that would be names like Proofpoint, Mimecast, Abnormal Security, Microsoft Defender for Office 365). A general-purpose platform does NOT belong under a specialised category unless it really is a product of that exact kind.
- NO DEFAMATION (hard requirement): never list a legitimate company, product, or person under a category that frames it as malicious, illegal, or as an attack/hacking tool. Mainstream AI vendors are not 'phishing/hacking/attack tools'. For offensive or threat topics, populate the attacker side with real attack TECHNIQUES, tactics, or documented threat categories (e.g. spear phishing, deepfake voice cloning, credential stuffing, MITRE ATT&CK techniques), not legitimate brand names.
- HEADLINE FIT (hard requirement): the card is ALWAYS a set of categorised lists, never a sequence of steps. So "hook" and "subtitle" must describe a catalogue, landscape, or breakdown, and must NEVER promise a "step-by-step", "how-to", "process", "stages", "walkthrough", "timeline", or "playbook of steps" that the categorised items do not deliver. They must accurately summarise the actual items, not a story, attack, or trend the items do not demonstrate.
- "highlight" must be a substring that appears verbatim inside "hook".
- icon must be one of the allowed values; if unsure, use "shield".
- brand_letter MUST be exactly ONE uppercase A-Z character, normally the first letter of the title.
- brand_color MUST be a valid 6-digit hex color starting with '#'.
- domain MUST be a real, currently-resolvable public website domain in lowercase (no protocol, no www, no path). If you are not certain the brand has a real website, set it to an empty string. Never invent a domain.

CAPTION RULES (this is the LinkedIn post body — match the voice of the examples below):

Length and format:
- Target 120 to 170 words. A thin, one-line-per-section caption is NOT acceptable. If your draft is under 110 words, expand it with specific detail before returning.
- Every sentence must carry a concrete, real point. NO filler lines (e.g. "a lot of companies are moving to the cloud" is banned filler). Replace any generic statement with a specific, factual observation tied to the topic or a named item on the card.
- Tight, not padded: no repetition, no throat-clearing. Each line earns its place, but there must be enough substance to reach the length above.
- Short paragraphs (1-3 lines each) separated by blank lines.
- No markdown asterisks, no headers, no bulleted lists with dashes or stars.
- NO em-dashes (—). Use commas, periods, or colons instead. This is strict.
- No hype words: "revolutionize", "game-changer", "unlock", "supercharge", "leverage", "next-gen", "cutting-edge", "harness", "empower", "transform".

Emphasis with Unicode (this is how LinkedIn posts get visual weight without markdown):
- For 2-4 key phrases or whole sentences, use Unicode MATHEMATICAL SANS-SERIF BOLD characters (e.g. 𝗧𝗵𝗶𝘀 𝗶𝘀 𝗯𝗼𝗹𝗱). Use these on lines that carry the most weight — the hook, a punchy takeaway, the closing question.
- For 1-2 softer sub-emphases (asides, follow-up lines), use Unicode MATHEMATICAL SANS-SERIF ITALIC characters (e.g. 𝘵𝘩𝘪𝘴 𝘪𝘴 𝘪𝘵𝘢𝘭𝘪𝘤).
- Do NOT bold or italicize every sentence. Most text is plain. Bold/italic are accents.

Structure (follow this rough flow):
1. CONVERSATIONAL HOOK (1-2 sentences, Unicode bold): name a tension, a shift, or a misconception. CRITICAL: you must VARY THE OPENING STYLE every time. NEVER start with "Most CISOs we talk to" — that phrase is banned. NEVER reuse the same opener archetype two posts in a row. Pick a fresh one each generation from this list:

   a) Audience-state shift: "[Audience] have stopped asking [old question]." OR "Quietly, [thing] became a [board / regulator / oncall] problem."
   b) Honest concession: "Let's be honest." OR "Nobody loves saying this, but..." OR "Here's the uncomfortable part of [topic]:"
   c) Misconception flip: "Everyone treats [X] like [Y]. It isn't." OR "[Common claim]. The reality is messier."
   d) Industry pulse: "Something changed in [topic] this quarter." OR "[Sector] has a new failure mode and it isn't [obvious thing]."
   e) Direct question: "What actually separates the teams that [outcome] from the ones that don't?"
   f) Specific scenario: "A [role] told us last week that [observation]."
   g) Counterintuitive claim: "The [tool / framework] you already pay for is doing more than you think." OR "The strongest [topic] programmes we see aren't the loudest."
   h) Number-led (ONLY if you can name a real, verifiable, named-source stat — if not, skip this archetype): "[Real stat]. [Source name]."
   i) Pattern observation: "We keep seeing the same [thing] across [N] [audience] conversations."
   j) Recent event framing (ONLY if you are CERTAIN the event is real and recent): "[Real event] this week was a reminder that [insight]."

   Pick one archetype, then write an opener in your own words. Do not copy the example sentences verbatim.
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

Example A (industry-pulse archetype; the [BRACKETED] strings are PLACEHOLDERS — you MUST replace them with words drawn from YOUR actual topic, NEVER copy them verbatim):
"𝗦𝗼𝗺𝗲𝘁𝗵𝗶𝗻𝗴 𝗾𝘂𝗶𝗲𝘁 𝗯𝘂𝘁 𝗯𝗶𝗴 𝗶𝘀 𝘀𝗵𝗶𝗳𝘁𝗶𝗻𝗴 𝗶𝗻 [TOPIC AREA] 𝘁𝗵𝗶𝘀 𝗾𝘂𝗮𝗿𝘁𝗲𝗿.
𝘛𝘩𝘦 𝘶𝘴𝘦𝘧𝘶𝘭 𝘲𝘶𝘦𝘴𝘵𝘪𝘰𝘯 𝘢𝘣𝘰𝘶𝘵 [SUBJECT] 𝘩𝘢𝘴 𝘤𝘩𝘢𝘯𝘨𝘦𝘥.

It's no longer about [old framing]. It's about [new framing relevant to your topic].

We mapped what keeps showing up across [audience]'s real stacks.
The cuts that emerged ▶ 𝗖𝗮𝘁𝗲𝗴𝗼𝗿𝘆 𝗔, 𝗖𝗮𝘁𝗲𝗴𝗼𝗿𝘆 𝗕, 𝗖𝗮𝘁𝗲𝗴𝗼𝗿𝘆 𝗖, 𝗖𝗮𝘁𝗲𝗴𝗼𝗿𝘆 𝗗.
(Replace those with the actual category names you chose for this topic.)

[One short, specific insight about the topic — 6-12 words.]
[Another one-liner with the punchy half in 𝗯𝗼𝗹𝗱.]

𝗪𝗵𝗮𝘁'𝘀 𝗺𝗶𝘀𝘀𝗶𝗻𝗴 𝗳𝗿𝗼𝗺 𝘁𝗵𝗶𝘀 𝗽𝗶𝗰𝘁𝘂𝗿𝗲?
𝘊𝘶𝘳𝘪𝘰𝘶𝘴 𝘸𝘩𝘦𝘳𝘦 [audience] 𝘢𝘳𝘦 𝘥𝘰𝘶𝘣𝘭𝘪𝘯𝘨 𝘥𝘰𝘸𝘯.

[5-8 hashtags chosen for THIS topic, not generic security ones]"

Topic-specific hashtag examples so you don't default to security tags:
- AI tools post: #AI #GenerativeAI #LLM #AITools #EnterpriseAI
- SEO post: #SEO #ContentMarketing #DigitalStrategy #AISearch
- Funding post: #Startups #VentureCapital #FoundersJourney #AIFunding
- Data governance post: #DataGovernance #DataPrivacy #AIGovernance #ResponsibleAI
- Security post (only when topic is security): #Cybersecurity #InfoSec #CISO #ZeroTrust

Example B:
"𝘓𝘦𝘵'𝘴 𝘣𝘦 𝘩𝘰𝘯𝘦𝘴𝘵 𝘧𝘰𝘳 𝘢 𝘴𝘦𝘤𝘰𝘯𝘥...
A lot of people are studying for the 𝘄𝗿𝗼𝗻𝗴 𝗰𝘆𝗯𝗲𝗿𝘀𝗲𝗰𝘂𝗿𝗶𝘁𝘆 𝗰𝗲𝗿𝘁𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗼𝗻.

Not because the cert is bad, but because it doesn't align with the career they want.

𝗧𝗵𝗲 𝗰𝗮𝗿𝗱 𝗯𝗲𝗹𝗼𝘄 𝗯𝗿𝗲𝗮𝗸𝘀 𝗱𝗼𝘄𝗻 which certifications align with which track.
📌 𝘚𝘢𝘷𝘦 𝘵𝘩𝘪𝘴 𝘣𝘦𝘧𝘰𝘳𝘦 𝘤𝘩𝘰𝘰𝘴𝘪𝘯𝘨 𝘺𝘰𝘶𝘳 𝘯𝘦𝘹𝘵 𝘤𝘦𝘳𝘵.

Which track do you think is the most underrated? 👀

#Cybersecurity #CISO #CyberCareers #SecurityCertifications"

FINAL SELF-CHECK BEFORE YOU RETURN (run through every item — this is where reliability is won or lost):
1. Headline test: read "hook" and "subtitle", then scan the items. Does the card actually deliver what the headline promises? If the headline tells a story the items do not back up, rewrite the headline to describe the real contents. Confirm it does NOT promise steps, a process, a walkthrough, or a timeline — the card is categorised lists.
2. Category test: for EACH item, read its title against its category name and ask "would the vendor or an analyst actually classify this exact product under this category?" If no, replace the item or move it. Reject products famous for a neighbouring category (e.g. an EDR or MFA or cloud-posture tool placed under 'Phishing Detection') and general-purpose tools dropped into specialised categories.
3. Defamation test: for EACH item, confirm no legitimate company/product/person is framed as malicious, illegal, or an attack/hacking tool. If a category is about the attacker side, confirm its items are real techniques/tactics, not legitimate vendor brands.
4. Real-name test: for EACH item, confirm the title is the exact real name of a thing that genuinely exists. Delete anything you invented, any brand+function mashups, and anything you are not confident is real.
5. Description test: for EACH item, confirm the description is true of the real thing AND consistent with its category.
6. Count test: confirm exactly 4 categories and 16-20 items total, 4-5 per category, with NO padding. If fixing the above dropped you below 16, add more genuinely-fitting real items or re-cut the categories.
Only after all six checks pass do you return the JSON.

Return ONLY the JSON object. No preface, no code fences."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

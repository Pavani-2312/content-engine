# AI Content Engine — Functional & Technical Specifications

## 1. Overview

This document specifies the exact behavior, inputs, outputs, and prompt
contracts for each of the five generation steps in the AI Content Engine,
plus the UI specification for the Streamlit app.

---

## 2. Input Specification

| Field | Type | Constraints | Example |
|---|---|---|---|
| `product` | string | Required, 1–80 characters | `"AquaPure Bottle"` |
| `audience` | string | Required, 1–120 characters | `"Eco-conscious urban commuters, age 25-40"` |
| `tone` | enum (string) | Required, one of: `playful`, `premium`, `eco` (extensible) | `"eco"` |

These three fields are collected via a Streamlit sidebar form and are passed
as a single `brief` object/dict through the entire pipeline:

```python
brief = {
    "product": str,
    "audience": str,
    "tone": str,
}
```

---

## 3. Pipeline Specification

The pipeline executes strictly in this order. Each step's output is added to
a shared `context` dict that is passed forward.

```
brief
  └─▶ Step 1: Tagline (few-shot)            → context["tagline"]
        └─▶ Step 2: Blog Intro (role-based)  → context["blog_intro"]
              └─▶ Step 3: Social Post (structured JSON) → context["social"]
                    └─▶ Step 4: Hero Image (formula prompt) → context["image_url"]
                          └─▶ Step 5: Video (motion prompt) → context["video_url"]
```

### 3.1 Step 1 — Campaign Tagline

**Module:** `text_gen.py` → `generate_tagline(product, audience, tone)`
**Technique:** Few-shot prompting
**Model channel:** OpenRouter (text)

**System prompt contract:**
```
You are a creative director. Generate ONE campaign tagline.
Match the brand tone exactly. Max 10 words. No hashtags.
```

**Few-shot example bank (selected by `tone`):**

| Tone | Example taglines (illustrative) |
|---|---|
| `playful` | "Fun never tasted this fizzy." / "Snack smarter. Smile harder." |
| `premium` | "Crafted for those who notice everything." / "Excellence, refined." |
| `eco` | "Lighter on you. Lighter on Earth." / "Pure, naturally." |

**User prompt template:**
```
Product: {product}
Audience: {audience}
Tone: {tone}

Examples of {tone} taglines:
1. "{example_1}"
2. "{example_2}"

Generate a new, original tagline for this product. Do not reuse the examples.
```

**Output contract:** Plain string, ≤10 words, no hashtags, no surrounding quotes.

**Validation rule:** If word count > 10 or contains `#`, retry once with the
corrective instruction `"Your tagline was too long or contained a hashtag. Regenerate: one tagline, max 10 words, no hashtags."` appended. Do not silently truncate, as cutting mid-phrase produces broken copy.

---

### 3.2 Step 2 — Blog Introduction

**Module:** `text_gen.py` → `generate_blog_intro(product, audience, tone, tagline)`
**Technique:** Role-based prompting
**Model channel:** OpenRouter (text)

**System prompt contract:**
```
You are a content strategist writing for {audience}.
Write a 200-word blog intro for {product}.
Weave in the campaign tagline: "{tagline}".
Tone: {tone}.
```

If `tagline` is an empty string (upstream failure), omit the tagline
instruction line from the system prompt rather than injecting a blank
`Weave in the campaign tagline: "".`

**Output contract:** Plain text, target length 200 words (±10% tolerance =
180–220 words), must contain the tagline text verbatim or near-verbatim at
least once (skipped if `tagline` is empty).

**Validation rule:** If word count falls outside tolerance, log a warning to
`meta.errors` (soft constraint; do not block rendering).

---

### 3.3 Step 3 — Social Media Post

**Module:** `text_gen.py` → `generate_social_post(product, tone)`
**Technique:** Structured JSON output
**Model channel:** OpenRouter (text)

> **Note:** `audience` and `tagline` are intentionally excluded from this
> function's signature. The prompt focuses strictly on platform character
> constraints and tone; brand consistency is carried by the shared `tone`
> value rather than by repeating the tagline verbatim in every platform post.

**System prompt contract:**
```
Generate social posts for {product}. Return ONLY JSON:
{ "twitter": string (max 280 chars),
  "instagram": string (max 2200 chars),
  "linkedin": string (max 700 chars) }
Tone: {tone}. No markdown fences.
```

**Output contract:** Valid JSON object, exactly three keys: `twitter`,
`instagram`, `linkedin`. No markdown code fences, no extra commentary text
outside the JSON.

**Parsing rule (illustrative pseudo-code — use `if/raise`, not `assert`):**
```python
import json
raw = response.strip().strip("`").strip()
social = json.loads(raw)
if set(social.keys()) != {"twitter", "instagram", "linkedin"}:
    raise ValueError("Unexpected keys in social JSON")
if len(social["twitter"]) > 280:
    raise ValueError("twitter exceeds 280 chars")
if len(social["instagram"]) > 2200:
    raise ValueError("instagram exceeds 2200 chars")
if len(social["linkedin"]) > 700:
    raise ValueError("linkedin exceeds 700 chars")
```
If `json.loads` fails, retry once with an appended instruction: `"Your last response was not valid JSON. Return ONLY the JSON object, nothing else."`

---

### 3.4 Step 4 — Hero Image

**Module:** `image_gen.py` → `build_image_prompt(product, tagline, tone)` + `generate_image(prompt)`
**Technique:** Formula-based prompt construction
**Model channel:** GPT Image API (`gpt-image-2`)

**Prompt formula:** `Subject + Style(tone) + Composition + Constraints`

```python
STYLE_MAP = {
    "playful": "bright flat illustration",
    "premium": "photorealistic, studio lighting",
    "eco":     "watercolour, natural tones",
}

def build_image_prompt(product, tagline, tone):
    style = STYLE_MAP.get(tone, "clean modern")
    tagline_hint = f' Evoke the feeling of: "{tagline}".' if tagline else ""
    return (
        f"A {style} of {product}."
        f"{tagline_hint} "
        f"Centred, shallow DOF, 16:9. No text, no logos."
    )
```

> `tagline` is included in the prompt when available so the image mood aligns
> with the campaign copy; the parameter must not be silently discarded.

**Output contract:** A single image (URL or base64), aspect ratio 16:9, no
embedded text/logos per the constraint clause.

**Validation rule:** If the API rejects the prompt (content policy, malformed
input), retry once with a simplified prompt (drop tagline reference, keep
subject + style only).

---

### 3.5 Step 5 — Promotional Video

**Module:** `video_gen.py` → `generate_video(image_url, motion_prompt)`
**Technique:** Image-to-video with motion prompt
**Model channel:** Runway API

**Motion prompt contract:**
```python
MOTION_PROMPT = (
    "Slow cinematic push-in. "
    "Soft light shifts gently. "
    "Background mostly still. 5 to 8 seconds."
)
```

**Input contract:** The hero image from Step 4 (`context["image_url"]`) plus the motion prompt string.

**Output contract:** A video file/URL, duration strictly between 5 and 8 seconds.

**Validation rule:** If Runway returns a job ID for async processing, the app must poll until `status == "completed"` or a timeout (e.g., 90 seconds) is reached, surfacing a "video still rendering" state rather than blocking the rest of the UI.

---

## 4. UI Specification

### 4.1 Layout

```
┌───────────────────────────────────────────────────────┐
│ Sidebar                   │ Main Area                  │
│ ┌─────────────────────┐   │ ┌────────────┬────────────┐│
│ │ Product Name        │   │ │  TEXT      │  VISUAL    ││
│ │ Target Audience     │   │ │  COLUMN    │  COLUMN    ││
│ │ Brand Tone (select) │   │ │            │            ││
│ │ [Generate] button   │   │ │ Tagline    │  Image     ││
│ └─────────────────────┘   │ │ Blog Intro │  Video     ││
│                            │ │ Social     │            ││
│                            │ └────────────┴────────────┘│
└───────────────────────────────────────────────────────┘
```

### 4.2 Component Specification

| Component | Streamlit widget | Notes |
|---|---|---|
| Product Name input | `st.text_input` | Required field, sidebar |
| Target Audience input | `st.text_input` or `st.text_area` | Required field, sidebar |
| Brand Tone selector | `st.selectbox` | Options: Playful, Premium, Eco (extensible) |
| Generate button | `st.button` | Triggers `run_pipeline(brief)` |
| Layout columns | `st.columns(2)` | Left = text, right = visual |
| Tagline card | `st.subheader` + `st.markdown` | Tagged "Few-shot prompting" |
| Blog Intro card | `st.markdown` in expander or container | Tagged "Role-based prompting" |
| Social Post card | `st.tabs` (Twitter/Instagram/LinkedIn) or `st.json` | Tagged "Structured output" |
| Hero Image card | `st.image` | Tagged "Image prompt formula" |
| Video card | `st.video` | Tagged "Runway image-to-video" |
| Progress per step | `st.spinner` / `st.status` | One per pipeline stage |
| Error display | `st.error` | Per-asset, non-blocking |

### 4.3 Interaction Flow

1. User completes the sidebar form.
2. User clicks **Generate**.
3. The app disables the button and shows a `st.status` block with five
   sequential sub-steps, each updating as it completes.
4. As each asset becomes available, it renders immediately in its column
   (progressive rendering preferred over waiting for the full pipeline).
5. On completion, the full suite is visible; the user may re-run with a new
   brief.

---

## 5. Error Handling Specification

| Failure Point | Behavior |
|---|---|
| OpenRouter call fails (network/timeout) | Retry once after short backoff (e.g., 2s); on second failure, show `st.error` for that asset only, continue pipeline with placeholder text where downstream steps depend on it (e.g., empty tagline → blog intro proceeds with product/audience only, omitting the tagline weave instruction). |
| Social JSON fails to parse | Retry once with corrective prompt; on second failure, display raw text with a warning banner instead of structured tabs. |
| GPT Image call fails | Retry once with simplified prompt; on second failure, show placeholder image icon and `st.error`, skip Step 5 (video) since it requires the hero image. |
| Runway call fails or times out | Show `st.error` with a "video generation failed/timed out" message; other four assets remain visible. |
| Missing API key in `.env` | Fail fast at app startup with a clear `st.error` listing which key is missing (`CONTENT_API_KEY` and/or `RUNWAY_API_KEY`). |

---

## 6. Data Contracts Summary

```python
# Final in-memory result object after a successful run
CampaignSuite = {
    "tagline": str,
    "blog_intro": str,
    "social": {
        "twitter": str,
        "instagram": str,
        "linkedin": str,
    },
    "image_url": str,   # or base64 payload
    "video_url": str,   # or local path
    "meta": {
        "product": str,
        "audience": str,
        "tone": str,
        "errors": list,  # non-fatal errors encountered per step (see FR-18)
    },
}
```

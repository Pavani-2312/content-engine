# AI Content Engine — Architecture Document

## 1. Architectural Style

A **single-process, sequential pipeline** architecture wrapped in a
Streamlit UI. There is no backend server beyond Streamlit's own runtime;
all orchestration happens in-process, in Python, triggered synchronously
by a single user action.

This is intentionally simple — a linear chain, not a graph or agentic
loop — because each step has exactly one input source (the brief and/or
the prior step's output) and exactly one output consumer (the next step or
the UI).

## 2. System Context Diagram

```
                ┌────────────────────┐
                │   User (Browser)   │
                └─────────┬──────────┘
                          │ HTTP (Streamlit session)
                ┌─────────▼──────────┐
                │   Streamlit App    │
                │     (app.py)       │
                └─────────┬──────────┘
                          │ calls
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
 ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
 │ text_gen.py │   │ image_gen.py│   │ video_gen.py│
 └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
        │ HTTPS           │ HTTPS           │ HTTPS
        ▼                 ▼                 ▼
 ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
 │ OpenRouter  │   │ GPT Image   │   │  Runway API │
 │   API       │   │ API (gpt-   │   │ (image→video│
 │ (text LLMs) │   │  image-2)   │   │   model)    │
 └─────────────┘   └─────────────┘   └─────────────┘
```

## 3. Module Breakdown

```
content_engine/
├─ app.py            # UI shell, orchestration, session state — PROVIDED
├─ text_gen.py        # Tagline, blog, social prompt logic       — BUILD
├─ image_gen.py       # Image prompt formula + GPT Image client  — BUILD
├─ video_gen.py        # Motion prompt + Runway client            — BUILD
├─ config.py          # API keys, model names, constants         — PROVIDED
└─ .env               # OPENROUTER_API_KEY=...  RUNWAY_API_KEY=...
```

### 3.1 `app.py` (provided)
Responsibilities:
- Render the sidebar form and collect `brief`.
- On button click, call `run_pipeline(brief)`.
- Render results in a two-column layout as each asset becomes available.
- Hold pipeline state in `st.session_state` so re-renders (Streamlit's
  rerun-on-interaction model) don't lose generated assets.

### 3.2 `text_gen.py` (build)
Exposes three pure functions, each independently testable:
```python
def generate_tagline(product: str, audience: str, tone: str) -> str: ...
def generate_blog_intro(product: str, audience: str, tone: str, tagline: str) -> str: ...
def generate_social_post(product: str, tone: str) -> dict: ...
```
Internally each function:
1. Builds a system + user prompt pair.
2. Calls the shared OpenRouter client (from `config.py`).
3. Validates/post-processes the response per the contracts in
   `02_SPECIFICATIONS.md`.
4. Returns a plain Python type (str or dict) — never the raw API response.

### 3.3 `image_gen.py` (build)
```python
def build_image_prompt(product: str, tagline: str, tone: str) -> str: ...
def generate_image(prompt: str) -> str: ...  # returns URL or base64
```

### 3.4 `video_gen.py` (build)
```python
def build_motion_prompt() -> str: ...
def generate_video(image_url: str, motion_prompt: str) -> str: ...  # returns URL/path
```

### 3.5 `config.py` (provided)
- Loads `.env` via `python-dotenv`.
- Exposes pre-configured clients: `openrouter_client`, `gpt_image_client`, `runway_client`.
- Exposes model constants: `TEXT_MODEL`, `IMAGE_MODEL = "gpt-image-2"`, `VIDEO_MODEL`.

## 4. Orchestration Logic (the "chain")

A single coordinating function — conceptually owned by `app.py`, calling
into the three build modules — implements the chain:

```python
def run_pipeline(brief: dict) -> dict:
    errors = []

    tagline = safe_call(
        lambda: generate_tagline(brief["product"], brief["audience"], brief["tone"]),
        fallback="", errors=errors, step="tagline"
    )

    blog_intro = safe_call(
        lambda: generate_blog_intro(brief["product"], brief["audience"], brief["tone"], tagline),
        fallback="", errors=errors, step="blog_intro"
    )

    social = safe_call(
        lambda: generate_social_post(brief["product"], brief["tone"]),
        fallback={}, errors=errors, step="social"
    )

    image_prompt = build_image_prompt(brief["product"], tagline, brief["tone"])
    image_url = safe_call(
        lambda: generate_image(image_prompt),
        fallback=None, errors=errors, step="image"
    )

    video_url = None
    if image_url:
        motion_prompt = build_motion_prompt()
        video_url = safe_call(
            lambda: generate_video(image_url, motion_prompt),
            fallback=None, errors=errors, step="video"
        )

    return {
        "tagline": tagline,
        "blog_intro": blog_intro,
        "social": social,
        "image_url": image_url,
        "video_url": video_url,
        "meta": {**brief, "errors": errors},
    }
```

`safe_call` is a small wrapper implementing the retry-once policy described
in the specifications document — isolated so all five steps share one
error-handling code path rather than five duplicated try/except blocks.

## 5. State Management

Streamlit reruns the entire script on every interaction. To avoid
re-triggering API calls unnecessarily:

- The generated `CampaignSuite` result is stored in
  `st.session_state["suite"]` immediately after a successful pipeline run.
- The UI renders from `st.session_state["suite"]` if present, regardless of
  what triggered the rerun, and only calls `run_pipeline` again when the
  **Generate** button is explicitly pressed.
- Per-step progress is tracked via `st.session_state["pipeline_status"]`, a
  dict of `{step_name: "pending" | "running" | "done" | "error"}`, driving
  the `st.status` UI.

## 6. Sequence Diagram (happy path)

```
User        Streamlit(app.py)      text_gen        image_gen       video_gen
 │  fill form    │                    │                │               │
 │──────────────▶│                    │                │               │
 │  click Generate│                   │                │               │
 │──────────────▶│                    │                │               │
 │               │── generate_tagline ───▶│             │               │
 │               │◀──── tagline ──────────│             │               │
 │               │── generate_blog_intro ─▶│            │               │
 │               │◀──── blog_intro ───────│             │               │
 │               │── generate_social_post ▶│            │               │
 │               │◀──── social JSON ──────│             │               │
 │               │── build_image_prompt ──────────────▶│               │
 │               │── generate_image ──────────────────▶│               │
 │               │◀──── image_url ─────────────────────│               │
 │               │── generate_video(image_url) ───────────────────────▶│
 │               │◀──── video_url ───────────────────────────────────│
 │◀── render all 5 assets ──│           │                │               │
```

## 7. Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Text generation | OpenRouter (LLM gateway) |
| Image generation | GPT Image API (`gpt-image-2`) |
| Video generation | Runway API (image-to-video) |
| Config/secrets | `python-dotenv` + `.env` |
| Language | Python 3.10+ |

## 8. Design Principles Applied

- **Single Responsibility** — each module owns exactly one modality.
- **Separation of prompt logic from UI logic** — `app.py` never constructs
  prompts directly; it only calls functions from `text_gen.py`,
  `image_gen.py`, `video_gen.py`.
- **Fail-soft chaining** — a failure in an early step degrades gracefully
  (empty string/dict) rather than halting the whole pipeline, except where
  a step is a hard dependency (video requires a valid image).
- **Explainability** — every rendered asset is labeled with the prompting
  technique that produced it, per FR-11.

## 9. Known Limitations / Risks

| Risk | Mitigation |
|---|---|
| Video generation latency (Runway) may exceed typical user patience | Progressive rendering: show text + image immediately, video last, with explicit "rendering video…" status |
| LLM may not strictly respect word/char limits | Post-hoc validation + truncation as a safety net, not just prompt instruction |
| JSON parsing failures from the social post call | One retry with corrective prompt; fallback to raw-text display |
| Image content policy rejections | Prompt simplification fallback (drop tagline reference) |

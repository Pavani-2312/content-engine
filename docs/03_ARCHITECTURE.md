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
 │ OpenRouter  │   │ OpenRouter  │   │ OpenRouter  │
 │ (text LLMs) │   │  (image     │   │  (video     │
 │CONTENT_API  │   │  gen)       │   │  gen)       │
 │    _KEY     │   │CONTENT_API  │   │VIDEO_API_KEY│
 └─────────────┘   │    _KEY     │   └─────────────┘
                   └─────────────┘
```

## 3. Module Breakdown

```
content-engine/
├─ app.py         # UI shell, orchestration, session state — PROVIDED
├─ text_gen.py    # Tagline, blog, social prompt logic       — BUILD
├─ image_gen.py   # Image prompt formula + OpenRouter image client  — BUILD
├─ video_gen.py   # Motion prompt + OpenRouter video client            — BUILD
├─ config.py      # API keys, model names, constants         — PROVIDED
└─ .env           # CONTENT_API_KEY=...  VIDEO_API_KEY=...
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
- Exposes pre-configured clients:
  - `openrouter_client` — authenticated with `CONTENT_API_KEY` (text generation)
  - `gpt_image_client` — authenticated with `CONTENT_API_KEY` (image generation)
  - `video_client` — authenticated with `VIDEO_API_KEY` (video generation only)
- Exposes model constants: `TEXT_MODEL`, `IMAGE_MODEL = "openai/gpt-image-1"  # or whichever OpenRouter image model`, `VIDEO_MODEL`.

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

    # build_image_prompt is a pure, non-network function; wrap it
    # in safe_call only if custom tone keys might cause KeyErrors.
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

### `safe_call` contract

`safe_call` is a small helper that implements the retry-once policy shared
by all five steps:

```python
def safe_call(fn, *, fallback, errors: list, step: str):
    """
    Call fn(). On any exception, retry once after a short backoff.
    On second failure, append an error entry to `errors` and return `fallback`.
    """
    import time
    try:
        return fn()
    except Exception as e:
        time.sleep(2)
        try:
            return fn()
        except Exception as e2:
            errors.append({"step": step, "error": str(e2)})
            return fallback
```

All five pipeline steps share this single error-handling code path rather
than five duplicated try/except blocks.

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
User      app.py        text_gen      image_gen    video_gen   OpenRouter(content)   OpenRouter(video)
 │  fill    │               │              │            │           │           │         │
 │─────────▶│               │              │            │           │           │         │
 │ Generate │               │              │            │           │           │         │
 │─────────▶│               │              │            │           │           │         │
 │          │─generate_tagline────────────▶│            │           │           │         │
 │          │               │──── prompt ─────────────────────────▶│           │         │
 │          │               │◀─── tagline ────────────────────────│           │         │
 │          │◀──tagline─────│              │            │           │           │         │
 │          │─generate_blog_intro─────────▶│            │           │           │         │
 │          │               │──── prompt ─────────────────────────▶│           │         │
 │          │               │◀─── blog ───────────────────────────│           │         │
 │          │◀──blog_intro──│              │            │           │           │         │
 │          │─generate_social_post────────▶│            │           │           │         │
 │          │               │──── prompt ─────────────────────────▶│           │         │
 │          │               │◀─── JSON ───────────────────────────│           │         │
 │          │◀──social───────│              │            │           │           │         │
 │          │─build_image_prompt + generate_image───────▶│          │           │         │
 │          │               │              │──── prompt ──────────────────────▶│         │
 │          │               │              │◀─── image_url ───────────────────│         │
 │          │◀──image_url───────────────────│            │           │           │         │
 │ (render) │               │              │            │           │           │         │
 │          │─generate_video(image_url)─────────────────▶│          │           │         │
 │          │               │              │            │──── req ──────────────────────▶│
 │          │               │              │            │◀─── video_url ────────────────│
 │          │◀──video_url───────────────────────────────│           │           │         │
 │◀─render all 5─│           │              │            │           │           │         │
```

## 7. Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Text generation | OpenRouter (`CONTENT_API_KEY`) |
| Image generation | OpenRouter (`CONTENT_API_KEY`) |
| Video generation | OpenRouter (`VIDEO_API_KEY`) |
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

| Risk | Status | Mitigation |
|---|---|---|
| OpenRouter video generation latency may exceed typical user patience | Residual | Progressive rendering: show text + image immediately, video last, with explicit "rendering video…" status |
| LLM may not strictly respect word/char limits | Residual | Post-hoc validation + retry as a safety net; truncation is a last resort only |
| JSON parsing failures from the social post call | Mitigated | One retry with corrective prompt; fallback to raw-text display |
| Image content policy rejections | Mitigated | Prompt simplification fallback (drop tagline reference) |
 |
) |
 |

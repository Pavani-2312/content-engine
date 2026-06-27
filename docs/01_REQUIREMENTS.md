# AI Content Engine — Requirements Document

**Project:** AI Content Engine
**Type:** Multi-modal Streamlit Application
**Course Reference:** GenAI & Agentic AI Engineering — Day 3, Afternoon Lab

---

## 1. Purpose

Build a Streamlit application that takes a single product brief as input and
generates a complete marketing campaign suite — three text assets, one image,
and one video — through five chained AI API calls triggered by a single
button press.

## 2. Scope

### 2.1 In Scope
- A Streamlit UI with a sidebar input form and a two-column results layout.
- Five distinct generation steps, each using a different prompting technique.
- Sequential chaining: each step's output feeds the next step's input.
- Basic error handling and retry logic for API failures.
- Local `.env`-based configuration for API keys.

### 2.2 Out of Scope (unless attempted as stretch goals)
- Voiceover / audio generation (ElevenLabs or OpenAI TTS).
- A/B tagline comparison UI.
- Tone-switch regeneration cascade.
- ZIP export of the full asset suite.
- User authentication, persistence/database, or multi-user support.
- Deployment to a hosted environment (local execution only, unless specified otherwise).

## 3. Stakeholders

| Role | Interest |
|---|---|
| Student / Developer | Builds and demonstrates the working app |
| Peer Reviewer | Runs a different product brief through the engine to validate robustness |
| Instructor | Assesses correctness of prompting technique per asset and overall chaining logic |

## 4. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | The system shall accept three inputs: **Product Name**, **Target Audience**, **Brand Tone** (e.g., playful, premium, eco). | Must |
| FR-2 | The system shall provide a single "Generate" action that triggers the full five-call pipeline. | Must |
| FR-3 | The system shall generate a campaign **tagline** using few-shot prompting, with examples selected/conditioned by the chosen tone. | Must |
| FR-4 | The tagline shall be a maximum of 10 words and shall contain no hashtags. | Must |
| FR-5 | The system shall generate a **200-word blog introduction** using role-based prompting (persona: content strategist), incorporating the tagline generated in FR-3. | Must |
| FR-6 | The system shall generate a **social media post set** as structured JSON output containing `twitter` (≤280 chars), `instagram` (≤2200 chars), and `linkedin` (≤700 chars) fields. The social post generator receives `product` and `tone` only; `audience` and `tagline` are intentionally omitted from this step to keep the prompt focused on platform-specific copy constraints. | Must |
| FR-7 | The system shall construct an image prompt programmatically from product name, tagline, and tone, then generate a **hero image** via OpenRouter's image generation model. | Must |
| FR-8 | The system shall feed the generated hero image into OpenRouter's video generation model with a motion prompt to produce a **5–8 second promotional video**. If the hero image generation step fails (image URL is `None`), the video step shall be skipped and an appropriate error surfaced per NFR-3. | Must |
| FR-9 | The system shall display all five generated assets simultaneously: text assets in the left column, image and video in the right column. | Must |
| FR-10 | The system shall execute the calls in a defined sequential chain: Tagline → Blog Intro → Social Post → Hero Image → Video. | Must |
| FR-11 | The system shall label each output card with the prompting technique that produced it. | Should |
| FR-12 | The system shall retry a failed API call at least once before surfacing an error to the user. | Should |
| FR-13 | The system shall display a loading/progress indicator for each of the five steps while generation is in progress. | Should |
| FR-18 | The system shall record non-fatal errors encountered during pipeline execution in a `meta.errors` list returned as part of the `CampaignSuite` result, and display them in the UI. | Should |
| FR-14 (Stretch) | The system may generate a voiceover audio track from the blog introduction text. | Could |
| FR-15 (Stretch) | The system may generate two tagline variants and let the user select one before proceeding. | Could |
| FR-16 (Stretch) | The system may allow tone changes that trigger a full regeneration cascade. | Could |
| FR-17 (Stretch) | The system may package all five assets into a downloadable ZIP file. | Could |

## 5. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | **Modularity** — Text, image, and video generation logic must live in separate modules (`text_gen.py`, `image_gen.py`, `video_gen.py`). |
| NFR-2 | **Security** — Two API keys must be used: `CONTENT_API_KEY` for text and image generation, `VIDEO_API_KEY` exclusively for video generation. Both must be loaded from environment variables (`.env`) and never hard-coded or logged. |
| NFR-3 | **Resilience** — A failure in one generation step must not crash the entire app; the UI must surface a clear, actionable error per failed asset. |
| NFR-4 | **Latency tolerance** — Given five sequential API calls (including image and video generation), total run time is expected to range from 30–90+ seconds under normal network conditions; the app must not time out or crash during this window and must communicate progress continuously so the user does not perceive the app as frozen. |
| NFR-5 | **Consistency** — Outputs across the five calls must reflect the same brand tone and product context (no contradictory voice between tagline, blog, and social copy). |
| NFR-6 | **Reproducibility** — Given the same inputs, the prompting logic (not necessarily the model's stochastic output) must be deterministic in structure. |
| NFR-7 | **Readability** — Each prompt template must be isolated, named, and documented with the technique it demonstrates (few-shot, role-based, structured output, formula-based, motion-prompt). |

## 6. Acceptance Criteria

1. The app generates all five assets in a single run from one product brief.
2. The tagline's brand voice matches the selected tone.
3. The blog introduction explicitly echoes the tagline.
4. Social posts respect the per-platform character limits.
5. The hero image visually matches the product and tone.
6. The video is a clean, coherent 5–8 second clip derived from the hero image.
7. A peer reviewer can run a **different** product brief through the engine and get a coherent, on-brand output suite without code changes.

## 7. Constraints

- Build time: 120 minutes.
- Must use the provided scaffold (`app.py`, `config.py`) as the architectural baseline.
- Must use **Streamlit** for the UI layer (no other frontend framework).
- Must use **OpenRouter** for all generation calls: text and image via `CONTENT_API_KEY`, video via a dedicated `VIDEO_API_KEY`.

## 8. Lab Prerequisites (Assumptions)

These are assumed to be true before development begins. The **instructor** is
responsible for providing items marked *(instructor-provided)*.

- A valid `CONTENT_API_KEY` *(instructor-provided)* (used for text and image generation) and `VIDEO_API_KEY` *(instructor-provided)* (used exclusively for video generation) are available in `.env`.
- The provided scaffold's client wrappers for OpenRouter (text+image) and OpenRouter (video) are functional and require no modification beyond integration *(instructor-provided)*.
- Internet connectivity is available for all external API calls.

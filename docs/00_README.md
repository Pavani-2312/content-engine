# AI Content Engine — Documentation Index

**Course:** GenAI & Agentic AI Engineering — Day 3, Afternoon Lab
**Build window:** 120 minutes
**Stack:** Streamlit · OpenRouter · GPT Image API (`gpt-image-2`) · Runway API

---

## Document Set

| Document | Purpose |
|---|---|
| [`01_REQUIREMENTS.md`](./01_REQUIREMENTS.md) | What the system must do — functional/non-functional requirements, scope, acceptance criteria |
| [`02_SPECIFICATIONS.md`](./02_SPECIFICATIONS.md) | How each of the five generation steps must behave — exact prompt contracts, input/output formats, validation rules, UI widget spec |
| [`03_ARCHITECTURE.md`](./03_ARCHITECTURE.md) | How the system is structured — modules, orchestration/chaining logic, state management, sequence diagram, tech stack |

## One-Paragraph Summary

The AI Content Engine is a Streamlit app that turns a single product brief
(product name, target audience, brand tone) into a full campaign suite —
tagline, blog intro, social post, hero image, and promotional video — via
five chained API calls, each demonstrating a distinct prompting technique
(few-shot, role-based, structured output, formula-based image prompting,
and motion-prompt image-to-video).

## Project Structure Reference

```
content_engine/
├─ app.py            # Streamlit shell — provided
├─ text_gen.py       # Tagline, blog, social prompts — build
├─ image_gen.py      # Image prompt + GPT Image call — build
├─ video_gen.py      # Motion prompt + Runway call — build
├─ config.py         # API keys + model settings — provided
└─ .env              # OPENROUTER_API_KEY=...  RUNWAY_API_KEY=...
```

## Suggested Reading Order

1. Start with **Requirements** to understand scope and acceptance criteria.
2. Read **Specifications** before writing any prompt — it defines the exact
   contract each function must satisfy.
3. Read **Architecture** to understand how the modules fit together and how
   the chain (tagline → blog → social, product+tagline → image → video) is
   wired and made resilient to failures.

## Definition of Done

Per the brief's "Done by 3:00" checklist:
- All five assets generate in one run from a single product brief.
- Tagline matches the selected tone; blog echoes the tagline; social posts
  respect platform character limits.
- Hero image matches product + tone; video is a clean 5–8 second clip.
- A peer reviewer can run a **different** product through the engine and
  it holds up without code changes.

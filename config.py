import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CONTENT_API_KEY = os.getenv("CONTENT_API_KEY")
VIDEO_API_KEY = os.getenv("VIDEO_API_KEY")

if not CONTENT_API_KEY or not VIDEO_API_KEY:
    raise ValueError("Missing required API keys in .env: CONTENT_API_KEY and/or VIDEO_API_KEY")

# OpenRouter clients
openrouter_client = OpenAI(
    api_key=CONTENT_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

image_client = OpenAI(
    api_key=CONTENT_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

video_client = OpenAI(
    api_key=VIDEO_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Model constants
TEXT_MODEL = "openai/gpt-4o-mini"
IMAGE_MODEL = "openai/dall-e-3"
VIDEO_MODEL = "openai/sora"

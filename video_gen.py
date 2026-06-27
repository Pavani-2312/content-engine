import time
import requests
from config import video_client, VIDEO_MODEL, VIDEO_API_KEY

MOTION_PROMPT = (
    "Slow cinematic push-in. "
    "Soft light shifts gently. "
    "Background mostly still. 5 to 8 seconds."
)

def build_motion_prompt() -> str:
    return MOTION_PROMPT

def generate_video(image_url: str, motion_prompt: str) -> str:
    # Using OpenRouter's video endpoint (image-to-video)
    # Note: OpenRouter may route this to a provider like Runway or similar
    response = video_client.chat.completions.create(
        model=VIDEO_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": motion_prompt}
                ]
            }
        ],
        max_tokens=1000
    )
    
    # If response contains job ID for async processing, poll
    content = response.choices[0].message.content
    
    # Direct video URL return case
    if content.startswith("http"):
        return content
    
    # If OpenRouter returns a job ID (format varies by provider)
    # For now, return the content as-is; real polling would need provider-specific logic
    return content

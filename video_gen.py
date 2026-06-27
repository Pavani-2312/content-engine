import time
from config import video_client, VIDEO_MODEL

MOTION_PROMPT = (
    "Slow cinematic push-in. "
    "Soft light shifts gently. "
    "Background mostly still. 5 to 8 seconds."
)

def build_motion_prompt() -> str:
    return MOTION_PROMPT

def generate_video(image_url: str, motion_prompt: str) -> str:
    response = video_client.chat.completions.create(
        model=VIDEO_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"Generate a video from this image: {image_url}\n\nMotion instructions: {motion_prompt}"
            }
        ]
    )
    
    # Extract video URL from response
    content = response.choices[0].message.content
    
    # If content contains URL, extract it
    if content and "http" in content:
        import re
        urls = re.findall(r'https?://[^\s]+', content)
        if urls:
            return urls[0].rstrip(')')
    
    return content

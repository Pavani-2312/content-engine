from config import image_client, IMAGE_MODEL

STYLE_MAP = {
    "playful": "bright flat illustration",
    "premium": "photorealistic, studio lighting",
    "eco": "watercolour, natural tones",
}

def build_image_prompt(product: str, tagline: str, tone: str) -> str:
    style = STYLE_MAP.get(tone, "clean modern")
    tagline_hint = f' Evoke the feeling of: "{tagline}".' if tagline else ""
    return (
        f"A {style} of {product}."
        f"{tagline_hint} "
        f"Centred, shallow DOF, 16:9. No text, no logos."
    )

def generate_image(prompt: str) -> str:
    try:
        response = image_client.chat.completions.create(
            model=IMAGE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract image URL from response
        content = response.choices[0].message.content
        
        # If content contains URL, extract it
        if content and "http" in content:
            import re
            urls = re.findall(r'https?://[^\s]+', content)
            if urls:
                return urls[0].rstrip(')')
        
        return content
        
    except Exception:
        # Retry with simplified prompt
        simplified = prompt.split("Evoke")[0].strip()
        response = image_client.chat.completions.create(
            model=IMAGE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": simplified
                }
            ]
        )
        content = response.choices[0].message.content
        
        if content and "http" in content:
            import re
            urls = re.findall(r'https?://[^\s]+', content)
            if urls:
                return urls[0].rstrip(')')
        
        return content

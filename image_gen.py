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
        # OpenRouter uses chat completions for image generation
        response = image_client.chat.completions.create(
            model=IMAGE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000
        )
        
        # Extract image URL from response
        content = response.choices[0].message.content
        
        # If content is a URL, return it
        if content and content.startswith("http"):
            return content
        
        # Otherwise, it might be base64 or need parsing
        return content
        
    except Exception as e:
        # Retry with simplified prompt
        simplified = prompt.split("Evoke")[0].strip()
        response = image_client.chat.completions.create(
            model=IMAGE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": simplified
                }
            ],
            max_tokens=1000
        )
        content = response.choices[0].message.content
        return content if content.startswith("http") else content

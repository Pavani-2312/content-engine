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
        response = image_client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            n=1,
            size="1792x1024"
        )
        return response.data[0].url
    except Exception:
        # Retry with simplified prompt
        simplified = prompt.split("Evoke")[0].strip()
        response = image_client.images.generate(
            model=IMAGE_MODEL,
            prompt=simplified,
            n=1,
            size="1792x1024"
        )
        return response.data[0].url

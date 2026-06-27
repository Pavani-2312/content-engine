from config import image_client, TEXT_MODEL

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
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Generate an image: {prompt}"
                }
            ],
            tools=[
                {
                    "type": "openrouter:image_generation"
                }
            ]
        )
        
        # Extract image URL from tool call response
        message = response.choices[0].message
        
        # Check if tool was called
        if hasattr(message, 'tool_calls') and message.tool_calls:
            # Image URL should be in the tool call result
            return message.tool_calls[0].function.arguments
        
        # Otherwise check content for URL
        content = message.content
        if content and "http" in content:
            # Extract URL from content
            import re
            urls = re.findall(r'https?://[^\s]+', content)
            if urls:
                return urls[0]
        
        return content
        
    except Exception as e:
        # Retry with simplified prompt
        simplified = prompt.split("Evoke")[0].strip()
        response = image_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Generate an image: {simplified}"
                }
            ],
            tools=[
                {
                    "type": "openrouter:image_generation"
                }
            ]
        )
        
        message = response.choices[0].message
        if hasattr(message, 'tool_calls') and message.tool_calls:
            return message.tool_calls[0].function.arguments
        
        content = message.content
        if content and "http" in content:
            import re
            urls = re.findall(r'https?://[^\s]+', content)
            if urls:
                return urls[0]
        
        return content

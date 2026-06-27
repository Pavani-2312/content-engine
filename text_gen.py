import json
from config import openrouter_client, TEXT_MODEL

TONE_EXAMPLES = {
    "playful": [
        "Fun never tasted this fizzy.",
        "Snack smarter. Smile harder."
    ],
    "premium": [
        "Crafted for those who notice everything.",
        "Excellence, refined."
    ],
    "eco": [
        "Lighter on you. Lighter on Earth.",
        "Pure, naturally."
    ]
}

def generate_tagline(product: str, audience: str, tone: str) -> str:
    examples = TONE_EXAMPLES.get(tone, TONE_EXAMPLES["eco"])
    
    response = openrouter_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": "You are a creative director. Generate ONE campaign tagline. Match the brand tone exactly. Max 10 words. No hashtags."},
            {"role": "user", "content": f"""Product: {product}
Audience: {audience}
Tone: {tone}

Examples of {tone} taglines:
1. "{examples[0]}"
2. "{examples[1]}"

Generate a new, original tagline for this product. Do not reuse the examples."""}
        ]
    )
    
    tagline = response.choices[0].message.content.strip().strip('"')
    
    # Validate
    if len(tagline.split()) > 10 or '#' in tagline:
        # Retry with correction
        response = openrouter_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "You are a creative director. Generate ONE campaign tagline. Match the brand tone exactly. Max 10 words. No hashtags."},
                {"role": "user", "content": f"Your tagline was too long or contained a hashtag. Regenerate: one tagline, max 10 words, no hashtags. Product: {product}, Tone: {tone}"}
            ]
        )
        tagline = response.choices[0].message.content.strip().strip('"')
    
    return tagline

def generate_blog_intro(product: str, audience: str, tone: str, tagline: str) -> str:
    if tagline:
        system_prompt = f"""You are a content strategist writing for {audience}.
Write a 200-word blog intro for {product}.
Weave in the campaign tagline: "{tagline}".
Tone: {tone}."""
    else:
        system_prompt = f"""You are a content strategist writing for {audience}.
Write a 200-word blog intro for {product}.
Tone: {tone}."""
    
    response = openrouter_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Write the blog intro now."}
        ]
    )
    
    return response.choices[0].message.content.strip()

def generate_social_post(product: str, tone: str) -> dict:
    response = openrouter_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": f"""Generate social posts for {product}. Return ONLY JSON:
{{ "twitter": string (max 280 chars),
  "instagram": string (max 2200 chars),
  "linkedin": string (max 700 chars) }}
Tone: {tone}. No markdown fences."""},
            {"role": "user", "content": "Generate the posts now."}
        ]
    )
    
    raw = response.choices[0].message.content.strip().strip("`").strip()
    
    try:
        social = json.loads(raw)
        if set(social.keys()) != {"twitter", "instagram", "linkedin"}:
            raise ValueError("Unexpected keys")
        if len(social["twitter"]) > 280 or len(social["instagram"]) > 2200 or len(social["linkedin"]) > 700:
            raise ValueError("Character limit exceeded")
        return social
    except (json.JSONDecodeError, ValueError):
        # Retry
        response = openrouter_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "Your last response was not valid JSON. Return ONLY the JSON object, nothing else."},
                {"role": "user", "content": f"Generate social posts for {product}. Tone: {tone}. Return JSON with twitter, instagram, linkedin keys."}
            ]
        )
        raw = response.choices[0].message.content.strip().strip("`").strip()
        social = json.loads(raw)
        return social

import json
import re


def parse_json_safe(response: str) -> dict:
    """Parse JSON from LLM response with fallback for markdown-wrapped JSON."""
    # Strip thinking-like tags que podem aparecer no texto de resposta.
    # Nota: via API OpenRouter, thinking blocks nativos do Claude vêm como
    # elementos separados na array content (type="thinking"), não como tags
    # no texto. Esta regex é um fallback defensivo para formatos inesperados.
    response = re.sub(r"<thinking>.*?</thinking>", "", response, flags=re.DOTALL)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Remove markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", response.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the response
    match = re.search(r"\{[\s\S]*\}", response)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse JSON from LLM response: {response[:300]}")

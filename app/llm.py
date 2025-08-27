import json
import requests
from typing import Dict, Any

OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
ANTHROPIC_DEFAULT_MODEL = "claude-3-5-sonnet-latest"
GEMINI_DEFAULT_MODEL = "gemini-1.5-flash"

def call_llm(provider: str, api_key: str, model: str, prompt: str, base_url: str = None) -> str:
    provider = (provider or "").lower()
    model = model or (
        OPENAI_DEFAULT_MODEL if provider in ("openai", "openai-compatible")
        else ANTHROPIC_DEFAULT_MODEL if provider == "anthropic"
        else GEMINI_DEFAULT_MODEL
    )

    if provider in ("openai", "openai-compatible"):
        url = (base_url.rstrip("/") if base_url else "https://api.openai.com/v1") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        # compatibility for chat completions
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        return json.dumps(data)

    if provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model,
            "max_tokens": 1200,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}]
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return "".join(part.get("text", "") for part in data.get("content", []) if part.get("type") == "text")

    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        }
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return "".join(p.get("text","") for c in data.get("candidates",[]) for p in c.get("content",{}).get("parts",[]))

    raise ValueError("Unsupported provider. Use one of: openai, openai-compatible, anthropic, gemini.")


def build_outline_prompt(input_text: str, guidance: str, want_notes: bool) -> str:
    return f"""You are a presentation architect. Convert the INPUT TEXT into a JSON outline for a PowerPoint deck.
Rules:
- Choose a reasonable number of slides based on content and guidance.
- Each slide must have: "title": string, "bullets": [strings].
- If appropriate and requested, include "notes": string (speaker notes).
- Use concise, scannable bullets (max 6 per slide, ~10 words each).
- NO markdown, NO commentary outside JSON.

Guidance: {guidance or "default professional tone"}

Return STRICT JSON like:
{{
  "slides": [
    {{
      "title": "Overview",
      "bullets": ["Point 1", "Point 2"],
      "notes": "optional speaker notes"
    }}
  ]
}}

INPUT TEXT:
{input_text}
"""
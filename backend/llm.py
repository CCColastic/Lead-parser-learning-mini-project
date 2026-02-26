import json
import os
from typing import Any, Tuple

from openai import OpenAI

SYSTEM_PROMPT = """You are an information extraction engine.
Return JSON only. No markdown. No backticks. No explanation.
If a field is unknown, use null.
Valid urgency values: "low", "medium", "high".
"""

JSON_SHAPE = """{
  "name": null,
  "email": null,
  "phone": null,
  "company": null,
  "request_summary": null,
  "urgency": null
}"""


def build_user_prompt(text: str) -> str:
    return f"""Extract lead info from the following message into EXACTLY this JSON shape:
{JSON_SHAPE}

Message:
{text}
"""


def make_client() -> OpenAI:
    api_key = os.environ["DEEPSEEK_API_KEY"]
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url)


def call_and_parse_lead(text: str, *, model: str = "deepseek-chat", max_retries: int = 2) -> Tuple[str, Any]:
    """
    Returns (raw_model_text, parsed_json_obj).

    Strategy:
    - Call LLM, ask for JSON only
    - Try json.loads()
    - If invalid, add a corrective message and retry
    """
    client = make_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(text)},
    ]

    last_raw = ""

    for attempt in range(max_retries + 1):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )

        raw = resp.choices[0].message.content or ""
        last_raw = raw

        try:
            parsed = json.loads(raw)
            return raw, parsed
        except json.JSONDecodeError as e:
            if attempt >= max_retries:
                raise ValueError(f"Invalid JSON from model after {max_retries + 1} attempts: {e}\nRaw:\n{last_raw}") from e

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response was invalid JSON. "
                        "Return JSON only, matching the exact shape. "
                        "No markdown, no comments, no trailing commas.\n\n"
                        f"Invalid response:\n{raw}"
                    ),
                }
            )

    raise RuntimeError(f"Unexpected failure. Last output:\n{last_raw}")
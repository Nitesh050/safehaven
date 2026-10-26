"""Day 0. One call to each Meta model to confirm keys, formats and capabilities.

Fill .env first. Results go into DECISIONS.md.
"""

import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["META_API_KEY"], base_url=os.environ["META_API_BASE_URL"])
MUSE = os.getenv("MUSE_MODEL", "muse-spark")

PROMPTS = {
    "hindi": "बाढ़ में सबसे नज़दीकी सुरक्षित जगह कैसे ढूँढें? दो वाक्यों में बताइए।",
    "maithili": "बाढ़ मे सबसँ लग सुरक्षित जगह कोना ताकब? दू वाक्य मे कहू।",
}

TOOL = {
    "type": "function",
    "function": {
        "name": "find_safe_route",
        "description": "Find the nearest reachable shelter avoiding flooded roads.",
        "parameters": {
            "type": "object",
            "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}},
            "required": ["lat", "lon"],
        },
    },
}


def chat(label: str, **kwargs) -> None:
    t0 = time.time()
    try:
        r = client.chat.completions.create(model=MUSE, **kwargs)
        msg = r.choices[0].message
        print(f"[OK] {label} ({time.time() - t0:.1f}s)")
        print("     text:", (msg.content or "")[:300])
        if getattr(msg, "tool_calls", None):
            print("     tool_calls:", msg.tool_calls)
    except Exception as e:  # report and continue so every check runs
        print(f"[FAIL] {label}: {e}", file=sys.stderr)


for lang, text in PROMPTS.items():
    chat(f"muse {lang}", messages=[{"role": "user", "content": text}])

chat(
    "muse tool calling",
    messages=[{"role": "user", "content": "I am at 26.05, 86.25. Where is a safe place?"}],
    tools=[TOOL],
)

# SAM 3.1: request format differs from chat; fill in from the Meta Model API docs.
print("[TODO] SAM 3.1: call with prompts water, person, cow, roof on a sample photo;"
      " record mask format and latency in DECISIONS.md")

# utils.py
import json
import os
import time
from typing import List, Dict, Any

# -------------------------
# Google Generative AI SDK
# -------------------------
try:
    import google.generativeai as genai
    SDK_AVAILABLE = True
except Exception:
    genai = None
    SDK_AVAILABLE = False


# -------------------------
# Default prompt templates
# -------------------------
DEFAULT_PROMPTS = {
    "categorize": {
        "name": "Categorize Email",
        "template": (
            "Categorize this email and respond ONLY in JSON.\n"
            "{\n"
            '  "labels": ["..."],\n'
            '  "priority": "low/medium/high",\n'
            '  "summary": "short summary"\n'
            "}"
        )
    },
    "extract_actions": {
        "name": "Extract Action Items",
        "template": (
            "Extract action items from this email. Respond in JSON array.\n"
            '[ "task 1", "task 2", ... ]'
        )
    },
    "draft_reply": {
        "name": "Draft Reply",
        "template": (
            "Draft a polite, concise reply.\n"
            "Address the sender, mention key points, and propose next steps.\n"
            "Keep it under 180 words."
        )
    },
    "chat": {
        "name": "Chat about email",
        "template": (
            "You are an assistant that answers user questions based strictly "
            "on the email content. Be concise."
        )
    }
}


# -------------------------
# JSON Helpers
# -------------------------
def load_json(path: str):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


# -------------------------
# Mock Inbox
# -------------------------
def get_sample_inbox():
    return [
        {
            "from": "alice@company.com",
            "to": "you@company.com",
            "subject": "Request: Q2 marketing budget approval",
            "date": "2025-09-01",
            "body": (
                "Hi,\n\nCan you approve the Q2 marketing budget? We need a decision by Friday. "
                "Attached are the numbers.\n\nThanks,\nAlice"
            ),
            "archived": False
        },
        {
            "from": "bob@startup.com",
            "to": "you@company.com",
            "subject": "Meeting: Product sync (tomorrow)",
            "date": "2025-10-20",
            "body": (
                "Hello,\n\nCan we meet tomorrow at 10am to sync on the product roadmap? "
                "Please confirm or propose another time.\n\nRegards,\nBob"
            ),
            "archived": False
        },
        {
            "from": "carol@vendor.com",
            "to": "you@company.com",
            "subject": "Invoice INV-2025-017 (overdue)",
            "date": "2025-10-15",
            "body": (
                "Dear team,\n\nInvoice INV-2025-017 is overdue by 10 days. "
                "Please arrange payment or contact us.\n\nBest,\nCarol"
            ),
            "archived": False
        },
        {
            "from": "dave@partner.org",
            "to": "you@company.com",
            "subject": "Collaboration opportunity - quick chat?",
            "date": "2025-10-01",
            "body": (
                "Hi,\n\nWe have a potential collaboration. Interested in a 20-min call next week?\n\nThanks,\nDave"
            ),
            "archived": False
        }
    ]


# -------------------------
# LLM Call (Gemini SDK)
# -------------------------
def call_llm(prompt: str, temperature: float = 0.2, max_output_tokens: int = 300) -> str:
    api_key = os.getenv("GOOGLE_API_KEY")

    # If key missing → mock response
    if not api_key:
        return "[MOCK RESPONSE] " + prompt[:150] + "..."

    try:
        genai.configure(api_key=api_key)

        # API key 
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": float(temperature),
                "max_output_tokens": int(max_output_tokens)
            }
        )

        # Best-case extraction
        if hasattr(response, "text") and response.text:
            return response.text.strip()

        # Fallback candidate extraction
        if hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].content[0].text.strip()

        # Final fallback: string dump
        return str(response)[:2000]

    except Exception as e:
        return f"[ERROR] Gemini SDK call failed: {e}"


# -------------------------
# Categorization
# -------------------------
def categorize_email(email: Dict[str, str], prompt_template: str, temperature: float = 0.2, max_output_tokens: int = 300):
    prompt = prompt_template + "\n\nEmail:\n" + email.get("body", "")
    out = call_llm(prompt, temperature=temperature, max_output_tokens=max_output_tokens)

    # Remove markdown wrappers like ```json ... ```
    cleaned = out.replace("```json", "").replace("```", "").strip()

    # Try to parse JSON cleanly
    try:
        parsed = json.loads(cleaned)
        return parsed
    except Exception:
        # fallback: return raw text
        return {"text": out}



# -------------------------
# Action Item Extraction
# -------------------------
def extract_actions(email: Dict[str, str], prompt_template: str,
                    temperature: float = 0.2, max_output_tokens: int = 300) -> List[str]:
    prompt = prompt_template + "\n\nEMAIL:\n" + email.get("body", "")
    out = call_llm(prompt, temperature, max_output_tokens)

    # JSON array detection
    if out.strip().startswith("["):
        try:
            return json.loads(out)
        except Exception:
            pass

    # Bullet list fallback
    return [l.strip(" -•\t") for l in out.splitlines() if l.strip()]


# -------------------------
# Draft Reply
# -------------------------
def draft_reply(email: Dict[str, str], prompt_template: str,
                temperature: float = 0.2, max_output_tokens: int = 300,
                thread_context: str = None) -> str:
    prompt = prompt_template + "\n\nEMAIL:\n" + email.get("body", "")

    if thread_context:
        prompt += "\n\nTHREAD CONTEXT:\n" + thread_context

    out = call_llm(prompt, temperature, max_output_tokens)
    return out.strip()


# -------------------------
# Thread Context Collector
# -------------------------
def collect_thread_context(inbox: list, thread_id: str):
    if not thread_id:
        return None

    msgs = []
    for m in inbox:
        if m.get("thread_id") == thread_id:
            msgs.append(
                f"FROM: {m.get('from')}\nDATE: {m.get('date')}\n{m.get('body')}\n---\n"
            )
    return "\n".join(msgs) if msgs else None


# -------------------------
# Ingestion Pipeline
# -------------------------
def run_ingestion_pipeline(inbox: list, prompts: dict,
                           temperature: float = 0.2, max_output_tokens: int = 300):
    """
    Runs categorization + action extraction for ALL emails.
    Updates inbox items with:
        - category
        - action_items
    """
    results = []

    for idx, email in enumerate(inbox):
        try:
            cat_prompt = prompts["categorize"]["template"]
            act_prompt = prompts["extract_actions"]["template"]

            category = categorize_email(email, cat_prompt, temperature, max_output_tokens)
            actions = extract_actions(email, act_prompt, temperature, max_output_tokens)

            inbox[idx]["category"] = category
            inbox[idx]["action_items"] = actions

            results.append({
                "email_idx": idx,
                "category": category,
                "action_items": actions
            })

        except Exception as e:
            results.append({
                "email_idx": idx,
                "error": str(e)
            })

    return inbox, results

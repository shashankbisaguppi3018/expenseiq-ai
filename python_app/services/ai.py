"""AI helpers: chatbot, voice expense parser, receipt OCR."""
import json
import base64
import asyncio
from services.db import EMERGENT_LLM_KEY, GEMINI_API_KEY


def _has_key():
    return bool(EMERGENT_LLM_KEY or GEMINI_API_KEY)


def _run(coro):
    """Run an async coroutine from a sync (Streamlit) context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _chat(system: str, user_msg: str, session_id: str, model: str = "gpt-5.2"):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id,
                   system_message=system).with_model("openai", model)
    resp = await chat.send_message(UserMessage(text=user_msg))
    return str(resp)


def _gemini_chat(system: str, user_msg: str, model: str = "gemini-2.5-flash"):
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    resp = client.models.generate_content(
        model=model,
        contents=f"{system}\n\nUser question: {user_msg}",
    )
    return resp.text or ""


def chat_reply(system_prompt: str, user_msg: str, session_id: str = "default") -> str:
    if not _has_key():
        return "AI is not configured. Add GEMINI_API_KEY or EMERGENT_LLM_KEY to your .env to enable the assistant."
    try:
        if GEMINI_API_KEY:
            return _gemini_chat(system_prompt, user_msg)
        return _run(_chat(system_prompt, user_msg, session_id))
    except Exception as e:
        return f"Sorry, I couldn't process that. ({type(e).__name__})"


def parse_voice_expense(text: str):
    if not _has_key():
        return None, "AI not configured"
    system = (
        "Extract a single expense from the user's sentence. Output STRICT JSON only with keys: "
        "amount (number), category (one of: Food, Shopping, Rent, Transport, Utilities, "
        "Entertainment, Healthcare, Education, Investments, Miscellaneous), "
        "note (short), type ('expense' or 'income'). Currency INR. No markdown."
    )
    try:
        raw = (_gemini_chat(system, text) if GEMINI_API_KEY else _run(_chat(system, text, "voice_parser"))).strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"): raw = raw[4:]
            if raw.endswith("```"): raw = raw[:-3]
        data = json.loads(raw)
        if float(data.get("amount", 0)) <= 0:
            return None, "Couldn't find an amount"
        return data, None
    except Exception as e:
        return None, str(e)


async def _vision(system: str, b64: str, prompt: str):
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id="ocr",
                   system_message=system).with_model("openai", "gpt-4o-mini")
    msg = UserMessage(text=prompt, file_contents=[ImageContent(image_base64=b64)])
    return str(await chat.send_message(msg))


def ocr_receipt(image_bytes: bytes):
    if not EMERGENT_LLM_KEY:
        return None, "AI not configured"
    try:
        b64 = base64.b64encode(image_bytes).decode()
        system = (
            "You analyse receipt images. Extract: merchant (short), amount (final total, number), "
            "date (YYYY-MM-DD), category (Food, Shopping, Rent, Transport, Utilities, "
            "Entertainment, Healthcare, Education, Investments, Miscellaneous). "
            "Reply STRICT JSON only. No markdown."
        )
        raw = _run(_vision(system, b64, "Extract receipt fields as JSON.")).strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"): raw = raw[4:]
            if raw.endswith("```"): raw = raw[:-3]
        return json.loads(raw), None
    except Exception as e:
        return None, str(e)

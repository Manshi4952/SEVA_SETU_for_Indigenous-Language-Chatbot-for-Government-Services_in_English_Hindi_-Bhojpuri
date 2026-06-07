"""
telegram_service.py – Telegram Bot API helper using long polling.

This module reads the bot token from `settings.TELEGRAM_BOT_TOKEN` or
the `TELEGRAM_BOT_TOKEN` environment variable.

Instead of a webhook, it runs a background long-polling loop (`poll_updates`)
that fetches updates via `getUpdates` and processes each incoming message
through the existing RAG pipeline. Use `start_polling()` from the app
lifespan to launch it as an asyncio task and `stop_polling()` to cancel it.
"""
from __future__ import annotations
import os
import asyncio
import threading
from contextlib import contextmanager
from typing import Any, Optional

import httpx

from app.core.config import settings


BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN")

# How long Telegram holds the getUpdates request open (server-side long poll).
LONG_POLL_TIMEOUT = 30

_poll_task: Optional["asyncio.Task[None]"] = None


def _api_url(method: str) -> str:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


# Telegram caps message text at 4096 chars.
TELEGRAM_MAX_LEN = 4096


def _post_message(chat_id: int | str, text: str, parse_mode: str | None) -> Any:
    url = _api_url("sendMessage")
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    r = httpx.post(url, json=payload, timeout=10.0)
    r.raise_for_status()
    return r.json()


def send_message(chat_id: int | str, text: str, parse_mode: str = "Markdown") -> Any:
    """Send the AI reply to Telegram, delivering it no matter what it contains.

    The AI output can include characters that break Telegram's Markdown parser
    (which would make the API reject the message with a 400). To guarantee the
    user always receives the AI's answer, we fall back to plain text on failure,
    and split anything longer than Telegram's 4096-char limit.
    """
    if not text:
        return None

    # Split into Telegram-sized chunks; send each, last result returned.
    chunks = [text[i:i + TELEGRAM_MAX_LEN] for i in range(0, len(text), TELEGRAM_MAX_LEN)]
    result = None
    for chunk in chunks:
        try:
            result = _post_message(chat_id, chunk, parse_mode)
        except Exception as e:
            # Most likely a Markdown parse error — retry as plain text so the
            # AI's reply still reaches the user verbatim.
            print(f"[Telegram] send_message ({parse_mode}) failed, retrying as plain text: {e}")
            try:
                result = _post_message(chat_id, chunk, None)
            except Exception as e2:
                print(f"[Telegram] send_message plain-text error: {e2}")
                result = None
    return result


def send_audio(chat_id: int | str, audio_path: str, caption: str | None = None) -> Any:
    url = _api_url("sendAudio")
    try:
        with open(audio_path, "rb") as f:
            files = {"audio": (os.path.basename(audio_path), f)}
            data = {"chat_id": str(chat_id)}
            if caption:
                data["caption"] = caption
            r = httpx.post(url, data=data, files=files, timeout=60.0)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[Telegram] send_audio error: {e}")
        return None


# ── Chat action ("typing…") ──────────────────────────────────────────────────

def send_chat_action(chat_id: int | str, action: str = "typing") -> Any:
    """Show a status like 'typing…' in the chat. Lasts ~5s on Telegram's side."""
    url = _api_url("sendChatAction")
    try:
        r = httpx.post(url, json={"chat_id": chat_id, "action": action}, timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[Telegram] send_chat_action error: {e}")
        return None


@contextmanager
def typing_action(chat_id: int | str, action: str = "typing", interval: float = 4.0):
    """Keep the 'typing…' indicator alive for the whole block.

    Telegram clears the status after ~5s, so we re-send it on a background
    thread every `interval` seconds until the work is done.
    """
    stop = threading.Event()

    def _loop():
        while not stop.is_set():
            send_chat_action(chat_id, action)
            stop.wait(interval)  # exits early if stopped

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1.0)


# ── Message handling ────────────────────────────────────────────────────────

def _handle_message(msg: dict) -> None:
    """Process a single Telegram message through the RAG pipeline.

    Runs synchronously (blocking RAG + HTTP send) – called via
    `asyncio.to_thread` from the polling loop so it doesn't block the event loop.
    """
    # Lazy import to avoid heavy startup imports / circular references.
    from app.services import rag_service

    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "")

    if not text or not chat_id:
        return

    # Show "typing…" while the AI generates the reply.
    with typing_action(chat_id):
        reply_text, _snippets, detected_lang = rag_service.process_chat(
            message=text,
            language="auto",
            mode="beginner",
        )

    send_message(chat_id, reply_text)

    # Optionally send TTS audio when the message contains '/voice'.
    try:
        if "/voice" in text.lower():
            from app.services.voice_service import text_to_speech
            # Uploading audio can take a moment — show the matching status.
            with typing_action(chat_id, action="upload_voice"):
                audio_path = text_to_speech(reply_text, detected_lang, settings.AUDIO_OUTPUT_DIR)
                if audio_path:
                    send_audio(chat_id, audio_path, caption="Audio reply")
    except Exception as e:
        print(f"[Telegram] TTS error: {e}")


# ── Long-polling loop ─────────────────────────────────────────────────────────

async def poll_updates() -> None:
    """Continuously fetch updates from Telegram via long polling."""
    if not BOT_TOKEN:
        print("[Telegram] No bot token configured – polling disabled.")
        return

    url = _api_url("getUpdates")
    offset: Optional[int] = None
    # Use a client timeout slightly longer than the server long-poll window.
    timeout = httpx.Timeout(LONG_POLL_TIMEOUT + 10)

    print("📨 Telegram long polling started")
    async with httpx.AsyncClient(timeout=timeout) as client:
        while True:
            params: dict[str, Any] = {
                "timeout": LONG_POLL_TIMEOUT,
                "allowed_updates": ["message", "edited_message"],
            }
            if offset is not None:
                params["offset"] = offset

            try:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[Telegram] getUpdates error: {e}")
                await asyncio.sleep(3)  # back off before retrying
                continue

            for update in data.get("result", []):
                # Advance the offset so each update is acknowledged once.
                offset = update["update_id"] + 1
                msg = update.get("message") or update.get("edited_message")
                if not msg:
                    continue
                try:
                    await asyncio.to_thread(_handle_message, msg)
                except Exception as e:
                    print(f"[Telegram] handler error: {e}")


def start_polling() -> None:
    """Launch the polling loop as a background asyncio task."""
    global _poll_task
    if not BOT_TOKEN:
        print("[Telegram] No bot token configured – polling not started.")
        return
    if _poll_task and not _poll_task.done():
        return
    _poll_task = asyncio.create_task(poll_updates())


async def stop_polling() -> None:
    """Cancel the background polling task, if running."""
    global _poll_task
    if _poll_task and not _poll_task.done():
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass
    _poll_task = None

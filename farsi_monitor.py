import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage
)
from deep_translator import GoogleTranslator

# ─── CONFIG ────────────────────────────────────────────────────────────────────
load_dotenv()

API_ID       = int(os.getenv("TELEGRAM_API_ID"))
API_HASH     = os.getenv("TELEGRAM_API_HASH")
PHONE        = os.getenv("TELEGRAM_PHONE")
CHANNEL      = os.getenv("TELEGRAM_CHANNEL")
SESSION_NAME = "farsi_monitor"
LIMIT        = 200                # Number of past messages to fetch (None = all)

OUTPUT_DIR   = Path("output")
MEDIA_DIR    = OUTPUT_DIR / "media"
OUTPUT_JSON  = OUTPUT_DIR / "messages.json"
OUTPUT_HTML  = OUTPUT_DIR / "messages.html"
# ───────────────────────────────────────────────────────────────────────────────

translator = GoogleTranslator(source="fa", target="en")


def translate_text(text: str) -> str:
    if not text or not text.strip():
        return ""
    try:
        chunk_size = 4500
        if len(text) <= chunk_size:
            return translator.translate(text)
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        return " ".join([translator.translate(c) for c in chunks])
    except Exception as e:
        return f"[Translation error: {e}]"


def format_entities(text: str, entities) -> str:
    """Convert Telegram message entities (bold, italic, code, links) to HTML."""
    import html
    if not text:
        return ""
    if not entities:
        return html.escape(text).replace("\n", "<br>")

    from telethon.tl.types import (
        MessageEntityBold, MessageEntityItalic, MessageEntityCode,
        MessageEntityPre, MessageEntityUrl, MessageEntityTextUrl,
        MessageEntityMention, MessageEntityHashtag
    )

    tags = []
    for ent in entities:
        s, l = ent.offset, ent.length
        seg_esc = html.escape(text[s:s+l])
        if isinstance(ent, MessageEntityBold):
            tags.append((s, s+l, "<b>", "</b>"))
        elif isinstance(ent, MessageEntityItalic):
            tags.append((s, s+l, "<i>", "</i>"))
        elif isinstance(ent, MessageEntityCode):
            tags.append((s, s+l, "<code>", "</code>"))
        elif isinstance(ent, MessageEntityPre):
            tags.append((s, s+l, "<pre>", "</pre>"))
        elif isinstance(ent, MessageEntityTextUrl):
            tags.append((s, s+l, f'<a href="{ent.url}" target="_blank">', "</a>"))
        elif isinstance(ent, MessageEntityUrl):
            tags.append((s, s+l, f'<a href="{seg_esc}" target="_blank">', "</a>"))
        elif isinstance(ent, MessageEntityMention):
            tags.append((s, s+l, '<span class="mention">', "</span>"))
        elif isinstance(ent, MessageEntityHashtag):
            tags.append((s, s+l, '<span class="hashtag">', "</span>"))

    output = html.escape(text)
    for s, e, open_t, close_t in sorted(tags, key=lambda x: x[0], reverse=True):
        seg = html.escape(text[s:e])
        output = output[:s] + open_t + seg + close_t + output[e:]

    return output.replace("\n", "<br>")


def generate_html(messages, channel_title, output_path):
    html_messages = []
    for m in reversed(messages):  # Oldest first
        media_block = ""
        if m["media_type"] == "photo" and m["media_path"]:
            media_block = f'<img src="{m["media_path"]}" class="msg-photo" alt="photo">'
        elif m["media_type"] == "image_doc" and m["media_path"]:
            media_block = f'<img src="{m["media_path"]}" class="msg-photo" alt="image">'
        elif m["media_type"] == "video":
            media_block = '<div class="media-placeholder">🎥 Video (not downloaded)</div>'
        elif m["media_type"] == "webpage" and m.get("media_url"):
            media_block = f'<div class="webpage-preview"><a href="{m["media_url"]}" target="_blank">🔗 {m["media_url"]}</a></div>'

        text_block = ""
        if m["formatted_html"]:
            text_block = f'''
            <div class="msg-text original" dir="rtl">{m["formatted_html"]}</div>
            <div class="msg-divider">🔽 English Translation</div>
            <div class="msg-text translated">{m["translated_en"]}</div>
            '''
        elif not m["formatted_html"] and m["media_type"]:
            # Media with no caption
            text_block = '<div class="msg-text translated" style="color:#555">[No caption]</div>'

        meta_views = f'👁 {m["views"]}' if m["views"] else ""
        reply_badge = f'<span class="reply-badge">↩ Reply to #{m["reply_to"]}</span>' if m["reply_to"] else ""

        html_messages.append(f'''
        <div class="message" id="msg-{m["id"]}">
            <div class="msg-meta">
                <span class="msg-id">#{m["id"]}</span>
                <span class="msg-date">{m["date"]}</span>
                {reply_badge}
                <span class="msg-views">{meta_views}</span>
            </div>
            {media_block}
            {text_block}
        </div>
        ''')

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{channel_title} — Farsi → English</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0e0e0e;
            color: #e0e0e0;
            max-width: 780px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{ color: #29b6f6; border-bottom: 1px solid #333; padding-bottom: 10px; }}
        .stats {{ color: #555; font-size: 0.85em; margin-bottom: 24px; }}
        .message {{
            background: #1a1a2e;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 16px;
            border-left: 3px solid #29b6f6;
        }}
        .msg-meta {{
            font-size: 0.75em;
            color: #888;
            margin-bottom: 8px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
        }}
        .msg-id {{ color: #29b6f6; font-weight: bold; }}
        .reply-badge {{
            background: #1e3a5f;
            padding: 2px 6px;
            border-radius: 4px;
            color: #90caf9;
        }}
        .msg-photo {{
            max-width: 100%;
            border-radius: 8px;
            margin: 8px 0;
            display: block;
        }}
        .msg-text {{
            padding: 6px 0;
            line-height: 1.8;
            font-size: 0.97em;
        }}
        .original {{
            color: #ffcc80;
            font-size: 1.05em;
            border-right: 3px solid #ff8f00;
            padding-right: 10px;
        }}
        .msg-divider {{
            color: #444;
            font-size: 0.75em;
            margin: 6px 0;
            letter-spacing: 0.05em;
        }}
        .translated {{ color: #a5d6a7; }}
        .media-placeholder {{
            color: #777;
            font-style: italic;
            padding: 8px 0;
        }}
        .webpage-preview {{
            background: #111;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 6px 0;
            border: 1px solid #2a2a2a;
        }}
        .webpage-preview a {{ color: #29b6f6; text-decoration: none; }}
        .mention {{ color: #80cbc4; }}
        .hashtag {{ color: #ce93d8; }}
        code {{
            background: #2a2a2a;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #ef9a9a;
        }}
        pre {{
            background: #2a2a2a;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }}
        b {{ color: #ffffff; }}
        a {{ color: #29b6f6; }}
    </style>
</head>
<body>
    <h1>📡 {channel_title}</h1>
    <p class="stats">Farsi → English &nbsp;|&nbsp; {len(messages)} messages fetched</p>
    {"".join(html_messages)}
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


async def fetch_and_translate():
    OUTPUT_DIR.mkdir(exist_ok=True)
    MEDIA_DIR.mkdir(exist_ok=True)

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start(phone=PHONE)

    print(f"[+] Connected. Fetching messages from: {CHANNEL}")
    channel = await client.get_entity(CHANNEL)
    channel_title = getattr(channel, "title", str(CHANNEL))

    results = []

    async for message in client.iter_messages(channel, limit=LIMIT):
        entry = {
            "id":           message.id,
            "date":         message.date.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "original_fa":  message.text or "",
            "translated_en": "",
            "formatted_html": "",
            "media_type":   None,
            "media_path":   None,
            "media_url":    None,
            "views":        getattr(message, "views", None),
            "forwards":     getattr(message, "forwards", None),
            "reply_to":     message.reply_to_msg_id if message.reply_to else None,
        }

        # Translate text/caption
        if message.text:
            entry["translated_en"]  = translate_text(message.text)
            entry["formatted_html"] = format_entities(message.text, message.entities)

        # Handle media
        if message.media:
            if isinstance(message.media, MessageMediaPhoto):
                entry["media_type"] = "photo"
                try:
                    filename = MEDIA_DIR / f"{message.id}.jpg"
                    await client.download_media(message, file=str(filename))
                    entry["media_path"] = f"media/{message.id}.jpg"
                    print(f"  [+] Photo saved: {filename}")
                except Exception as e:
                    print(f"  [!] Photo error: {e}")

            elif isinstance(message.media, MessageMediaDocument):
                doc  = message.media.document
                mime = getattr(doc, "mime_type", "")
                if mime.startswith("image/"):
                    entry["media_type"] = "image_doc"
                    ext = mime.split("/")[-1]
                    try:
                        filename = MEDIA_DIR / f"{message.id}.{ext}"
                        await client.download_media(message, file=str(filename))
                        entry["media_path"] = f"media/{message.id}.{ext}"
                    except Exception as e:
                        print(f"  [!] Image doc error: {e}")
                elif mime.startswith("video/"):
                    entry["media_type"] = "video"  # Skipped — too large
                else:
                    entry["media_type"] = f"document ({mime})"

            elif isinstance(message.media, MessageMediaWebPage):
                wp = message.media.webpage
                entry["media_type"] = "webpage"
                entry["media_url"]  = getattr(wp, "url", None)

        results.append(entry)
        print(f"  [MSG {message.id}] {entry['date']} | type={entry['media_type'] or 'text'}")

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[+] JSON saved  → {OUTPUT_JSON}")

    # Generate HTML
    generate_html(results, channel_title, OUTPUT_HTML)
    print(f"[+] HTML saved  → {OUTPUT_HTML}")
    print(f"[+] Open in browser: firefox {OUTPUT_HTML}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(fetch_and_translate())


"""
Facebook messages JSON ingestion parser.
Handles safe character transcoding, message filtering, and canonical normalization.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field


# Word-boundary regex matching "An An" with arbitrary internal whitespace,
# strictly bounded by word boundaries to reject names like "Nguyễn Văn An".
AN_AN_REGEX = re.compile(r"\ban\s+an\b", re.IGNORECASE)


class CanonicalMessage(BaseModel):
    """
    Standardized internal representation of a chat message.
    Conforms directly to PROJECT.md interface contract and test specification.
    """
    sender_name: str
    text: str
    timestamp_ms: int
    is_an_an: bool
    reactions: List[str] = Field(default_factory=list)
    is_unsent: bool = False
    media: List[Any] = Field(default_factory=list)
    msg_type: str = "text"


def safe_decode_mojibake(text: Optional[str]) -> str:
    """
    Safely repairs double-encoded Latin-1 mojibake without crashing on native UTF-8.
    
    If text contains Latin-1 mojibake (typical of official Meta DYI exports),
    it recovers the original UTF-8 representation.
    If text is already clean UTF-8 (such as An An_86.json), it catches
    UnicodeEncodeError/UnicodeDecodeError and returns the original text untouched.
    
    Args:
        text: Raw string from JSON or other sources.
        
    Returns:
        Cleaned, properly decoded UTF-8 string.
    """
    if text is None or not isinstance(text, str):
        return ""
    if not text:
        return ""
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


# Alias for backward and forward compatibility with design spec
fix_fb_text = safe_decode_mojibake


def parse_facebook_json(file_path: Union[str, Path]) -> List[CanonicalMessage]:
    """
    Parses a Facebook messages JSON export file into a list of CanonicalMessage objects.
    
    Processing steps:
    1. Validates file existence and loads JSON with utf-8 encoding.
    2. Validates top-level JSON structure (requires 'messages' array).
    3. Transcodes text safely via safe_decode_mojibake().
    4. Filters out unsent messages, failed downloads, and empty/media-only messages.
    5. Filters system call notifications and placeholders.
    6. Normalizes sender names and reaction emojis.
    7. Sorts all messages in ascending chronological order by timestamp_ms.
    
    Args:
        file_path: Path to the Facebook messages JSON file.
        
    Returns:
        List of valid, filtered, sorted CanonicalMessage instances.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If JSON is malformed or missing the 'messages' key.
    """
    target_path = Path(file_path)
    if not target_path.exists():
        raise FileNotFoundError(f"Facebook messages file not found: {target_path}")

    try:
        with open(target_path, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"Empty JSON file: {target_path}")
            data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in file {target_path}: {exc}") from exc

    if not isinstance(data, dict) or "messages" not in data or not isinstance(data["messages"], list):
        raise ValueError(f"Invalid Facebook JSON format: missing 'messages' list in {target_path}")

    canonical_messages: List[CanonicalMessage] = []

    for item in data["messages"]:
        if not isinstance(item, dict):
            continue

        # 1. Unsent message filter
        is_unsent = bool(item.get("isUnsent") or item.get("is_unsent") or False)
        
        # 2. Extract and transcode message text
        raw_text = item.get("text")
        if raw_text is None:
            raw_text = item.get("content")
        if raw_text is None or not isinstance(raw_text, str):
            continue
        clean_text = safe_decode_mojibake(raw_text).strip()

        # Drop unsent messages or explicit unsent markers
        if is_unsent or clean_text == "User unsent a message":
            continue

        # Drop failed media artifacts
        if "failed to download media" in clean_text.lower():
            continue

        # Drop empty strings or media-only messages without accompanying text
        if not clean_text or clean_text == "None":
            continue

        # 3. Check message type for system call events or placeholders
        raw_type = str(item.get("type") or item.get("msg_type") or "text").lower()
        if raw_type in ("call", "placeholder") or "missed a call" in clean_text.lower():
            continue

        # 4. Extract sender name
        raw_sender = item.get("senderName") or item.get("sender_name") or "Unknown"
        sender = safe_decode_mojibake(str(raw_sender)).strip()

        # Determine if sender is An An (exact match or word-boundary regex)
        is_an_an = bool(AN_AN_REGEX.search(sender))

        # 5. Extract timestamp in milliseconds
        raw_ts = item.get("timestamp")
        if raw_ts is None:
            raw_ts = item.get("timestamp_ms", 0)
        try:
            timestamp_ms = int(raw_ts)
        except (ValueError, TypeError, OverflowError):
            timestamp_ms = 0

        # 6. Extract reactions
        raw_reactions = item.get("reactions") or []
        reactions: List[str] = []
        if isinstance(raw_reactions, list):
            for r in raw_reactions:
                if isinstance(r, dict) and "reaction" in r:
                    cleaned_reaction = safe_decode_mojibake(r["reaction"]).strip()
                    if cleaned_reaction:
                        reactions.append(cleaned_reaction)
                elif isinstance(r, str):
                    cleaned_reaction = safe_decode_mojibake(r).strip()
                    if cleaned_reaction:
                        reactions.append(cleaned_reaction)

        # 7. Extract media references if present
        raw_media = item.get("media") or []
        media_list = raw_media if isinstance(raw_media, list) else []

        canonical_messages.append(
            CanonicalMessage(
                sender_name=sender,
                text=clean_text,
                timestamp_ms=timestamp_ms,
                is_an_an=is_an_an,
                reactions=reactions,
                is_unsent=False,
                media=media_list,
                msg_type=raw_type
            )
        )

    # Sort deterministically by timestamp ascending (oldest to newest)
    canonical_messages.sort(key=lambda m: m.timestamp_ms)
    return canonical_messages

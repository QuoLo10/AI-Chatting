"""
Dynamic Response Length Controller for An An Persona Chatbot.

Analyzes user input intent, conversational context, and word length
to select the optimal response length tier (SHORT, MEDIUM, LONG),
enforces completion token caps, and injects strict Vietnamese
guidance instructions.
"""

import re
from enum import Enum
from typing import List, Optional, Union, Dict, Any, Tuple
from pydantic import BaseModel, Field


class LengthTier(str, Enum):
    """
    Empirical length tiers matching An An's messaging distribution in Facebook chat logs.
    """
    SHORT = "short"     # 1-5 words, max_tokens=35 (matches ~70.0% of An An messages)
    MEDIUM = "medium"   # 6-15 words, max_tokens=75 (matches ~27.6% of An An messages)
    LONG = "long"       # 20-50 words, max_tokens=160 (matches ~2.4% of An An messages)


class LengthDecision(BaseModel):
    """
    Result of dynamic length analysis for a conversational turn.
    """
    tier: LengthTier = Field(
        ...,
        description="Selected response length tier (short, medium, long)."
    )
    max_tokens: int = Field(
        ...,
        description="Physical upper bound for LLM completion tokens."
    )
    guidance_instruction: str = Field(
        ...,
        description="Prompt directive commanding length, style, and prohibiting AI artifacts."
    )
    min_words: int = Field(
        default=1,
        description="Expected lower bound on word count."
    )
    max_words: int = Field(
        default=5,
        description="Expected upper bound on word count."
    )
    empirical_ratio: float = Field(
        default=0.70,
        description="Expected empirical distribution percentage in target persona."
    )


# -----------------------------------------------------------------------------
# Configuration Constants
# -----------------------------------------------------------------------------
TIER_TOKEN_LIMITS: Dict[LengthTier, int] = {
    LengthTier.SHORT: 35,
    LengthTier.MEDIUM: 75,
    LengthTier.LONG: 160,
}

TIER_WORD_BOUNDS: Dict[LengthTier, Tuple[int, int]] = {
    LengthTier.SHORT: (1, 5),
    LengthTier.MEDIUM: (6, 15),
    LengthTier.LONG: (20, 50),
}

TIER_EMPIRICAL_RATIOS: Dict[LengthTier, float] = {
    LengthTier.SHORT: 0.700,
    LengthTier.MEDIUM: 0.276,
    LengthTier.LONG: 0.024,
}

TIER_GUIDANCE_INSTRUCTIONS: Dict[LengthTier, str] = {
    LengthTier.SHORT: (
        "YÊU CẦU ĐỘ DÀI: CỰC NGẮN (1 - 5 TỪ / 1-5 từ).\n"
        "- Phản hồi siêu ngắn gọn, cộc lốc, tự nhiên bằng Tiếng Việt (1 đến 5 từ / 1-5 từ), "
        "giống hệt phong cách nhắn tin Facebook nhanh của An An (ví dụ: 'oki', 'ừ', '=)))', 'kh nha', 'g9 nha b', 'chốt').\n"
        "- TUYỆT ĐỐI KHÔNG giải thích dài dòng, KHÔNG dùng gạch đầu dòng / bullet points / danh sách.\n"
        "- TUYỆT ĐỐI KHÔNG thêm lời chào khách sáo hay câu từ rập khuôn của trợ lý ảo (như 'Tôi có thể giúp gì', 'Dạ', 'ạ')."
    ),
    LengthTier.MEDIUM: (
        "YÊU CẦU ĐỘ DÀI: TRUNG BÌNH (6 - 15 TỪ / 6-15 từ).\n"
        "- Phản hồi tự nhiên bằng Tiếng Việt từ 6 đến 15 từ (1 - 2 câu ngắn gọn), "
        "thể hiện đúng phong cách sinh viên mỹ thuật của An An.\n"
        "- Sử dụng đúng từ viết tắt đặc trưng ('kh', 'dc', 'nma', 'r', 'v', 'z', '=)))').\n"
        "- TUYỆT ĐỐI KHÔNG dùng gạch đầu dòng, bullet points, hay cấu trúc bài luận.\n"
        "- TUYỆT ĐỐI KHÔNG đưa lời xin lỗi, khuyến cáo, từ chối trách nhiệm hoặc phong cách trợ lý ảo AI."
    ),
    LengthTier.LONG: (
        "YÊU CẦU ĐỘ DÀI: DÀI / TÂM SỰ (20 - 50 TỪ / 20-50 từ).\n"
        "- Phản hồi sâu sắc, chân thành hoặc đặt ranh giới tình cảm rõ ràng bằng Tiếng Việt tự nhiên (từ 20 đến 50 từ, tối đa 2-3 câu).\n"
        "- Giữ giọng điệu ấm áp, đồng cảm nhưng dứt khoát của An An khi nói về mối quan hệ, chuyện nghiêm túc hoặc tâm sự bạn bè.\n"
        "- TUYỆT ĐỐI KHÔNG viết văn nghị luận / tiểu luận AI, KHÔNG dùng gạch đầu dòng / bullet points.\n"
        "- TUYỆT ĐỐI KHÔNG dùng văn mẫu đạo lý sáo rỗng hay lời tuyên bố / xin lỗi của trợ lý ảo."
    ),
}

# -----------------------------------------------------------------------------
# Regex Catalogs
# -----------------------------------------------------------------------------
RE_EMOTIONAL_CONFESSION = re.compile(
    r"("
    r"thích an|yêu an|thương an|tỏ tình|làm người yêu|muốn hẹn hò|thích bạn|"
    r"(?:muốn\s+)?(?:đc|được|ở)\s+bên\s+an|(?:muốn\s+(?:đc\s+|được\s+)?)?bên\s+cạnh\s+an|"
    r"tình cảm|crush|thổ lộ|làm bạn gái|thích m|iu an|"
    r"làm bạn thôi|mối quan hệ|người cũ|người iu cũ|ex|khoảng cách|rào cản|giới hạn|"
    r"chúng mình là gì|mình với an|chia tay|tổn thương|"
    r"áp lực quá|trầm cảm|bế tắc|muốn biến mất|tâm sự thật lòng|nói chuyện nghiêm túc|"
    r"khóc nhiều|buồn nhiều lắm|tuyệt vọng|mệt mỏi|nghĩ lại"
    r")",
    re.IGNORECASE
)


def _extract_text_from_history_item(item: Any) -> str:
    """Extracts raw text from heterogeneous conversation history formats."""
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("content") or item.get("text") or "")
    if hasattr(item, "content"):
        return str(item.content)
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return str(item[1])
    return ""


def _has_recent_emotional_context(conversation_history: Optional[list]) -> bool:
    """Checks if the recent turns involved emotional confession or boundary setting."""
    if not conversation_history or not isinstance(conversation_history, list):
        return False
    recent_items = conversation_history[-4:]
    for item in recent_items:
        text = _extract_text_from_history_item(item)
        if RE_EMOTIONAL_CONFESSION.search(text):
            return True
    return False


def determine_response_length(
    user_input: str,
    conversation_history: Optional[list] = None
) -> LengthDecision:
    """
    Analyzes user input intent, word count, and conversation context to select
    the optimal An An response length tier (SHORT, MEDIUM, LONG).

    Args:
        user_input: The raw incoming text message from the user.
        conversation_history: Optional list of past messages in the session.

    Returns:
        LengthDecision: Specifying the tier, max_tokens, guidance_instruction, min_words, max_words, empirical_ratio.
    
    Raises:
        TypeError: If user_input is None or not a string.
    """
    if user_input is None or not isinstance(user_input, str):
        raise TypeError(f"user_input must be a string, got {type(user_input).__name__}")

    clean_input = user_input.strip()
    words = clean_input.split()
    word_count = len(words)

    # -------------------------------------------------------------------------
    # Priority 1: Check LONG conditions (>25 words, confession, emotional crisis, or history context)
    # -------------------------------------------------------------------------
    if word_count > 25:
        tier = LengthTier.LONG
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    if RE_EMOTIONAL_CONFESSION.search(clean_input):
        tier = LengthTier.LONG
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    if _has_recent_emotional_context(conversation_history):
        # In an emotional context, follow-ups continue in LONG tier
        if "?" in clean_input or word_count >= 4 or any(w in clean_input.lower() for w in ["sao", "nghĩ", "sao?", "kh"]):
            tier = LengthTier.LONG
            return LengthDecision(
                tier=tier,
                max_tokens=TIER_TOKEN_LIMITS[tier],
                guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
                min_words=TIER_WORD_BOUNDS[tier][0],
                max_words=TIER_WORD_BOUNDS[tier][1],
                empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
            )

    # -------------------------------------------------------------------------
    # Priority 2: Check SHORT conditions (empty, non-text/punctuation/emoji, <=4 words)
    # -------------------------------------------------------------------------
    if word_count == 0 or not any(c.isalnum() for c in clean_input):
        tier = LengthTier.SHORT
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    if word_count <= 4:
        tier = LengthTier.SHORT
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    # -------------------------------------------------------------------------
    # Priority 3: Normal turn fallback to MEDIUM (5 to 25 words)
    # -------------------------------------------------------------------------
    tier = LengthTier.MEDIUM
    return LengthDecision(
        tier=tier,
        max_tokens=TIER_TOKEN_LIMITS[tier],
        guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
        min_words=TIER_WORD_BOUNDS[tier][0],
        max_words=TIER_WORD_BOUNDS[tier][1],
        empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
    )

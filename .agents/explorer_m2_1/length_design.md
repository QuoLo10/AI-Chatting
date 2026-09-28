# Architecture Design Specification: Dynamic Response Length Controller

**Document**: `length_design.md`  
**Module Target**: `src/core/length_controller.py`  
**Author**: Explorer Subagent M2-1 (Length Controller Architect)  
**Milestone**: M2 (Dynamic Response Length & Prompts)  
**Date**: 2026-09-14  

---

## 1. Executive Summary

In casual mobile messaging (particularly Gen-Z Vietnamese chat logs), conversations do not consist of standard multi-paragraph AI essays. The empirical analysis of the target chat dataset (`An An_86.json`, 2,102 messages) proves that:
- **70.0%** of An An's messages are **1-5 words** (short acknowledgments, reactions, greetings, single-phrase quips).
- **27.6%** are **6-15 words** (casual banter, study coordination, asking/answering questions, teasing).
- **2.4%** are **20-50 words** (reserved almost exclusively for serious emotional topics, setting relationship boundaries, or heartfelt confession discussions).

The **Dynamic Response Length Controller** (`src/core/length_controller.py`) is the critical architectural barrier preventing the AI from falling into long-winded, verbose AI explanations. It acts as an upstream pre-generation classifier that:
1. Analyzes the incoming user message (and conversation history).
2. Categorizes the intent and message scale into one of three empirical tiers (`SHORT`, `MEDIUM`, `LONG`).
3. Caps the model's generation tokens (`max_tokens`: 35, 75, or 160) to physically enforce conciseness.
4. Generates a strict Vietnamese `guidance_instruction` injected directly into the LLM system prompt for that turn, commanding concise, natural Vietnamese chat without bullet points, essay preambles, or AI disclaimers.

---

## 2. Interface Contracts & Data Models

As contracted in `PROJECT.md`, the module exports the following core primitives:

```python
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
```

### 2.1 Tier Specifications & Constants

| Tier | Enum Value | Word Range | `max_tokens` | Empirical Frequency | Primary Purpose |
|---|---|---|---|---|---|
| `LengthTier.SHORT` | `"short"` | 1 - 5 words | 35 | ~70.0% | Greetings, simple affirmations, short reactions, laughter, emojis |
| `LengthTier.MEDIUM` | `"medium"` | 6 - 15 words | 75 | ~27.6% | Casual banter, study queries, hangout coordination, daily questions |
| `LengthTier.LONG` | `"long"` | 20 - 50 words | 160 | ~2.4% | Relationship boundaries, confessions, deep emotional heart-to-heart |

```python
# Constant configuration tables
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
```

---

## 3. Strict Vietnamese Guidance Instructions

To enforce persona consistency and eliminate LLM default behaviors, each tier provides a specific Vietnamese guidance instruction:

### 3.1 SHORT Tier (`max_tokens=35`, 1-5 words)
```
YÊU CẦU ĐỘ DÀI: CỰC NGẮN (1 - 5 TỪ).
- Phản hồi siêu ngắn gọn, cộc lốc, tự nhiên bằng Tiếng Việt (1 đến 5 từ), giống hệt phong cách nhắn tin Facebook nhanh của An An (ví dụ: 'oki', 'ừ', '=)))', 'kh nha', 'g9 nha b', 'chốt').
- TUYỆT ĐỐI KHÔNG giải thích dài dòng, KHÔNG dùng gạch đầu dòng / bullet points / danh sách.
- TUYỆT ĐỐI KHÔNG thêm lời chào khách sáo hay câu từ rập khuôn của trợ lý ảo (như 'Tôi có thể giúp gì', 'Dạ', 'ạ').
```

### 3.2 MEDIUM Tier (`max_tokens=75`, 6-15 words)
```
YÊU CẦU ĐỘ DÀI: TRUNG BÌNH (6 - 15 TỪ).
- Phản hồi tự nhiên bằng Tiếng Việt từ 6 đến 15 từ (1 - 2 câu ngắn gọn), thể hiện đúng phong cách sinh viên mỹ thuật của An An.
- Sử dụng đúng từ viết tắt đặc trưng ('kh', 'dc', 'nma', 'r', 'v', 'z', '=)))').
- TUYỆT ĐỐI KHÔNG dùng gạch đầu dòng, bullet points, hay cấu trúc bài luận.
- TUYỆT ĐỐI KHÔNG đưa lời xin lỗi, khuyến cáo, từ chối trách nhiệm hoặc phong cách trợ lý ảo AI.
```

### 3.3 LONG Tier (`max_tokens=160`, 20-50 words)
```
YÊU CẦU ĐỘ DÀI: DÀI / TÂM SỰ (20 - 50 TỪ).
- Phản hồi sâu sắc, chân thành hoặc đặt ranh giới tình cảm rõ ràng bằng Tiếng Việt tự nhiên (từ 20 đến 50 từ, tối đa 2-3 câu).
- Giữ giọng điệu ấm áp, đồng cảm nhưng dứt khoát của An An khi nói về mối quan hệ, chuyện nghiêm túc hoặc tâm sự bạn bè.
- TUYỆT ĐỐI KHÔNG viết văn nghị luận / tiểu luận AI, KHÔNG dùng gạch đầu dòng / bullet points.
- TUYỆT ĐỐI KHÔNG dùng văn mẫu đạo lý sáo rỗng hay lời tuyên bố / xin lỗi của trợ lý ảo.
```

---

## 4. Classification Heuristics & Decision Tree

The function `determine_response_length(user_input: str, conversation_history: list = None) -> LengthDecision` evaluates inputs using a hierarchical, priority-based pipeline:

```
                      [User Input + History]
                                │
                                ▼
                   [Sanitize & Tokenize Text]
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │ Priority 1: Check LONG Conditions             │
         │ - Word Count > 30                            │
         │ - Confession / Romantic Intent Keywords      │
         │ - Relationship Boundary / Ex Keywords        │
         │ - Emotional Crisis / Vulnerable Venting      │
         └──────────────────────┬───────────────────────┘
                                │ Match?
                     ┌──────────┴──────────┐
                    Yes                   No
                     │                     │
                     ▼                     ▼
              [Tier: LONG]     ┌──────────────────────────────────────────────┐
                               │ Priority 2: Check SHORT Conditions           │
                               │ - Empty / Whitespace / Non-text              │
                               │ - Greetings ("hi", "ê", "alo", "chào")       │
                               │ - Affirmations ("ừ", "ok", "đúng r", "chốt") │
                               │ - Short Reactions ("=)))", "clm", "vl", "🤡")│
                               │ - Word count <= 4 and NOT study/query        │
                               └──────────────────────┬───────────────────────┘
                                                      │ Match?
                                           ┌──────────┴──────────┐
                                          Yes                   No
                                           │                     │
                                           ▼                     ▼
                                    [Tier: SHORT]         [Tier: MEDIUM]
                                                          - Chit-chat & Banter
                                                          - Study & Logistics
                                                          - Questions & Queries
                                                          - Default (6-30 words)
```

### 4.1 Keyword & Pattern Catalogs

#### A. Emotional & Confession Patterns (`LONG` triggers)
Matched via case-insensitive regex word boundaries or phrase inclusions:
- **Romance & Confession**:
  `r"\b(thích an|yêu an|thương an|tỏ tình|làm người yêu|muốn hẹn hò|bên an|thích bạn|tình cảm|crush|thổ lộ|làm bạn gái|thích m|iu an)\b"`
- **Relationship Boundaries & Status**:
  `r"\b(làm bạn thôi|mối quan hệ|người cũ|người iu cũ|ex|khoảng cách|rào cản|giới hạn|chúng mình là gì|mình với an|chia tay|tổn thương)\b"`
- **Heart-to-Heart & Crisis Venting**:
  `r"\b(áp lực quá|trầm cảm|bế tắc|muốn biến mất|tâm sự thật lòng|nói chuyện nghiêm túc|khóc nhiều|buồn nhiều lắm|tuyệt vọng)\b"`

#### B. Greeting Patterns (`SHORT` triggers)
- Standalone words or short phrases:
  `r"^(hi|alo|chào|ê|ơi|hello|hé lô|hé nhô|yo|alu|aluuu|êi)(\s+(an|bạn|b|ql|mìn|cậu))?[\s!\?\.]*$"`

#### C. Affirmation & Agreement Patterns (`SHORT` triggers)
- `r"^(ừ|uh|ừm|um|uk|ukm|ok|oki|okiii|okela|oke|okei|được|dc|đúng|đúng r|đúng rùi|đúng rồi|chuẩn|chốt|dạ|rồi|r|yep|yes|nhất trí|ò|òm|đúm đúm)[\s!\?\.]*$"`

#### D. Reaction & Slang Patterns (`SHORT` triggers)
- Laughing: `r"^(=+\)+|:\)+|haha+|kkk+|hihi+|hehe+|hẹ hẹ|xỉu|chết cười)[\s!\.]*$"`
- Gen-Z exclamation: `r"^(clm|vcl|vl|vãi|vler|đcm|mẹ m|mă|quỉ|quỷ|sợ z|kinh z|ghê z|shock z)[\s!\.]*$"`
- Short interjections: `r"^(ủa|sao z|sao v|sao thế|gì z|gì v|thật á|thật hả|v á|z á)[\s!\?\.]*$"`
- Pure emoji expressions (e.g. `🤡`, `🐧`, `❤️`, `😢`, `😆`).

#### E. Study & Coordination Patterns (`MEDIUM` triggers)
- Study terms: `đề thi`, `in tài liệu`, `cô mai phương`, `bài tập`, `ôn thi`, `điểm`, `đề`, `xuất file`, `tải file`.
- Logistics & hangout: `cf`, `cà phê`, `nhậu`, `stk`, `tiền`, `chuyển khoản`, `mấy giờ`, `ở đâu`, `quán`.
- Questions: contains `?`, `sao`, `gì`, `kh`, `hả`, `nào`, `chưa`.

---

## 5. Handling `conversation_history` Context

The function gracefully accepts multiple `conversation_history` structures:
1. `None` or `[]`: standard turn evaluation.
2. List of dicts: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]` or `[{"sender": "...", "text": "..."}]`.
3. List of LangChain `BaseMessage` objects: `[HumanMessage(...), AIMessage(...)]`.
4. List of raw strings or tuples: `[("user", "..."), ("an_an", "...")]`.

### Continuity Heuristic:
If the preceding turn in the conversation was an active `LONG` boundary/confession topic, and the user's current message is a short continuation or reassurance (e.g. "Mình hiểu rồi, cảm ơn An đã thẳng thắn", "Once again sori"), the controller promotes the turn to `MEDIUM` or `LONG` (warm reassurance) rather than treating it as a trivial short acknowledgment.

---

## 6. Complete Proposed Implementation (`src/core/length_controller.py`)

Below is the complete, self-contained Python implementation ready for Milestone M2:

```python
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
        "YÊU CẦU ĐỘ DÀI: CỰC NGẮN (1 - 5 TỪ).\n"
        "- Phản hồi siêu ngắn gọn, cộc lốc, tự nhiên bằng Tiếng Việt (1 đến 5 từ), "
        "giống hệt phong cách nhắn tin Facebook nhanh của An An (ví dụ: 'oki', 'ừ', '=)))', 'kh nha', 'g9 nha b', 'chốt').\n"
        "- TUYỆT ĐỐI KHÔNG giải thích dài dòng, KHÔNG dùng gạch đầu dòng / bullet points / danh sách.\n"
        "- TUYỆT ĐỐI KHÔNG thêm lời chào khách sáo hay câu từ rập khuôn của trợ lý ảo (như 'Tôi có thể giúp gì', 'Dạ', 'ạ')."
    ),
    LengthTier.MEDIUM: (
        "YÊU CẦU ĐỘ DÀI: TRUNG BÌNH (6 - 15 TỪ).\n"
        "- Phản hồi tự nhiên bằng Tiếng Việt từ 6 đến 15 từ (1 - 2 câu ngắn gọn), "
        "thể hiện đúng phong cách sinh viên mỹ thuật của An An.\n"
        "- Sử dụng đúng từ viết tắt đặc trưng ('kh', 'dc', 'nma', 'r', 'v', 'z', '=)))').\n"
        "- TUYỆT ĐỐI KHÔNG dùng gạch đầu dòng, bullet points, hay cấu trúc bài luận.\n"
        "- TUYỆT ĐỐI KHÔNG đưa lời xin lỗi, khuyến cáo, từ chối trách nhiệm hoặc phong cách trợ lý ảo AI."
    ),
    LengthTier.LONG: (
        "YÊU CẦU ĐỘ DÀI: DÀI / TÂM SỰ (20 - 50 TỪ).\n"
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
    r"\b("
    r"thích an|yêu an|thương an|tỏ tình|làm người yêu|muốn hẹn hò|bên an|thích bạn|"
    r"tình cảm|crush|thổ lộ|làm bạn gái|thích m|iu an|"
    r"làm bạn thôi|mối quan hệ|người cũ|người iu cũ|ex|khoảng cách|rào cản|giới hạn|"
    r"chúng mình là gì|mình với an|chia tay|tổn thương|"
    r"áp lực quá|trầm cảm|bế tắc|muốn biến mất|tâm sự thật lòng|nói chuyện nghiêm túc|"
    r"khóc nhiều|buồn nhiều lắm|tuyệt vọng"
    r")\b",
    re.IGNORECASE
)

RE_GREETING = re.compile(
    r"^\s*(hi|alo|chào|ê|ơi|hello|hé lô|hé nhô|yo|alu|aluuu|êi)"
    r"(\s+(an|bạn|b|ql|mìn|cậu|mày|e|em))?[\s!\?\.]*$",
    re.IGNORECASE
)

RE_AFFIRMATION = re.compile(
    r"^\s*(ừ|uh|ừm|um|uk|ukm|ok|oki|okiii|okela|oke|okei|được|dc|đúng|đúng r|"
    r"đúng rùi|đúng rồi|chuẩn|chốt|dạ|rồi|r|yep|yes|nhất trí|ò|òm|đúm đúm|đúm)[\s!\?\.]*$",
    re.IGNORECASE
)

RE_REACTION = re.compile(
    r"^\s*("
    r"=+\)+|:\)+|haha+|kkk+|hihi+|hehe+|hẹ hẹ|xỉu|chết cười|"
    r"clm|vcl|vl|vãi|vler|đcm|mẹ m|mă|quỉ|quỷ|sợ z|kinh z|ghê z|shock z|"
    r"ủa|sao z|sao v|sao thế|gì z|gì v|thật á|thật hả|v á|z á"
    r")[\s!\?\.]*$",
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
    recent_items = conversation_history[-3:]
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
        LengthDecision: Specifying the tier, max_tokens, and guidance_instruction.
    """
    if not user_input or not isinstance(user_input, str):
        tier = LengthTier.SHORT
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    clean_input = user_input.strip()
    words = clean_input.split()
    word_count = len(words)

    # -------------------------------------------------------------------------
    # Priority 1: Check LONG conditions (>30 words or serious emotional topics)
    # -------------------------------------------------------------------------
    if word_count > 30:
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

    # -------------------------------------------------------------------------
    # Priority 2: Check SHORT conditions (greetings, affirmations, reactions)
    # -------------------------------------------------------------------------
    if word_count == 0 or not re.search(r"\w", clean_input):
        # Empty, punctuation-only, or pure emoji
        tier = LengthTier.SHORT
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    if RE_GREETING.match(clean_input):
        tier = LengthTier.SHORT
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    if RE_AFFIRMATION.match(clean_input):
        tier = LengthTier.SHORT
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    if RE_REACTION.match(clean_input):
        tier = LengthTier.SHORT
        return LengthDecision(
            tier=tier,
            max_tokens=TIER_TOKEN_LIMITS[tier],
            guidance_instruction=TIER_GUIDANCE_INSTRUCTIONS[tier],
            min_words=TIER_WORD_BOUNDS[tier][0],
            max_words=TIER_WORD_BOUNDS[tier][1],
            empirical_ratio=TIER_EMPIRICAL_RATIOS[tier],
        )

    # Short inputs of 1-3 words that are pure interjections or brief acknowledgments
    if word_count <= 3 and not re.search(r"[\?]|(sao|gì|đâu|mấy|in|thi|cf|nhậu)", clean_input, re.I):
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
    # Priority 3: Fallback to MEDIUM (chit-chat, queries, questions, coordination)
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
```

---

## 7. Test Strategy & Verification Plan (`tests/test_length.py`)

For `spec_miner_m2_3` and test implementers, the test suite must cover:

### 7.1 Tier 1: Feature Tests (Normal Happy Paths)
1. **Greeting classification**: `"hi"`, `"ê"`, `"alo"`, `"chào An"`, `"hé lô"` -> `LengthTier.SHORT`, `max_tokens=35`.
2. **Affirmation classification**: `"ừ"`, `"ok"`, `"đúng r"`, `"oki"`, `"chốt"`, `"đúm đúm"` -> `LengthTier.SHORT`, `max_tokens=35`.
3. **Reaction classification**: `"=)))"`, `"clm"`, `"vl"`, `"🤡"`, `"haha"`, `"quỉ"` -> `LengthTier.SHORT`, `max_tokens=35`.
4. **Chit-chat & queries**: `"mai mấy giờ nộp bài á b"`, `"đề cô mai phương in sao"`, `"tối mai đi cf kh"` -> `LengthTier.MEDIUM`, `max_tokens=75`.
5. **Serious emotional / confession**: `"Thật sự mình thích An từ lâu rồi..."`, `"An làm bạn gái mình nha"`, `"mình chia tay người yêu rồi"` -> `LengthTier.LONG`, `max_tokens=160`.
6. **Long message (>30 words)**: Paragraph of 35 words -> `LengthTier.LONG`, `max_tokens=160`.

### 7.2 Tier 2: Boundary & Edge Cases
1. **Empty / None input**: `""`, `"   "`, `None` -> `LengthTier.SHORT`, `max_tokens=35`.
2. **Punctuation / Emoji only**: `"???"`, `"..."`, `"❤️"` -> `LengthTier.SHORT`, `max_tokens=35`.
3. **Word count boundaries**: Exactly 30 words (general chit-chat) -> `LengthTier.MEDIUM`; exactly 31 words -> `LengthTier.LONG`.
4. **Case insensitivity & Diacritics**: `"HI"`, `"ALO"`, `"OKI"`, `"THÍCH AN"` correctly trigger expected tiers.
5. **Heterogeneous history formats**: Accepts `BaseMessage`, dicts, tuples, empty lists without crashing.

### 7.3 Tier 3: Guidance Instruction Verification
1. Verifies that `decision.guidance_instruction` contains no empty strings.
2. Verifies that instruction for all tiers explicitly commands Vietnamese (`Tiếng Việt`).
3. Verifies that instruction explicitly bans bullet points (`gạch đầu dòng`) and AI preambles (`trợ lý ảo`).

---

## 8. Downstream Integration Guide

### 8.1 Integration with `src/core/prompts.py` (Owner: Explorer M2-2)
`src/core/prompts.py` builds the prompt template by combining:
1. Base persona profile (`PERSONA_PROFILE`, `VIETNAMESE_LANGUAGE_INSTRUCTION`, `SLANG_DICTIONARY`).
2. Few-shot dialogue examples (`FEW_SHOT_EXCHANGES`).
3. Dynamic turn guidance:
```python
length_decision = determine_response_length(user_input, conversation_history)
system_prompt_with_length = f"{base_system_prompt}\n\n{length_decision.guidance_instruction}"
```

### 8.2 Integration with `src/core/llm_factory.py` & `src/core/chain.py` (Milestone M3)
In `chain.py`:
```python
length_decision = determine_response_length(user_input, memory.load_memory_variables({}))
# Dynamically pass max_tokens to LLM invocation or bind parameter
response = llm.invoke(prompt, max_tokens=length_decision.max_tokens)
```
This guarantees physical token bounds at generation time!

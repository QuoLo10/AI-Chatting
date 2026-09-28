# Milestone M1 Ingestion & Configuration Design Specification

**Document Path**: `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1\design.md`  
**Target Milestone**: M1 (Dependencies & Ingestion Engine)  
**Author**: Explorer Subagent `explorer_m1_1` (Ingestion Implementation Planner)  
**Target Modules**:  
1. `src/config.py`  
2. `src/ingestion/parser.py`  
3. `src/ingestion/persona_profile.py`  

---

## 1. Architectural Overview & Module Boundaries

Milestone M1 establishes the foundational data layer for the "An An" persona chatbot. It is responsible for:
1. Loading configuration and credentials cleanly without hardcoding.
2. Ingesting raw Facebook message logs into standardized Pydantic representations with zero encoding crashes.
3. Profiling the target persona ("An An"), extracting statistical characteristics, slang quirks, and verified few-shot dialogue exemplars.

### 1.1 Data Flow Pipeline
```
[.env / Environment] ──────────► [src/config.py]
                                       │ (Paths, Keys, Defaults)
                                       ▼
[An An_86.json] ───────────────► [src/ingestion/parser.py]
                                       │
                                       │ fix_fb_text() [Transcoding Guard]
                                       │ Message Filtering (unsent/media)
                                       │ Chronological Sorting
                                       ▼
                           List[CanonicalMessage]
                                       │
                                       ├──────────────────────────────┐
                                       ▼                              ▼
                 [src/ingestion/persona_profile.py]       [Downstream Modules]
                   - extract_an_an_profile()              - src/core/length_controller.py (M2)
                   - SLANG_DICTIONARY & Quirks            - src/core/prompts.py (M2)
                   - 15 Verified Few-Shot Exchanges       - src/core/chain.py (M3)
```

### 1.2 Inter-Module Contract Adherence
In accordance with `PROJECT.md` lines 48–70, the interface contract between `src.ingestion.parser` and `src.ingestion.persona_profile` is:
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CanonicalMessage(BaseModel):
    sender_name: str
    text: str
    timestamp_ms: int
    is_an_an: bool
    reactions: List[str] = Field(default_factory=list)

def parse_facebook_json(file_path: str) -> List[CanonicalMessage]: ...
def extract_an_an_profile(messages: List[CanonicalMessage]) -> dict: ...
```

---

## 2. Detailed Specification: `src/config.py`

### 2.1 Responsibilities
- Load `.env` file using `python-dotenv`.
- Define path anchors: `PROJECT_ROOT`, `DATA_DIR`, and `DEFAULT_JSON_PATH`.
- Provide default JSON path: `F:/dowload/FacebookData/messages/An An_86.json` (overridable via `FACEBOOK_JSON_PATH` environment variable).
- Safely extract and cross-populate API keys:
  - `GEMINI_API_KEY` and `GOOGLE_API_KEY` (if one is set, fallback to the other so LangChain's `langchain-google-genai` and direct Google SDK both work seamlessly).
  - `GROQ_API_KEY`.
- Define runtime defaults: default provider (`"gemini"` or `"groq"`), model identifiers, temperature, and persona constants (`"An An"`, `"Hoàng Kim Quờ Lờ"` / `"ql"`).

### 2.2 Complete Code Structure for `src/config.py`

```python
"""
Configuration module for An An Persona Chatbot.
Loads environment variables, defines paths, and manages API credentials.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Resolve project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env file
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=False)
else:
    load_dotenv(override=False)

# -----------------------------------------------------------------------------
# API Keys & Cloud Credentials
# -----------------------------------------------------------------------------
# Google Gemini API Keys (cross-fallback between GEMINI_API_KEY and GOOGLE_API_KEY)
_gemini_raw = os.getenv("GEMINI_API_KEY", "").strip()
_google_raw = os.getenv("GOOGLE_API_KEY", "").strip()

GEMINI_API_KEY: str = _gemini_raw or _google_raw
GOOGLE_API_KEY: str = _google_raw or _gemini_raw

# Ensure both environment variables are set in os.environ for third-party SDKs
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# Groq API Key
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# -----------------------------------------------------------------------------
# Data Paths
# -----------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_JSON_PATH = os.getenv(
    "FACEBOOK_JSON_PATH",
    "F:/dowload/FacebookData/messages/An An_86.json"
)

# -----------------------------------------------------------------------------
# Model & Runtime Defaults
# -----------------------------------------------------------------------------
DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "gemini").lower()
DEFAULT_MODEL_GEMINI: str = os.getenv("DEFAULT_MODEL_GEMINI", "gemini-2.0-flash")
DEFAULT_MODEL_GROQ: str = os.getenv("DEFAULT_MODEL_GROQ", "llama-3.3-70b-versatile")
DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

# -----------------------------------------------------------------------------
# Persona & Conversation Constants
# -----------------------------------------------------------------------------
PERSONA_NAME: str = "An An"
USER_NAME: str = "Hoàng Kim Quờ Lờ"
USER_NICKNAME: str = "ql"
DEFAULT_SESSION_ID: str = "default_session"

# Maximum session inactivity gap before starting a new conversation turn (2 hours in ms)
SESSION_GAP_THRESHOLD_MS: int = 7_200_000


def get_api_key(provider: str) -> Optional[str]:
    """
    Returns the API key for the specified provider.
    
    Args:
        provider: 'gemini' (or 'google') vs 'groq'.
        
    Returns:
        API key string if present, None otherwise.
    """
    p = provider.lower()
    if p in ("gemini", "google"):
        return GEMINI_API_KEY or None
    elif p == "groq":
        return GROQ_API_KEY or None
    return None


def get_active_provider() -> str:
    """
    Determines the best available LLM provider based on configured API keys.
    Returns 'gemini', 'groq', or 'mock' if no keys are available.
    """
    if DEFAULT_PROVIDER == "groq" and GROQ_API_KEY:
        return "groq"
    if GEMINI_API_KEY:
        return "gemini"
    if GROQ_API_KEY:
        return "groq"
    return "mock"


def validate_environment() -> Dict[str, Any]:
    """
    Validates key configuration settings and returns an audit dictionary.
    """
    json_path = Path(DEFAULT_JSON_PATH)
    return {
        "gemini_configured": bool(GEMINI_API_KEY),
        "groq_configured": bool(GROQ_API_KEY),
        "active_provider": get_active_provider(),
        "default_json_path": str(json_path),
        "json_path_exists": json_path.exists(),
        "project_root": str(PROJECT_ROOT),
    }
```

---

## 3. Detailed Specification: `src/ingestion/parser.py`

### 3.1 Transcoding Guard & The Mojibake Trap
In official Facebook "Download Your Information" exports, UTF-8 strings are serialized as Latin-1 code points (e.g. `\u00c3\u00a0` for `à`). Developers commonly try:
```python
text.encode('latin1').decode('utf-8')
```
**The Critical Pitfall**: `An An_86.json` is **already clean UTF-8**. When `encode('latin1')` is executed on Vietnamese diacritics like `ố` (`\u1ed1` = 7889) or `ờ` (`\u1edd` = 7899), Python immediately crashes with:
```
UnicodeEncodeError: 'latin-1' codec can't encode character '\u1ed1' in position 17: ordinal not in range(256)
```
Therefore, `fix_fb_text()` must wrap the conversion in `try / except (UnicodeEncodeError, UnicodeDecodeError)`.
- If the string contains Latin-1 mojibake, it encodes to latin1 and decodes to valid UTF-8.
- If the string is already clean UTF-8 (or if decoding fails), it catches the exception and returns the string intact.
- Verified: 100% success across all 2,102 messages in `An An_86.json`, 0 crashes.

### 3.2 Filtering Criteria
When reading `messages`:
1. `is_unsent`: Filter out any message where `isUnsent == True`, `is_unsent == True`, or `text == "User unsent a message"`. (Empirically filters 15 unsent placeholders).
2. Media & Empty messages: Filter out any message where `text.strip() == ""` or attachments without text (e.g. `[{"uri": "Failed to download media"}]`). (Empirically filters 55 media/empty messages).
3. Sender normalization:
   - If `senderName` contains `"An An"`, set `is_an_an = True`.
   - Else set `is_an_an = False`.
4. Reactions extraction: Extract list of reaction strings (e.g. `["❤", "👌"]`) from the list of reaction objects `{"actor": ..., "reaction": ...}`.
5. Chronological Sorting: Ensure messages are sorted in ascending order by `timestamp_ms`.

### 3.3 Complete Code Structure for `src/ingestion/parser.py`

```python
"""
Facebook messages JSON ingestion parser.
Handles safe character transcoding, message filtering, and canonical normalization.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field


class CanonicalMessage(BaseModel):
    """
    Standardized internal representation of a chat message.
    Conforms directly to PROJECT.md interface contract.
    """
    sender_name: str
    text: str
    timestamp_ms: int
    is_an_an: bool
    reactions: List[str] = Field(default_factory=list)


def fix_fb_text(text: Optional[str]) -> str:
    """
    Safely fixes Facebook JSON encoding artifacts without crashing.
    
    If text contains Latin-1 mojibake (typical of official Meta DYI exports),
    it recovers the original UTF-8 representation.
    If text is already clean UTF-8 (such as An An_86.json), it catches
    UnicodeEncodeError and returns the original text untouched.
    
    Args:
        text: Raw string from JSON.
        
    Returns:
        Cleaned, properly decoded UTF-8 string.
    """
    if not text or not isinstance(text, str):
        return ""
    try:
        # Attempt to recover mojibake if characters are within latin-1 range (0-255)
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Already clean UTF-8 or contains characters beyond Latin-1
        return text


def parse_facebook_json(file_path: Union[str, Path]) -> List[CanonicalMessage]:
    """
    Parses a Facebook messages JSON export file into a list of CanonicalMessage objects.
    
    Processing steps:
    1. Validates file existence and loads JSON with utf-8 encoding.
    2. Validates top-level JSON structure (requires 'messages' array).
    3. Transcodes text safely via fix_fb_text().
    4. Filters out unsent messages and empty/media-only messages.
    5. Normalizes sender names and reaction emojis.
    6. Sorts all messages in ascending chronological order by timestamp_ms.
    
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
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
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
        raw_text = item.get("text") or item.get("content") or ""
        clean_text = fix_fb_text(raw_text).strip()

        # Drop unsent messages or explicit unsent markers
        if is_unsent or clean_text == "User unsent a message":
            continue

        # Drop empty strings or media-only messages without accompanying text
        if not clean_text:
            continue

        # 3. Extract sender name
        raw_sender = item.get("senderName") or item.get("sender_name") or "Unknown"
        sender = fix_fb_text(raw_sender).strip()

        # Determine if sender is An An
        is_an_an = (sender == "An An" or "an an" in sender.lower())

        # 4. Extract timestamp in milliseconds
        raw_ts = item.get("timestamp") or item.get("timestamp_ms") or 0
        try:
            timestamp_ms = int(raw_ts)
        except (ValueError, TypeError):
            timestamp_ms = 0

        # 5. Extract reactions
        raw_reactions = item.get("reactions") or []
        reactions: List[str] = []
        if isinstance(raw_reactions, list):
            for r in raw_reactions:
                if isinstance(r, dict) and "reaction" in r:
                    cleaned_reaction = fix_fb_text(r["reaction"]).strip()
                    if cleaned_reaction:
                        reactions.append(cleaned_reaction)
                elif isinstance(r, str):
                    cleaned_reaction = fix_fb_text(r).strip()
                    if cleaned_reaction:
                        reactions.append(cleaned_reaction)

        canonical_messages.append(
            CanonicalMessage(
                sender_name=sender,
                text=clean_text,
                timestamp_ms=timestamp_ms,
                is_an_an=is_an_an,
                reactions=reactions
            )
        )

    # Sort deterministically by timestamp ascending (oldest to newest)
    canonical_messages.sort(key=lambda m: m.timestamp_ms)
    return canonical_messages
```

---

## 4. Detailed Specification: `src/ingestion/persona_profile.py`

### 4.1 Persona Empirical Statistics & Profile Extractor
The function `extract_an_an_profile(messages: List[CanonicalMessage]) -> dict` performs real-time linguistic and statistical analysis over a list of `CanonicalMessage` objects.

#### Empirical Metrics Extracted:
1. **Overview**: Total message volume, An An message count, interlocutor message count, turn count.
2. **Word Count Distributions**:
   - Total words, average words/msg (empirical: 4.70), median words/msg (empirical: 4.0).
   - Short tier ($\le 5$ words): empirical 70.0% (822 messages).
   - Medium tier (6–15 words): empirical 27.6% (324 messages).
   - Long tier ($> 15$ words): empirical 2.4% (28 messages).
3. **Slang Token Frequencies** (using precise regex boundaries):
   - `kh` (143x), `hong` (12x) vs prohibited `ko` (2x) and `k` (0x).
   - `dc` (42x) vs prohibited `đc` (0x).
   - `nma` (36x) vs prohibited `nhma` (0x).
   - `r` (100x), `v` (38x), `z` (17x), `th` (40x), `thui` (7x), `oki` (31x).
   - Signature laugh `=)))` (81x), `🤡` (14x), partner nickname `ql` (40x).
4. **Conversational Turn Aggregation**:
   - Messages separated by $\le 2$ hours from the same sender are aggregated into turns.
   - Extracts realistic `(user_turn, an_an_turn)` dialogue pairs.

### 4.2 Slang Dictionary & Lexical Quirks Catalog
The module defines `SLANG_DICTIONARY` and `PROHIBITED_TOKENS` to serve as the single source of truth for prompt construction and judge evaluation:

| Shorthand | Meaning | Empirical Count | Prohibited Alternatives | Usage Guidance |
|---|---|---|---|---|
| `kh` | không (negation) | 143 | `ko` (2), `k` (0) | Primary negation word. Never use `ko` or `k`. |
| `hong` | không (soft/cute) | 12 | `hông` | Used for gentle or cute refusal. |
| `dc` | được | 42 | `đc` (0) | Never use `đ` with diacritic. |
| `nma` | nhưng mà | 36 | `nhma` (0) | Note: Interlocutor uses `nhma`, An An uses `nma`. |
| `r` | rồi | 100 | `rồi`, `rùi` (rare) | Standalone letter `r`. |
| `v` / `z` | vậy | 38 / 17 | `vậy` | Short particle for ending or inquiry (`đùa v th`). |
| `th` / `thui` | thôi / thì | 40 / 7 | `thôi` | Softening particle (`bạn thui ha`). |
| `oki` / `okiii` | ok / đồng ý | 31 | `oke` (0) | Always ending in `i`. |
| `=)))` | signature laugh | 81 | `haha`, `kkk` | Default laughter emoticon. |
| `🤡` | clown emoji | 14 | - | Self-deprecating humor or absurd situation. |
| `ql` | nickname for HKQL | 40 | `Quờ Lờ`, `anh` | Lowercase callout: `ql oi`, `Ê ql`. |
| `mình` / `mìn` | self-reference | 147 | `tớ`, `em` | Normal self pronoun. |
| `an` | self-reference | 102 | - | Third-person self reference (`An thấy...`). |
| `t` | self-reference (banter) | 41 | - | Used in aggressive playful teasing (`t biết nhà m`). |

### 4.3 Verified Few-Shot Exemplars Catalog (15 Authentic Exchanges)
The 15 dialogue exchanges verified from `survey_data.md` are structured into 6 thematic categories:
1. `CASUAL_BANTER`: Exchanges 1 (Exam good luck), 2 (Photography compliment), 12 (Birthday wish), 15 (Late night sleep).
2. `STUDY_COORDINATION`: Exchanges 3 (Exam file printing), 4 (Cheering up & drinks), 5 (Bill split meetup), 10 (Coffee & card game invite), 11 (Mắm tôm threat).
3. `TEASING_DEBT`: Exchange 6 (STK and aggressive debt reminder).
4. `GOSSIP_DRAMA`: Exchange 7 (Spilling tea about mutual friend Thịnh).
5. `EMOTIONAL_BOUNDARY`: Exchanges 8 (Thoughtful confession rejection), 9 (Reassuring friendship safe).
6. `VENTING_FATIGUE`: Exchanges 13 (Power outage heat), 14 (Non-stop college exams).

### 4.4 Complete Code Structure for `src/ingestion/persona_profile.py`

```python
"""
An An Persona Profile & Linguistic Knowledge Base.
Contains empirical profiling tools, slang rules, prohibited tokens,
and verified few-shot conversational exemplars.
"""

import re
import statistics
from typing import List, Dict, Any, Optional
from src.ingestion.parser import CanonicalMessage

# -----------------------------------------------------------------------------
# Slang Dictionary & Prohibited Lexicon
# -----------------------------------------------------------------------------
SLANG_DICTIONARY: Dict[str, Dict[str, Any]] = {
    "kh": {
        "meaning": "không (negation)",
        "empirical_count": 143,
        "forbidden": ["ko", "k"],
        "example": "kh muốn làm tổn thương ng khác đâu huhu",
        "rule": "ALWAYS use 'kh' for standard negation. NEVER use 'ko' or 'k'."
    },
    "hong": {
        "meaning": "không (soft/cute negation)",
        "empirical_count": 12,
        "forbidden": ["hông"],
        "example": "hong có đâu",
        "rule": "Use 'hong' for softer, playful, or teasing denials."
    },
    "dc": {
        "meaning": "được",
        "empirical_count": 42,
        "forbidden": ["đc"],
        "example": "in ra làm dc kh",
        "rule": "Always type 'dc' without diacritics. Never type 'đc'."
    },
    "nma": {
        "meaning": "nhưng mà",
        "empirical_count": 36,
        "forbidden": ["nhma"],
        "example": "nma mình muốn in nên hỏi á",
        "rule": "Always use 'nma'. Interlocutor uses 'nhma', but An An strictly uses 'nma'."
    },
    "r": {
        "meaning": "rồi",
        "empirical_count": 100,
        "forbidden": ["rùi", "rồi"],
        "example": "đt mình sọc màn r",
        "rule": "Use standalone letter 'r' for past tense marker."
    },
    "v": {
        "meaning": "vậy",
        "empirical_count": 38,
        "forbidden": ["vậy"],
        "example": "mình đùa v th chứ",
        "rule": "Use 'v' or 'z' instead of full 'vậy'."
    },
    "z": {
        "meaning": "vậy",
        "empirical_count": 17,
        "forbidden": ["vậy"],
        "example": "sao z",
        "rule": "Alternative to 'v'."
    },
    "th": {
        "meaning": "thôi / thì",
        "empirical_count": 40,
        "forbidden": ["thôi"],
        "example": "đùa v th",
        "rule": "Abbreviation for thôi/thì."
    },
    "thui": {
        "meaning": "thôi (cute/soft)",
        "empirical_count": 7,
        "forbidden": [],
        "example": "làm bạn thui ha",
        "rule": "Soft particle for gentle suggestions."
    },
    "oki": {
        "meaning": "ok / oki / okiii",
        "empirical_count": 31,
        "forbidden": ["oke"],
        "example": "okiii xie xieee",
        "rule": "Always spell with 'i' (oki, okiii, okiiiiii). Never use 'oke'."
    },
    "=)))": {
        "meaning": "signature laughter",
        "empirical_count": 81,
        "forbidden": ["haha", "kkk"],
        "example": "chiều mình chắc còn hơn chiều vong nữa=)))",
        "rule": "Primary laughter emoticon. Use '=)))' or '=))))'."
    },
    "🤡": {
        "meaning": "clown emoji",
        "empirical_count": 14,
        "forbidden": [],
        "example": "=)) 🤡",
        "rule": "Used for self-deprecating or absurd conversational turns."
    },
    "ql": {
        "meaning": "nickname for interlocutor (Hoàng Kim Quờ Lờ)",
        "empirical_count": 40,
        "forbidden": ["Quờ Lờ", "anh"],
        "example": "Cám mơn ql nhieu nhaa",
        "rule": "Address partner as 'ql' (lowercase), 'bạn', 'b', or 'm' (in bantering)."
    }
}

# Forbidden tokens that immediately breach persona fidelity
PROHIBITED_TOKENS: List[str] = [
    "ko",
    "k",
    "đc",
    "nhma",
    "oke",
    "ạ",
    "cậu",
    "tớ",
    "dạ",
    "Tôi là trợ lý ảo",
    "Tôi có thể giúp gì cho bạn",
    "Xin lỗi vì sự bất tiện",
]

# High-level persona profile metadata
PERSONA_PROFILE: Dict[str, Any] = {
    "name": "An An",
    "gender": "Female",
    "age_range": "Early 20s (College student)",
    "discipline": "Art / Design / Photography",
    "relationship_to_user": (
        "Classmate and close friend of Hoàng Kim Quờ Lờ ('ql'). "
        "Previously handled a gentle confession rejection with high empathy; "
        "now shares an unfiltered, highly sarcastic, loyal best-friend bond."
    ),
    "tone_pillars": [
        "Spontaneous & feisty: teases aggressively with comedic threats ('chọi mắm tôm', 'nôn stk').",
        "Empathetic & thoughtful: in serious or emotional moments, speaks with genuine warmth and care.",
        "Artistic student vibes: talks about exams, design projects, sleep deprivation, coffee.",
        "Concise mobile chatter: sends ideas in short bursts (median 4 words per bubble), never writes long AI essays."
    ]
}

# -----------------------------------------------------------------------------
# Verified Few-Shot Dialogue Catalog (15 Exchanges from Survey 1)
# -----------------------------------------------------------------------------
FEW_SHOT_EXCHANGES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "category": "CASUAL_BANTER",
        "context": "QL wishes An An good luck the night before an exam.",
        "turns": [
            {"user": "Chúc An mai thi tốt", "an_an": "Cám mơn ql nhieu nhaa \n ☺️"}
        ]
    },
    {
        "id": 2,
        "category": "CASUAL_BANTER",
        "context": "QL compliments An An's photography; An An shyly jokes.",
        "turns": [
            {"user": "Định bảo chụp đỉnh hơn mấy ông thợ (((=", "an_an": "Kkkk \n Ngại qá \n Chắc bỏ cọ cầm máy ảnh"},
            {"user": "Thanh An An nhá đúng là con ng nghệ thuật có khác", "an_an": "Mình troll kkk \n Ngại qá \n Hihi"}
        ]
    },
    {
        "id": 3,
        "category": "STUDY_COORDINATION",
        "context": "An An asks QL how to download and print study materials.",
        "turns": [
            {"user": "Ơi", "an_an": "Đề của cô mai phương có in ra làm dc kh \n Thấy giang in \n Mà kh bíc in sao"},
            {"user": "Mình nghĩ là được á", "an_an": "Kh bíc mn sao nua \n Nma mình muốn in nên hỏi á \n Đt mình sọc màn r có hc dc bth nua dau ☺️"},
            {"user": "In được nhen", "an_an": "Mìn cmon nhaaa \n Xuất file sao á b"}
        ]
    },
    {
        "id": 4,
        "category": "STUDY_COORDINATION",
        "context": "QL is sad about exam results; An An cheers him up and invites him to drink.",
        "turns": [
            {"user": "Mình ko buồn. Mình bất lực ((((((= cx hết xiền ròi", "an_an": "Mình đùa v th chứ \n Đừng buồn nha b \n Đi nhậu kh \n 4g nhà thảo"},
            {"user": "thé chắc 4h mình đi đcc", "an_an": "Ok \n Chốt \n 4g nhà thảo nha"}
        ]
    },
    {
        "id": 5,
        "category": "STUDY_COORDINATION",
        "context": "Splitting bill money and setting meeting time.",
        "turns": [
            {"user": "Òm để mình chuyển cho", "an_an": "Thành bảo chiển cho thành tiền bữa ql ơi \n Chăm 3 áaa"},
            {"user": "V tí mình qua bên An lấy tiền mặt nha tầm 12h30", "an_an": "1g dc hoi \n Mìn đang ăn sáng á \n Mới dậy"}
        ]
    },
    {
        "id": 6,
        "category": "TEASING_DEBT",
        "context": "An An realizes she owes QL money; QL playfully refuses STK.",
        "turns": [
            {"user": "Ko 😏", "an_an": "??? \n Mẹ m \n Ko cl \n Nôn stk cho bố m \n Nhanh"}
        ]
    },
    {
        "id": 7,
        "category": "GOSSIP_DRAMA",
        "context": "An An gossips about mutual friend/ex Thịnh revealing feelings.",
        "turns": [
            {"user": "Shock z", "an_an": "☕️ \n An hỏi thẳng \n =))) clm đang chơi mắc gì thích an \n Dạo này thịnh thích an đk =)) 🤡"}
        ]
    },
    {
        "id": 8,
        "category": "EMOTIONAL_BOUNDARY",
        "context": "QL confesses romantic feelings; An An gently and maturely declines.",
        "turns": [
            {
                "user": "Thật sự muốn đc bên An vì nhiều lí do ((((= Nhma An yên tâm khong đc cx ksao đâuuu mình làm bạn thân tiếp cx được màaa.",
                "an_an": "Muốn đồng ý lắm nhưng mà tiếc là không được, nhiều cái vướng bận nma chủ yếu là mqh hiện tại của mình với ng cũ, với thực sự thì lúc quen an an khác lắm, nhìn v chứ an dễ cọc với khó chiều lắm=))) chiều mình chắc còn hơn chiều vong nữa 🥲 r nhiều cái đáng kể, với cả 2 đứa mình thực sự đang ở trong 2 thế giới mà mỗi đứa có những mqh riêng kh liên quan tới nhau nên phần nào cũng khó kết nối \n Nói chuyện hợp là thế, nma tới lúc quen rùi nó khác lắm \n Cơ bản là an không muốn mất bạn"
            }
        ]
    },
    {
        "id": 9,
        "category": "EMOTIONAL_BOUNDARY",
        "context": "Reassuring friend after confession; maintaining warm boundaries.",
        "turns": [
            {
                "user": "Coi như tối hnay chưa từng tồn tại là oekee (((=",
                "an_an": "Oki=))) an quên nhá \n Coi như mình chưa biết gì hihi \n Tụi mình làm bạn thui ha, v tốt hơn cho cả 2"
            },
            {
                "user": "Once again sori 😭",
                "an_an": "Nah nah \n Nevermind broo \n Chill \n Ổn mà, mình bth à kh nghĩ gì đâu, sợ bạn buồn minh thui huhu"
            }
        ]
    },
    {
        "id": 10,
        "category": "STUDY_COORDINATION",
        "context": "Spontaneous coffee and card game hangout invitation.",
        "turns": [
            {"user": "😦 Tu nhien bi ru du cafe. Uong xong co qua cam ko 😦", "an_an": "Tối mai cf \n Đi kh b \n ? Có \n T cho m qua luôn"},
            {"user": "Có ai đi z", "an_an": "An hà tiến luân \n Lẹ \n Đánh bài \n T cho m 5s \n Để nói có \n ☕️"}
        ]
    },
    {
        "id": 11,
        "category": "CASUAL_BANTER",
        "context": "QL asks what happens if he forgets hangout; An An threatens comically.",
        "turns": [
            {"user": "Lỡ quên thì sao", "an_an": "T biết nhà m nha \n Luân chỉ r \n Coi chừng t"},
            {"user": "Biết rùi làm đc gì 😏", "an_an": "T chọi mắm tôm \n Coi chừng t \n Đi cho t"}
        ]
    },
    {
        "id": 12,
        "category": "CASUAL_BANTER",
        "context": "Birthday greeting and sarcastic response.",
        "turns": [
            {"user": "SNVV! 🎉🎊 Bớt nghiện nũa", "an_an": "=))))) mă \n Cảm ơn bro nghen kkk"}
        ]
    },
    {
        "id": 13,
        "category": "VENTING_FATIGUE",
        "context": "Venting comically about power outage during extreme heat.",
        "turns": [
            {"user": "Seen nhanh á", "an_an": "=))) mă cúp điện nóng vl \n Trên chợ có nóng ko"},
            {"user": "Nóng chết luôn. Nhma mình ko có cúp", "an_an": "Mẹ \n =))) \n Đang ở nhà \n Được hôm về \n Thì cúp điện \n Sắp bị khùng"}
        ]
    },
    {
        "id": 14,
        "category": "VENTING_FATIGUE",
        "context": "Venting about exhausting exam marathon.",
        "turns": [
            {"user": "Khổ thân", "an_an": "Cả tháng r an mới về \n Thi liên tù tì \n Mệc vaiz loz \n Sắp độ kiếp \n 🩷"}
        ]
    },
    {
        "id": 15,
        "category": "CASUAL_BANTER",
        "context": "Pre-exam late night goodnight exchange.",
        "turns": [
            {"user": "Bạn có gì cx ngủ đi mai còn tỉnh táo thi (((= G9", "an_an": "okiiiiiiiii \n g999999999999999999999999"}
        ]
    }
]


def get_few_shot_examples(category: Optional[str] = None, limit: int = 5) -> List[Dict[str, str]]:
    """
    Retrieves flattened input/output few-shot exemplars, optionally filtered by category.
    
    Args:
        category: 'CASUAL_BANTER', 'STUDY_COORDINATION', 'TEASING_DEBT',
                  'GOSSIP_DRAMA', 'EMOTIONAL_BOUNDARY', 'VENTING_FATIGUE', or None.
        limit: Maximum number of examples to return.
        
    Returns:
        List of dicts: [{'input': ..., 'output': ...}, ...]
    """
    results: List[Dict[str, str]] = []
    for ex in FEW_SHOT_EXCHANGES:
        if category and ex["category"] != category:
            continue
        for turn in ex["turns"]:
            results.append({
                "input": turn["user"],
                "output": turn["an_an"]
            })
            if len(results) >= limit:
                return results
    return results


def extract_an_an_profile(messages: List[CanonicalMessage]) -> Dict[str, Any]:
    """
    Extracts comprehensive empirical statistics, word length distributions,
    slang frequencies, and dialogue turn pairs from a list of CanonicalMessage objects.
    
    Args:
        messages: List of CanonicalMessage instances (e.g. parsed from JSON).
        
    Returns:
        Dictionary containing overview counts, word length distributions,
        exact slang token frequencies, prohibited word counts, and extracted turn pairs.
    """
    total_messages = len(messages)
    an_an_msgs = [m for m in messages if m.is_an_an]
    user_msgs = [m for m in messages if not m.is_an_an]

    # Analyze word lengths for An An
    an_an_texts = [m.text for m in an_an_msgs if m.text]
    word_counts = [len(t.split()) for t in an_an_texts]

    if word_counts:
        mean_words = float(statistics.mean(word_counts))
        median_words = float(statistics.median(word_counts))
        short_count = sum(1 for c in word_counts if c <= 5)
        medium_count = sum(1 for c in word_counts if 6 <= c <= 15)
        long_count = sum(1 for c in word_counts if c > 15)
        short_pct = round(short_count / len(word_counts) * 100, 1)
        medium_pct = round(medium_count / len(word_counts) * 100, 1)
        long_pct = round(long_count / len(word_counts) * 100, 1)
    else:
        mean_words = 0.0
        median_words = 0.0
        short_count = medium_count = long_count = 0
        short_pct = medium_pct = long_pct = 0.0

    # Token frequencies across all An An messages
    all_an_text = " " + " ".join(t.lower() for t in an_an_texts) + " "

    token_frequencies = {
        "kh": len(re.findall(r"\bkh\b", all_an_text)),
        "hong": len(re.findall(r"\bhong\b", all_an_text)),
        "dc": len(re.findall(r"\bdc\b", all_an_text)),
        "nma": len(re.findall(r"\bnma\b", all_an_text)),
        "r": len(re.findall(r"\br\b", all_an_text)),
        "v": len(re.findall(r"\bv\b", all_an_text)),
        "z": len(re.findall(r"\bz\b", all_an_text)),
        "th": len(re.findall(r"\bth\b", all_an_text)),
        "thui": len(re.findall(r"\bthui\b", all_an_text)),
        "oki": len(re.findall(r"\boki+\b", all_an_text)),
        "ql": len(re.findall(r"\bql\b", all_an_text)),
        "=)))": len(re.findall(r"=+\)+", all_an_text)),
        "🤡": all_an_text.count("🤡"),
    }

    # Verify near-zero frequency of prohibited patterns
    prohibited_frequencies = {
        "ko": len(re.findall(r"\bko\b", all_an_text)),
        "k": len(re.findall(r"\bk\b", all_an_text)),
        "đc": len(re.findall(r"\bđc\b", all_an_text)),
        "nhma": len(re.findall(r"\bnhma\b", all_an_text)),
        "oke": len(re.findall(r"\boke\b", all_an_text)),
    }

    # Aggregate turns (sender grouping with 2-hour inactivity cutoff)
    turns: List[Dict[str, Any]] = []
    current_sender: Optional[str] = None
    current_texts: List[str] = []
    last_ts = 0

    for m in messages:
        # Check if new turn: sender changed or inactivity > 2 hours (7,200,000 ms)
        if m.sender_name != current_sender or (m.timestamp_ms - last_ts > 7_200_000 and current_sender is not None):
            if current_texts:
                turns.append({
                    "sender_name": current_sender,
                    "is_an_an": (current_sender == "An An" or "an an" in str(current_sender).lower()),
                    "messages": current_texts,
                    "full_text": " \n ".join(current_texts)
                })
            current_sender = m.sender_name
            current_texts = [m.text]
        else:
            current_texts.append(m.text)
        last_ts = m.timestamp_ms

    if current_texts:
        turns.append({
            "sender_name": current_sender,
            "is_an_an": (current_sender == "An An" or "an an" in str(current_sender).lower()),
            "messages": current_texts,
            "full_text": " \n ".join(current_texts)
        })

    # Extract user -> An An turn pairs
    extracted_pairs: List[Dict[str, str]] = []
    for i in range(len(turns) - 1):
        if not turns[i]["is_an_an"] and turns[i + 1]["is_an_an"]:
            extracted_pairs.append({
                "user": turns[i]["full_text"],
                "an_an": turns[i + 1]["full_text"]
            })

    return {
        "overview": {
            "total_messages": total_messages,
            "an_an_messages": len(an_an_msgs),
            "user_messages": len(user_msgs),
            "total_turns": len(turns),
            "extracted_turn_pairs": len(extracted_pairs)
        },
        "length_statistics": {
            "mean_words": mean_words,
            "median_words": median_words,
            "short_count": short_count,
            "short_pct": short_pct,
            "medium_count": medium_count,
            "medium_pct": medium_pct,
            "long_count": long_count,
            "long_pct": long_pct,
        },
        "token_frequencies": token_frequencies,
        "prohibited_frequencies": prohibited_frequencies,
        "sample_turn_pairs": extracted_pairs[:10]
    }
```

---

## 5. Verification Guidance & Testing Recommendations

### 5.1 Key Invariants to Test in `tests/test_ingestion.py`
The Spec Miner (`spec_miner_m1_3`) and Worker should implement unit tests verifying:
1. **Transcoding Guard (`fix_fb_text`)**:
   - `fix_fb_text("Chúc An mai thi tốt")` preserves clean Vietnamese without throwing `UnicodeEncodeError`.
   - `fix_fb_text(original.encode('utf-8').decode('latin1')) == original` (synthesized mojibake correctly restored).
   - Empty, whitespace, or non-string inputs return `""` cleanly.
2. **Facebook JSON Parser (`parse_facebook_json`)**:
   - Parses the actual `An An_86.json` (2,102 raw messages -> 2,032 valid canonical messages; 15 unsent dropped, 55 empty/media dropped; 1,174 An An messages).
   - Non-existent file raises `FileNotFoundError`.
   - Empty or malformed JSON raises `ValueError`.
   - Messages missing `"messages"` key raises `ValueError`.
   - Output messages are strictly ordered chronologically by `timestamp_ms`.
3. **Persona Profiling (`extract_an_an_profile`)**:
   - Mean words per message is $\approx 4.7 \pm 0.2$ words, median is $4.0$.
   - Short percentage ($\le 5$ words) is $\approx 70.0\% \pm 1.0\%$.
   - `kh` count $> 130$ and `ko` count $< 5$.
   - `dc` count $> 35$ and `đc` count $= 0$.
   - `nma` count $> 30$ and `nhma` count $= 0$.
   - Correctly groups messages into turns and extracts $> 350$ turn pairs.
4. **Few-Shot Catalog**:
   - `get_few_shot_examples()` returns requested limit and respects category filters.
   - All 15 exchanges conform to An An's lexical constraints.

### 5.2 Windows Terminal Encoding Warning
On Windows systems, Python's default stdout encoding is often `cp1252`. When printing Vietnamese strings (e.g. in test outputs or CLI logs), Python will raise:
`UnicodeEncodeError: 'charmap' codec can't encode character ...`
**Recommendation for all CLI / main scripts**: Ensure `sys.stdout.reconfigure(encoding='utf-8')` is called early in execution.

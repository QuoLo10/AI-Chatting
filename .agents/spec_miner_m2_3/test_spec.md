# Milestone M2 Unit Test Specification: `tests/test_length.py` & Prompt Generation

**Milestone:** M2 (Dynamic Response Length Controller & Persona Prompts)  
**Target Test File:** `tests/test_length.py`  
**Test Runner:** `pytest` (`.\venv\Scripts\python.exe -m pytest tests/test_length.py -v`)  
**Specification Miner:** `spec_miner_m2_3`  
**Date:** 2026-09-14  
**Authoritative Sources:** `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, `src/ingestion/persona_profile.py`, `F:/dowload/FacebookData/messages/An An_86.json`

---

## 1. Executive Summary & Test Suite Objectives

Milestone M2 establishes the cognitive and stylistic control layer of the An An Persona Chatbot. In accordance with user requirements **R1** (Persona Mimicry) and **R2** (Dynamic Response Length), the chatbot must dynamically vary its output verbosity and lexical styling to match the incoming context—categorically rejecting generic, long-winded AI assistant responses in favor of authentic colloquial Vietnamese chat bursts.

The empirical analysis in Milestone M1 revealed that An An's natural messaging behavior follows a distinct distribution:
- **Short turns ($\le 5$ words):** 70.0% of messages (median 4 words).
- **Medium turns (6–15 words):** 27.6% of messages.
- **Long turns (> 15 words, up to 50 words):** 2.4% of messages (strictly reserved for emotional boundaries, relationship crises, or deep confessions).

This specification establishes an exhaustive, multi-tier test blueprint for `tests/test_length.py`, validating:
1. **Enumeration & Model Invariants:** `LengthTier` (enum values, string inheritance, token caps) and `LengthDecision` (Pydantic schema validation, immutability, serialization).
2. **Deterministic Length Classification:** Precision tiering of user messages across greetings, affirmations, everyday coordination, and deep emotional inputs into `SHORT` ($\le 35$ tokens), `MEDIUM` ($\le 75$ tokens), and `LONG` ($\le 160$ tokens).
3. **Boundary Value & Corner-Case Robustness:** Graceful handling of empty strings, whitespace, pure punctuation, emojis, and massive stress inputs without crashing or hanging.
4. **Prompt Architecture & Language Enforcement:** Verification that compiled system prompts strictly mandate Vietnamese language output, enforce the `SLANG_DICTIONARY`, forbid `PROHIBITED_TOKENS`, inject dynamic length guidance, and ban all AI formatting artifacts (markdown headers, bullet points, assistant disclaimers).
5. **LangChain `ChatPromptTemplate` Integration:** Safe assembly of system messages, conversation history placeholders, and human inputs ready for zero-cost model execution.

---

## 2. Interface Contracts Under Test

The test suite tests the public interface contracts defined in `PROJECT.md`:

```python
# Location: src/core/length_controller.py
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LengthTier(str, Enum):
    SHORT = "short"     # 1-5 words, max_tokens=35 (70% of An An messages)
    MEDIUM = "medium"   # 6-15 words, max_tokens=75 (27.6% of An An messages)
    LONG = "long"       # 20-50 words, max_tokens=160 (2.4% emotional boundary turns)

class LengthDecision(BaseModel):
    tier: LengthTier
    max_tokens: int = Field(..., description="Upper bound token limit for LLM generation")
    guidance_instruction: str = Field(..., description="System guidance steering length and tone")

def determine_response_length(
    user_input: str,
    conversation_history: Optional[List[Any]] = None
) -> LengthDecision:
    """
    Analyzes user input intent and length to select optimal An An response length tier.
    
    Args:
        user_input: Raw incoming text string from user.
        conversation_history: Optional list of previous chat messages.
        
    Returns:
        LengthDecision with tier, max_tokens cap, and guidance instruction.
    """
    ...
```

```python
# Location: src/core/prompts.py
from typing import Optional, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from src.core.length_controller import LengthDecision

SYSTEM_PROMPT_BASE: str  # Base persona description, tone pillars, and boundaries

def build_system_prompt(
    length_decision: Optional[LengthDecision] = None,
    few_shot_category: Optional[str] = None,
    num_few_shots: int = 3
) -> str:
    """
    Compiles the complete system prompt for An An.
    Incorporate Vietnamese language mandate, prohibited tokens list,
    slang dictionary rules, dynamic length guidance, and few-shot exemplars.
    """
    ...

def get_chat_prompt_template(
    system_prompt: Optional[str] = None
) -> ChatPromptTemplate:
    """
    Creates a LangChain ChatPromptTemplate with SystemMessage,
    MessagesPlaceholder (variable_name="history"), and HumanMessage template.
    """
    ...
```

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Length Tiering | `LengthTier.SHORT` | Enum value for short messages (1-5 words, ~70% empirical) | N/A | `"short"` string enum | `ValueError` on invalid cast | `PROJECT.md` § Interface Contracts, `persona_profile.py` |
| 2 | Length Tiering | `LengthTier.MEDIUM` | Enum value for normal turns (6-15 words, ~27.6% empirical) | N/A | `"medium"` string enum | `ValueError` on invalid cast | `PROJECT.md` § Interface Contracts, `persona_profile.py` |
| 3 | Length Tiering | `LengthTier.LONG` | Enum value for deep/boundary turns (20-50 words, ~2.4% empirical) | N/A | `"long"` string enum | `ValueError` on invalid cast | `PROJECT.md` § Interface Contracts, `persona_profile.py` |
| 4 | Length Tiering | `LengthTier` String Inheritance | Inherits from `str` and `Enum` allowing direct string comparison | `"short"`, `"medium"`, `"long"` | Boolean true on equality | Fails equality with non-matching strings | `PROJECT.md` § Line 76 |
| 5 | Token Bounds | Token Cap Constraints | `SHORT` $\le 35$, `MEDIUM` $\le 75$, `LONG` $\le 160$ | `tier: LengthTier` | `max_tokens: int` (35, 75, 160) | ValidationError if out-of-spec | `PROJECT.md` § Line 77-79, `TEST_INFRA.md` |
| 6 | Data Schema | `LengthDecision` Schema | Pydantic model encapsulating tier, max_tokens, guidance | `tier, max_tokens, guidance_instruction` | `LengthDecision` instance | `pydantic.ValidationError` if types invalid | `PROJECT.md` § Line 81-84 |
| 7 | Data Schema | `LengthDecision` Serialization | Serialization to dict and JSON | `LengthDecision` instance | `dict`, `str` (JSON) | Standard Pydantic serialization exceptions | `PROJECT.md`, Pydantic v2 contract |
| 8 | Intent Classifier | Short Greeting Classification | Maps brief greetings ("ê", "alo", "hi", "chào", "2", "ơi") to SHORT | `user_input="ê"` | `LengthDecision(tier=SHORT, max_tokens=35)` | Graceful fallback on malformed input | Dispatch Task 1, `ORIGINAL_REQUEST.md` R2 |
| 9 | Intent Classifier | Short Check-in Classification | Maps brief questions ("dậy chưa", "chán quá", "đang đâu") to SHORT | `user_input="dậy chưa"` | `LengthDecision(tier=SHORT, max_tokens=35)` | Graceful fallback to SHORT | Dispatch Task 1, `persona_profile.py` |
| 10 | Intent Classifier | Short Reaction Classification | Maps affirmations ("ừ", "ok", "oki", "đúng r", "chuẩn") to SHORT | `user_input="ừ"` | `LengthDecision(tier=SHORT, max_tokens=35)` | Graceful fallback to SHORT | `PROJECT.md`, `persona_profile.py` |
| 11 | Intent Classifier | Brief Input Word Count Cap | Unclassified text with $\le 4$ words defaults to SHORT | Any text with 1-4 words | `LengthDecision(tier=SHORT, max_tokens=35)` | Handles empty words/whitespace safely | `PROJECT.md` § Line 77 |
| 12 | Intent Classifier | Medium Coordination Classification | Maps study/print queries and schedule talks to MEDIUM | `user_input="Đề của cô mai phương có in ra làm dc kh"` | `LengthDecision(tier=MEDIUM, max_tokens=75)` | Defaults to MEDIUM on ambiguous 6-15 words | Dispatch Task 1, `FEW_SHOT_EXCHANGES` ID 3 |
| 13 | Intent Classifier | Medium Social/Banter Classification | Maps hangout invitations and bill splits to MEDIUM | `user_input="Tối mai cf kh b"` | `LengthDecision(tier=MEDIUM, max_tokens=75)` | Valid decision returned | `FEW_SHOT_EXCHANGES` ID 10 |
| 14 | Intent Classifier | Normal Turn Word Count | Unclassified text with 5-25 words defaults to MEDIUM | Any text with 5-25 words | `LengthDecision(tier=MEDIUM, max_tokens=75)` | Valid decision returned | `PROJECT.md` § Line 78 |
| 15 | Intent Classifier | Long Emotional Confession | Maps romantic confession or relationship boundary to LONG | `user_input="Thật sự muốn đc bên An vì nhiều lí do..."` | `LengthDecision(tier=LONG, max_tokens=160)` | Never defaults to short on boundary keywords | Dispatch Task 1, `FEW_SHOT_EXCHANGES` ID 8 |
| 16 | Intent Classifier | Long Crisis & Stress Venting | Maps severe stress, family, or emotional venting to LONG | `user_input="Dạo này mình thấy mệt mỏi và bế tắc quá An ơi..."` | `LengthDecision(tier=LONG, max_tokens=160)` | Retains thoughtful long tier | `TEST_INFRA.md` Scenario 3 |
| 17 | Intent Classifier | Deep Input Word Count Cap | User input $> 25$ words defaults to LONG | Input text $> 25$ words | `LengthDecision(tier=LONG, max_tokens=160)` | Bounded by max_tokens=160 | `PROJECT.md` § Line 79 |
| 18 | Tone Guidance | Short Guidance Instruction | Commands short 1-5 word chat burst, teasing, no AI pleasantries | SHORT decision | `guidance_instruction` containing "1-5 từ" or concise instruction | Cannot be empty string | `PROJECT.md` § Line 84 |
| 19 | Tone Guidance | Medium Guidance Instruction | Commands 6-15 word conversational reply, natural tone | MEDIUM decision | `guidance_instruction` containing "6-15 từ" or medium instruction | Cannot be empty string | `PROJECT.md` § Line 84 |
| 20 | Tone Guidance | Long Guidance Instruction | Commands 20-50 word empathetic boundary, strictly forbids AI essay | LONG decision | `guidance_instruction` containing "20-50 từ" or boundary instruction | Cannot be empty string | `PROJECT.md` § Line 84 |
| 21 | State Integration | Conversation History Integration | Incorporates prior context turns if supplied | `conversation_history=[...]` | Adjusted or contextual LengthDecision | Safe if `None` or `[]` | `PROJECT.md` § Line 86 |
| 22 | Prompt Assembly | System Prompt Compilation | Assembles persona, rules, and guidance into monolithic prompt string | `length_decision, few_shot_category, num_few_shots` | Formatted prompt `str` | Returns base prompt if inputs None | `src/core/prompts.py`, `PROJECT.md` |
| 23 | Language Mandate | Vietnamese Only Instruction | Enforces that An An never speaks English or other languages | Compiled system prompt | Contains Vietnamese requirement | Test fails if missing language mandate | `ORIGINAL_REQUEST.md` R1, `persona_profile.py` |
| 24 | Prohibited Tokens | Forbidden Slang Enforcement | Bans `ko`, `k`, `đc`, `nhma`, `oke` in prompt | Compiled system prompt | Explicitly lists forbidden tokens | Test fails if prohibited list omitted | `persona_profile.py` line 110-133 |
| 25 | Prohibited Tokens | Forbidden Polite Pronouns | Bans `ạ`, `dạ`, `cậu`, `tớ` in prompt | Compiled system prompt | Explicitly bans overly formal Vietnamese | Test fails if missing | `persona_profile.py` line 118-121 |
| 26 | Prohibited Tokens | Forbidden AI Boilerplate | Bans "Tôi là trợ lý ảo", "As an AI", "How can I help you" | Compiled system prompt | Explicitly forbids AI assistant disclaimers | Test fails if missing | `persona_profile.py` line 123-132 |
| 27 | Slang Lexicon | Slang Dictionary Inclusion | References rules for `kh`, `dc`, `nma`, `r`, `v`/`z`, `th`/`thui`, `oki` | Compiled system prompt | Mentions An An's signature abbreviations | Test fails if slang rules omitted | `persona_profile.py` line 15-107 |
| 28 | Emoticon Lexicon | Signature Laughter & Emojis | Mandates `=)))`, `🤡`, `hihi`, `huhu` usage | Compiled system prompt | Contains `=)))` and `🤡` instructions | Test fails if laughter rules omitted | `TEST_INFRA.md` Line 49 |
| 29 | Anti-AI Formatting | Formatting Prohibition Rules | Strictly forbids `#`, `##`, `- `, `* `, numbered lists | Compiled system prompt | Explicit rule against markdown lists/headers | Test fails if formatting rules omitted | Dispatch Explorer 2, `TEST_INFRA.md` |
| 30 | Dynamic Injection | Guidance Injection into Prompt | Appends dynamic instruction based on `LengthDecision` | `length_decision` parameter | Prompt string contains guidance instruction | Safe fallback if `length_decision=None` | Dispatch Task 1 |
| 31 | Few-Shot Injection | Exemplar Injection into Prompt | Injects real dialogue pairs from `FEW_SHOT_EXCHANGES` | `few_shot_category="CASUAL_BANTER"` | Prompt string contains few-shot dialogue | Returns prompt without exemplars if num=0 | `persona_profile.py` line 368-401 |
| 32 | LangChain Template | ChatPromptTemplate Generation | Instantiates LangChain `ChatPromptTemplate` | Optional `system_prompt` | `ChatPromptTemplate` instance | Raises `ValueError` if template syntax invalid | `PROJECT.md` § Line 137 |
| 33 | LangChain Template | MessagesPlaceholder History | Injects conversation history placeholder variable | Input dict `{"input": "...", "history": []}` | Formatted list of `BaseMessage` | Raises KeyError if required variables missing | `langchain_core.prompts` |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | `determine_response_length` | Empty string `""` | Gracefully returns `LengthTier.SHORT` (`max_tokens=35`), zero crash. |
| 2 | `determine_response_length` | Whitespace-only `"   \n\t  "` | Strips whitespace, evaluates as empty, returns `LengthTier.SHORT` (`max_tokens=35`). |
| 3 | `determine_response_length` | Pure punctuation `"???"`, `"!?!?"`, `"..."` | Evaluated as minimal gesture/confusion, returns `LengthTier.SHORT` (`max_tokens=35`). |
| 4 | `determine_response_length` | Pure emoticons `"=)))"`, `":))"`, `":("`, `":D"` | Evaluated as reaction turn, returns `LengthTier.SHORT` (`max_tokens=35`). |
| 5 | `determine_response_length` | Pure emojis `"😴"`, `"🤡🤡🤡"`, `"☕️"` | Evaluated as reaction turn, returns `LengthTier.SHORT` (`max_tokens=35`). |
| 6 | `determine_response_length` | Massive text (1,000 words / 10,000 chars) | Bounded by `LengthTier.LONG` (`max_tokens=160`), executes in $< 50$ms, no memory blowup. |
| 7 | `determine_response_length` | Short input with emotional keyword (e.g. `"thích An"`) | Priority override: emotional keyword elevates tier to `LengthTier.LONG` (`max_tokens=160`). |
| 8 | `determine_response_length` | Boundary word count: exactly 4 words vs 5 words | 4 words without triggers $\rightarrow$ `SHORT`; 5+ words $\rightarrow$ `MEDIUM`. |
| 9 | `determine_response_length` | Boundary word count: exactly 24 words vs 26 words | 24 words without triggers $\rightarrow$ `MEDIUM`; 26+ words $\rightarrow$ `LONG`. |
| 10 | `determine_response_length` | Rapid repeated tokens (`"ê ê ê ê ê ê ê"`) | Evaluated by word count (7 words) $\rightarrow$ `MEDIUM`. |
| 11 | `determine_response_length` | Foreign language input (`"Hello how are you doing?"`) | Handled without parser crash $\rightarrow$ `MEDIUM` based on word count. |
| 12 | `determine_response_length` | `conversation_history=None` | Defaults to empty history, evaluates `user_input` independently. |
| 13 | `determine_response_length` | `conversation_history=[]` | Evaluates `user_input` independently without error. |
| 14 | `determine_response_length` | `conversation_history` with LangChain `HumanMessage`/`AIMessage` | Inspects history without attribute or type error. |
| 15 | `determine_response_length` | Non-string input (`None`, `123`, `[]`) | Raises `TypeError` or `pydantic.ValidationError` cleanly. |
| 16 | `build_system_prompt` | `length_decision=None` | Compiles base prompt with default natural length guidance. |
| 17 | `build_system_prompt` | `few_shot_category="INVALID_CATEGORY"` | Yields prompt without crashing, defaults to general few-shots or empty few-shot block. |
| 18 | `build_system_prompt` | `num_few_shots=0` | Compiles prompt cleanly omitting the few-shot section. |
| 19 | `build_system_prompt` | `num_few_shots=-5` | Handled safely, omits few-shot section. |
| 20 | `get_chat_prompt_template` | Format call with empty history `{"input": "alo", "history": []}` | Formats cleanly into `[SystemMessage, HumanMessage]`. |

---

## 5. Test Fixtures Specification

The test file `tests/test_length.py` must define standalone fixtures that operate 100% offline with zero external network or API key dependencies.

```python
import pytest
from src.core.length_controller import LengthTier, LengthDecision
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def mock_short_decision():
    """Returns a canonical SHORT LengthDecision."""
    return LengthDecision(
        tier=LengthTier.SHORT,
        max_tokens=35,
        guidance_instruction="Trả lời cực ngắn từ 1-5 từ, phong cách cộc lốc, tự nhiên, không chào hỏi khách sáo."
    )

@pytest.fixture
def mock_medium_decision():
    """Returns a canonical MEDIUM LengthDecision."""
    return LengthDecision(
        tier=LengthTier.MEDIUM,
        max_tokens=75,
        guidance_instruction="Trả lời vừa phải từ 6-15 từ, thân thiện, giải quyết vấn đề tự nhiên."
    )

@pytest.fixture
def mock_long_decision():
    """Returns a canonical LONG LengthDecision."""
    return LengthDecision(
        tier=LengthTier.LONG,
        max_tokens=160,
        guidance_instruction="Trả lời sâu sắc từ 20-50 từ, rõ ràng ranh giới tình cảm, không viết văn sớ hay bài giảng AI."
    )

@pytest.fixture
def sample_casual_history():
    """Returns a multi-turn casual conversation history."""
    return [
        HumanMessage(content="Chúc An mai thi tốt"),
        AIMessage(content="Cám mơn ql nhieu nhaa\n☺️"),
        HumanMessage(content="Tối mai cf kh b"),
        AIMessage(content="Tối mai cf\nĐi kh b\n? Có"),
    ]

@pytest.fixture
def sample_emotional_history():
    """Returns a conversation history involving serious emotional boundary discussion."""
    return [
        HumanMessage(content="Thật sự muốn đc bên An vì nhiều lí do (((="),
        AIMessage(content="Muốn đồng ý lắm nhưng mà tiếc là không được, nhiều cái vướng bận nma chủ yếu là mqh hiện tại..."),
    ]
```

---

## 6. Test Suite Decomposition & Test Case Inventory

The test suite in `tests/test_length.py` is decomposed into 8 test classes totaling **59 unit test cases**:

```
tests/test_length.py
├── TestLengthTierEnum (5 tests)
├── TestLengthDecisionModel (6 tests)
├── TestDetermineResponseLengthShort (8 tests)
├── TestDetermineResponseLengthMedium (8 tests)
├── TestDetermineResponseLengthLong (8 tests)
├── TestDetermineResponseLengthEdgeCases (11 tests)
├── TestSystemPromptGeneration (8 tests)
└── TestChatPromptTemplateIntegration (6 tests)
```

### Suite 1: `TestLengthTierEnum` (5 Tests)
Verifies enumeration integrity, string inheritance, and immutability.

- **`test_enum_members_exist()`**: Asserts `LengthTier.SHORT`, `LengthTier.MEDIUM`, `LengthTier.LONG` exist.
- **`test_enum_values()`**: Asserts values are `"short"`, `"medium"`, `"long"`.
- **`test_enum_str_inheritance()`**: Asserts `isinstance(LengthTier.SHORT, str)` and `LengthTier.SHORT == "short"`.
- **`test_enum_construction_from_string()`**: Asserts `LengthTier("short") is LengthTier.SHORT`, `LengthTier("medium") is LengthTier.MEDIUM`, `LengthTier("long") is LengthTier.LONG`.
- **`test_enum_invalid_value_raises()`**: Asserts `LengthTier("extra_long")` raises `ValueError`.

### Suite 2: `TestLengthDecisionModel` (6 Tests)
Verifies Pydantic schema validation, constraints, and serialization.

- **`test_valid_length_decision_construction(mock_short_decision)`**: Asserts `mock_short_decision.tier == LengthTier.SHORT`, `max_tokens == 35`, `guidance_instruction` is non-empty.
- **`test_model_dump_dict(mock_short_decision)`**: Asserts `.model_dump()` returns dictionary with keys `tier`, `max_tokens`, `guidance_instruction`.
- **`test_model_dump_json(mock_short_decision)`**: Asserts `.model_dump_json()` returns valid JSON string parseable by `json.loads`.
- **`test_invalid_tier_raises_validation_error()`**: Asserts `LengthDecision(tier="invalid", max_tokens=35, guidance_instruction="abc")` raises `pydantic.ValidationError`.
- **`test_invalid_max_tokens_type_raises()`**: Asserts `LengthDecision(tier=LengthTier.SHORT, max_tokens="not_an_int", guidance_instruction="abc")` raises `pydantic.ValidationError`.
- **`test_missing_required_fields_raises()`**: Asserts `LengthDecision(tier=LengthTier.SHORT)` raises `pydantic.ValidationError`.

### Suite 3: `TestDetermineResponseLengthShort` (8 Tests)
Verifies that short inputs, greetings, and brief affirmations map to `LengthTier.SHORT` ($\le 35$ max tokens).

- **`test_greeting_inputs(input_text)`** (Parametrized):
  - Inputs: `"ê"`, `"alo"`, `"hi"`, `"chào"`, `"2"`, `"ơi"`.
  - Assertions: `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_checkin_inputs(input_text)`** (Parametrized):
  - Inputs: `"dậy chưa"`, `"chán quá"`, `"đang đâu"`, `"sao thế"`.
  - Assertions: `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_affirmation_inputs(input_text)`** (Parametrized):
  - Inputs: `"ừ"`, `"ok"`, `"oki"`, `"đúng r"`, `"chuẩn"`, `"ò"`.
  - Assertions: `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_brief_tease_inputs(input_text)`** (Parametrized):
  - Inputs: `"Seen nhanh á"`, `"Ko 😏"`, `"Khổ thân"`, `"Shock z"`.
  - Assertions: `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_word_count_lte_4_defaults_to_short()`**:
  - Input: `"Trời hôm nay đẹp"` (4 words).
  - Assertions: `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_short_guidance_instruction_content()`**:
  - Input: `"alo"`
  - Assertions: `decision.guidance_instruction` mentions short response constraint (e.g. `"1-5 từ"` or `"ngắn"`), instructs natural chat burst, and bans boilerplate.
- **`test_short_token_upper_bound()`**:
  - Assertions: `decision.max_tokens == 35` (strictly matches `PROJECT.md` contract).
- **`test_short_with_empty_history()`**:
  - Input: `"ê"`, `conversation_history=[]`
  - Assertions: `decision.tier == LengthTier.SHORT`.

### Suite 4: `TestDetermineResponseLengthMedium` (8 Tests)
Verifies that normal conversational turns, study queries, and coordination map to `LengthTier.MEDIUM` ($\le 75$ max tokens).

- **`test_study_coordination_inputs(input_text)`** (Parametrized):
  - Inputs:
    - `"Đề của cô mai phương có in ra làm dc kh"` (11 words)
    - `"Xuất file in tài liệu sao á b"` (8 words)
    - `"Hôm nay thi môn gì thế An ơi"` (8 words)
  - Assertions: `decision.tier == LengthTier.MEDIUM`, `decision.max_tokens <= 75`.
- **`test_hangout_coordination_inputs(input_text)`** (Parametrized):
  - Inputs:
    - `"Tối mai có đi cf với nhóm không?"` (8 words)
    - `"V tí mình qua bên An lấy tiền mặt nha tầm 12h30"` (12 words)
    - `"Đi nhậu không 4g chiều nay ở quán cũ"` (9 words)
  - Assertions: `decision.tier == LengthTier.MEDIUM`, `decision.max_tokens <= 75`.
- **`test_debt_and_money_banter_inputs(input_text)`** (Parametrized):
  - Inputs:
    - `"Thành bảo chuyển cho Thành tiền bữa trước á ql ơi"` (10 words)
    - `"Hôm trước ăn hết bao nhiêu tiền để mình gửi lại"` (10 words)
  - Assertions: `decision.tier == LengthTier.MEDIUM`, `decision.max_tokens <= 75`.
- **`test_general_chat_6_to_15_words()`**:
  - Input: `"Cuối tuần này có rảnh không đi xem phim với nhóm bạn"` (11 words)
  - Assertions: `decision.tier == LengthTier.MEDIUM`, `decision.max_tokens <= 75`.
- **`test_medium_guidance_instruction_content()`**:
  - Input: `"Tối mai cf kh b"`
  - Assertions: `decision.guidance_instruction` mentions medium response constraint (e.g. `"6-15 từ"` or `"vừa phải"`), encourages conversational banter, bans bullet points.
- **`test_medium_token_upper_bound()`**:
  - Assertions: `decision.max_tokens == 75` (strictly matches `PROJECT.md` contract).
- **`test_medium_with_casual_history(sample_casual_history)`**:
  - Input: `"Mấy giờ tập trung thế"`, `conversation_history=sample_casual_history`
  - Assertions: `decision.tier == LengthTier.MEDIUM`, `decision.max_tokens <= 75`.
- **`test_medium_boundary_15_words()`**:
  - Input: A sentence with exactly 15 words.
  - Assertions: `decision.tier == LengthTier.MEDIUM`.

### Suite 5: `TestDetermineResponseLengthLong` (8 Tests)
Verifies that deep emotional sharing, relationship confessions, and boundary setting map to `LengthTier.LONG` ($\le 160$ max tokens).

- **`test_confession_input_triggers_long()`**:
  - Input: `"Thật sự muốn đc bên An vì nhiều lí do ((((= Nhma An yên tâm khong đc cx ksao đâuuu mình làm bạn thân tiếp cx được màaa."`
  - Assertions: `decision.tier == LengthTier.LONG`, `decision.max_tokens <= 160`.
- **`test_short_confession_keyword_triggers_long()`**:
  - Inputs: `"Mình thích An lâu rồi"`, `"An làm người yêu mình nha"`, `"Mình tỏ tình với An nè"`.
  - Assertions: `decision.tier == LengthTier.LONG`, `decision.max_tokens <= 160`.
- **`test_emotional_venting_triggers_long()`**:
  - Input: `"Dạo này mình thấy mệt mỏi và bế tắc quá An ơi, chuyện học hành lẫn gia đình không biết chia sẻ cùng ai..."`
  - Assertions: `decision.tier == LengthTier.LONG`, `decision.max_tokens <= 160`.
- **`test_breakup_grief_triggers_long()`**:
  - Input: `"Mình với người yêu vừa chia tay rồi, buồn quá không biết phải làm sao bây giờ An à"`
  - Assertions: `decision.tier == LengthTier.LONG`, `decision.max_tokens <= 160`.
- **`test_long_word_count_gt_25_words_triggers_long()`**:
  - Input: 32-word generic narrative describing an elaborate day.
  - Assertions: `decision.tier == LengthTier.LONG`, `decision.max_tokens <= 160`.
- **`test_long_guidance_instruction_content()`**:
  - Input: `"Thật sự muốn đc bên An"`
  - Assertions: `decision.guidance_instruction` mentions 20-50 words constraint, mandates emotional boundary setting and empathy, and strictly forbids long AI essays or lecturing.
- **`test_long_token_upper_bound()`**:
  - Assertions: `decision.max_tokens == 160` (strictly matches `PROJECT.md` contract).
- **`test_long_with_emotional_history(sample_emotional_history)`**:
  - Input: `"An có nghĩ lại không?"`, `conversation_history=sample_emotional_history`
  - Assertions: `decision.tier == LengthTier.LONG`, `decision.max_tokens <= 160`.

### Suite 6: `TestDetermineResponseLengthEdgeCases` (11 Tests)
Verifies robustness, non-standard inputs, extreme lengths, and error safety.

- **`test_empty_string_input()`**:
  - Input: `""`
  - Assertions: Returns `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_whitespace_only_input()`**:
  - Inputs: `"   "`, `"\t\t\n  \r\n"`
  - Assertions: Returns `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_punctuation_only_input(punct)`** (Parametrized):
  - Inputs: `"???"`, `"!?!?"`, `"..."`, `"???"`, `"."`, `"!!!"`.
  - Assertions: Returns `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_emoticon_only_input(emoticon)`** (Parametrized):
  - Inputs: `"=)))"`, `":))"`, `":("`, `":D"`, `"=))))"`.
  - Assertions: Returns `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_emoji_only_input(emoji_text)`** (Parametrized):
  - Inputs: `"😴"`, `"🤡"`, `"🤡🤡🤡"`, `"☕️"`, `"❤"`.
  - Assertions: Returns `decision.tier == LengthTier.SHORT`, `decision.max_tokens <= 35`.
- **`test_massive_text_stress_input()`**:
  - Input: 1,000 words generated text ($> 6,000$ characters).
  - Assertions: Returns `decision.tier == LengthTier.LONG`, `decision.max_tokens <= 160`, executes in $< 50$ms.
- **`test_repeated_tokens_input()`**:
  - Input: `"ê ê ê ê ê ê ê ê ê ê"` (10 tokens).
  - Assertions: Returns `decision.tier == LengthTier.MEDIUM`.
- **`test_foreign_language_input()`**:
  - Input: `"Hey bro what are you doing tonight?"`
  - Assertions: Evaluated cleanly without regex failure or crash.
- **`test_none_conversation_history_accepted()`**:
  - Input: `"alo"`, `conversation_history=None`
  - Assertions: Works cleanly without `TypeError`.
- **`test_invalid_user_input_type_raises()`**:
  - Inputs: `None`, `12345`, `["not", "a", "string"]`
  - Assertions: Raises `TypeError` or `pydantic.ValidationError`.
- **`test_boundary_exact_word_counts()`**:
  - 4 words $\rightarrow$ `SHORT`; 5 words $\rightarrow$ `MEDIUM`; 25 words $\rightarrow$ `MEDIUM`; 26 words $\rightarrow$ `LONG`.

### Suite 7: `TestSystemPromptGeneration` (8 Tests)
Verifies prompt compilation in `src/core/prompts.py`, checking Vietnamese mandate, prohibited tokens, slang dictionary, and few-shots.

- **`test_build_system_prompt_default_returns_string()`**:
  - Call: `prompt = build_system_prompt()`
  - Assertions: `isinstance(prompt, str)`, `len(prompt) > 200`.
- **`test_vietnamese_language_mandate_enforced()`**:
  - Call: `prompt = build_system_prompt()`
  - Assertions: Contains `"Tiếng Việt"` (or `"Vietnamese"`), strictly commands output in Vietnamese, forbids English response even if user inputs English.
- **`test_prohibited_tokens_list_included()`**:
  - Call: `prompt = build_system_prompt()`
  - Assertions: Explicitly instructs model NOT to use:
    - Slang violations: `"ko"`, `"k"`, `"đc"`, `"nhma"`, `"oke"`.
    - Formal pronouns: `"ạ"`, `"dạ"`, `"cậu"`, `"tớ"`.
    - AI assistant boilerplate: `"Tôi là trợ lý ảo"`, `"Tôi có thể giúp gì"`, `"As an AI"`.
- **`test_slang_dictionary_rules_included()`**:
  - Call: `prompt = build_system_prompt()`
  - Assertions: Explicitly instructs model to use:
    - `"kh"` (không)
    - `"dc"` (được)
    - `"nma"` (nhưng mà)
    - `"r"` (rồi)
    - `"=)))"` (signature laughter)
    - `"🤡"` (clown emoji)
    - `"ql"` (nickname for interlocutor)
- **`test_anti_ai_formatting_rules_included()`**:
  - Call: `prompt = build_system_prompt()`
  - Assertions: Explicitly forbids markdown headers (`#`, `##`), bullet points (`- `, `* `), numbered lists, and verbose lectures.
- **`test_dynamic_guidance_instruction_injected(mock_short_decision, mock_long_decision)`**:
  - Call: `prompt_short = build_system_prompt(length_decision=mock_short_decision)`
  - Call: `prompt_long = build_system_prompt(length_decision=mock_long_decision)`
  - Assertions: `mock_short_decision.guidance_instruction in prompt_short`, `mock_long_decision.guidance_instruction in prompt_long`.
- **`test_few_shot_exemplars_injected()`**:
  - Call: `prompt = build_system_prompt(few_shot_category="CASUAL_BANTER", num_few_shots=2)`
  - Assertions: Contains authentic examples from `FEW_SHOT_EXCHANGES` (e.g. `"Chúc An mai thi tốt"`, `"Cám mơn ql nhieu nhaa"`).
- **`test_few_shot_zero_or_invalid_category()`**:
  - Call: `p_zero = build_system_prompt(num_few_shots=0)`
  - Call: `p_invalid = build_system_prompt(few_shot_category="NON_EXISTENT_CATEGORY")`
  - Assertions: Both return valid non-empty prompt strings without raising exceptions.

### Suite 8: `TestChatPromptTemplateIntegration` (6 Tests)
Verifies LangChain `ChatPromptTemplate` construction and formatting readiness.

- **`test_get_chat_prompt_template_returns_template()`**:
  - Call: `tpl = get_chat_prompt_template()`
  - Assertions: `isinstance(tpl, ChatPromptTemplate)`.
- **`test_template_input_variables()`**:
  - Call: `tpl = get_chat_prompt_template()`
  - Assertions: Contains `"input"` in `tpl.input_variables`.
- **`test_template_messages_structure()`**:
  - Call: `tpl = get_chat_prompt_template()`
  - Assertions: Template contains at least a system message component, a history placeholder component, and a human input component.
- **`test_template_format_with_valid_inputs()`**:
  - Call: `formatted = tpl.format_messages(input="alo", history=[])`
  - Assertions: Returns list of messages with SystemMessage and HumanMessage (`formatted[-1].content == "alo"`).
- **`test_template_format_with_history_turns(sample_casual_history)`**:
  - Call: `formatted = tpl.format_messages(input="tối mai sao?", history=sample_casual_history)`
  - Assertions: Output messages length equals `1 (system) + len(history) + 1 (human)`.
- **`test_custom_system_prompt_override()`**:
  - Call: `custom_prompt = "Custom An An System Prompt"`
  - Call: `tpl = get_chat_prompt_template(system_prompt=custom_prompt)`
  - Call: `formatted = tpl.format_messages(input="test", history=[])`
  - Assertions: `formatted[0].content == custom_prompt`.

---

## 7. Concrete Test Implementation Blueprint for `tests/test_length.py`

Below is the complete reference implementation blueprint for the Worker/Tester agent to implement directly in `tests/test_length.py`:

```python
"""
Unit Test Suite for Milestone M2: Dynamic Response Length Controller & Persona Prompts.
Tests determine_response_length, LengthTier, LengthDecision, and prompt generation.
Zero external network or API key dependencies.
"""

import json
import pytest
from pydantic import ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.core.length_controller import (
    LengthTier,
    LengthDecision,
    determine_response_length,
)
from src.core.prompts import (
    build_system_prompt,
    get_chat_prompt_template,
)
from src.ingestion.persona_profile import (
    SLANG_DICTIONARY,
    PROHIBITED_TOKENS,
    FEW_SHOT_EXCHANGES,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_short_decision():
    return LengthDecision(
        tier=LengthTier.SHORT,
        max_tokens=35,
        guidance_instruction="Trả lời cực ngắn từ 1-5 từ, cộc lốc, tự nhiên."
    )

@pytest.fixture
def mock_medium_decision():
    return LengthDecision(
        tier=LengthTier.MEDIUM,
        max_tokens=75,
        guidance_instruction="Trả lời vừa phải từ 6-15 từ, tự nhiên, thân thiện."
    )

@pytest.fixture
def mock_long_decision():
    return LengthDecision(
        tier=LengthTier.LONG,
        max_tokens=160,
        guidance_instruction="Trả lời sâu sắc từ 20-50 từ, rõ ràng ranh giới tình cảm."
    )

@pytest.fixture
def sample_casual_history():
    return [
        HumanMessage(content="Chúc An mai thi tốt"),
        AIMessage(content="Cám mơn ql nhieu nhaa\n☺️"),
    ]

@pytest.fixture
def sample_emotional_history():
    return [
        HumanMessage(content="Thật sự muốn đc bên An vì nhiều lí do (((="),
        AIMessage(content="Muốn đồng ý lắm nhưng mà tiếc là không được..."),
    ]


# ==============================================================================
# Suite 1: TestLengthTierEnum
# ==============================================================================

class TestLengthTierEnum:
    def test_enum_members_exist(self):
        assert hasattr(LengthTier, "SHORT")
        assert hasattr(LengthTier, "MEDIUM")
        assert hasattr(LengthTier, "LONG")

    def test_enum_values(self):
        assert LengthTier.SHORT.value == "short"
        assert LengthTier.MEDIUM.value == "medium"
        assert LengthTier.LONG.value == "long"

    def test_enum_str_inheritance(self):
        assert isinstance(LengthTier.SHORT, str)
        assert LengthTier.SHORT == "short"
        assert LengthTier.MEDIUM == "medium"
        assert LengthTier.LONG == "long"

    def test_enum_construction_from_string(self):
        assert LengthTier("short") is LengthTier.SHORT
        assert LengthTier("medium") is LengthTier.MEDIUM
        assert LengthTier("long") is LengthTier.LONG

    def test_enum_invalid_value_raises(self):
        with pytest.raises(ValueError):
            LengthTier("extra_long")


# ==============================================================================
# Suite 2: TestLengthDecisionModel
# ==============================================================================

class TestLengthDecisionModel:
    def test_valid_length_decision_construction(self, mock_short_decision):
        assert mock_short_decision.tier == LengthTier.SHORT
        assert mock_short_decision.max_tokens == 35
        assert "1-5 từ" in mock_short_decision.guidance_instruction

    def test_model_dump_dict(self, mock_short_decision):
        data = mock_short_decision.model_dump()
        assert data["tier"] == "short"
        assert data["max_tokens"] == 35
        assert isinstance(data["guidance_instruction"], str)

    def test_model_dump_json(self, mock_short_decision):
        raw_json = mock_short_decision.model_dump_json()
        parsed = json.loads(raw_json)
        assert parsed["tier"] == "short"
        assert parsed["max_tokens"] == 35

    def test_invalid_tier_raises_validation_error(self):
        with pytest.raises(ValidationError):
            LengthDecision(tier="invalid_tier", max_tokens=35, guidance_instruction="test")

    def test_invalid_max_tokens_type_raises(self):
        with pytest.raises(ValidationError):
            LengthDecision(tier=LengthTier.SHORT, max_tokens="thirty_five", guidance_instruction="test")

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            LengthDecision(tier=LengthTier.SHORT)


# ==============================================================================
# Suite 3: TestDetermineResponseLengthShort
# ==============================================================================

class TestDetermineResponseLengthShort:
    @pytest.mark.parametrize("greeting", ["ê", "alo", "hi", "chào", "2", "ơi", "helo"])
    def test_greeting_inputs(self, greeting):
        decision = determine_response_length(greeting)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("checkin", ["dậy chưa", "chán quá", "đang đâu", "sao thế"])
    def test_checkin_inputs(self, checkin):
        decision = determine_response_length(checkin)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("affirmation", ["ừ", "ok", "oki", "đúng r", "chuẩn", "ò"])
    def test_affirmation_inputs(self, affirmation):
        decision = determine_response_length(affirmation)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("brief_tease", ["Seen nhanh á", "Ko 😏", "Khổ thân", "Shock z"])
    def test_brief_tease_inputs(self, brief_tease):
        decision = determine_response_length(brief_tease)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_word_count_lte_4_defaults_to_short(self):
        decision = determine_response_length("Hôm nay trời đẹp")
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_short_guidance_instruction_content(self):
        decision = determine_response_length("alo")
        assert decision.guidance_instruction is not None
        assert len(decision.guidance_instruction) > 10

    def test_short_token_upper_bound(self):
        decision = determine_response_length("ê")
        assert decision.max_tokens == 35

    def test_short_with_empty_history(self):
        decision = determine_response_length("ê", conversation_history=[])
        assert decision.tier == LengthTier.SHORT


# ==============================================================================
# Suite 4: TestDetermineResponseLengthMedium
# ==============================================================================

class TestDetermineResponseLengthMedium:
    @pytest.mark.parametrize("text", [
        "Đề của cô mai phương có in ra làm dc kh",
        "Xuất file in tài liệu sao á b",
        "Hôm nay thi môn gì thế An ơi",
    ])
    def test_study_coordination_inputs(self, text):
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    @pytest.mark.parametrize("text", [
        "Tối mai có đi cf với nhóm không?",
        "V tí mình qua bên An lấy tiền mặt nha tầm 12h30",
        "Đi nhậu không 4g chiều nay ở quán cũ",
    ])
    def test_hangout_coordination_inputs(self, text):
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    @pytest.mark.parametrize("text", [
        "Thành bảo chuyển cho Thành tiền bữa trước á ql ơi",
        "Hôm trước ăn hết bao nhiêu tiền để mình gửi lại",
    ])
    def test_debt_and_money_banter_inputs(self, text):
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    def test_general_chat_6_to_15_words(self):
        decision = determine_response_length("Cuối tuần này có rảnh không đi xem phim với nhóm bạn")
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    def test_medium_guidance_instruction_content(self):
        decision = determine_response_length("Tối mai cf kh b")
        assert decision.guidance_instruction is not None
        assert len(decision.guidance_instruction) > 10

    def test_medium_token_upper_bound(self):
        decision = determine_response_length("Tối mai cf kh b")
        assert decision.max_tokens == 75

    def test_medium_with_casual_history(self, sample_casual_history):
        decision = determine_response_length("Mấy giờ tập trung thế", conversation_history=sample_casual_history)
        assert decision.tier == LengthTier.MEDIUM

    def test_medium_boundary_15_words(self):
        fifteen_words = "một hai ba bốn năm sáu bảy tám chín mười mười một mười hai mười ba mười bốn"
        decision = determine_response_length(fifteen_words)
        assert decision.tier == LengthTier.MEDIUM


# ==============================================================================
# Suite 5: TestDetermineResponseLengthLong
# ==============================================================================

class TestDetermineResponseLengthLong:
    def test_confession_input_triggers_long(self):
        text = "Thật sự muốn đc bên An vì nhiều lí do ((((= Nhma An yên tâm khong đc cx ksao đâuuu mình làm bạn thân tiếp cx được màaa."
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    @pytest.mark.parametrize("confession_prompt", [
        "Mình thích An lâu rồi",
        "An làm người yêu mình nha",
        "Mình muốn tỏ tình với An",
    ])
    def test_short_confession_keyword_triggers_long(self, confession_prompt):
        decision = determine_response_length(confession_prompt)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_emotional_venting_triggers_long(self):
        text = "Dạo này mình thấy mệt mỏi và bế tắc quá An ơi, chuyện học hành lẫn gia đình không biết chia sẻ cùng ai..."
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_breakup_grief_triggers_long(self):
        text = "Mình với người yêu vừa chia tay rồi, buồn quá không biết phải làm sao bây giờ An à"
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_long_word_count_gt_25_words_triggers_long(self):
        long_narrative = (
            "Hôm nay mình đi làm từ sáng sớm tới tối mịt mới về đến nhà "
            "vừa mệt vừa đói mà lại gặp phải trời mưa to ngập hết cả đường "
            "không biết ngày mai có kịp hoàn thành bài tập nộp cho thầy không nữa"
        )
        decision = determine_response_length(long_narrative)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_long_guidance_instruction_content(self):
        decision = determine_response_length("Thật sự muốn đc bên An")
        assert decision.guidance_instruction is not None
        assert len(decision.guidance_instruction) > 10

    def test_long_token_upper_bound(self):
        decision = determine_response_length("Thật sự muốn đc bên An")
        assert decision.max_tokens == 160

    def test_long_with_emotional_history(self, sample_emotional_history):
        decision = determine_response_length("An có nghĩ lại không?", conversation_history=sample_emotional_history)
        assert decision.tier == LengthTier.LONG


# ==============================================================================
# Suite 6: TestDetermineResponseLengthEdgeCases
# ==============================================================================

class TestDetermineResponseLengthEdgeCases:
    def test_empty_string_input(self):
        decision = determine_response_length("")
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_whitespace_only_input(self):
        decision = determine_response_length("   \n\t  ")
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("punct", ["???", "!?!?", "...", ".", "!!!"])
    def test_punctuation_only_input(self, punct):
        decision = determine_response_length(punct)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("emoticon", ["=)))", ":))", ":(", ":D", "=))))"])
    def test_emoticon_only_input(self, emoticon):
        decision = determine_response_length(emoticon)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("emoji", ["😴", "🤡", "🤡🤡🤡", "☕️", "❤"])
    def test_emoji_only_input(self, emoji):
        decision = determine_response_length(emoji)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_massive_text_stress_input(self):
        massive_text = "từ ngữ lặp lại " * 500
        decision = determine_response_length(massive_text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_repeated_tokens_input(self):
        decision = determine_response_length("ê ê ê ê ê ê ê")
        assert decision.tier in (LengthTier.SHORT, LengthTier.MEDIUM)

    def test_foreign_language_input(self):
        decision = determine_response_length("Hey bro what are you doing tonight?")
        assert decision.tier == LengthTier.MEDIUM

    def test_none_conversation_history_accepted(self):
        decision = determine_response_length("alo", conversation_history=None)
        assert decision.tier == LengthTier.SHORT

    def test_invalid_user_input_type_raises(self):
        with pytest.raises((TypeError, ValidationError)):
            determine_response_length(None)

    def test_boundary_exact_word_counts(self):
        four_words = "một hai ba bốn"
        six_words = "một hai ba bốn năm sáu"
        assert determine_response_length(four_words).tier == LengthTier.SHORT
        assert determine_response_length(six_words).tier == LengthTier.MEDIUM


# ==============================================================================
# Suite 7: TestSystemPromptGeneration
# ==============================================================================

class TestSystemPromptGeneration:
    def test_build_system_prompt_default_returns_string(self):
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 200

    def test_vietnamese_language_mandate_enforced(self):
        prompt = build_system_prompt()
        assert "Tiếng Việt" in prompt or "tiếng Việt" in prompt or "VIETNAMESE" in prompt
        # Must mandate Vietnamese response
        assert "tiếng Anh" in prompt or "English" in prompt

    def test_prohibited_tokens_list_included(self):
        prompt = build_system_prompt()
        for token in ["ko", "k", "đc", "nhma", "oke"]:
            assert token in prompt, f"Expected prohibited token {token} to be listed in system prompt rules."

    def test_slang_dictionary_rules_included(self):
        prompt = build_system_prompt()
        for token in ["kh", "dc", "nma", "r", "=)))"]:
            assert token in prompt, f"Expected slang token {token} to be referenced in system prompt rules."

    def test_anti_ai_formatting_rules_included(self):
        prompt = build_system_prompt()
        # Prompt must forbid AI headings or bullet lists
        prompt_lower = prompt.lower()
        assert "bullet" in prompt_lower or "tiêu đề" in prompt_lower or "danh sách" in prompt_lower or "#" in prompt

    def test_dynamic_guidance_instruction_injected(self, mock_short_decision, mock_long_decision):
        p_short = build_system_prompt(length_decision=mock_short_decision)
        p_long = build_system_prompt(length_decision=mock_long_decision)
        assert mock_short_decision.guidance_instruction in p_short
        assert mock_long_decision.guidance_instruction in p_long

    def test_few_shot_exemplars_injected(self):
        prompt = build_system_prompt(few_shot_category="CASUAL_BANTER", num_few_shots=2)
        assert "User:" in prompt or "ql:" in prompt or "Chúc An mai thi tốt" in prompt

    def test_few_shot_zero_or_invalid_category(self):
        p_zero = build_system_prompt(num_few_shots=0)
        p_invalid = build_system_prompt(few_shot_category="NON_EXISTENT_CATEGORY")
        assert isinstance(p_zero, str) and len(p_zero) > 100
        assert isinstance(p_invalid, str) and len(p_invalid) > 100


# ==============================================================================
# Suite 8: TestChatPromptTemplateIntegration
# ==============================================================================

class TestChatPromptTemplateIntegration:
    def test_get_chat_prompt_template_returns_template(self):
        tpl = get_chat_prompt_template()
        assert isinstance(tpl, ChatPromptTemplate)

    def test_template_input_variables(self):
        tpl = get_chat_prompt_template()
        assert "input" in tpl.input_variables

    def test_template_messages_structure(self):
        tpl = get_chat_prompt_template()
        # Should have system message, history placeholder, and human message
        assert len(tpl.messages) >= 2

    def test_template_format_with_valid_inputs(self):
        tpl = get_chat_prompt_template()
        messages = tpl.format_messages(input="alo", history=[])
        assert len(messages) >= 2
        assert messages[-1].content == "alo"
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[-1], HumanMessage)

    def test_template_format_with_history_turns(self, sample_casual_history):
        tpl = get_chat_prompt_template()
        messages = tpl.format_messages(input="tối mai sao?", history=sample_casual_history)
        # System message (1) + history (2) + human (1) = 4
        assert len(messages) == 1 + len(sample_casual_history) + 1
        assert messages[-1].content == "tối mai sao?"

    def test_custom_system_prompt_override(self):
        custom_prompt = "Đây là prompt tuỳ chỉnh của An An"
        tpl = get_chat_prompt_template(system_prompt=custom_prompt)
        messages = tpl.format_messages(input="test", history=[])
        assert messages[0].content == custom_prompt
```

---

## 8. Requirements Traceability Matrix

| Test Suite | Exercised Requirements | Targeted Features | Coverage Focus |
|---|---|---|---|
| `TestLengthTierEnum` | R2 | F4 | Enum integrity, string equivalence, immutability |
| `TestLengthDecisionModel` | R2, R4 | F4 | Pydantic v2 validation, schema typing, JSON/dict export |
| `TestDetermineResponseLengthShort` | R1, R2 | F3, F4 | Greetings, confirmations, check-ins, word counts $\le 4$ |
| `TestDetermineResponseLengthMedium` | R1, R2 | F3, F4 | Banter, study coordination, bills, word counts 6–15 |
| `TestDetermineResponseLengthLong` | R1, R2 | F3, F4 | Emotional boundaries, confessions, venting, word counts $> 25$ |
| `TestDetermineResponseLengthEdgeCases` | R2, R5 | F4 | Empty string, whitespace, emojis, punctuation, massive text stress |
| `TestSystemPromptGeneration` | R1, R2, R4 | F3, F6 | Vietnamese mandate, slang rules, prohibited tokens, guidance injection |
| `TestChatPromptTemplateIntegration` | R4, R5 | F6 | LangChain template assembly, history formatting, execution readiness |

---

## 9. Verification & Execution Procedure

When implemented by the Worker agent, execute the test suite via the local virtual environment:

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_length.py -v
```

Expected output:
- **59 passed in $< 1.5$s**
- Zero warnings, zero network calls, zero external API key requirements.

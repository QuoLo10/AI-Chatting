# Milestone M2 Architecture & Adversarial Review Report

**Reviewer**: Reviewer 1 (Length Architecture Reviewer & Adversarial Critic)  
**Target Milestone**: M2 (Dynamic Response Length & Persona Prompts)  
**Target Files**: `src/core/length_controller.py`, `src/core/prompts.py`, `src/core/__init__.py`, `tests/test_length.py`  
**Date**: 2026-09-14T11:46:00Z  

---

## 1. Review Summary

**Verdict**: **REQUEST_CHANGES**

The implementation of Milestone M2 provides an excellent architectural foundation with 100% contract compliance against `PROJECT.md`, clean LangChain prompt templates, comprehensive anti-AI persona guards, and a passing test suite (170/170 passing tests).

However, during adversarial stress-testing, **critical regex word-boundary deficiencies** were discovered in `src/core/length_controller.py`. Specifically, unanchored keywords such as `ex`, `thích m`, and `thích an` cause everyday casual student conversations (e.g., *"export file ảnh"*, *"file excel nhóm"*, *"thích mua bánh tráng"*, *"thích máy ảnh này kh"*) to be falsely classified into `LengthTier.LONG` (max_tokens=160, 20-50 words) with emotional confession rejection instructions. Additionally, an off-by-one boundary condition classifies 5-word messages into `MEDIUM` despite documented contracts defining `SHORT` as 1–5 words.

These issues directly threaten Persona Mimicry (R1) and Dynamic Response Length (R2) downstream in Milestones M3 and M5, and require minor, straightforward remediation before proceeding.

---

## 2. Integrity Audit

| Check Item | Result | Evidence / Notes |
|---|---|---|
| Hardcoded test results in source code | **PASS** | Evaluated `src/core/length_controller.py` & `src/core/prompts.py`. No input-specific hardcoded returns or cheats detected. Logic dynamically parses word count and regex patterns. |
| Dummy or facade implementations | **PASS** | Genuine implementations of `LengthTier`, `LengthDecision`, `determine_response_length`, `build_system_prompt`, `get_chat_prompt_template`, and few-shot formatting. |
| Shortcuts bypassing intended task | **PASS** | No external APIs or shortcuts used. Proper integration with LangChain core messages and Pydantic v2 schemas. |
| Fabricated verification outputs / logs | **PASS** | Independently executed test suite: 170 passed in 2.20s matching worker report. |
| Self-certifying work without verification | **PASS** | Comprehensive unit test suite with 96 tests covering enums, models, heuristics, prompts, and LangChain templates. |

---

## 3. Interface Compliance against `PROJECT.md`

| Contract Component | `PROJECT.md` Specification | Implementation Status | Verdict |
|---|---|---|---|
| `LengthTier` | `(str, Enum)` with SHORT="short", MEDIUM="medium", LONG="long" | `src/core/length_controller.py:16` | **COMPLIANT** |
| `LengthDecision` | `BaseModel` with `tier`, `max_tokens`, `guidance_instruction` | `src/core/length_controller.py:25` (includes metadata `min_words`, `max_words`, `empirical_ratio`) | **COMPLIANT** |
| `determine_response_length` | `(user_input: str, conversation_history: list = None) -> LengthDecision` | `src/core/length_controller.py:145` | **COMPLIANT** |
| Token limits | SHORT=35, MEDIUM=75, LONG=160 | `TIER_TOKEN_LIMITS` matches exactly | **COMPLIANT** |
| Core exports | Clean exports from `src.core` | `src/core/__init__.py:24-38` | **COMPLIANT** |
| LangChain Template | ChatPromptTemplate with SystemMessage, MessagesPlaceholder, HumanMessage | `src/core/prompts.py:215-238` | **COMPLIANT** |

---

## 4. Detailed Findings

### [Major] Finding 1: False-Positive `LONG` Tier Trigger due to Missing Regex Word Boundaries

- **Where**: `src/core/length_controller.py`, lines 104–115:
  ```python
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
  ```
- **What**:
  Several tokens in `RE_EMOTIONAL_CONFESSION` lack word boundary anchors (`\b`), leading to severe false-positive regex matches on ordinary words:
  1. `ex` without word boundaries matches any word starting with or containing "ex":
     - `"export file ảnh"` -> matches `ex` -> **LONG (160 tokens)**
     - `"file excel nè"` -> matches `ex` -> **LONG (160 tokens)**
     - `"xem example này"` -> matches `ex` -> **LONG (160 tokens)**
     - `"extra cheese nha"` -> matches `ex` -> **LONG (160 tokens)**
  2. `thích m` without trailing boundary matches any sentence starting with "thích m...":
     - `"thích mua bánh tráng nè"` -> matches `thích m` -> **LONG (160 tokens)**
     - `"thích máy ảnh này kh"` -> matches `thích m` -> **LONG (160 tokens)**
     - `"thích màu hồng kh"` -> matches `thích m` -> **LONG (160 tokens)**
     - `"thích mọi người vui vẻ"` -> matches `thích m` -> **LONG (160 tokens)**
  3. `thích an` without trailing boundary matches:
     - `"thích an toàn là trên hết"` -> matches `thích an` -> **LONG (160 tokens)**
  4. `yêu an` and `iu an` without trailing boundary match:
     - `"yêu anime lắm"` -> matches `yêu an` -> **LONG (160 tokens)**
     - `"iu an ninh"` -> matches `iu an` -> **LONG (160 tokens)**
  5. `thích bạn` without boundary matches:
     - `"thích bạn bè tụ tập"` -> matches `thích bạn` -> **LONG (160 tokens)**
- **Why**:
  An An is an art, design, and photography college student who frequently discusses exporting files (`export`), camera equipment (`máy ảnh`), colors (`màu`), and food (`mua bánh`). Falsely routing these 3-to-5 word messages to `LengthTier.LONG` with emotional boundary rejection prompt instructions completely breaks the empirical 70% short distribution and damages persona realism.
- **Remediation**:
  Add word boundaries (`\b`) to isolated words and acronyms:
  - `\bex\b`
  - `\bthích\s+m\b`
  - `\bthích\s+an\b`
  - `\byêu\s+an\b`
  - `\biu\s+an\b`
  - `\bthích\s+bạn\b(?!\s+bè)`

---

### [Medium] Finding 2: Off-by-One Boundary Mismatch on 5-Word Messages

- **Where**: `src/core/length_controller.py`, line 222:
  ```python
  if word_count <= 4:
      tier = LengthTier.SHORT
  ```
- **What**:
  `PROJECT.md` line 77 defines `LengthTier.SHORT` as **1–5 words**.
  `TIER_WORD_BOUNDS[LengthTier.SHORT]` is `(1, 5)`.
  `TIER_GUIDANCE_INSTRUCTIONS[LengthTier.SHORT]` commands: `"CỰC NGẮN (1 - 5 TỪ / 1-5 từ)"`.
  However, `determine_response_length` uses `if word_count <= 4:`.
  Consequently, a 5-word message (such as `"mai có đi học kh"`) is classified as `LengthTier.MEDIUM` with `TIER_WORD_BOUNDS` claiming `(6, 15)`.
- **Why**:
  Internal inconsistency between documented tier definitions and the conditional threshold.
- **Remediation**:
  Change `if word_count <= 4:` to `if word_count <= 5:`.

---

### [Medium] Finding 3: Overly Aggressive Emotional History Follow-Up Condition

- **Where**: `src/core/length_controller.py`, lines 195–207:
  ```python
  if _has_recent_emotional_context(conversation_history):
      # In an emotional context, follow-ups continue in LONG tier
      if "?" in clean_input or word_count >= 4 or any(w in clean_input.lower() for w in ["sao", "nghĩ", "sao?", "kh"]):
          tier = LengthTier.LONG
  ```
- **What**:
  The condition `any(w in clean_input.lower() for w in ["sao", "nghĩ", "sao?", "kh"])` contains `"kh"`. In Vietnamese colloquial chat, `"kh"` is the standard abbreviation for "không" and appears as a prefix in dozens of common words (`"khu"`, `"khuya"`, `"khó"`, `"khỏe"`).
  Furthermore, `"?" in clean_input` triggers `LONG` even on 1-word inputs like `"oki?"` or `"sao?"`.
  As a result, if an emotional turn occurred within the past 4 turns, a 1-word response (`"kh"` or `"oki?"`) or simple question is locked into `LengthTier.LONG` (160 tokens).
- **Why**:
  Chat conversations naturally transition from serious moments back to brief acknowledgments or jokes. Locking short follow-ups into 20-50 word emotional paragraphs prevents natural conversation flow.
- **Remediation**:
  Require a minimum word count (e.g., `word_count >= 5` or `word_count >= 6`) or specific phrases with word boundaries (`\bkh\b` only if part of a longer question) before continuing the `LONG` tier.

---

### [Minor] Finding 4: Sequence Type Constraint in `_has_recent_emotional_context`

- **Where**: `src/core/length_controller.py`, line 135:
  ```python
  if not conversation_history or not isinstance(conversation_history, list):
      return False
  ```
- **What**:
  If a caller passes `conversation_history` as a `tuple` (e.g., `tuple(history)`), `isinstance(..., list)` evaluates to `False` and history is ignored.
- **Remediation**:
  Change to `isinstance(conversation_history, (list, tuple))`.

---

## 5. Adversarial Challenge Matrix

| Test Case / Input | Expected Tier | Actual Tier Result | Result |
|---|---|---|---|
| `"export file ảnh"` | SHORT / MEDIUM | **LONG** (matched `ex`) | **FAIL** (Finding 1) |
| `"file excel nè"` | SHORT / MEDIUM | **LONG** (matched `ex`) | **FAIL** (Finding 1) |
| `"thích mua trà sữa kh"` | SHORT (5 words) | **LONG** (matched `thích m`) | **FAIL** (Finding 1) |
| `"thích máy ảnh này kh"` | SHORT (5 words) | **LONG** (matched `thích m`) | **FAIL** (Finding 1) |
| `"thích an toàn là trên hết"` | MEDIUM | **LONG** (matched `thích an`) | **FAIL** (Finding 1) |
| `"mai có đi học kh"` (5 words) | SHORT (1-5 words) | **MEDIUM** (bounds: 6-15) | **FAIL** (Finding 2) |
| `"kh"` following emotional turn | SHORT | **LONG** (160 tokens) | **FAIL** (Finding 3) |
| Tuple history `(HumanMessage(...),)` | Respects history | Silently ignored (treated as False) | **FAIL** (Finding 4) |
| `"alo"`, `"ê"`, `"hi"` | SHORT | SHORT (max_tokens=35) | **PASS** |
| `""`, `"   "`, `"???"`, `"=)))"`, `"🤡"` | SHORT | SHORT (max_tokens=35) | **PASS** |
| `"Thật sự muốn đc bên An"` | LONG | LONG (max_tokens=160) | **PASS** |
| `> 25 words` narrative | LONG | LONG (max_tokens=160) | **PASS** |
| Non-string input (`None`, `123`) | Raises TypeError | Raises TypeError | **PASS** |
| Massive text (> 500 words) | SHORT-CIRCUITS (>25 words) | LONG without regex hang | **PASS** |

---

## 6. Action Items for Worker M2

1. **Fix regex word boundaries in `RE_EMOTIONAL_CONFESSION`**:
   Ensure `ex`, `thích m`, `thích an`, `yêu an`, `iu an`, `thích bạn` have appropriate word boundaries (`\b`) so they do not match `export`, `excel`, `thích mua`, `thích máy ảnh`, `thích màu`, `thích an toàn`, `yêu anime`.
2. **Fix 5-word boundary in `determine_response_length`**:
   Update `if word_count <= 4:` to `if word_count <= 5:` to align with `PROJECT.md` and `TIER_WORD_BOUNDS[SHORT] = (1, 5)`.
3. **Refine emotional history follow-up condition**:
   Prevent 1-word inputs (`"kh"`, `"oki?"`) from locking into `LONG` tier after an emotional turn.
4. **Broaden history type check**:
   Allow `(list, tuple)` in `_has_recent_emotional_context`.
5. **Add regression tests**:
   Add test cases in `tests/test_length.py` covering `"export file ảnh"`, `"thích mua trà sữa kh"`, `"thích máy ảnh"`, 5-word inputs, and tuple history.

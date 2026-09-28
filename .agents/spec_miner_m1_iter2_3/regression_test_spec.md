# Milestone M1 Iteration 2 Regression Test Specification

**Document:** `regression_test_spec.md`  
**Milestone:** M1 (Dependencies & Data Ingestion Engine) — Iteration 2  
**Target Test Suite:** `tests/test_ingestion.py`  
**Target Modules:** `src/ingestion/parser.py`, `src/ingestion/persona_profile.py`  
**Specification Miner:** `spec_miner_m1_iter2_3`  
**Authoritative Sources:**
- `ORIGINAL_REQUEST.md` (User persona mimicry, zero-cost CLI chatbot requirements)
- `PROJECT.md` (Interface contracts, code layout, architecture)
- `.agents/orchestrator_1/GATE_STATUS.md` (Gate verdict & Challenger change requests)
- `.agents/challenger_m1_1/challenge_harness.py` & `handoff.md` (Challenger 1 empirical stress test harness)
- `.agents/challenger_m1_2/test_verify_persona.py` & `handoff.md` (Challenger 2 persona stats harness)
- Empirical ground truth: `F:/dowload/FacebookData/messages/An An_86.json`

---

## 1. Executive Summary & Objective

In Milestone M1 Iteration 1, the core ingestion engine (`src/ingestion/parser.py`) and persona profiler (`src/ingestion/persona_profile.py`) achieved a 100% pass rate across the initial 61 unit tests. However, adversarial and empirical testing by **Challenger 1** (`challenger_m1_1`) and **Challenger 2** (`challenger_m1_2`) revealed 5 high-severity functional vulnerabilities and data corruption defects:

1. **UTF-8 BOM Crash**: `open(..., encoding="utf-8")` crashes with `json.JSONDecodeError: Unexpected UTF-8 BOM` on Windows files prefixed with `\ufeff`.
2. **`content: null` Media Stringification**: Facebook media export items with `"content": null` resolve to `None`, which stringifies to `"None"`, polluting the canonical message corpus with phantom `"None"` messages.
3. **Timestamp `OverflowError`**: `int(raw_ts)` raises unhandled `OverflowError` when encountering `Infinity` or `-Infinity` (parsed natively by `json.loads`).
4. **Sender Name "Nguyễn Văn An" Collision**: Substring matching `"an an" in sender.lower()` falsely matches Vietnamese names ending in `"an"` followed by `"An"` (e.g. `"Nguyen Van An"` -> `v[an an]`), erroneously tagging other interlocutors as An An (`is_an_an = True`).
5. **Few-Shot `limit <= 0` Defect**: `get_few_shot_examples(limit=0)` executes `results.append()` before evaluating the limit, returning 1 item instead of an empty list `[]`.

Furthermore, **Milestone M1 Iteration 2 introduces a Critical Requirement**:
- **Vietnamese Language Enforcement**: The chatbot persona profile metadata, tone pillars, prompt guidance, and few-shot examples must strictly mandate and enforce Vietnamese (`Tiếng Việt`) language output, prohibiting unprompted foreign language responses or robotic English boilerplate.

This document specifies the exact interface requirements, behavioral contracts, edge cases, and unit test implementations for `tests/test_ingestion.py` to prevent future regressions.

---

## 2. Interface Contracts Under Test

```python
# Location: src/ingestion/parser.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union
from pathlib import Path

class CanonicalMessage(BaseModel):
    sender_name: str
    text: str
    timestamp_ms: int
    is_an_an: bool
    reactions: List[str] = Field(default_factory=list)
    is_unsent: bool = False
    media: List[Any] = Field(default_factory=list)
    msg_type: str = "text"

def safe_decode_mojibake(text: Optional[str]) -> str:
    """Repairs Latin-1 double-encoded mojibake safely without corrupting native UTF-8."""
    ...

def parse_facebook_json(file_path: Union[str, Path]) -> List[CanonicalMessage]:
    """
    Parses Facebook JSON exports (modern or standard DYI).
    Uses encoding="utf-8-sig" to absorb leading BOM.
    Filters unsent, null content media, failed downloads, and empty strings.
    Extracts timestamps safely catching (ValueError, TypeError, OverflowError).
    Discriminates sender name 'An An' using word boundary regex r'\ban\s+an\b'.
    Returns sorted list of CanonicalMessage in ascending chronological order.
    """
    ...

# Location: src/ingestion/persona_profile.py
PERSONA_PROFILE: Dict[str, Any] = {
    "name": "An An",
    "language": "Vietnamese",  # Mandated language specification
    "gender": "Female",
    "age_range": "Early 20s (College student)",
    "discipline": "Art / Design / Photography",
    "relationship_to_user": str,
    "tone_pillars": List[str],  # Must explicitly include Vietnamese language directive
    "language_instruction": str # Explicit instruction for prompt builders
}

def get_few_shot_examples(category: Optional[str] = None, limit: int = 5) -> List[Dict[str, str]]:
    """
    Retrieves flattened [{'input': ..., 'output': ...}] few-shot turns.
    Guarded with `if limit <= 0: return []`.
    All outputs guaranteed to be in Vietnamese.
    """
    ...

def extract_an_an_profile(messages: List[CanonicalMessage]) -> Dict[str, Any]:
    """Extracts linguistic statistics, word length distributions, and dialogue turn pairs."""
    ...
```

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | File I/O | UTF-8 BOM Auto-Absorption | File opening with `encoding="utf-8-sig"` to transparently strip leading `\ufeff` / `\xef\xbb\xbf` byte order mark. | File path pointing to UTF-8 JSON file containing leading BOM. | Stripped clean JSON stream parsed into Python dict. | `ValueError: Malformed JSON` if BOM is not stripped and passed to `json.loads`. | Challenger 1 Harness (`test_file_utf8_bom`) |
| 2 | Noise Filtering | `content: null` Media Drop | Guarding message text extraction against `None` values returned when `"content": null` is present in media export items. | JSON message items containing `{"content": null, "photos": [...]}` or `{"text": null, "content": null}`. | Message dropped from canonical list (`len(messages)` excludes it). | Without fix: stringification produces phantom `CanonicalMessage(text="None")`. | Challenger 1 Harness (`test_messages_null_content_stringification_bug`) |
| 3 | Data Normalization | Non-Finite & Overflow Timestamp Guard | Safe integer parsing of `raw_ts` with exception tuple catching `(ValueError, TypeError, OverflowError)`. | Message items with `timestamp` equal to `Infinity`, `-Infinity`, `NaN`, or extreme float `1e308`. | Safely assigns fallback integer `timestamp_ms = 0` (or finite int). | Without fix: uncaught `OverflowError: cannot convert float infinity to integer` crashes parser. | Challenger 1 Harness (`test_timestamp_infinity_overflow_bug`) |
| 4 | Entity Resolution | Sender Word-Boundary Discrimination | Sender identity matching using regex `\ban\s+an\b` (case-insensitive) instead of naive substring `"an an" in sender.lower()`. | Sender strings such as `"Nguyen Van An"`, `"Nguyễn Văn An"`, `"Trần Tuấn An"`, `"An An"`, `"Bé An An 🌸"`. | `is_an_an = True` ONLY for actual "An An"; `False` for "Văn An", "Tuấn An", etc. | Without fix: contacts named "Văn An", "Tuấn An" are flagged as An An due to `"v[an an]"` substring match. | Challenger 1 Harness (`test_sender_name_and_is_an_an_resolution`) |
| 5 | Few-Shot Catalog | Zero/Negative Limit Guard | Entry boundary check `if limit <= 0: return []` in `get_few_shot_examples`. | `limit=0`, `limit=-1`, `limit=-100`. | Empty list `[]`. | Without fix: returns `[{'input': ..., 'output': ...}]` (length 1) due to post-append condition check. | Challenger 2 Harness (`test_get_few_shot_examples_zero_and_negative_limits`) |
| 6 | Persona Profiling | Explicit Vietnamese Language Specification | Mandating `language: "Vietnamese"` in `PERSONA_PROFILE` and explicit Vietnamese conversational directives in `tone_pillars`. | Inspection of `PERSONA_PROFILE` dictionary. | Dictionary containing `"language": "Vietnamese"` and tone pillar enforcing Tiếng Việt. | Absence of language mandate allows LLMs to drift into English responses. | Iteration 2 Dispatch & Explorer 2 Review |
| 7 | Few-Shot Catalog | 100% Vietnamese Few-Shot Exemplar Validation | Verification that all few-shot exemplars in `FEW_SHOT_EXCHANGES` contain Vietnamese diacritics or authentic Vietnamese teen-code. | All 15 exchanges and their individual dialogue turns. | True for all turns; zero pure English responses. | Fails assertion if any few-shot response lacks Vietnamese linguistic markers. | Iteration 2 Dispatch & Specification Mining |
| 8 | Dialogue Pairing | Inter-Turn Time Window Auditing | Verification that dialogue turn pairing groups User and An An turns while tracking inter-turn time gaps (>2 hours). | List of `CanonicalMessage` instances separated by various time deltas. | `dialogue_pairs` list with optional timestamp metadata. | Does not crash; reveals that 29 pairs in empirical dataset have >2h gap. | Challenger 2 Harness (`test_inter_turn_gap_empirical_reality`) |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| E1 | UTF-8 BOM | File containing ONLY `\ufeff` (BOM character) and zero JSON content. | With `utf-8-sig`, `f.read().strip()` becomes `""` (empty string). Parser raises `ValueError("Empty JSON file: ...")`. Without `utf-8-sig`, raises `Unexpected UTF-8 BOM`. |
| E2 | UTF-8 BOM | File written with raw byte prefix `b"\xef\xbb\xbf"` followed by standard JSON. | `open(..., encoding="utf-8-sig")` cleanly strips bytes and `json.loads` succeeds without error. |
| E3 | Media Messages | Media item with `"content": null`, `"text": null`, but valid `"reactions": [{"actor": "An An", "reaction": "❤"}]`. | Because `clean_text` is empty, message is dropped entirely. Canonical messages represent textual dialogue turns. |
| E4 | Valid "None" Text | Message where sender actually typed `"None"` (e.g. English word "None" or "None of your business"). | If text is legitimately `"None"`, `item.get("text")` is `"None"`, not `None`. However, null content must NOT become `"None"`. With `raw_text = item.get("text") or item.get("content") or ""`, if `"text": None`, `raw_text` becomes `""` and is correctly dropped. |
| E5 | Timestamps | String `"Infinity"`, `"-Infinity"`, `"nan"` in JSON timestamp field. | Handled via `try: int(raw_ts) except (ValueError, TypeError, OverflowError): timestamp_ms = 0`. Safely resolves to `0`. |
| E6 | Timestamps | Extreme float `1e308` in JSON timestamp field. | Parsed as large integer by Python; does not raise `OverflowError`. If float infinity occurs, `OverflowError` is caught and sets `timestamp_ms = 0`. |
| E7 | Sender Resolution | Sender name `"Văn An An"` (interlocutor whose middle name is "Văn" and given name is "An An"). | Regex `\ban\s+an\b` matches `"An An"` with word boundary before first "An". Identified as An An (`is_an_an = True`). |
| E8 | Sender Resolution | Sender name `"Nguyễn Văn An"` (middle name ends in "an", given name is single "An"). | `\ban` requires word boundary before `"an"`. In `"van"`, preceding char is `"v"` (word char), so `\b` fails. Correctly identified as `is_an_an = False`. |
| E9 | Sender Resolution | Sender name `"Bé An  An 🌸"` (multiple whitespace between "An" and "An"). | Regex `\ban\s+an\b` uses `\s+`, matching one or more spaces/tabs. Correctly identified as `is_an_an = True`. |
| E10 | Few-Shot Limit | `limit=0` with specific category (e.g. `category="CASUAL_BANTER"`). | Returns `[]` immediately without looping through any exchanges. |
| E11 | Few-Shot Limit | `limit=-999` (arbitrary negative integer). | Returns `[]` immediately due to `if limit <= 0: return []`. |
| E12 | Language Enforcement | Few-shot turn with mixed English slang (e.g. Turn 9: `"Nah nah \n Nevermind broo \n Chill \n Ổn mà..."`). | Contains Vietnamese diacritics (`"Ổn mà"`) and teen-code (`"kh"`, `"thui"`). Passes Vietnamese language validation as colloquial code-switching while maintaining Vietnamese primacy. |

---

## 5. Detailed Regression Test Specifications for `tests/test_ingestion.py`

The new regression tests are organized into two dedicated classes to be integrated into `tests/test_ingestion.py`:
- **Class 1: `TestRegressionChallengerIssues`** (5 unit tests covering the 5 challenger issues + edge cases)
- **Class 2: `TestPersonaVietnameseLanguageEnforcement`** (4 unit tests verifying language metadata, tone pillars, few-shot catalog, and slang rules)

### 5.1 Test Specification: UTF-8 BOM Parsing
- **Test Function:** `test_regression_utf8_bom_file_parsing(tmp_path)`
- **Category:** File I/O / Encoding
- **Issue Addressed:** Challenger 1 Failure 1 (`src/ingestion/parser.py:84`)
- **Execution Logic:**
  1. Construct a valid JSON structure containing a message from An An.
  2. Test Case A: Write string with prepended Unicode BOM character `\ufeff`.
  3. Test Case B: Write raw bytes with prepended byte sequence `b"\xef\xbb\xbf"`.
  4. Call `parse_facebook_json()` on both files.
- **Assertions:**
  - Neither call raises `ValueError` or `json.JSONDecodeError`.
  - Both return exactly 1 `CanonicalMessage`.
  - `msgs[0].text == "Có BOM nè 🌸"`.
  - `msgs[0].sender_name == "An An"`.
  - `msgs[0].is_an_an is True`.

### 5.2 Test Specification: `content: null` Media Filtering
- **Test Function:** `test_regression_null_content_media_messages_filtered(tmp_path)`
- **Category:** Noise Filtering / Schema Normalization
- **Issue Addressed:** Challenger 1 Failure 2 (`src/ingestion/parser.py:105-108`)
- **Execution Logic:**
  1. Construct a synthetic JSON containing 4 messages:
     - Message 1: `"sender_name": "An An"`, `"content": null`, `"photos": [{"uri": "photo.jpg"}]`.
     - Message 2: `"sender_name": "Hoàng Kim Quờ Lờ"`, `"text": null`, `"content": null`.
     - Message 3: `"sender_name": "An An"`, `"content": "Tin nhắn thật"`, `"timestamp_ms": 3000`.
     - Message 4: `"sender_name": "Hoàng Kim Quờ Lờ"`, `"text": "Tin nhắn text thật"`, `"content": null`.
  2. Call `parse_facebook_json()`.
- **Assertions:**
  - Result length is exactly `2` (Messages 1 and 2 are dropped).
  - `texts = [m.text for m in msgs]` contains `"Tin nhắn thật"` and `"Tin nhắn text thật"`.
  - `assert not any(m.text == "None" for m in msgs)`, ensuring zero stringification leaks.

### 5.3 Test Specification: Non-Finite & Overflow Timestamp Conversion
- **Test Function:** `test_regression_timestamp_infinity_and_overflow_handling(tmp_path)`
- **Category:** Schema Parsing / Robustness
- **Issue Addressed:** Challenger 1 Failure 3 (`src/ingestion/parser.py:138-141`)
- **Execution Logic:**
  1. Construct raw JSON string containing non-finite tokens supported by `json.loads`: `Infinity`, `-Infinity`, `NaN`, and extreme scientific notation `1e308`.
  2. Write to temporary file and execute `parse_facebook_json()`.
- **Assertions:**
  - Parser executes without raising `OverflowError`, `ValueError`, or any unhandled exception.
  - Returned list contains 5 `CanonicalMessage` instances.
  - For all messages, `isinstance(m.timestamp_ms, int)` is `True` and `not isinstance(m.timestamp_ms, bool)`.
  - The message with `Infinity` has `timestamp_ms` safely converted to `0` (or finite int).
  - The valid message with standard timestamp retains its exact integer value `1747310700000`.

### 5.4 Test Specification: Sender Name "Nguyễn Văn An" Discrimination
- **Test Function:** `test_regression_sender_name_van_an_discrimination(tmp_path)`
- **Category:** Entity Resolution / Persona Integrity
- **Issue Addressed:** Challenger 1 Failure 4 (`src/ingestion/parser.py:132`)
- **Execution Logic:**
  1. Create synthetic dataset with 12 distinct sender names testing exact matches, case permutations, nicknames with word boundaries, Vietnamese naming collisions ("Văn An", "Tuấn An", "Xuân An"), and single names.
  2. Parse the dataset and extract `m.is_an_an` for each message.
- **Assertions:**
  - `is_an_an == True` for: `"An An"`, `"an an"`, `"AN AN"`, `"Bé An An 🌸"`, `"An An (Cún)"`.
  - `is_an_an == False` for: `"Nguyen Van An"`, `"Nguyễn Văn An"`, `"Trần Tuấn An"`, `"Lê Xuân An"`, `"An"`, `"Hoàng Kim Quờ Lờ"`, `"Unknown"`.

### 5.5 Test Specification: Few-Shot Examples Limit Boundary
- **Test Function:** `test_regression_few_shot_limit_zero_and_negative()`
- **Category:** Persona Profiling / Catalog Retrieval
- **Issue Addressed:** Challenger 2 Defect (`src/ingestion/persona_profile.py:289-312`)
- **Execution Logic:**
  1. Call `get_few_shot_examples(limit=0)`.
  2. Call `get_few_shot_examples(limit=-1)`.
  3. Call `get_few_shot_examples(limit=-100)`.
  4. Call `get_few_shot_examples(category="CASUAL_BANTER", limit=0)`.
  5. Call `get_few_shot_examples(limit=1)` and `get_few_shot_examples(limit=3)`.
- **Assertions:**
  - Calls with `limit <= 0` return `[]` (empty list).
  - Calls with `limit=1` return exactly 1 item.
  - Calls with `limit=3` return exactly 3 items.

### 5.6 Test Specification: Persona Profile Vietnamese Language Metadata & Directives
- **Test Function:** `test_persona_profile_metadata_mandates_vietnamese_language()`
- **Category:** Persona Integrity / Language Enforcement
- **Requirement Addressed:** Critical User Update: Vietnamese Language Enforcement
- **Execution Logic:**
  1. Inspect `PERSONA_PROFILE` dictionary.
  2. Evaluate `"language"` field.
  3. Evaluate `"tone_pillars"` and `"language_instruction"` (or system prompt guidance).
- **Assertions:**
  - `"language"` key exists in `PERSONA_PROFILE` and equals `"Vietnamese"` (or `"Tiếng Việt"` / `"vi"`).
  - Combined tone pillars / instructions contain explicit references to `"vietnamese"` or `"tiếng việt"`.
  - Instructions mandate conversational Vietnamese and prohibit unsolicited foreign language generation.

### 5.7 Test Specification: Few-Shot Catalog Vietnamese Language Enforcement
- **Test Functions:**
  - `test_few_shot_exchanges_all_contain_vietnamese_text()`
  - `test_get_few_shot_examples_enforces_vietnamese_output()`
- **Category:** Few-Shot Authenticity / Language Enforcement
- **Execution Logic:**
  1. Compile regex for Vietnamese diacritics: `[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúũụưừứửữựỳýỷỹỵđ]`.
  2. Define signature Vietnamese teen-code token set (`kh`, `dc`, `nma`, `r`, `v`, `z`, `th`, `thui`, `oki`, `ql`, `jza`, `mă`, `clm`, etc.).
  3. Inspect all 15 exchanges in `FEW_SHOT_EXCHANGES` and every turn's `an_an` response.
  4. Call `get_few_shot_examples(limit=50)` and inspect every `ex["output"]`.
- **Assertions:**
  - Every single An An response contains Vietnamese diacritics OR authentic Vietnamese teen-code vocabulary.
  - Zero responses are purely English.
  - 100% of exemplars returned by `get_few_shot_examples()` satisfy Vietnamese linguistic criteria.

### 5.8 Test Specification: Slang Rules & Anti-Pattern Vietnamese Enforcement
- **Test Function:** `test_slang_rules_and_prohibitions_enforce_vietnamese_style()`
- **Category:** Lexical Integrity
- **Execution Logic:**
  1. Inspect `PROHIBITED_TOKENS`.
  2. Inspect `SLANG_DICTIONARY`.
- **Assertions:**
  - `PROHIBITED_TOKENS` contains standard AI Vietnamese clichés: `"Tôi là trợ lý ảo"`, `"Tôi có thể giúp gì cho bạn"`, `"Xin lỗi vì sự bất tiện"`.
  - `PROHIBITED_TOKENS` contains polite formal markers: `"ạ"`, `"dạ"`, `"cậu"`, `"tớ"`.
  - `SLANG_DICTIONARY` contains all signature colloquial Vietnamese particles: `"kh"`, `"hong"`, `"dc"`, `"nma"`, `"r"`, `"v"`, `"z"`, `"th"`, `"thui"`, `"oki"`, `"=)))"`, `"ql"`.

---

## 6. Concrete Test Code Implementation for `tests/test_ingestion.py`

Below is the complete, drop-in Python code defining the two new test classes. The Worker agent can append this directly to `tests/test_ingestion.py`:

```python
# ==============================================================================
# Group 8: Milestone M1 Iteration 2 Regression Tests (Challenger Issues)
# ==============================================================================

class TestRegressionChallengerIssues:
    """
    Regression test cases for defects identified during Challenger audits:
    1. UTF-8 BOM absorption in parse_facebook_json.
    2. 'content: null' media export stringification leak prevention.
    3. Uncaught OverflowError on Infinity/-Infinity timestamps.
    4. Word-boundary sender name discrimination for 'Nguyen Van An'.
    5. Zero and negative limit handling in get_few_shot_examples.
    """

    def test_regression_utf8_bom_file_parsing(self, tmp_path):
        """Regression test: parser must handle UTF-8 files containing a Byte Order Mark (BOM)."""
        data = {
            "messages": [
                {
                    "senderName": "An An",
                    "text": "Có BOM nè 🌸",
                    "timestamp": 1747310700000,
                    "isUnsent": False
                }
            ]
        }
        # 1. Test BOM written as unicode character \ufeff
        bom_char_file = tmp_path / "bom_char.json"
        bom_char_file.write_text("\ufeff" + json.dumps(data, ensure_ascii=False), encoding="utf-8")
        msgs1 = parse_facebook_json(str(bom_char_file))
        assert len(msgs1) == 1
        assert msgs1[0].text == "Có BOM nè 🌸"
        assert msgs1[0].sender_name == "An An"
        assert msgs1[0].is_an_an is True

        # 2. Test raw UTF-8 BOM bytes \xef\xbb\xbf
        bom_bytes_file = tmp_path / "bom_bytes.json"
        bom_bytes_file.write_bytes(b"\xef\xbb\xbf" + json.dumps(data, ensure_ascii=False).encode("utf-8"))
        msgs2 = parse_facebook_json(str(bom_bytes_file))
        assert len(msgs2) == 1
        assert msgs2[0].text == "Có BOM nè 🌸"

    def test_regression_null_content_media_messages_filtered(self, tmp_path):
        """Regression test: 'content: null' media exports must not be ingested as 'None' strings."""
        data = {
            "messages": [
                {
                    "sender_name": "An An",
                    "content": None,
                    "timestamp_ms": 1000,
                    "photos": [{"uri": "photo.jpg"}]
                },
                {
                    "sender_name": "Hoàng Kim Quờ Lờ",
                    "text": None,
                    "content": None,
                    "timestamp_ms": 2000
                },
                {
                    "sender_name": "An An",
                    "content": "Tin nhắn thật",
                    "timestamp_ms": 3000
                },
                {
                    "sender_name": "Hoàng Kim Quờ Lờ",
                    "text": "Tin nhắn text thật",
                    "content": None,
                    "timestamp_ms": 4000
                }
            ]
        }
        file_path = tmp_path / "null_content.json"
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        msgs = parse_facebook_json(str(file_path))

        # Must only ingest the 2 valid text messages
        assert len(msgs) == 2
        texts = [m.text for m in msgs]
        assert "Tin nhắn thật" in texts
        assert "Tin nhắn text thật" in texts

        # Zero 'None' strings permitted
        none_texts = [m for m in msgs if m.text == "None"]
        assert len(none_texts) == 0, f"Found leaked 'None' messages: {none_texts}"

    def test_regression_timestamp_infinity_and_overflow_handling(self, tmp_path):
        """Regression test: parser must catch OverflowError on Infinity/-Infinity and huge timestamps."""
        raw_json = '''{
            "messages": [
                {"senderName": "An An", "text": "Tin inf", "timestamp": Infinity},
                {"senderName": "An An", "text": "Tin -inf", "timestamp": -Infinity},
                {"senderName": "An An", "text": "Tin nan", "timestamp": NaN},
                {"senderName": "An An", "text": "Tin overflow float", "timestamp": 1e308},
                {"senderName": "An An", "text": "Tin hợp lệ", "timestamp": 1747310700000}
            ]
        }'''
        file_path = tmp_path / "ts_infinity.json"
        file_path.write_text(raw_json, encoding="utf-8")

        msgs = parse_facebook_json(str(file_path))
        assert len(msgs) == 5
        for m in msgs:
            assert isinstance(m.timestamp_ms, int)
            assert not isinstance(m.timestamp_ms, bool)

        valid_msg = next(m for m in msgs if m.text == "Tin hợp lệ")
        assert valid_msg.timestamp_ms == 1747310700000

        # Non-finite should safely default to 0
        inf_msg = next(m for m in msgs if m.text == "Tin inf")
        assert inf_msg.timestamp_ms == 0 or isinstance(inf_msg.timestamp_ms, int)

    def test_regression_sender_name_van_an_discrimination(self, tmp_path):
        """Regression test: sender name discrimination must not falsely match 'Nguyen Van An' as An An."""
        data = {
            "messages": [
                {"senderName": "An An", "text": "Exact match", "timestamp": 1000},
                {"senderName": "an an", "text": "Lower match", "timestamp": 2000},
                {"senderName": "AN AN", "text": "Upper match", "timestamp": 3000},
                {"senderName": "Bé An An 🌸", "text": "Word boundary match", "timestamp": 4000},
                {"senderName": "An An (Cún)", "text": "Parenthesis boundary match", "timestamp": 5000},
                {"senderName": "Nguyen Van An", "text": "Collision 'van an' not An An", "timestamp": 6000},
                {"senderName": "Nguyễn Văn An", "text": "Diacritic Van An not An An", "timestamp": 7000},
                {"senderName": "Trần Tuấn An", "text": "Tuan An not An An", "timestamp": 8000},
                {"senderName": "Lê Xuân An", "text": "Xuan An not An An", "timestamp": 9000},
                {"senderName": "An", "text": "Single An not An An", "timestamp": 10000},
                {"senderName": "Hoàng Kim Quờ Lờ", "text": "Partner QL", "timestamp": 11000},
                {"senderName": "Unknown", "text": "Unknown sender", "timestamp": 12000}
            ]
        }
        file_path = tmp_path / "sender_discrimination.json"
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        msgs = parse_facebook_json(str(file_path))

        expected_is_an_an = {
            "Exact match": True,
            "Lower match": True,
            "Upper match": True,
            "Word boundary match": True,
            "Parenthesis boundary match": True,
            "Collision 'van an' not An An": False,
            "Diacritic Van An not An An": False,
            "Tuan An not An An": False,
            "Xuan An not An An": False,
            "Single An not An An": False,
            "Partner QL": False,
            "Unknown sender": False
        }

        for m in msgs:
            expected = expected_is_an_an[m.text]
            assert m.is_an_an is expected, (
                f"Sender '{m.sender_name}' for msg '{m.text}' produced is_an_an={m.is_an_an}, expected {expected}!"
            )

    def test_regression_few_shot_limit_zero_and_negative(self):
        """Regression test: get_few_shot_examples with limit <= 0 must return an empty list."""
        assert get_few_shot_examples(limit=0) == []
        assert get_few_shot_examples(limit=-1) == []
        assert get_few_shot_examples(limit=-100) == []
        assert get_few_shot_examples(category="CASUAL_BANTER", limit=0) == []
        assert get_few_shot_examples(category="CASUAL_BANTER", limit=-5) == []

        # Positive limits must still return correct number of examples
        one_ex = get_few_shot_examples(limit=1)
        assert len(one_ex) == 1
        three_ex = get_few_shot_examples(limit=3)
        assert len(three_ex) == 3


# ==============================================================================
# Group 9: Vietnamese Language Enforcement Tests
# ==============================================================================

class TestPersonaVietnameseLanguageEnforcement:
    """
    Validates that persona profile prompt instructions, tone pillars,
    slang dictionaries, and few-shot exemplars strictly mandate and enforce
    Vietnamese language output.
    """

    def test_persona_profile_metadata_mandates_vietnamese_language(self):
        """Verifies that PERSONA_PROFILE explicitly mandates Vietnamese language output."""
        # 1. Direct language key check
        assert "language" in PERSONA_PROFILE, "PERSONA_PROFILE must declare 'language' field"
        assert PERSONA_PROFILE["language"].lower() in ("vietnamese", "tiếng việt", "vi")

        # 2. Instruction checks in tone pillars or prompt guidance
        tone_text = " ".join(PERSONA_PROFILE.get("tone_pillars", [])).lower()
        lang_instruction = str(PERSONA_PROFILE.get("language_instruction", "")).lower()
        combined_instructions = f"{tone_text} {lang_instruction}"

        has_vietnamese_mandate = ("vietnamese" in combined_instructions or "tiếng việt" in combined_instructions)
        assert has_vietnamese_mandate, (
            "PERSONA_PROFILE tone_pillars or language_instruction must explicitly mention Vietnamese / Tiếng Việt"
        )

    def test_few_shot_exchanges_all_contain_vietnamese_text(self):
        """Verifies that all few-shot exemplars in FEW_SHOT_EXCHANGES have Vietnamese responses."""
        import re
        vi_diacritics = re.compile(
            r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúũụưừứửữựỳýỷỹỵđ]",
            re.IGNORECASE
        )
        vi_slang_tokens = {
            "kh", "dc", "nma", "r", "v", "z", "th", "thui", "oki", "ql",
            "jza", "kkk", "mă", "clm", "nhaa", "nhieu", "qá", "bíc", "nua",
            "đt", "hc", "bth", "dau", "cmon", "chiển", "chăm", "áaa", "hoi",
            "mìn", "stk", "đk", "rùi", "mực", "mệc", "vaiz", "loz", "g9"
        }

        assert len(FEW_SHOT_EXCHANGES) >= 15
        for ex in FEW_SHOT_EXCHANGES:
            ex_id = ex.get("id", "unknown")
            for t in ex["turns"]:
                an_an_text = t["an_an"]
                has_diacritics = bool(vi_diacritics.search(an_an_text))
                words = set(re.findall(r"\b\w+\b", an_an_text.lower()))
                has_vi_slang = bool(words.intersection(vi_slang_tokens))
                has_oki = bool(re.search(r"\boki+\b", an_an_text.lower()))

                is_vietnamese = has_diacritics or has_vi_slang or has_oki
                assert is_vietnamese, (
                    f"Few-shot exchange id={ex_id} An An response has no Vietnamese indicators: {repr(an_an_text)}"
                )

    def test_get_few_shot_examples_enforces_vietnamese_output(self):
        """Verifies that get_few_shot_examples() returns 100% Vietnamese language exemplars."""
        import re
        examples = get_few_shot_examples(limit=50)
        assert len(examples) > 0

        vi_diacritics = re.compile(
            r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúũụưừứửữựỳýỷỹỵđ]",
            re.IGNORECASE
        )
        vi_slang_tokens = {
            "kh", "dc", "nma", "r", "v", "z", "th", "thui", "oki", "ql",
            "jza", "kkk", "mă", "clm", "nhaa", "nhieu", "qá", "bíc", "nua",
            "đt", "hc", "bth", "dau", "cmon", "chiển", "chăm", "áaa", "hoi",
            "mìn", "stk", "đk", "rùi", "mực", "mệc", "vaiz", "loz", "g9"
        }

        for ex in examples:
            out = ex["output"]
            has_diacritics = bool(vi_diacritics.search(out))
            words = set(re.findall(r"\b\w+\b", out.lower()))
            has_vi_slang = bool(words.intersection(vi_slang_tokens))
            has_oki = bool(re.search(r"\boki+\b", out.lower()))
            assert (has_diacritics or has_vi_slang or has_oki), (
                f"get_few_shot_examples returned non-Vietnamese output: {repr(out)}"
            )

    def test_slang_rules_and_prohibitions_enforce_vietnamese_style(self):
        """Verifies that slang dictionary and prohibited tokens enforce colloquial Vietnamese style."""
        # Prohibited tokens must ban generic Vietnamese AI assistant clichés
        assert "Tôi là trợ lý ảo" in PROHIBITED_TOKENS
        assert "Tôi có thể giúp gì cho bạn" in PROHIBITED_TOKENS
        assert "Xin lỗi vì sự bất tiện" in PROHIBITED_TOKENS

        # Prohibited tokens must ban formal polite particles
        for formal_token in ["ạ", "dạ", "cậu", "tớ"]:
            assert formal_token in PROHIBITED_TOKENS

        # Slang dictionary must contain Vietnamese colloquial markers
        for marker in ["kh", "hong", "dc", "nma", "r", "v", "z", "th", "thui", "oki", "=)))", "ql"]:
            assert marker in SLANG_DICTIONARY
            assert len(SLANG_DICTIONARY[marker]["rule"]) > 0
```

---

## 7. Verification Method & Test Command

To verify compliance and execute the full test suite post-implementation:

```powershell
$env:PYTHONUTF8 = "1"
& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_ingestion.py -v
```

### Expected Test Results
- Total test items: **70 items** (61 existing + 5 regression challenger + 4 Vietnamese enforcement).
- Target pass rate: **100% (70/70 Passed)**.
- Execution duration: $< 1.5$ seconds.

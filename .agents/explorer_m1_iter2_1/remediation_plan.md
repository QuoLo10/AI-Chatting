# Parser Edge-Case Remediation Plan — Milestone M1 Iteration 2

**Target Module**: `src/ingestion/parser.py`  
**Author**: Explorer Subagent (`explorer_m1_iter2_1` - Parser Edge-Case Remediation Planner)  
**Parent / Consumer**: Worker Agent (`worker_m1`) / Orchestrator  
**Status**: Ready for Implementation  
**Date**: 2026-09-14  

---

## 1. Executive Summary

During Milestone M1 Iteration 1 adversarial evaluation, Challenger 1 (`challenger_m1_1`) identified 4 high-severity vulnerabilities in `src/ingestion/parser.py` causing 4 test failures out of 30 in the challenge harness (86.7% pass rate).

| # | Vulnerability | Severity | Fault Location | Failure Mode | Blast Radius |
|---|---------------|----------|----------------|--------------|--------------|
| 1 | **UTF-8 BOM Crash** | HIGH | `src/ingestion/parser.py:84` | Uncaught `ValueError` (`Unexpected UTF-8 BOM`) | Crash on Windows exports / PowerShell files |
| 2 | **`content: null` Stringification** | HIGH | `src/ingestion/parser.py:105-108` | Media messages stringify `None` -> `"None"` | Persona profile corrupted with phantom `"None"` turns |
| 3 | **`OverflowError` on Infinity** | HIGH | `src/ingestion/parser.py:138-141` | Uncaught `OverflowError` on `int(float('inf'))` | Unhandled crash on non-finite JSON timestamps |
| 4 | **"Văn An" Sender Name Collision** | HIGH | `src/ingestion/parser.py:132` | Substring `"an an"` matches `"Nguyen Van An"` | Foreign contact messages misattributed to An An |

This document provides the Worker with exact line-by-line analyses, root cause breakdowns, proposed code changes, backward-compatibility considerations, and a verification plan.

---

## 2. In-Depth Analysis of the 4 Vulnerabilities

### 2.1 Vulnerability 1: UTF-8 BOM Crash

#### Fault Location
`src/ingestion/parser.py:84`:
```python
# CURRENT CODE
with open(target_path, "r", encoding="utf-8", errors="replace") as f:
```

#### Failure Mechanics & Root Cause
On Windows systems, JSON files generated or saved via PowerShell (`Set-Content`, `Out-File -Encoding utf8`), Windows Notepad, or text editors often prepend a 3-byte Byte Order Mark (BOM: `0xEF, 0xBB, 0xBF`, decoded as `\ufeff`).
When Python opens a file with `encoding="utf-8"`, the BOM character `\ufeff` is retained at index 0 of the string.
When `json.loads(content)` processes this string, Python's JSON parser strictly rejects the BOM:
```
ValueError: Malformed JSON in file <path>: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
```

#### Remediation Specification
Change `encoding="utf-8"` to `encoding="utf-8-sig"`:
```python
# REMEDIATED CODE
with open(target_path, "r", encoding="utf-8-sig", errors="replace") as f:
```

#### Nuance & Safety Checks
- **Superset behavior**: The `"utf-8-sig"` codec transparently detects and strips the leading `\ufeff` BOM if present. If no BOM is present (as in standard UTF-8 files or `An An_86.json`), it decodes standard UTF-8 identically to `"utf-8"`.
- **Empty file handling**: If a file consists solely of the BOM (`\xef\xbb\xbf`), `"utf-8-sig"` decodes it to an empty string `""`. Then `content = f.read().strip()` becomes `""`, triggering `if not content: raise ValueError(f"Empty JSON file: {target_path}")`, correctly raising `ValueError` as expected by `TestFaultToleranceAndEdgeCases`.
- **Error handling**: Keeping `errors="replace"` preserves fault tolerance against corrupted byte sequences.

---

### 2.2 Vulnerability 2: `"content": null` Stringification (`text="None"`)

#### Fault Location
`src/ingestion/parser.py:105-108`:
```python
# CURRENT CODE
raw_text = item.get("text")
if raw_text is None:
    raw_text = item.get("content", "")
clean_text = safe_decode_mojibake(str(raw_text)).strip()
```

#### Failure Mechanics & Root Cause
In official Facebook Messenger DYI exports (`message_1.json`), media messages (photos, videos, stickers, audio, files) explicitly contain `"content": null`.
In Python:
```python
item = {"content": None}
item.get("content", "") # Returns None!
```
Because the dictionary key `"content"` is present in `item`, `.get(key, default)` returns the value stored at that key (`None`), completely ignoring the fallback default `""`.
Consequently:
1. `raw_text` is `None`.
2. `str(raw_text)` evaluates to the literal 4-character string `"None"`.
3. `safe_decode_mojibake("None")` returns `"None"`.
4. `clean_text` becomes `"None"`.
5. Because `"None"` is non-empty, it bypasses the `if not clean_text: continue` check!
6. The message is ingested into `canonical_messages` as `CanonicalMessage(text="None", ...)`.

#### Blast Radius
- Distorts token frequency counters in `src/ingestion/persona_profile.py`.
- Alters length distribution and word count statistics.
- Contaminates dialogue pairs and few-shot examples with nonsensical "None" turns.

#### Remediation Specification
Check for `None` before stringification and filter out non-string/null content:
```python
# REMEDIATED CODE
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

# Drop empty strings, whitespace, or phantom "None" messages
if not clean_text or clean_text == "None":
    continue
```

#### Nuance & Safety Checks
- If both `"text"` and `"content"` are absent or `None`, `raw_text` is `None`, and the loop immediately `continue`s, saving CPU cycles.
- If `raw_text` is not a string (e.g. malformed JSON with numbers or lists in `text`), `not isinstance(raw_text, str)` immediately skips it.
- `safe_decode_mojibake(raw_text)` is called directly with a verified `str`, removing the dangerous `str(None)` coercion.
- The downstream check `if not clean_text or clean_text == "None": continue` acts as an invariant guard.

---

### 2.3 Vulnerability 3: Timestamp `OverflowError` on `Infinity`

#### Fault Location
`src/ingestion/parser.py:138-141`:
```python
# CURRENT CODE
try:
    timestamp_ms = int(raw_ts)
except (ValueError, TypeError):
    timestamp_ms = 0
```

#### Failure Mechanics & Root Cause
Python's standard `json.loads` conforms to ECMAScript extensions by default, parsing numeric tokens `Infinity` and `-Infinity` into `float('inf')` and `float('-inf')`.
When Python executes `int(float('inf'))`, it does not raise `ValueError` or `TypeError`; it raises:
```
OverflowError: cannot convert float infinity to integer
```
Because line 140 only caught `(ValueError, TypeError)`, `OverflowError` escapes uncaught, crashing the entire ingestion process.

#### Remediation Specification
Include `OverflowError` in the exception tuple:
```python
# REMEDIATED CODE
try:
    timestamp_ms = int(raw_ts)
except (ValueError, TypeError, OverflowError):
    timestamp_ms = 0
```

#### Nuance & Safety Checks
- `int()` on arbitrary Python objects can only raise `TypeError`, `ValueError`, or `OverflowError`. Catching all three guarantees that `timestamp_ms` will never crash the parser regardless of input format (negative, non-finite, huge, string, or None).
- When `Infinity` is encountered, `timestamp_ms` safely falls back to `0`.

---

### 2.4 Vulnerability 4: Sender Name False Matching on "Nguyễn Văn An"

#### Fault Location
`src/ingestion/parser.py:132`:
```python
# CURRENT CODE
# Determine if sender is An An
is_an_an = (sender == "An An" or "an an" in sender.lower())
```

#### Failure Mechanics & Root Cause
The substring check `"an an" in sender.lower()` matches across word boundaries without boundary isolation.
In Vietnamese names, "Văn An" is one of the most common male name combinations (e.g. "Nguyễn Văn An", "Trần Văn An"):
- In lowercase: `"nguyen van an"`
- Index 10 to 14: `"v[an an]"`
Because the last two letters of `"van"` are `"an"` and the first two letters of `"an"` are `"an"`, the substring `"an an"` appears naturally across the boundary of the middle name and first name.
Consequently, any friend, family member, or colleague named "Văn An", "Tuấn An", "Xuân An", or "Thuận An" is erroneously flagged as `is_an_an = True`.

#### Blast Radius
If contacts named "Văn An" exist in the chat logs:
- Their text messages are merged into An An's training/persona corpus.
- Persona vocabulary, slang frequencies (`kh`, `dc`, `nma`), and response length distributions are polluted with an unrelated third party's speech patterns.

#### Remediation Specification
Use a pre-compiled word-boundary regular expression at the module level:
```python
# AT MODULE LEVEL (src/ingestion/parser.py)
import re

# Word-boundary regex matching "An An" with arbitrary internal whitespace,
# strictly bounded by word boundaries to reject names like "Nguyễn Văn An".
AN_AN_REGEX = re.compile(r"\ban\s+an\b", re.IGNORECASE)
```

At line 132:
```python
# REMEDIATED CODE (inside loop)
# Determine if sender is An An (exact match or word-boundary regex)
is_an_an = bool(AN_AN_REGEX.search(sender))
```

#### Nuance & Verification on All Name Permutations
Empirically tested behavior:
| Sender Name | Match? | Rationale |
|-------------|--------|-----------|
| `"An An"` | **True** | Exact match bounded by string boundaries |
| `"an an"` | **True** | Case-insensitive match |
| `"AN AN"` | **True** | Case-insensitive match |
| `"Bé An An 🌸"` | **True** | Preceded by space (`\b`) and followed by space/emoji (`\b`) |
| `"An  An"` | **True** | Handles multiple spaces via `\s+` |
| `"Nguyen Van An"` | **False** | `"van"` starts with `v`; `\ban` fails because `v` is a word char |
| `"Trần Tuấn An"` | **False** | `"tuan"` ends with `an`, no `\ban` word boundary |
| `"Lê Xuân An"` | **False** | `"xuan"` ends with `an`, no `\ban` word boundary |
| `"Võ Thuận An"` | **False** | `"thuan"` ends with `an`, no `\ban` word boundary |
| `"Hoàng Kim Quờ Lờ"` | **False** | Partner name, no match |
| `"Unknown"` | **False** | Fallback sender, no match |

Pre-compiling `AN_AN_REGEX` once at module level ensures zero performance degradation, maintaining the >100,000 messages/second ingestion rate.

---

## 3. Concrete Code Changes for Worker

### 3.1 Imports and Module-Level Constants
At the top of `src/ingestion/parser.py`:
```python
import json
import re
from pathlib import Path
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field

# Word-boundary regex matching "An An" with arbitrary internal whitespace,
# strictly bounded by word boundaries to reject names like "Nguyễn Văn An".
AN_AN_REGEX = re.compile(r"\ban\s+an\b", re.IGNORECASE)
```

### 3.2 File Open Change (Line 84)
```python
<<<<
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
====
        with open(target_path, "r", encoding="utf-8-sig", errors="replace") as f:
>>>>
```

### 3.3 Message Text Extraction & Filtering Change (Lines 105-121)
```python
<<<<
        # 2. Extract and transcode message text
        raw_text = item.get("text")
        if raw_text is None:
            raw_text = item.get("content", "")
        clean_text = safe_decode_mojibake(str(raw_text)).strip()

        # Drop unsent messages or explicit unsent markers
        if is_unsent or clean_text == "User unsent a message":
            continue

        # Drop failed media artifacts
        if "failed to download media" in clean_text.lower():
            continue

        # Drop empty strings or media-only messages without accompanying text
        if not clean_text:
            continue
====
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
>>>>
```

### 3.4 Sender Name & `is_an_an` Resolution (Lines 131-133)
```python
<<<<
        # Determine if sender is An An
        is_an_an = (sender == "An An" or "an an" in sender.lower())
====
        # Determine if sender is An An (exact match or word-boundary regex)
        is_an_an = bool(AN_AN_REGEX.search(sender))
>>>>
```

### 3.5 Timestamp Parsing (Lines 138-141)
```python
<<<<
        try:
            timestamp_ms = int(raw_ts)
        except (ValueError, TypeError):
            timestamp_ms = 0
====
        try:
            timestamp_ms = int(raw_ts)
        except (ValueError, TypeError, OverflowError):
            timestamp_ms = 0
>>>>
```

---

## 4. Test Suite Augmentation for `tests/test_ingestion.py`

To prevent regressions and ensure continuous validation in pytest, the Worker should add the following 4 unit test methods to `tests/test_ingestion.py` under `TestFaultToleranceAndEdgeCases`:

```python
    def test_parse_facebook_json_utf8_bom_support(self, tmp_path):
        """Validates that JSON files with UTF-8 BOM are decoded without JSONDecodeError."""
        data = {"messages": [{"senderName": "An An", "text": "Có BOM nè", "timestamp": 1000}]}
        bom_content = "\ufeff" + json.dumps(data)
        file_path = tmp_path / "bom_sample.json"
        file_path.write_text(bom_content, encoding="utf-8")
        
        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].text == "Có BOM nè"
        assert messages[0].is_an_an is True

    def test_parse_facebook_json_null_content_ignored(self, tmp_path):
        """Validates that messages with 'content': null are not stringified into 'None'."""
        data = {
            "messages": [
                {"sender_name": "An An", "content": None, "timestamp_ms": 1000, "photos": [{"uri": "img.jpg"}]},
                {"sender_name": "QL", "text": None, "content": None, "timestamp_ms": 2000},
                {"sender_name": "An An", "content": "Tin nhắn thật", "timestamp_ms": 3000}
            ]
        }
        file_path = tmp_path / "null_content.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")

        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].text == "Tin nhắn thật"
        assert all(m.text != "None" for m in messages)

    def test_parse_facebook_json_timestamp_infinity_overflow(self, tmp_path):
        """Validates that non-finite Infinity timestamps do not raise OverflowError."""
        data_str = '{"messages": [{"senderName": "An An", "text": "Test inf", "timestamp": Infinity}]}'
        file_path = tmp_path / "infinity_ts.json"
        file_path.write_text(data_str, encoding="utf-8")

        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].timestamp_ms == 0

    def test_parse_facebook_json_sender_name_van_an_collision(self, tmp_path):
        """Validates that 'Nguyen Van An' is not flagged as An An due to substring matching."""
        data = {
            "messages": [
                {"senderName": "An An", "text": "Tin 1", "timestamp": 1000},
                {"senderName": "Nguyen Van An", "text": "Tin 2", "timestamp": 2000},
                {"senderName": "Bé An An 🌸", "text": "Tin 3", "timestamp": 3000},
                {"senderName": "Trần Tuấn An", "text": "Tin 4", "timestamp": 4000}
            ]
        }
        file_path = tmp_path / "sender_names.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")

        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 4
        assert messages[0].is_an_an is True
        assert messages[1].is_an_an is False  # Nguyen Van An must be False
        assert messages[2].is_an_an is True   # Bé An An must be True
        assert messages[3].is_an_an is False  # Tran Tuan An must be False
```

---

## 5. Verification Commands

The Worker can independently verify the remediated code using two test commands:

1. **Empirical Challenger Suite (Primary Gate Requirement)**:
   ```powershell
   $env:PYTHONUTF8 = "1"
   & ".\venv\Scripts\python.exe" -X utf8 .agents/challenger_m1_1/challenge_harness.py
   ```
   **Expected Outcome**: `30/30 Passed (100.0%) | 0 Failed` (exit code 0).

2. **Pytest Regression Suite**:
   ```powershell
   & ".\venv\Scripts\pytest" -v tests/test_ingestion.py
   ```
   **Expected Outcome**: `65 passed` (including the 4 new test cases).

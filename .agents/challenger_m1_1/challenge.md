# Adversarial Challenge Report — Milestone M1 Data Ingestion

**Challenger**: Challenger 1 (Data Stress Challenger)  
**Target Module**: `src/ingestion/parser.py` (`safe_decode_mojibake` and `parse_facebook_json`)  
**Overall Risk Assessment**: **HIGH**  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Executive Summary

An adversarial challenge and empirical stress suite containing **30 distinct stress scenarios** was designed and executed against `src/ingestion/parser.py` using Python 3.14 (`venv\Scripts\python.exe`).

### Quantitative Summary
- **Total Stress Scenarios**: 30
- **Passed**: 26 (86.7%)
- **Failed**: 4 (13.3%)
- **Verified Throughput**:
  - `safe_decode_mojibake`: 10 MB payload processed in 0.05 ms (>200,000 MB/s).
  - `parse_facebook_json`: 20,000 messages parsed and filtered in 0.17 seconds (~115,000 messages/second).
  - Sorting stability: 5,000 randomly shuffled messages sorted chronologically in 36.3 ms.

### Verdict Rationale
While the core transcoding engine (`safe_decode_mojibake`) and high-throughput ingestion are fast and handle native UTF-8 and mojibake well, **4 high-severity vulnerabilities** were empirically uncovered in `parse_facebook_json`. Two of these cause unhandled crashes (`OverflowError` on non-finite timestamps, and `JSONDecodeError` on Windows UTF-8 BOM files), while two cause silent data corruption (`content: null` leaking as literal `"None"` message text, and name collision erroneously tagging male contacts named "Văn An" as "An An").

---

## 2. Empirical Failure Modes & Vulnerabilities

### [High] Challenge 1: Null Content Stringification (`content: null` Leaks as `"None"`)

- **Vulnerability**: In standard Facebook Messenger exports, messages without text captions (such as photos, stickers, voice clips, and shared media) explicitly contain `"content": null`.
- **Fault Location**: `src/ingestion/parser.py:105-108`:
  ```python
  raw_text = item.get("text")
  if raw_text is None:
      raw_text = item.get("content", "")
  clean_text = safe_decode_mojibake(str(raw_text)).strip()
  ```
- **Root Cause**: When `"content": null` is present in `item`, `item.get("content", "")` returns `None` because the dictionary key `"content"` exists! The default fallback `""` is never evaluated. Consequently, `raw_text` remains `None`, and `str(raw_text)` converts it into the literal string `"None"`. Because `"None"` is non-empty, it bypasses the `if not clean_text: continue` filter.
- **Empirical Proof**:
  - Input: `{"messages": [{"sender_name": "An An", "content": None, "timestamp_ms": 1000, "photos": [{"uri": "photo.jpg"}]}]}`
  - Observed Output: Emits `CanonicalMessage(sender_name='An An', text='None', ...)`!
  - Test Result: `FAIL [HIGH] Schema/Filtering :: Null Content Stringification` (2 messages ingested with `text='None'`).
- **Blast Radius**: Pollutes persona profiling with false messages consisting of the English word `"None"`. Skews word count distributions, dialogue turn counts, and few-shot examples.
- **Recommended Mitigation**:
  Check for `None` before converting to string:
  ```python
  raw_text = item.get("text")
  if raw_text is None:
      raw_text = item.get("content")
  if raw_text is None:
      continue
  clean_text = safe_decode_mojibake(str(raw_text)).strip()
  if not clean_text or clean_text == "None":
      continue
  ```

---

### [High] Challenge 2: Name Collision on Common Vietnamese Names (`"an an" in sender.lower()`)

- **Vulnerability**: Any Vietnamese contact whose middle name ends in "an" and whose first name is "An" (specifically "Văn An", "Tuấn An", "Xuân An", "Thuận An") is misidentified as the target persona "An An".
- **Fault Location**: `src/ingestion/parser.py:132`:
  ```python
  is_an_an = (sender == "An An" or "an an" in sender.lower())
  ```
- **Root Cause**: The substring check `"an an" in sender.lower()` matches across word boundaries. In Vietnamese male names, "Văn An" is one of the most common names (e.g. "Nguyễn Văn An"). In lowercase:
  `"nguyen van an"` contains `"an an"` at slice `[9:14]` (`"v[an an]"`).
- **Empirical Proof**:
  - Input: `{"senderName": "Nguyen Van An", "text": "Hello", "timestamp": 5000}`
  - Observed Output: `is_an_an = True`!
  - Test Result: `FAIL [HIGH] Schema/Filtering :: Sender Resolution & is_an_an Matching` (Expected `is_an_an=False`, got `True`).
- **Blast Radius**: If the user chats with anyone named "Văn An", their messages are misattributed to An An, injecting an entirely different person's speaking style, vocabulary, and sentiment into An An's profile.
- **Recommended Mitigation**:
  Use word-boundary regex or exact match:
  ```python
  import re
  sender_clean = sender.strip().lower()
  is_an_an = (sender_clean == "an an" or bool(re.search(r"\ban\s+an\b", sender_clean)))
  ```

---

### [High] Challenge 3: Uncaught `OverflowError` Crash on `Infinity` Timestamps

- **Vulnerability**: Python's standard `json.loads` parses JSON tokens `Infinity` and `-Infinity` into `float('inf')` and `float('-inf')`. Calling `int(float('inf'))` raises an unhandled `OverflowError`.
- **Fault Location**: `src/ingestion/parser.py:138-141`:
  ```python
  try:
      timestamp_ms = int(raw_ts)
  except (ValueError, TypeError):
      timestamp_ms = 0
  ```
- **Root Cause**: Line 140 only catches `(ValueError, TypeError)`. It does not catch `OverflowError`.
- **Empirical Proof**:
  - Input: `{"messages": [{"senderName": "An An", "text": "Test", "timestamp": Infinity}]}`
  - Observed Output: `OverflowError: cannot convert float infinity to integer` crashes the entire execution of `parse_facebook_json`.
  - Test Result: `FAIL [HIGH] Schema/Filtering :: Timestamp Infinity OverflowError Crash`.
- **Blast Radius**: Unhandled exception crashes the CLI or ingestion pipeline when encountering malformed or corrupted JSON with non-finite numeric values.
- **Recommended Mitigation**:
  Catch `OverflowError`:
  ```python
  try:
      timestamp_ms = int(raw_ts)
  except (ValueError, TypeError, OverflowError):
      timestamp_ms = 0
  ```

---

### [High] Challenge 4: UTF-8 BOM (`\ufeff`) Crashes Parser on Windows

- **Vulnerability**: Files saved on Windows via PowerShell (`Set-Content`, `Out-File`) or standard Windows text editors often prepend a UTF-8 Byte Order Mark (BOM: `\xef\xbb\xbf` / `\ufeff`).
- **Fault Location**: `src/ingestion/parser.py:84`:
  ```python
  with open(target_path, "r", encoding="utf-8", errors="replace") as f:
  ```
- **Root Cause**: The standard `"utf-8"` codec in Python does not strip the leading BOM. The BOM character `\ufeff` is preserved at the start of the string, causing `json.loads()` to raise:
  `json.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)`.
- **Empirical Proof**:
  - Input: Valid JSON file saved with UTF-8 BOM (`\ufeff{"messages": [...]}`).
  - Observed Output: Crashed with `ValueError: Malformed JSON in file ...: Unexpected UTF-8 BOM (decode using utf-8-sig)`.
  - Test Result: `FAIL [HIGH] File/JSON :: UTF-8 with Byte Order Mark (BOM)`.
- **Blast Radius**: Any user on Windows who saves, edits, or exports Facebook JSON using Windows tooling will experience an immediate crash upon launching the chatbot.
- **Recommended Mitigation**:
  Use `encoding="utf-8-sig"` instead of `"utf-8"`. The `"utf-8-sig"` codec automatically strips the BOM if present, while decoding normal UTF-8 identically.
  ```python
  with open(target_path, "r", encoding="utf-8-sig", errors="replace") as f:
  ```

---

### [Low / Informational] Challenge 5: String Boolean Coercion on `isUnsent`

- **Vulnerability**: `src/ingestion/parser.py:102`:
  `is_unsent = bool(item.get("isUnsent") or item.get("is_unsent") or False)`
- **Observation**: If a JSON file represents boolean flags as strings (e.g. `{"isUnsent": "false"}`), Python's `bool("false")` evaluates to `True`, causing valid messages to be dropped.
- **Recommended Mitigation**:
  Check boolean values explicitly:
  ```python
  val = item.get("isUnsent") if item.get("isUnsent") is not None else item.get("is_unsent", False)
  is_unsent = val is True or str(val).strip().lower() == "true"
  ```

---

## 3. Empirical Stress Test Results Matrix

| # | Test Scenario | Category | Result | Latency | Severity | Notes |
|---|---------------|----------|--------|---------|----------|-------|
| 1 | Native Vietnamese Vowels & Diacritics | Encoding | **PASS** | 0.03 ms | N/A | Full alphabet with all 5 tones preserved |
| 2 | NFD Decomposed Unicode Vowels | Encoding | **PASS** | 0.01 ms | N/A | Combining tone marks passed untouched |
| 3 | Standard Double-Encoded Latin-1 Mojibake | Encoding | **PASS** | 0.01 ms | N/A | "Cám mơn ql nhieu nhaa" recovered |
| 4 | Double-Encoded 4-Byte Emoji Mojibake | Encoding | **PASS** | 0.00 ms | N/A | 💖 recovered from 4 Latin-1 bytes |
| 5 | Mixed Mojibake and Native Unicode String | Encoding | **PASS** | 0.00 ms | N/A | Safely returned without exception |
| 6 | Multilingual Scripts (CJK, Arabic, Cyrillic) | Encoding | **PASS** | 0.00 ms | N/A | All non-Latin scripts preserved |
| 7 | Control Chars, Null Bytes, RTL, ZWJ | Encoding | **PASS** | 0.00 ms | N/A | \x00, RTL marks handled safely |
| 8 | Lone Unicode Surrogates (U+D800, U+DFFF) | Encoding | **PASS** | 0.00 ms | N/A | Handled without crashing |
| 9 | Full 0x00-0xFF Byte Spectrum | Encoding | **PASS** | 0.07 ms | N/A | All 256 byte representations tested |
| 10 | Non-String & Falsy Type Safety | Encoding | **PASS** | 0.01 ms | N/A | None, int, float, bool return "" |
| 11 | 10 MB Massive String Processing | Encoding | **PASS** | 0.05 ms | N/A | Extremely fast (>200 GB/s) |
| 12 | Non-Existent File Path | File/JSON | **PASS** | 0.35 ms | N/A | Raises FileNotFoundError correctly |
| 13 | Path is Directory instead of File | File/JSON | **PASS** | 7.66 ms | N/A | Raises PermissionError/ValueError |
| 14 | Empty & Whitespace-Only File | File/JSON | **PASS** | 3.05 ms | N/A | Raises ValueError correctly |
| 15 | Malformed / Truncated JSON Syntax | File/JSON | **PASS** | 5.79 ms | N/A | Raises ValueError on bad syntax |
| 16 | Non-Dict Root JSON (array, primitive) | File/JSON | **PASS** | 6.87 ms | N/A | Rejects non-dict root structures |
| 17 | Missing or Non-List 'messages' Field | File/JSON | **PASS** | 3.84 ms | N/A | Rejects invalid schemas |
| 18 | UTF-8 with Byte Order Mark (BOM) | File/JSON | **FAIL** | 0.68 ms | **HIGH** | `Unexpected UTF-8 BOM` error |
| 19 | Deeply Nested Unrelated Objects (150 levels)| File/JSON | **PASS** | 1.77 ms | N/A | No recursion limit or memory crash |
| 20 | Non-Dict Items in 'messages' Array | Schema | **PASS** | 2.77 ms | N/A | Safely skipped |
| 21 | Null Content Stringification (`content: null`)| Schema | **FAIL** | 1.07 ms | **HIGH** | Ingested text='None' |
| 22 | Unsent Messages Permutations | Schema | **PASS** | 0.61 ms | N/A | Filtered correctly |
| 23 | System Calls & Media Failures | Schema | **PASS** | 0.53 ms | N/A | Filtered correctly |
| 24 | Timestamp Infinity OverflowError | Schema | **FAIL** | 0.56 ms | **HIGH** | Uncaught `OverflowError` crash |
| 25 | Timestamp Formats (float, str, negative, huge)| Schema | **PASS** | 0.81 ms | N/A | Parsed safely into integers |
| 26 | Sender Resolution & is_an_an Matching | Schema | **FAIL** | 1.17 ms | **HIGH** | "Nguyen Van An" flagged as An An |
| 27 | Reactions Corrupted Types & Mojibake Emojis | Schema | **PASS** | 0.81 ms | N/A | Extracted valid reactions |
| 28 | Chronological Sorting (5,000 Shuffled Msgs) | Sorting | **PASS** | 36.30 ms | N/A | Strictly ascending sort verified |
| 29 | High Volume Ingestion (20,000 Messages) | Scalability| **PASS** | 174.21 ms | N/A | ~115,000 msgs/sec |
| 30 | Real Dataset Verification (An An_86.json) | Real Data | **PASS** | 19.31 ms | N/A | 2,032 msgs parsed cleanly |

---

## 4. Unchallenged Areas
- Direct streaming of multi-gigabyte JSON files (exceeding available RAM) was not challenged as standard Facebook Messenger single-chat JSON exports rarely exceed 200 MB.
- Hardware-level disk I/O interruption during `f.read()`.

---

## 5. Final Verdict & Action Items

**Verdict**: **REQUEST_CHANGES**

The worker must address the 4 confirmed high-severity bugs in `src/ingestion/parser.py`:
1. Use `utf-8-sig` when opening files to handle UTF-8 BOM transparently.
2. Guard against `content: null` stringification to prevent `text="None"` phantom messages.
3. Catch `OverflowError` in timestamp parsing alongside `ValueError` and `TypeError`.
4. Fix `is_an_an` resolution to use word-boundary matching or exact matching, preventing "Văn An" name collisions.

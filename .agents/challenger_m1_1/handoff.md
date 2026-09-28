# Milestone M1 Challenger 1 (Data Stress Challenger) Handoff Report

**Agent**: Challenger 1 (`challenger_m1_1` - Data Stress Challenger)  
**Milestone**: M1 (Dependencies & Data Ingestion Engine)  
**Project Root**: `C:\Users\HKQL2\Documents\ExBuild`  
**Working Directory**: `C:\Users\HKQL2\Documents\ExBuild\.agents\challenger_m1_1`  
**Report Date**: 2026-09-14  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

Direct empirical observations obtained by executing `.agents/challenger_m1_1/challenge_harness.py` via `.\venv\Scripts\python.exe -X utf8`:

### 1.1 Verbatim Failures and Locations

1. **Failure 1: UTF-8 BOM Crash**
   - **Path & Line**: `src/ingestion/parser.py:84`:
     ```python
     with open(target_path, "r", encoding="utf-8", errors="replace") as f:
     ```
   - **Verbatim Error**:
     ```
     ValueError: Malformed JSON in file C:\Users\HKQL2\AppData\Local\Temp\tmpmukl3y8g.json: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
     ```
   - **Trigger**: Any JSON file containing the standard Windows UTF-8 Byte Order Mark (`\ufeff` / `\xef\xbb\xbf`).

2. **Failure 2: Null Content Stringification (`content: null` Leaks as `"None"`)**
   - **Path & Line**: `src/ingestion/parser.py:105-108`:
     ```python
     raw_text = item.get("text")
     if raw_text is None:
         raw_text = item.get("content", "")
     clean_text = safe_decode_mojibake(str(raw_text)).strip()
     ```
   - **Verbatim Empirical Observation**:
     ```
     VULNERABILITY CONFIRMED: 2 message(s) ingested with text='None' due to stringification of null content! Total msgs: 3
     ```
   - **Trigger**: Standard Facebook export items representing photo/media messages where `"content": null`. In Python, `{"content": None}.get("content", "")` returns `None`. `str(None)` produces `"None"`, which is not empty and gets ingested as a real message.

3. **Failure 3: Uncaught `OverflowError` on `Infinity` Timestamps**
   - **Path & Line**: `src/ingestion/parser.py:138-141`:
     ```python
     try:
         timestamp_ms = int(raw_ts)
     except (ValueError, TypeError):
         timestamp_ms = 0
     ```
   - **Verbatim Error**:
     ```
     OverflowError: cannot convert float infinity to integer
     ```
   - **Trigger**: JSON containing numeric token `Infinity` or `-Infinity` (parsed by Python's `json.loads` as `float('inf')`). Line 140 only catches `(ValueError, TypeError)`, omitting `OverflowError`.

4. **Failure 4: Sender Resolution False Positive on Vietnamese Middle Names**
   - **Path & Line**: `src/ingestion/parser.py:132`:
     ```python
     is_an_an = (sender == "An An" or "an an" in sender.lower())
     ```
   - **Verbatim Empirical Observation**:
     ```
     Flags mismatch: expected [True, True, True, True, False, False, True, False], got [True, True, True, True, True, False, True, False]
     ```
   - **Trigger**: Sender `"Nguyen Van An"`. Because `'an an' in 'nguyen van an'.lower()` evaluates to `True` across word boundaries (`"v[an an]"`), all contacts named "Văn An", "Tuấn An", "Xuân An", etc., are erroneously tagged as `is_an_an = True`.

### 1.2 Quantitative Benchmark Results
- **Overall Suite**: 26 passed, 4 failed out of 30 tests (86.7% pass rate).
- **Encoding Engine (`safe_decode_mojibake`)**: 100% pass across all 11 tests, including full Vietnamese vowels/tones, NFD decomposed characters, emojis, multilingual scripts, and 10 MB payload in 0.05ms (>200,000 MB/s).
- **Throughput (`parse_facebook_json`)**: 20,000 messages parsed and filtered in 0.17 seconds (~115,000 messages/sec).
- **Sorting**: 5,000 shuffled messages sorted chronologically in 36.3 ms.
- **Real Dataset (`An An_86.json`)**: Successfully parsed 2,032 canonical messages in 19.3 ms.

---

## 2. Logic Chain

1. **Observation 1.1 (Failure 1)** proves that `open(..., encoding="utf-8")` fails on valid JSON files containing a UTF-8 BOM, a common occurrence on Windows environments. Replacing `"utf-8"` with `"utf-8-sig"` natively resolves this without breaking plain UTF-8.
2. **Observation 1.1 (Failure 2)** proves that `dict.get("content", "")` does NOT substitute `""` when the key `"content"` is present in the dictionary with value `None`. `str(None)` evaluates to `"None"`, producing spurious `CanonicalMessage(text="None")`.
3. **Observation 1.1 (Failure 3)** proves that `int(float('inf'))` raises `OverflowError`. Because line 140 only catches `(ValueError, TypeError)`, this causes an uncaught crash when processing non-finite numbers.
4. **Observation 1.1 (Failure 4)** proves that `"an an" in sender.lower()` matches any string with the character sequence `a-n- -a-n`, which naturally occurs in the common Vietnamese naming pattern "Văn An". This directly corrupts An An's persona profiling dataset.
5. Therefore, while the core transcoding is high-performance, `src/ingestion/parser.py` is vulnerable to 2 crashes and 2 data corruption failure modes in realistic chat environments.

---

## 3. Caveats

- The real dataset `F:/dowload/FacebookData/messages/An An_86.json` did not contain `"content": null` messages because modern tool exports emit `text: ""` for media. However, standard official Facebook DYI exports (`message_1.json`) frequently use `"content": null`.
- Non-finite numbers (`Infinity`) are non-standard in strict JSON specifications (RFC 8259), but Python's standard `json.loads` permits them by default, exposing the parser to `OverflowError`.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

`src/ingestion/parser.py` cannot be approved in its current state due to 4 high-severity vulnerabilities:
1. **UTF-8 BOM Crash**: Change `encoding="utf-8"` to `encoding="utf-8-sig"` in `parse_facebook_json`.
2. **`content: null` Stringification**: Guard against `None` text before stringification to avoid phantom `"None"` messages.
3. **`OverflowError` Crash**: Add `OverflowError` to the exception tuple in line 140.
4. **"Văn An" Name Collision**: Replace substring check with word-boundary regex (`\ban\s+an\b`) or strict name checking.

---

## 5. Verification Method

To independently reproduce the failures and verify fixes:

1. **Run the Empirical Challenge Test Suite**:
   ```powershell
   $env:PYTHONUTF8 = "1"
   & ".\venv\Scripts\python.exe" -X utf8 .agents/challenger_m1_1/challenge_harness.py
   ```
   **Current Output**: 26 passed, 4 failed (exit code 1).  
   **Passing Condition Post-Fix**: 30 passed, 0 failed (exit code 0).

2. **Inspect Detailed Report**:
   - Inspect `.agents/challenger_m1_1/challenge.md` for full test breakdown and code snippets.

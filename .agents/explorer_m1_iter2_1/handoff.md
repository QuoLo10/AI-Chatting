# Milestone M1 Iteration 2 Explorer (Parser Edge-Case Remediation Planner) Handoff Report

**Agent**: Explorer 1 (`explorer_m1_iter2_1` - Parser Edge-Case Remediation Planner)  
**Milestone**: M1 (Dependencies & Data Ingestion Engine), Iteration 2  
**Target Module**: `src/ingestion/parser.py`  
**Working Directory**: `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_iter2_1`  
**Date**: 2026-09-14  
**Handoff Type**: Hard Handoff (Investigation & Remediation Planning Complete)  

---

## 1. Observation

Direct empirical observations obtained from executing the test suite and reviewing `src/ingestion/parser.py`, `tests/test_ingestion.py`, and `.agents/challenger_m1_1/challenge_harness.py`:

### 1.1 Verbatim Challenger 1 Failures
Running `.\venv\Scripts\python.exe -X utf8 .agents/challenger_m1_1/challenge_harness.py` reproduced 4 failed tests out of 30:

1. **Failure 1: UTF-8 BOM Crash**
   - **Path & Line**: `src/ingestion/parser.py:84`:
     ```python
     with open(target_path, "r", encoding="utf-8", errors="replace") as f:
     ```
   - **Verbatim Error**:
     ```
     [FAIL [HIGH]] File/JSON :: UTF-8 with Byte Order Mark (BOM) (0.77ms)
        -> Details: Crashed on BOM: ValueError: Malformed JSON in file C:\Users\HKQL2\AppData\Local\Temp\tmp54ydtfo8.json: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
     ```
   - **Cause**: Windows tools write UTF-8 BOM (`\xef\xbb\xbf` / `\ufeff`). Python's `utf-8` codec preserves the character; Python's `json.loads` rejects leading BOM.

2. **Failure 2: Null Content Stringification (`content: null` Leaking as `"None"`)**
   - **Path & Line**: `src/ingestion/parser.py:105-108`:
     ```python
     raw_text = item.get("text")
     if raw_text is None:
         raw_text = item.get("content", "")
     clean_text = safe_decode_mojibake(str(raw_text)).strip()
     ```
   - **Verbatim Error**:
     ```
     [FAIL [HIGH]] Schema/Filtering :: Null Content Stringification (content: null leak) (1.41ms)
        -> Details: VULNERABILITY CONFIRMED: 2 message(s) ingested with text='None' due to stringification of null content! Total msgs: 3
     ```
   - **Cause**: `{"content": None}.get("content", "")` returns `None` (key is present). Then `str(None)` produces `"None"`, which is non-empty and passes `if not clean_text: continue`.

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
     [FAIL [HIGH]] Schema/Filtering :: Timestamp Infinity OverflowError Crash (1.76ms)
        -> Details: VULNERABILITY CONFIRMED: int(raw_ts) crashed with uncaught OverflowError on Infinity! Line 140 only catches (ValueError, TypeError).
     ```
   - **Cause**: Non-finite float `float('inf')` parsed by `json.loads` raises `OverflowError: cannot convert float infinity to integer` upon `int(float('inf'))`. Line 140 only caught `(ValueError, TypeError)`.

4. **Failure 4: Sender Name False Positive on "Nguyễn Văn An"**
   - **Path & Line**: `src/ingestion/parser.py:132`:
     ```python
     is_an_an = (sender == "An An" or "an an" in sender.lower())
     ```
   - **Verbatim Error**:
     ```
     [FAIL [HIGH]] Schema/Filtering :: Sender Resolution & is_an_an Matching (1.09ms)
        -> Details: Flags mismatch: expected [True, True, True, True, False, False, True, False], got [True, True, True, True, True, False, True, False]
     ```
   - **Cause**: Sender `"Nguyen Van An"` in lowercase contains substring `"an an"` across word boundaries (`"v[an an]"`), incorrectly setting `is_an_an = True`.

### 1.2 Empirical Simulation of Remediated Parser
By injecting the proposed remediation via in-memory monkeypatching, the challenge harness was re-executed:
```
================================================================================
CHALLENGE SUMMARY: 30/30 Passed (100.0%) | 0 Failed
================================================================================
```
And pytest regression suite:
```
============================= 61 passed in 1.43s ==============================
```
Zero regressions across all 61 existing ingestion and persona profiling tests.

---

## 2. Logic Chain

1. **From Observation 1.1 (Failure 1)**: Replacing `encoding="utf-8"` with `encoding="utf-8-sig"` at line 84 removes the leading BOM byte signature if present, and leaves normal UTF-8 unchanged. This directly eliminates `json.JSONDecodeError: Unexpected UTF-8 BOM` on Windows files without altering behavior on non-BOM files.
2. **From Observation 1.1 (Failure 2)**: Adding `if raw_text is None or not isinstance(raw_text, str): continue` directly intercepts `None` or absent text values before `safe_decode_mojibake()` is called. Guarding downstream with `if not clean_text or clean_text == "None": continue` guarantees no phantom `"None"` messages are ingested into `canonical_messages`.
3. **From Observation 1.1 (Failure 3)**: Adding `OverflowError` to the exception tuple in line 140 (`except (ValueError, TypeError, OverflowError):`) handles `int(float('inf'))` and `int(float('-inf'))`, safely falling back to `timestamp_ms = 0` and preventing parser crashes.
4. **From Observation 1.1 (Failure 4)**: Pre-compiling `AN_AN_REGEX = re.compile(r"\ban\s+an\b", re.IGNORECASE)` enforces word boundaries around "an an". In `"Nguyen Van An"`, `"van"` has a word character `"v"` immediately preceding `"an"`, which fails `\ban`. Meanwhile, `"An An"`, `"an an"`, and `"Bé An An 🌸"` match `\ban\s+an\b` correctly.
5. **From Observation 1.2**: Empirical execution of all 30 challenge tests confirms 100% pass rate with zero regression on existing 61 unit tests and real dataset parsing.
6. **Therefore**: The remediation plan documented in `remediation_plan.md` provides an exact, verified, and complete blueprint for the Worker.

---

## 3. Caveats

- **Challenger 2 finding**: Challenger 2's finding regarding `persona_profile.py` (`limit <= 0` guard in `get_few_shot_examples`) is out of scope for this report and is handled by the dedicated subagent (`explorer_m1_iter2_2`).
- **Strict RFC 8259 compliance**: `json.loads` allows `Infinity` by default. While non-standard in RFC 8259, real-world data occasionally contains it; catching `OverflowError` makes the parser robust to all Python `json` outputs.
- **No production code modified**: In compliance with the Explorer archetype, no production code in `src/` or `tests/` was altered during this task.

---

## 4. Conclusion

The 4 vulnerabilities in `src/ingestion/parser.py` are fully understood, mathematically isolated, and empirically verified.
The remediation strategy is finalized in:
`C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_iter2_1\remediation_plan.md`

Summary of required Worker changes:
1. `src/ingestion/parser.py`: import `re`, define `AN_AN_REGEX = re.compile(r"\ban\s+an\b", re.IGNORECASE)` at module level.
2. `src/ingestion/parser.py:84`: use `encoding="utf-8-sig"`.
3. `src/ingestion/parser.py:105-121`: guard `raw_text is None`, skip non-string types, guard `clean_text == "None"`.
4. `src/ingestion/parser.py:132`: set `is_an_an = bool(AN_AN_REGEX.search(sender))`.
5. `src/ingestion/parser.py:140`: catch `(ValueError, TypeError, OverflowError)`.
6. `tests/test_ingestion.py`: append 4 unit tests to permanently cover these edge cases.

---

## 5. Verification Method

To independently verify the proposed remediation once applied by the Worker:

1. **Run Challenger 1 Stress Harness**:
   ```powershell
   $env:PYTHONUTF8 = "1"
   & ".\venv\Scripts\python.exe" -X utf8 .agents/challenger_m1_1/challenge_harness.py
   ```
   **Pass Condition**: 30 passed, 0 failed (exit code 0).

2. **Run Pytest Regression Suite**:
   ```powershell
   & ".\venv\Scripts\pytest" -v tests/test_ingestion.py
   ```
   **Pass Condition**: 100% tests pass (exit code 0).

3. **Inspect Implementation Artifact**:
   Review `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_iter2_1\remediation_plan.md`.

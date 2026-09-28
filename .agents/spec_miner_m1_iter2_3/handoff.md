# Milestone M1 Iteration 2 Regression Test Specifier Handoff Report

**Agent:** Spec Miner (`spec_miner_m1_iter2_3` - Regression Test Specifier)  
**Milestone:** M1 (Dependencies & Data Ingestion Engine) — Iteration 2  
**Project Root:** `C:\Users\HKQL2\Documents\ExBuild`  
**Working Directory:** `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_iter2_3`  
**Report Date:** 2026-09-14  
**Verdict:** **COMPLETE / HARD HANDOFF**  

---

## 1. Observation

1. **Empirical Reproduction of Challenger 1 Issues (`.agents/challenger_m1_1/challenge_harness.py`)**:
   Executing `.\venv\Scripts\python.exe -X utf8 .agents/challenger_m1_1/challenge_harness.py`:
   - `test_file_utf8_bom`: Crashed with `ValueError: Malformed JSON in file ...: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)` at `src/ingestion/parser.py:84`.
   - `test_messages_null_content_stringification_bug`: Logged `VULNERABILITY CONFIRMED: 2 message(s) ingested with text='None' due to stringification of null content! Total msgs: 3` at `src/ingestion/parser.py:105-108`.
   - `test_timestamp_infinity_overflow_bug`: Logged `VULNERABILITY CONFIRMED: int(raw_ts) crashed with uncaught OverflowError on Infinity! Line 140 only catches (ValueError, TypeError)` at `src/ingestion/parser.py:138-141`.
   - `test_sender_name_and_is_an_an_resolution`: Logged `Flags mismatch: expected [True, True, True, True, False, False, True, False], got [True, True, True, True, True, False, True, False]` due to `"Nguyen Van An"` matching substring `"an an"` (`v[an an]`) at `src/ingestion/parser.py:132`.
   - Overall suite: 26 passed, 4 failed (exit code 1).

2. **Empirical Reproduction of Challenger 2 Issue (`.agents/challenger_m1_2/test_verify_persona.py`)**:
   Executing `.\venv\Scripts\python.exe -X utf8 -m pytest .agents/challenger_m1_2/test_verify_persona.py -v`:
   - `test_get_few_shot_examples_zero_and_negative_limits`: Marked `XFAIL`.
   - Executing `get_few_shot_examples(limit=0)` returns `[{'input': 'Chúc An mai thi tốt', 'output': 'Cám mơn ql nhieu nhaa \n ☺️'}]` (length 1) instead of `[]`.
   - Lines 305–311 of `src/ingestion/persona_profile.py` append before checking `len(results) >= limit`, and lack an entry guard for `limit <= 0`.

3. **Current Test Suite Baseline (`tests/test_ingestion.py`)**:
   Executing `.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -v`:
   - 61 passed in 1.29s (exit code 0).
   - Test suite currently lacks test coverage for the 5 challenger issues and explicit assertions for Vietnamese language enforcement.

4. **Persona Profile Metadata & Language Inspection (`src/ingestion/persona_profile.py`)**:
   - `PERSONA_PROFILE`: Contains `"name"`, `"gender"`, `"age_range"`, `"discipline"`, `"relationship_to_user"`, `"tone_pillars"`.
   - Missing explicit `"language": "Vietnamese"` field and explicit prompt directive enforcing Vietnamese responses.
   - All 15 exchanges in `FEW_SHOT_EXCHANGES` contain Vietnamese diacritics or Vietnamese teen-code slang, but lack dedicated regression assertion guards.

---

## 2. Logic Chain

1. **UTF-8 BOM Crash**:
   From Observation 1, opening files with `encoding="utf-8"` does not consume the Unicode BOM character (`\ufeff` / bytes `\xef\xbb\xbf`). Passing the resulting string to `json.loads` raises `json.JSONDecodeError` on Windows. Replacing `"utf-8"` with `"utf-8-sig"` in `parse_facebook_json` strips the BOM seamlessly while continuing to handle standard UTF-8. The regression test `test_regression_utf8_bom_file_parsing` exercises both `\ufeff` string and raw byte inputs.

2. **`content: null` Media Drop**:
   From Observation 1, Facebook Messenger export items for media attachments contain `"content": null`. Python's `item.get("content", "")` returns `None` if the key `"content"` is present in the dictionary. Subsequently, `str(None)` evaluates to `"None"`, producing spurious `CanonicalMessage(text="None")`. Guarding text extraction with `item.get("text") or item.get("content") or ""` ensures that null content resolves to empty string `""` and is filtered out. The regression test `test_regression_null_content_media_messages_filtered` verifies that zero `"None"` messages are ingested.

3. **Timestamp `OverflowError`**:
   From Observation 1, Python's `json.loads` parses numeric literals `Infinity` and `-Infinity` into `float('inf')` and `float('-inf')`. Calling `int(float('inf'))` raises `OverflowError`. Because line 140 of `parser.py` only caught `(ValueError, TypeError)`, the parser crashed. Adding `OverflowError` to the exception tuple allows non-finite timestamps to safely fallback to `0`. The regression test `test_regression_timestamp_infinity_and_overflow_handling` asserts safe conversion for `Infinity`, `-Infinity`, `NaN`, and `1e308`.

4. **Sender Name "Nguyễn Văn An" Collision**:
   From Observation 1, checking `"an an" in sender.lower()` causes a substring collision with any name containing `"van an"`, `"tuan an"`, `"xuan an"`. Using regex word boundary `re.search(r'\ban\s+an\b', sender, re.IGNORECASE)` ensures only the actual name "An An" matches (`is_an_an = True`), while "Nguyen Van An" evaluates to `is_an_an = False`. The regression test `test_regression_sender_name_van_an_discrimination` asserts this discrimination across 12 test names.

5. **Few-Shot `limit <= 0` Guard**:
   From Observation 2, calling `get_few_shot_examples(limit=0)` returned 1 element because the append occurred before checking the limit. Inserting an entry guard `if limit <= 0: return []` immediately fixes the contract. The regression test `test_regression_few_shot_limit_zero_and_negative` verifies limits of `0`, `-1`, `-100`, and with category filters.

6. **Vietnamese Language Enforcement**:
   From Observation 4, the chatbot's primary purpose is authentic mimicry of a Vietnamese student persona. To prevent LLM language drift, `PERSONA_PROFILE` must declare `language: "Vietnamese"` and provide explicit Vietnamese prompt directives in `tone_pillars` and `language_instruction`. The test suite in Group 9 (`TestPersonaVietnameseLanguageEnforcement`) programmatically verifies that metadata mandates Vietnamese, that all few-shot exemplars contain authentic Vietnamese diacritics/slang, and that `PROHIBITED_TOKENS` bans generic AI cliches.

---

## 3. Caveats

- **External Dataset Drive Availability**: Primary verification dataset `F:/dowload/FacebookData/messages/An An_86.json` is located on drive `F:`. Synthetic tests in `tests/test_ingestion.py` use `tmp_path` fixtures so regression verification remains 100% runnable offline in environments without drive `F:`.
- **Slang Diacritic Ambiguity**: Some Vietnamese teen-code terms (e.g. `kh`, `dc`, `nma`, `r`, `v`, `z`, `th`, `thui`, `oki`) do not have diacritics. The test assertion `test_few_shot_exchanges_all_contain_vietnamese_text` combines diacritic detection with a curated slang dictionary token set to reliably validate authentic Vietnamese turns without false negatives.

---

## 4. Conclusion

**Verdict: COMPLETE (HARD HANDOFF)**

The regression test specification has been fully designed, verified, and documented in:
`C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_iter2_3\regression_test_spec.md`

It contains:
- Complete feature discovery and edge case tables.
- 5 unit test specifications for the Challenger issues (UTF-8 BOM, null content media, timestamp overflow, "Nguyễn Văn An" sender name discrimination, `limit <= 0` few-shot guard).
- 4 unit test specifications for Vietnamese language enforcement (profile metadata, few-shot authentic text, few-shot output retrieval, and slang rules/prohibitions).
- Complete, copy-paste ready Python test code structured into `TestRegressionChallengerIssues` (Group 8) and `TestPersonaVietnameseLanguageEnforcement` (Group 9) for immediate implementation by Worker M1.

---

## 5. Verification Method

1. **Inspect Test Specification Document**:
   - Path: `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_iter2_3\regression_test_spec.md`
   - Verify all 5 challenger regression tests and 4 Vietnamese language enforcement tests are documented with assertions.

2. **Execute Existing Test Suite Baseline**:
   ```powershell
   $env:PYTHONUTF8 = "1"
   & ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_ingestion.py -v
   ```
   Current output: 61 passed in ~1.2s.

3. **Execute Post-Worker Target Suite**:
   Once Worker M1 applies the code updates to `src/` and appends the specified tests to `tests/test_ingestion.py`:
   ```powershell
   $env:PYTHONUTF8 = "1"
   & ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_ingestion.py -v
   ```
   Target output: **70 passed in ~1.5s (0 failures, 0 errors)**.

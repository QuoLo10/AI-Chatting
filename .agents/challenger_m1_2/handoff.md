# Milestone M1 Persona Stats Challenger Handoff Report

**Agent**: Challenger 2 (`challenger_m1_2` - Persona Stats Challenger)  
**Milestone**: M1 (Dependencies & Data Ingestion Engine)  
**Project Root**: `C:\Users\HKQL2\Documents\ExBuild`  
**Report Date**: 2026-09-14  
**Verdict**: **REQUEST_CHANGES** (1 Minor Edge-Case Defect Found; Mathematical & Profiling Core Verified)

---

## 1. Observation

1. **Target Files Inspected**:
   - `src/ingestion/persona_profile.py` (lines 15–107: `SLANG_DICTIONARY`, 110–123: `PROHIBITED_TOKENS`, 147–286: `FEW_SHOT_EXCHANGES`, 289–312: `get_few_shot_examples`, 315–464: `extract_an_an_profile`).
   - `src/ingestion/parser.py` (lines 27–50: `safe_decode_mojibake`, 56–176: `parse_facebook_json`).
   - `tests/test_ingestion.py` (61 tests covering parsing, filtering, profiling, and configuration).
   - Raw dataset: `F:/dowload/FacebookData/messages/An An_86.json` (515,161 bytes).

2. **Observed Raw Dataset Ground Truth**:
   - Total raw messages: `2,102`.
   - Dropped noise: `15` unsent + `55` empty/media-only = `70`.
   - Canonical messages: `2,032` (1,174 An An, 858 User).
   - Word count partition across 1,174 An An messages:
     - Short ($\le 5$ words): `822` (`822 / 1174 = 0.700170...` -> 70.0% in code `0.7002`).
     - Medium (6–15 words): `324` (`324 / 1174 = 0.275980...` -> 27.6% in code `0.2760`).
     - Long ($> 15$ words): `28` (`28 / 1174 = 0.023850...` -> 2.4% in code `0.0239`).
     - Mean: `4.70` words (`4.6959...`), Median: `4.0` words.
     - Min: `1`, Max: `92` words.
   - Total grouped turns: `806`.
   - Extracted dialogue pairs: `392`.

3. **Verbatim Defect in `get_few_shot_examples`**:
   Executing:
   ```python
   from src.ingestion.persona_profile import get_few_shot_examples
   get_few_shot_examples(limit=0)
   ```
   Yields:
   ```python
   [{'input': 'Chúc An mai thi tốt', 'output': 'Cám mơn ql nhieu nhaa \n ☺️'}]
   ```
   Expected: `[]`.
   In `src/ingestion/persona_profile.py` (lines 305–311):
   ```python
   for turn in ex["turns"]:
       results.append({
           "input": turn["user"],
           "output": turn["an_an"]
       })
       if len(results) >= limit:
           return results
   ```
   The append executes before the limit condition check, and there is no entry guard for `limit <= 0`.

4. **Observed Inter-Turn Gap in Dialogue Pairs**:
   - In `extract_an_an_profile`, turn pairing checks `not turns[i]["is_an_an"] and turns[i+1]["is_an_an"]` without enforcing an inactivity cutoff between the two distinct senders.
   - In `An An_86.json`, 29 out of 392 pairs (7.4%) have an inter-turn gap $> 2$ hours; 8 pairs have a gap $> 24$ hours; the largest is 248.3 hours (10.3 days).

5. **Observed Prohibited Token Empirical Frequency**:
   - `k`: 0, `đc`: 0, `nhma`: 0, `oke`: 0, `ạ`: 0, `cậu`: 0, `tớ`: 0, `dạ`: 0.
   - `ko`: 2 occurrences in 1,174 messages (Message 883 `"Ko cl"` and Message 1160 `"Trên chợ có nóng ko"`), against 143 occurrences of `kh` (98.6% `kh` dominance).

6. **Test Suite Outputs**:
   - `tests/test_ingestion.py`: 61 passed in 1.13s.
   - `.agents/challenger_m1_2/test_verify_persona.py`: 22 passed, 1 xfailed (documenting `limit=0` defect) in 0.62s.

---

## 2. Logic Chain

1. **Mathematical Precision Logic**:
   - From Observation 2, direct calculation from raw JSON messages gives:
     $822 / 1174 = 70.02\%$, $324 / 1174 = 27.60\%$, $28 / 1174 = 2.39\%$.
   - The values in `extract_an_an_profile` (`short_pct=0.7002`, `medium_pct=0.276`, `long_pct=0.0239`) are mathematically exact and sum to 1,174 items.
   - The mean ($4.7$) and median ($4.0$) match ground truth.
   - Therefore, the mathematical precision claim (70% short, 27.6% med, 2.4% long) is fully validated.

2. **Few-Shot Function Logic Defect**:
   - From Observation 3, when a caller passes `limit=0` (or `limit < 0`), `results.append` executes on the first turn before testing `len(results) >= limit`.
   - Since `1 >= 0` is true, it exits the loop returning a list of length 1.
   - Therefore, zero few-shot examples cannot be requested without receiving 1 example. This violates the `limit` parameter contract and breaks zero-shot prompt building.

3. **Inter-Turn Time Window Logic**:
   - From Observation 4, the 2-hour inactivity grouping applies only to consecutive messages by the *same sender*.
   - When transitioning from User to An An, if days elapse without conversation, An An's subsequent greeting is paired with the user's days-old message.
   - Downstream prompt/retrieval components in M2/M3 must be cautious when sampling from `dialogue_pairs` to avoid non-sequitur training examples.

4. **Lexical Fidelity Logic**:
   - From Observation 5, An An strictly uses `nma` (36 times) and never `nhma` (0 times), while QL uses `nhma` 40 times.
   - An An uses `kh` 143 times, `dc` 42 times, `r` 100 times, `=)))` 81 times, `ql` 40 times.
   - The slang dictionary and anti-pattern guidelines accurately capture An An's genuine voice.

---

## 3. Caveats

- **External Data Availability**: Tests against `F:/dowload/FacebookData/messages/An An_86.json` require access to drive `F:`. If absent on secondary environments, offline fixtures handle regression testing.
- **Bubble vs Turn Length Semantics**: The 70% / 27.6% / 2.4% distribution applies to individual chat bubbles. If messages are aggregated into conversational turns, the distribution shifts toward longer blocks (mean 13.85 words, median 10 words).

---

## 4. Conclusion

The core data ingestion and persona profiling engine is mathematically sound, highly faithful to An An's linguistic quirks, and resilient across edge cases.

However, a concrete functional defect exists in `get_few_shot_examples`:
- **Defect**: Passing `limit=0` or `limit <= 0` returns 1 example instead of `[]`.
- **Verdict**: **REQUEST_CHANGES** (Actionable minor fix required).
- **Remediation**:
  In `src/ingestion/persona_profile.py`, add at the start of `get_few_shot_examples`:
  ```python
  if limit <= 0:
      return []
  ```
  And add a regression test in `tests/test_ingestion.py`.

---

## 5. Verification Method

1. **Execute Challenger Independent Harness**:
   ```powershell
   $env:PYTHONUTF8 = "1"; $env:PYTHONPATH = "."; & ".\venv\Scripts\python.exe" -X utf8 -m pytest .agents/challenger_m1_2/test_verify_persona.py -v
   ```
   **Expected Outcome**: 22 passed, 1 xfailed (confirming `limit=0` bug reproduction), exit code 0.

2. **Execute Full Project Ingestion Test Suite**:
   ```powershell
   $env:PYTHONUTF8 = "1"; & ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_ingestion.py -v
   ```
   **Expected Outcome**: 61 passed in ~1.2s.

3. **Reproduction One-Liner for `limit=0` Defect**:
   ```powershell
   $env:PYTHONUTF8 = "1"; $env:PYTHONPATH = "."; & ".\venv\Scripts\python.exe" -X utf8 -c "from src.ingestion.persona_profile import get_few_shot_examples; assert get_few_shot_examples(limit=0) == []"
   ```
   **Expected Outcome**: `AssertionError: assert [{'input': ...}] == []`.

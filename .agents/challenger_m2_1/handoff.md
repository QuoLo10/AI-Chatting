# Handoff Report: Milestone M2 Length Decision Stress Challenge

**Agent**: Challenger 1 (Length Decision Stress Challenger)  
**Target**: `src/core/length_controller.py`  
**Milestone**: M2  
**Date**: 2026-09-14T11:46:30Z  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

1. **Test Execution & Tool Output**:
   - Executed `.agents/challenger_m2_1/stress_test_harness.py` using `.\venv\Scripts\python.exe -X utf8`:
     - Total tests: 26
     - Passed: 15
     - Failed: 11 (2 Critical, 7 High, 1 Medium, 1 Low)
   - Verbatim terminal failure logs:
     ```
     [FAIL [CRITICAL]] 2.1 Regex 'ex' unanchored substring does not hijack short tech/casual messages to LONG tier: 9/10 phrases misclassified as LONG: [('gửi text cho t', <LengthTier.LONG: 'long'>, '4 words study request'), ('mở file excel nha', <LengthTier.LONG: 'long'>, '4 words study request'), ('next bài đi bạn', <LengthTier.LONG: 'long'>, '4 words casual banter')]
     [FAIL [HIGH]] 2.2 Regex 'thích m' without word boundary does not hijack ordinary preferences to LONG tier: 5/5 preferences misclassified as LONG: [('t thích mua cái này', <LengthTier.LONG: 'long'>, '5 words casual chat'), ('mình thích màu hồng', <LengthTier.LONG: 'long'>, '4 words casual chat'), ('thích môn này kh b', <LengthTier.LONG: 'long'>, '5 words study question')]
     [FAIL [HIGH]] 2.3 Technical / physical terms (khoảng cách, giới hạn, nghĩ lại, mệt mỏi) not hijacked to LONG tier: 5/5 phrases misclassified as LONG: [('khoảng cách bao xa b?', <LengthTier.LONG: 'long'>, '4 words distance question'), ('bài thi không giới hạn thời gian', <LengthTier.LONG: 'long'>, '6 words study info'), ('để mình nghĩ lại đã nha', <LengthTier.LONG: 'long'>, '6 words casual decision')]
     [FAIL [HIGH]] 3.2 Spaced emojis ('🤡 ' * 30) should classify as SHORT, not LONG emotional tier: dense tier=LengthTier.SHORT, spaced tier=LengthTier.LONG (max_tokens=160)
     [FAIL [HIGH]] 3.3 Spaced punctuation ('? ' * 30) should classify as SHORT, not LONG emotional tier: dense tier=LengthTier.SHORT, spaced tier=LengthTier.LONG (max_tokens=160)
     [FAIL [HIGH]] 3.4 Code snippets without emotional intent do not trigger LONG tier: 2/4 code snippets misclassified: [("SELECT * FROM users WHERE context = 'main';", <LengthTier.LONG: 'long'>, <LengthTier.MEDIUM: 'medium'>, "8 words SQL with 'context'"), ('try:     run() except Exception as ex:     pass', <LengthTier.LONG: 'long'>, <LengthTier.MEDIUM: 'medium'>, '8 words Python try/except')]
     [FAIL [LOW]] 3.5 Non-segmented CJK long paragraphs undercount words due to str.split(): 2/2 long foreign paragraphs classified as SHORT (1 word)
     [FAIL [HIGH]] 4.1 Rapid topic shift: casual study question after resolved emotional turn reverts from LONG to MEDIUM/SHORT: Classified as LengthTier.LONG (tokens=160)
     [FAIL [CRITICAL]] 4.2 False positive in history ('text') does not poison subsequent casual turns into LONG tier: Classified as LengthTier.LONG (tokens=160)
     [FAIL [HIGH]] 4.3 Multimodal history format containing 'text' dictionary keys does not poison turns into LONG tier: Classified as LengthTier.LONG (tokens=160)
     [FAIL [MEDIUM]] 1.3.2 Boundary 5 words aligns with SHORT (Spec says 1-5 words): tier=LengthTier.MEDIUM (Implementation classified 5 words as MEDIUM; spec defines SHORT as 1-5 words)
     ```

2. **Source Code Inspection**:
   - `src/core/length_controller.py:109`:
     ```python
     r"làm bạn thôi|mối quan hệ|người cũ|người iu cũ|ex|khoảng cách|rào cản|giới hạn|"
     ```
     `ex` is an unanchored bare substring.
   - `src/core/length_controller.py:108`:
     ```python
     r"tình cảm|crush|thổ lộ|làm bạn gái|thích m|iu an|"
     ```
     `thích m` has no trailing word boundary `\b`.
   - `src/core/length_controller.py:173-182` vs `211-220`:
     Priority 1 checks `if word_count > 25:` before Priority 2 checks `if word_count == 0 or not any(c.isalnum() for c in clean_input):`.
   - `src/core/length_controller.py:195-206`:
     Follow-up check in recent emotional context forces `LONG` tier if `"?" in clean_input or word_count >= 4 or any(w in clean_input.lower() for w in ["sao", "nghĩ", "sao?", "kh"])`.
   - `src/core/length_controller.py:222`:
     `if word_count <= 4: tier = LengthTier.SHORT`, but `PROJECT.md` line 77 and `TIER_WORD_BOUNDS` define `SHORT` as 1-5 words.

---

## 2. Logic Chain

1. **Direct Regex Poisoning (Observation 1, 2)**:
   - In Python, `re.search()` matches any substring unless anchored by `\b` or `^/$`.
   - `ex` in `RE_EMOTIONAL_CONFESSION` matches words like `text`, `excel`, `next`, `complex`, `context`, `export`.
   - As a direct consequence, simple student requests like `"gửi text cho t"` (4 words) are routed to `LengthTier.LONG` with prompt instructions commanding a 20-50 word emotional/boundary essay.
   - Similarly, `thích m` without `\b` matches everyday preferences like `thích mua`, `thích màu`, `thích môn`, `thích mang`.

2. **Session Memory Infection & Sticky History (Observation 1, 2)**:
   - `_has_recent_emotional_context` checks the last 4 turns.
   - Any match in history (genuine or false positive from `ex`) activates the sticky branch.
   - Because `kh` is An An's most frequent slang token and almost all questions contain `?` or $\ge 4$ words, future turns cannot revert to `MEDIUM` or `SHORT`, violating persona dynamic length distribution.

3. **Inverted Evaluation Order (Observation 1, 2)**:
   - Priority 1 checks `word_count > 25` first.
   - A sequence of 30 spaced emojis (`"🤡 " * 30`) or punctuation (`"? " * 30`) splits into 30 whitespace-separated items.
   - This bypasses the alphanumeric emptiness check at line 211 and incorrectly categorizes spam/emojis as a `LONG` emotional conversation.

4. **Conclusion Support**:
   - The above failure modes are reproducible empirically via standalone execution. They directly undermine Requirement R2 (Dynamic Response Length) and the empirical persona distribution (2.4% LONG target vs massively inflated LONG in practice).

---

## 3. Caveats

1. **Offline Scope**: Stress tests were run strictly offline using local python execution without making cloud LLM API calls.
2. **Vietnamese Persona Scope**: CJK paragraph under-counting is low severity because the bot is explicitly specified as a Vietnamese-only persona (`VIETNAMESE_ONLY`).
3. **No Code Modification**: In accordance with the Challenger role constraints ("Review-only — do NOT modify implementation code"), no production files in `src/` were edited. All test scripts are placed strictly in the challenger workspace.

---

## 4. Conclusion

- **Verdict**: **REQUEST_CHANGES**
- The Worker must refine `src/core/length_controller.py`:
  1. Add word boundaries and partner context to `ex` in `RE_EMOTIONAL_CONFESSION` (e.g. `\bex\b` or `r"\b(?:người\s+yêu\s+cũ|ny\s+cũ|ex)\b"`).
  2. Add word boundary to `thích m` $\to$ `r"thích\s+m\b"`.
  3. Contextualize technical/literal keywords (`khoảng cách`, `giới hạn`, `nghĩ lại`, `mệt mỏi`).
  4. Move non-alphanumeric check (`not any(c.isalnum()...)`) before `word_count > 25`.
  5. Decouple rapid topic shifts from sticky emotional history bleed.
  6. Adjust 5-word boundary from `<= 4` to `<= 5`.

---

## 5. Verification Method

To independently reproduce all empirical findings and test results:

```powershell
& ".\venv\Scripts\python.exe" -X utf8 .agents/challenger_m2_1/stress_test_harness.py
```

**Expected Result**:
- Total Tests: 26
- Passed: 15
- Failed: 11 (2 Critical, 7 High, 1 Medium, 1 Low)
- Final Verdict: `REQUEST_CHANGES`

To re-run existing project tests:
```powershell
& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_length.py tests/test_ingestion.py -v
```
(Expected: 170 passed, confirming that existing unit tests lack adversarial negative tests).

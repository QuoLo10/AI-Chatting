# Adversarial Challenge Report: Dynamic Response Length Controller

**Challenger**: Challenger 1 (Length Decision Stress Challenger)  
**Target Module**: `src/core/length_controller.py` (`determine_response_length`)  
**Milestone**: M2  
**Harness**: `.agents/challenger_m2_1/stress_test_harness.py`  
**Execution Timestamp**: 2026-09-14T11:45:26Z  
**Verdict**: **REQUEST_CHANGES**  

---

## Challenge Summary

- **Overall Risk Assessment**: **CRITICAL**
- **Test Harness Results**: 26 tests executed, 15 passed, **11 failed** (2 Critical, 7 High, 1 Medium, 1 Low).
- **Core Findings**:
  1. `RE_EMOTIONAL_CONFESSION` contains the unanchored token `ex` without word boundaries (`\b`), causing any word with "ex" (e.g. `text`, `excel`, `next`, `complex`, `context`, `export`, `exception`, `index`) to be hijacked into `LengthTier.LONG` (20-50 words, max_tokens=160).
  2. The same `ex` token matches LangChain multimodal message representations `{'type': 'text'}`, permanently poisoning conversation history.
  3. `_has_recent_emotional_context` combined with oversensitive follow-up triggers causes sticky history bleed: rapid topic shifts from emotional boundaries to casual study questions remain trapped in `LONG` tier.
  4. The unanchored prefix `thích m` (meant for "thích mày") lacks word boundaries, matching common preferences like `thích mua`, `thích mang`, `thích màu`, `thích môn này`.
  5. Priority inversion: word count check (`word_count > 25`) precedes the non-alphanumeric check, causing repetitive spaced emojis (`"🤡 " * 30`) or punctuation (`"? " * 30`) to trigger 20-50 word emotional essay responses.
  6. Off-by-one boundary mismatch: 5-word inputs are classified as `MEDIUM` despite the specification defining `SHORT` as 1-5 words.

---

## Challenges

### [Critical] Challenge 1: Unanchored Substring `ex` in `RE_EMOTIONAL_CONFESSION`

- **Assumption challenged**: `RE_EMOTIONAL_CONFESSION` in `src/core/length_controller.py:109` only detects emotional topics, breakup grief, or relationship references ("ex" = ex-partner).
- **Observed code**:
  ```python
  RE_EMOTIONAL_CONFESSION = re.compile(
      r"("
      ...
      r"làm bạn thôi|mối quan hệ|người cũ|người iu cũ|ex|khoảng cách|rào cản|giới hạn|"
      ...
      r")",
      re.IGNORECASE
  )
  ```
- **Attack scenario**:
  The token `ex` has no regex word boundary (`\bex\b`). In Python `re.search()`, this matches any substring containing `ex`.
  Empirically verified false positives:
  - `"gửi text cho t"` (4 words) $\to$ matches `text` $\to$ returns `LengthTier.LONG` (max_tokens=160).
  - `"mở file excel nha"` (4 words) $\to$ matches `excel` $\to$ returns `LengthTier.LONG`.
  - `"next bài đi bạn"` (4 words) $\to$ matches `next` $\to$ returns `LengthTier.LONG`.
  - `"export file pdf"` (3 words) $\to$ matches `export` $\to$ returns `LengthTier.LONG`.
  - Code snippet `WHERE context = 'main'` $\to$ matches `context` $\to$ returns `LengthTier.LONG`.
  - Code snippet `except Exception as ex:` $\to$ matches `ex` $\to$ returns `LengthTier.LONG`.
- **Blast radius**:
  - Extremely high. In typical student/tech chats, words like `text`, `excel`, `next`, `export`, `flex`, `relax`, `index` are routine. All are misclassified as deep emotional crises, forcing An An to output 20-50 word boundary lectures.
  - Furthermore, LangChain multimodal messages containing dictionary key `'text'` (`{'type': 'text', ...}`) match `ex` when serialized, poisoning `_has_recent_emotional_context` for future turns.
- **Mitigation**:
  Replace bare `ex` with bounded word boundaries and contextual phrasing, e.g. `r"\b(?:người\s+yêu\s+cũ|ny\s+cũ|người\s+iu\s+cũ|\bex\b)\b"` or require explicit partner context.

---

### [Critical] Challenge 2: Sticky Emotional History Bleed & Rapid Topic Shift Contamination

- **Assumption challenged**: `_has_recent_emotional_context()` allows smooth multi-turn transitions and does not lock normal queries into `LONG` tier.
- **Observed code**:
  ```python
  if _has_recent_emotional_context(conversation_history):
      if "?" in clean_input or word_count >= 4 or any(w in clean_input.lower() for w in ["sao", "nghĩ", "sao?", "kh"]):
          tier = LengthTier.LONG
          return LengthDecision(...)
  ```
- **Attack scenario**:
  1. `_has_recent_emotional_context()` scans the last 4 turns.
  2. If an emotional confession occurred 3 turns ago and the conversation moved to acknowledgment (`User: "ok b"`, `An: "=)))"`), the next turn (`User: "mai đi học ca mấy thế b?"`) meets `word_count >= 4` and contains `?` and `b`.
  3. The controller classifies `"mai đi học ca mấy thế b?"` as `LengthTier.LONG` with guidance: *"Phản hồi sâu sắc, chân thành hoặc đặt ranh giới tình cảm rõ ràng"*.
  4. Even worse: if an innocent phrase like `"gửi text bài tập"` triggered Challenge 1 three turns ago, any follow-up question with `?`, `kh` (An An's primary slang token!), or $\ge 4$ words is hijacked into `LONG` tier.
- **Blast radius**:
  - Multi-turn conversations cannot naturally pivot from an emotional or tech turn back to casual study/hangout banter. An An remains locked in a 160-token solemn emotional persona.
- **Mitigation**:
  - Do not keep emotional context active if intermediate turns indicate resolution or topic change (e.g. affirmations like `ok`, `oki`, `=)))`, or explicit intent classifiers).
  - Only carry forward emotional tier if the current message itself expresses emotional sentiment, not merely containing `?` or `kh`.

---

### [High] Challenge 3: Unbounded Prefix `thích m` Captures Ordinary Preferences

- **Assumption challenged**: `thích m` in line 108 matches "thích mày" (I have feelings for you).
- **Attack scenario**:
  In regex: `thích m` without trailing word boundary matches any word starting with `m` following `thích `.
  Empirical failures:
  - `"t thích mua cái này"` $\to$ matches `thích mua` $\to$ `LONG`
  - `"mình thích màu hồng"` $\to$ matches `thích màu` $\to$ `LONG`
  - `"thích môn này kh b"` $\to$ matches `thích môn` $\to$ `LONG`
  - `"thích mang giày thể thao"` $\to$ matches `thích mang` $\to$ `LONG`
  - `"mình thích mở nhạc"` $\to$ matches `thích mở` $\to$ `LONG`
- **Blast radius**:
  - Normal everyday statements of preference and likes are misclassified as romantic confessions.
- **Mitigation**:
  Use strict word boundaries: `r"thích\s+(?:mày|m\b)"`.

---

### [High] Challenge 4: Priority Inversion: Repetitive Emojis & Punctuation with Spaces

- **Assumption challenged**: Emojis-only and punctuation-only inputs are always assigned to `LengthTier.SHORT`.
- **Observed code**:
  ```python
  # Line 173 (Priority 1)
  if word_count > 25:
      tier = LengthTier.LONG
      return LengthDecision(...)
  ...
  # Line 211 (Priority 2)
  if word_count == 0 or not any(c.isalnum() for c in clean_input):
      tier = LengthTier.SHORT
      return LengthDecision(...)
  ```
- **Attack scenario**:
  - `"🤡" * 30` (dense emojis) $\to$ `word_count = 1` $\to$ Priority 2 triggers $\to$ `SHORT` (pass).
  - `"🤡 " * 30` (spaced emojis) $\to$ `word_count = 30 > 25` $\to$ Priority 1 triggers $\to$ `LONG` (fail)!
  - `"? " * 30` (spaced punctuation) $\to$ `word_count = 30 > 25` $\to$ Priority 1 triggers $\to$ `LONG` (fail)!
- **Blast radius**:
  - Sending spaced clown emojis or question marks induces An An to write a 20-50 word emotional essay instead of sending a quick reaction bubble (`=)))`, `?`, etc.).
- **Mitigation**:
  Check `not any(c.isalnum() for c in clean_input)` BEFORE checking `word_count > 25`.

---

### [High] Challenge 5: Overmatching on Technical / Literal Vocabulary

- **Assumption challenged**: Words like `khoảng cách`, `giới hạn`, `nghĩ lại`, `mệt mỏi`, `mình với an` exclusively signal emotional distress.
- **Attack scenario**:
  - `"khoảng cách bao xa b?"` (geographic distance) $\to$ `LONG`
  - `"bài thi không giới hạn thời gian"` (exam time limit) $\to$ `LONG`
  - `"để mình nghĩ lại đã nha"` (thinking over a plan) $\to$ `LONG`
  - `"hôm nay đi bộ mệt mỏi ghê"` (physical fatigue) $\to$ `LONG`
  - `"thầy bảo mình với an làm chung"` (school group project) $\to$ `LONG`
- **Blast radius**:
  - Inflates `LONG` tier distribution far beyond the empirical 2.4% target specified in PROJECT.md.
- **Mitigation**:
  Require compound emotional context (e.g. `khoảng cách thế hệ`, `vượt quá giới hạn`, `mệt mỏi vì áp lực`, `mình với an là gì`).

---

### [Medium] Challenge 6: Boundary Discrepancy on 5-Word Threshold

- **Assumption challenged**: Boundary implementation matches project specification.
- **Observed code**:
  - PROJECT.md line 77: `SHORT: 1-5 words, max_tokens=35`, `MEDIUM: 6-15 words, max_tokens=75`.
  - `src/core/length_controller.py:65`: `TIER_WORD_BOUNDS = {LengthTier.SHORT: (1, 5), LengthTier.MEDIUM: (6, 15)}`.
  - Line 222: `if word_count <= 4: tier = LengthTier.SHORT`.
- **Attack scenario**:
  - An input of 5 words (e.g. `"một hai ba bốn năm"`) returns `LengthTier.MEDIUM` with metadata `min_words=6, max_words=15`.
- **Mitigation**:
  Change `if word_count <= 4:` to `if word_count <= 5:`.

---

### [Low] Challenge 7: Foreign Non-Segmented Languages (CJK) Under-counted

- **Assumption challenged**: Word counting via `clean_input.split()` works uniformly.
- **Attack scenario**:
  - Chinese and Japanese text without whitespace (e.g. a 43-character invitation to study) has `len(words) == 1`, defaulting to `SHORT`.
- **Blast radius**: Low, because An An is strictly a Vietnamese persona (`VIETNAMESE_ONLY`).
- **Mitigation**:
  Use character length fallback if no spaces are detected but string contains CJK characters.

---

## Stress Test Results Summary

| Suite | Test Case | Expected | Actual | Status |
|---|---|---|---|---|
| 1. Extreme Lengths | 0 words `""` | SHORT | SHORT | PASS |
| 1. Extreme Lengths | Whitespace variations | SHORT | SHORT | PASS |
| 1. Extreme Lengths | Exact 4 words | SHORT | SHORT | PASS |
| 1. Extreme Lengths | Exact 5 words | SHORT | MEDIUM | **FAIL [MEDIUM]** |
| 1. Extreme Lengths | Exact 15 words | MEDIUM | MEDIUM | PASS |
| 1. Extreme Lengths | Exact 25 words | MEDIUM | MEDIUM | PASS |
| 1. Extreme Lengths | Exact 26 words | LONG | LONG | PASS |
| 1. Extreme Lengths | 1,000 words | LONG (<50ms) | LONG (0.09ms) | PASS |
| 1. Extreme Lengths | 10,000 words | LONG (<100ms) | LONG (0.79ms) | PASS |
| 1. Extreme Lengths | 50,000 words | LONG (<500ms) | LONG (3.60ms) | PASS |
| 1. Extreme Lengths | 50k-char single token | SHORT (<200ms) | SHORT (15.72ms) | PASS |
| 2. Regex False Positives | 10 phrases with "ex" (text, excel, etc.) | SHORT | 9/10 LONG | **FAIL [CRITICAL]** |
| 2. Regex False Positives | 5 phrases with "thích m*" | SHORT/MEDIUM | 5/5 LONG | **FAIL [HIGH]** |
| 2. Regex False Positives | 5 technical/literal phrases | SHORT/MEDIUM | 5/5 LONG | **FAIL [HIGH]** |
| 3. Ambiguous / Emojis | Clustered emojis without spaces | SHORT | SHORT | PASS |
| 3. Ambiguous / Emojis | 30 emojis with spaces (`"🤡 " * 30`) | SHORT | LONG | **FAIL [HIGH]** |
| 3. Ambiguous / Emojis | 30 punctuation with spaces (`"? " * 30`) | SHORT | LONG | **FAIL [HIGH]** |
| 3. Code Snippets | 4 code snippets (import, SQL, try/except) | SHORT/MEDIUM | 2/4 LONG | **FAIL [HIGH]** |
| 3. Foreign Text | Long CJK paragraphs | MEDIUM/LONG | SHORT | **FAIL [LOW]** |
| 4. History / Shift | Casual query after emotional resolution | MEDIUM | LONG | **FAIL [HIGH]** |
| 4. History / Shift | Follow-up after "text" in history | MEDIUM | LONG | **FAIL [CRITICAL]** |
| 4. History / Shift | Multimodal message with `'text'` key | SHORT/MEDIUM | LONG | **FAIL [HIGH]** |
| 4. History / Shift | Heterogeneous/malformed history items | No crash | Handled cleanly | PASS |
| 5. Defensive Types | Non-string user_input types (int, float, list, etc.) | TypeError | TypeError (6/6) | PASS |
| 5. Defensive Types | Non-list conversation_history | Handled safely | Handled safely | PASS |

---

## Verdict & Recommendation

**VERDICT: REQUEST_CHANGES**

Worker M2 implemented an impressive initial scaffold with 170 passing unit tests. However, the unit tests exclusively tested positive cases crafted to pass the author's regexes. Adversarial stress-testing revealed critical flaws in regex boundary management, priority order, and history bleeding that fundamentally distort the chatbot's dynamic length decisions in real conversation.

The Worker must address:
1. Anchoring and refining `RE_EMOTIONAL_CONFESSION` (fix `ex`, `thích m`, and literal keywords).
2. Sanitizing history extraction to avoid dict key regex matches.
3. Checking `not any(c.isalnum() for c in clean_input)` before `word_count > 25`.
4. Decoupling rapid topic transitions from sticky emotional history.
5. Fixing the 5-word boundary condition (`<= 5` instead of `<= 4`).

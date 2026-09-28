# Persona Profile Remediation Plan — Milestone M1, Iteration 2

**Author**: Explorer Subagent (`explorer_m1_iter2_2` — Persona Profile Remediation Planner)  
**Target Component**: `src/ingestion/persona_profile.py` & `src/ingestion/__init__.py`  
**Milestone**: M1 (Dependencies & Data Ingestion Engine)  
**Project Root**: `C:\Users\HKQL2\Documents\ExBuild`  
**Date**: 2026-09-14  

---

## 1. Executive Summary

During Milestone M1 Gate 1 evaluation, Challenger 2 identified a functional boundary defect in `get_few_shot_examples(limit=0)` within `src/ingestion/persona_profile.py` and highlighted potential conversational incoherence when turns separated by multiple days are paired as question/response dialogues. Furthermore, the orchestrator dispatched a **Critical User Update**: the chatbot output language **MUST be Vietnamese**.

This remediation plan provides the Worker with exact, actionable code changes, design rationales, and test verification strategies across three areas:
1. **Fix for `get_few_shot_examples(limit <= 0)`**: Add an entry guard `if limit <= 0: return []`.
2. **Turn Pairing Gap Logic Evaluation & `max_gap_hours` Architecture**: Add an optional `max_gap_hours: Optional[float] = None` parameter to `extract_an_an_profile`, preserve timestamp metadata in aggregated turns, and enrich dialogue pairs with gap metrics while maintaining 100% backward compatibility for existing ground-truth assertions (392 pairs).
3. **Vietnamese Language Mandate**: Explicitly embed Vietnamese language requirements into `PERSONA_PROFILE` metadata, introduce English AI boilerplate anti-patterns into `PROHIBITED_TOKENS`, and provide a structured `format_few_shot_prompt` helper function that enforces natural Vietnamese colloquial style.

---

## 2. Issue 1: Boundary Defect in `get_few_shot_examples(limit=0)`

### 2.1 Problem Analysis & Root Cause
- **Location**: `src/ingestion/persona_profile.py`, lines 289–313.
- **Current Code**:
  ```python
  def get_few_shot_examples(category: Optional[str] = None, limit: int = 5) -> List[Dict[str, str]]:
      results: List[Dict[str, str]] = []
      for ex in FEW_SHOT_EXCHANGES:
          if category and ex["category"] != category:
              continue
          for turn in ex["turns"]:
              results.append({
                  "input": turn["user"],
                  "output": turn["an_an"]
              })
              if len(results) >= limit:
                  return results
      return results
  ```
- **Observed Bug**:
  Calling `get_few_shot_examples(limit=0)` returns:
  `[{'input': 'Chúc An mai thi tốt', 'output': 'Cám mơn ql nhieu nhaa \n ☺️'}]` (length 1).
  Calling `get_few_shot_examples(limit=-5)` also returns 1 element.
- **Root Cause**:
  1. `results.append(...)` is executed before checking `len(results) >= limit`. On the very first turn of the first exchange, `results` accumulates 1 item.
  2. The termination check `len(results) >= limit` evaluates `1 >= 0` (True), immediately returning a list containing 1 exemplar.
  3. No validation exists at function entry for non-positive limits (`limit <= 0`).
- **Impact**: Downstream components in Milestone M2/M3 (e.g., zero-shot prompts or context-constrained dynamic length controllers) attempting to disable few-shot exemplar injection by setting `limit=0` will inadvertently inject 1 few-shot example.

### 2.2 Prescribed Fix for Worker
In `src/ingestion/persona_profile.py`:
Add `if limit <= 0: return []` immediately after the docstring at line 301:

```python
def get_few_shot_examples(category: Optional[str] = None, limit: int = 5) -> List[Dict[str, str]]:
    """
    Retrieves flattened input/output few-shot exemplars, optionally filtered by category.
    All exemplars are authentic Vietnamese colloquial exchanges.
    
    Args:
        category: 'CASUAL_BANTER', 'STUDY_COORDINATION', 'TEASING_DEBT',
                  'GOSSIP_DRAMA', 'EMOTIONAL_BOUNDARY', 'VENTING_FATIGUE', or None.
        limit: Maximum number of examples to return. If <= 0, returns an empty list.
        
    Returns:
        List of dicts: [{'input': ..., 'output': ...}, ...]
    """
    if limit <= 0:
        return []

    results: List[Dict[str, str]] = []
    for ex in FEW_SHOT_EXCHANGES:
        if category and ex["category"] != category:
            continue
        for turn in ex["turns"]:
            results.append({
                "input": turn["user"],
                "output": turn["an_an"]
            })
            if len(results) >= limit:
                return results
    return results
```

### 2.3 Verification Criteria for Worker
1. `get_few_shot_examples(limit=0) == []`
2. `get_few_shot_examples(limit=-1) == []`
3. `get_few_shot_examples(limit=1)` returns exactly 1 item.
4. `get_few_shot_examples(limit=5)` returns exactly 5 items.
5. In `.agents/challenger_m1_2/test_verify_persona.py`, remove `@pytest.mark.xfail` from `test_get_few_shot_examples_zero_and_negative_limits` so it runs as an unconditional passing test.

---

## 3. Issue 2: Dialogue Turn Pairing Gap Logic & `max_gap_hours` Evaluation

### 3.1 Empirical Investigation of Inter-Turn Gaps
Challenger 2 observed that `extract_an_an_profile` in `src/ingestion/persona_profile.py` clusters consecutive messages from the **same sender** using a 2-hour inactivity threshold, but enforces **zero time constraint** when pairing a User turn with a subsequent An An turn:

```python
for i in range(len(turns) - 1):
    if not turns[i]["is_an_an"] and turns[i + 1]["is_an_an"]:
        extracted_pairs.append({ ... })
```

Empirical analysis on `F:/dowload/FacebookData/messages/An An_86.json` revealed:
- Total dialogue pairs extracted: **392**
- Pairs with inter-turn elapsed time $> 2$ hours: **29 pairs (7.4%)**
- Pairs with inter-turn elapsed time $> 24$ hours: **8 pairs**
- Pairs with inter-turn elapsed time $> 48$ hours: **4 pairs**
- Top multi-day gap anomalies:
  1. **248.3 hours (10.3 days)**: User discussed bike keys/schedule; 10 days later An An initiated a separate panic message (`"Ql\nCú\nBdkshf\nĐụ má\nGấp"`).
  2. **121.1 hours (5.0 days)**: User discussed keys; 5 days later An An asked to borrow a power bank (`"Quờ lờ oiii\nAn mượn cục sạc dự phòng tí dc khoqqw"`).
  3. **68.2 hours (2.8 days)**: User said `"tự tin lên cố lên 💪"`; An An replied 3 days later with `"Jza"`.

### 3.2 Backward Compatibility Analysis & Mandatory Design Decision
**CRITICAL FINDING**:
In existing test suites:
- `tests/test_ingestion.py`:
  - `test_extract_dialogue_pairs_total_count`: asserts `len(pairs) >= 380`
  - `test_extract_dialogue_pairs_ground_truth_turn_1`: asserts `pair_1["user_input"] == "tự tin lên cố lên"` and `pair_1["an_an_response"] == "Jza"`! (Pair 1 is the exact pair with the 68.2-hour gap!)
- `.agents/challenger_m1_2/test_verify_persona.py`:
  - `test_turn_aggregation_ground_truth_counts`: asserts `extracted_turn_pairs == 392`
  - `test_inter_turn_gap_empirical_reality`: asserts `len(pairs) == 392` and validates `pairs[1]` as `"tự tin lên cố lên 💪"` $\to$ `"Jza"`.

**Conclusion on Architecture**:
- Unconditionally filtering out pairs with $>2$ hours or $>24$ hours would **BREAK** existing unit tests and invalidate verified ground-truth counts (392 pairs).
- Therefore, `max_gap_hours` must be an **OPTIONAL parameter** defaulting to `None`:
  `def extract_an_an_profile(messages: List[CanonicalMessage], max_gap_hours: Optional[float] = None) -> Dict[str, Any]:`
- When `max_gap_hours is None`:
  - All 392 pairs are retained (100% backward compatible).
  - Each pair is enriched with `gap_ms` and `gap_hours` metadata so downstream consumers (e.g. prompt selector, length controller) can filter by gap dynamically.
- When `max_gap_hours` is specified:
  - If `max_gap_hours=24.0`, multi-day breaks are excluded, yielding 384 pairs.
  - If `max_gap_hours=2.0`, only immediate replies are retained, yielding 363 pairs.

### 3.3 Prescribed Fix for Worker
In `src/ingestion/persona_profile.py`:
Modify turn aggregation and dialogue pair extraction in `extract_an_an_profile`:

1. **Track Turn Timestamps & Accurate `is_an_an` Flag**:
   ```python
   def extract_an_an_profile(
       messages: List[CanonicalMessage],
       max_gap_hours: Optional[float] = None
   ) -> Dict[str, Any]:
       ...
       # Aggregate turns (sender grouping with 2-hour inactivity cutoff)
       turns: List[Dict[str, Any]] = []
       current_sender: Optional[str] = None
       current_is_an_an: bool = False
       current_texts: List[str] = []
       current_start_ts: int = 0
       current_end_ts: int = 0
       last_ts = 0

       for m in messages:
           # Check if new turn: sender changed or inactivity > 2 hours (7,200,000 ms)
           if m.sender_name != current_sender or (m.timestamp_ms - last_ts > 7_200_000 and current_sender is not None):
               if current_texts:
                   turns.append({
                       "sender_name": current_sender,
                       "is_an_an": current_is_an_an,
                       "messages": current_texts,
                       "full_text": "\n".join(current_texts),
                       "start_timestamp_ms": current_start_ts,
                       "end_timestamp_ms": current_end_ts,
                   })
               current_sender = m.sender_name
               current_is_an_an = m.is_an_an
               current_texts = [m.text]
               current_start_ts = m.timestamp_ms
               current_end_ts = m.timestamp_ms
           else:
               current_texts.append(m.text)
               current_end_ts = m.timestamp_ms
           last_ts = m.timestamp_ms

       if current_texts:
           turns.append({
               "sender_name": current_sender,
               "is_an_an": current_is_an_an,
               "messages": current_texts,
               "full_text": "\n".join(current_texts),
               "start_timestamp_ms": current_start_ts,
               "end_timestamp_ms": current_end_ts,
           })
   ```

2. **Pairing Logic with Optional `max_gap_hours` & Enriched Metadata**:
   ```python
       # Extract user -> An An turn pairs
       extracted_pairs: List[Dict[str, Any]] = []
       for i in range(len(turns) - 1):
           if not turns[i]["is_an_an"] and turns[i + 1]["is_an_an"]:
               gap_ms = max(0, turns[i + 1]["start_timestamp_ms"] - turns[i]["end_timestamp_ms"])
               if max_gap_hours is not None:
                   max_gap_ms = max_gap_hours * 3_600_000
                   if gap_ms > max_gap_ms:
                       continue
               extracted_pairs.append({
                   "user_input": turns[i]["full_text"],
                   "an_an_response": turns[i + 1]["full_text"],
                   "user": turns[i]["full_text"],
                   "an_an": turns[i + 1]["full_text"],
                   "gap_ms": gap_ms,
                   "gap_hours": round(gap_ms / 3_600_000, 2),
               })
   ```

### 3.4 Verification Criteria for Worker
1. `extract_an_an_profile(messages)` with default `max_gap_hours=None` returns exactly 392 pairs on `An An_86.json`.
2. `extract_an_an_profile(messages, max_gap_hours=24.0)` returns 384 pairs (filters out 8 pairs with gap $> 24$ hours).
3. `extract_an_an_profile(messages, max_gap_hours=2.0)` returns 363 pairs (filters out 29 pairs with gap $> 2$ hours).
4. Each element in `extracted_pairs` contains `"gap_ms"` and `"gap_hours"` floats/ints.

---

## 4. Issue 3: Critical User Update — Vietnamese Language Mandate

### 4.1 Requirement Breakdown
The orchestrator and user prompt dictate:
> "Chatbot output language MUST be Vietnamese. Ensure persona profile metadata and few-shot formatting explicitly mandate Vietnamese language responses."

An An's persona is an authentic Vietnamese university student from Ho Chi Minh City / Southern Vietnam. While her messages occasionally contain modern Vietnamese youth loanwords (`bro`, `chill`, `sori`, `g9`), her conversational language is **100% Vietnamese**. The chatbot must never reply in English or switch to AI assistant persona.

### 4.2 Metadata Updates in `PERSONA_PROFILE`
In `src/ingestion/persona_profile.py`, expand `PERSONA_PROFILE` (lines 126–142):

```python
PERSONA_PROFILE: Dict[str, Any] = {
    "name": "An An",
    "gender": "Female",
    "age_range": "Early 20s (College student)",
    "discipline": "Art / Design / Photography",
    "language": "Vietnamese",
    "primary_language": "Vietnamese (Tiếng Việt)",
    "language_mandate": (
        "CRITICAL REQUIREMENT: Chatbot output MUST always be in Vietnamese (Tiếng Việt). "
        "Under NO circumstances should An An respond in English or any other foreign language, "
        "even if the user prompts in English, Chinese, or any other language. "
        "An An must always maintain her authentic colloquial Vietnamese persona, using her signature "
        "slang and abbreviations ('kh', 'dc', 'nma', 'r', '=)))', '🤡', 'ql'). "
        "Only occasional Gen-Z youth loanwords already present in her real messages "
        "(such as 'chill', 'bro', 'sori', 'g9') are allowed as natural Vietnamese code-mixing."
    ),
    "relationship_to_user": (
        "Classmate and close friend of Hoàng Kim Quờ Lờ ('ql'). "
        "Previously handled a gentle confession rejection with high empathy; "
        "now shares an unfiltered, highly sarcastic, loyal best-friend bond."
    ),
    "tone_pillars": [
        "Native Vietnamese colloquial speaker: MUST always generate responses in Vietnamese (Tiếng Việt). Never switch to English, never output robotic or standard AI assistant boilerplate.",
        "Spontaneous & feisty: teases aggressively with comedic threats ('chọi mắm tôm', 'nôn stk').",
        "Empathetic & thoughtful: in serious or emotional moments, speaks with genuine warmth and care.",
        "Artistic student vibes: talks about exams, design projects, sleep deprivation, coffee.",
        "Concise mobile chatter: sends ideas in short bursts (median 4 words per bubble), never writes long AI essays."
    ]
}
```

### 4.3 Expansion of `PROHIBITED_TOKENS`
Add standard English AI boilerplate phrases to `PROHIBITED_TOKENS` (lines 110–123):

```python
PROHIBITED_TOKENS: List[str] = [
    # Persona slang violations
    "ko",
    "k",
    "đc",
    "nhma",
    "oke",
    # Overly polite / formal Vietnamese violations
    "ạ",
    "cậu",
    "tớ",
    "dạ",
    # Vietnamese AI assistant boilerplate
    "Tôi là trợ lý ảo",
    "Tôi có thể giúp gì cho bạn",
    "Xin lỗi vì sự bất tiện",
    # English AI assistant boilerplate (prevent language leakage)
    "As an AI",
    "How can I help you",
    "How can I assist",
    "I am an AI",
    "I'm an AI",
    "Sure, I can help with that",
]
```

### 4.4 Tagging Few-Shot Exchanges with Language
In `FEW_SHOT_EXCHANGES` (lines 147–286), add `"language": "vi"` to each of the 15 exchange dictionaries:

```python
FEW_SHOT_EXCHANGES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "category": "CASUAL_BANTER",
        "language": "vi",
        "context": "QL wishes An An good luck the night before an exam.",
        "turns": [
            {"user": "Chúc An mai thi tốt", "an_an": "Cám mơn ql nhieu nhaa \n ☺️"}
        ]
    },
    ...
]
```

### 4.5 Few-Shot Prompt Formatting Function: `format_few_shot_prompt`
Implement `VIETNAMESE_LANGUAGE_INSTRUCTION` and `format_few_shot_prompt` in `src/ingestion/persona_profile.py`:

```python
VIETNAMESE_LANGUAGE_INSTRUCTION: str = (
    "QUY TẮC BẮT BUỘC VỀ NGÔN NGỮ: Mọi phản hồi của An An BẮT BUỘC PHẢI bằng Tiếng Việt tự nhiên. "
    "Tuyệt đối KHÔNG trả lời bằng tiếng Anh hay bất kỳ ngôn ngữ nào khác kể cả khi người dùng chat bằng tiếng Anh. "
    "Luôn giữ văn phong nhắn tin của An An: cộc lốc, ngắn gọn, xưng hô 'ql', 'bạn-mình' hoặc 'm-t', "
    "dùng đúng từ viết tắt đặc trưng ('kh', 'dc', 'nma', 'r', '=)))')."
)


def format_few_shot_prompt(
    category: Optional[str] = None,
    limit: int = 5,
    include_instruction: bool = True
) -> str:
    """
    Formats few-shot exemplars into a structured text prompt block for LLM context,
    explicitly mandating Vietnamese language response fidelity.
    
    Args:
        category: Optional category filter ('CASUAL_BANTER', 'STUDY_COORDINATION', etc.).
        limit: Maximum number of dialogue turns to format (if <= 0, returns empty string).
        include_instruction: Whether to prepend the mandatory Vietnamese language instruction.
        
    Returns:
        Formatted prompt text string. Returns empty string if limit <= 0 or no examples match.
    """
    if limit <= 0:
        return ""

    examples = get_few_shot_examples(category=category, limit=limit)
    if not examples:
        return ""

    parts: List[str] = []
    if include_instruction:
        parts.append(VIETNAMESE_LANGUAGE_INSTRUCTION)
        parts.append("[HỘI THOẠI MẪU / FEW-SHOT EXAMPLES]:")

    for ex in examples:
        parts.append(f"User: {ex['input']}\nAn An: {ex['output']}")

    return "\n\n".join(parts)
```

### 4.6 Module Export Updates
In `src/ingestion/__init__.py`:
Export `VIETNAMESE_LANGUAGE_INSTRUCTION` and `format_few_shot_prompt` alongside existing exports:

```python
from src.ingestion.persona_profile import (
    extract_an_an_profile,
    SLANG_DICTIONARY,
    PROHIBITED_TOKENS,
    PERSONA_PROFILE,
    FEW_SHOT_EXCHANGES,
    get_few_shot_examples,
    VIETNAMESE_LANGUAGE_INSTRUCTION,
    format_few_shot_prompt,
)

__all__ = [
    "CanonicalMessage",
    "parse_facebook_json",
    "safe_decode_mojibake",
    "fix_fb_text",
    "extract_an_an_profile",
    "SLANG_DICTIONARY",
    "PROHIBITED_TOKENS",
    "PERSONA_PROFILE",
    "FEW_SHOT_EXCHANGES",
    "get_few_shot_examples",
    "VIETNAMESE_LANGUAGE_INSTRUCTION",
    "format_few_shot_prompt",
]
```

---

## 5. Integration with Milestone M2 & Downstream Pipeline

1. **`src/core/prompts.py` (M2)**:
   The system prompt builder will import `PERSONA_PROFILE["language_mandate"]` and `format_few_shot_prompt()`. When creating the LangChain `ChatPromptTemplate`:
   - System message includes `PERSONA_PROFILE["language_mandate"]`.
   - Few-shot examples are populated using `format_few_shot_prompt(limit=N)` or `get_few_shot_examples(limit=N)`.
   - If user input intent triggers zero-shot mode, passing `limit=0` returns `""` / `[]` cleanly.

2. **`src/core/length_controller.py` (M2)**:
   Dynamic token budgeting can inspect `pair["gap_hours"]` when selecting relevant context exemplars, avoiding pairing across long multi-day silences.

3. **`evaluation/judge_rubric.py` (M5)**:
   The Agent-as-Judge rubric will include a hard criterion:
   - **Language Check**: Response must be in Vietnamese. Any full-sentence English reply is an immediate score of 0.

---

## 6. Worker Execution Checklist

- [ ] Modify `src/ingestion/persona_profile.py`:
  - [ ] Add `if limit <= 0: return []` in `get_few_shot_examples`.
  - [ ] Update `PERSONA_PROFILE` with `language`, `primary_language`, `language_mandate`, and Vietnamese tone pillar.
  - [ ] Add English AI boilerplate to `PROHIBITED_TOKENS`.
  - [ ] Add `"language": "vi"` to each item in `FEW_SHOT_EXCHANGES`.
  - [ ] Add `VIETNAMESE_LANGUAGE_INSTRUCTION` constant and `format_few_shot_prompt` function.
  - [ ] Update `extract_an_an_profile`: add optional `max_gap_hours: Optional[float] = None`, track `start_timestamp_ms` and `end_timestamp_ms` on turns, compute `gap_ms` and `gap_hours`, filter if `max_gap_hours` is set.
- [ ] Modify `src/ingestion/__init__.py`:
  - [ ] Export `VIETNAMESE_LANGUAGE_INSTRUCTION` and `format_few_shot_prompt`.
- [ ] Run test verification:
  - [ ] `pytest tests/test_ingestion.py` (ensure all 61+ tests pass).
  - [ ] Un-xfail and run `.agents/challenger_m1_2/test_verify_persona.py` (ensure 23/23 tests pass).

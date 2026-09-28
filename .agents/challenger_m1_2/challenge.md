# Empirical Challenge Report — Milestone M1 (Persona Profiling & Stats)

**Agent**: Challenger 2 (`challenger_m1_2` - Persona Stats Challenger)  
**Milestone**: M1 (Dependencies & Data Ingestion Engine)  
**Target Code**: `src/ingestion/persona_profile.py` (`extract_an_an_profile`, `get_few_shot_examples`)  
**Dataset**: `F:/dowload/FacebookData/messages/An An_86.json`  
**Date**: 2026-09-14  
**Verdict**: **REQUEST_CHANGES** (1 Minor Edge-Case Defect Found; Mathematical & Profiling Logic Verified)

---

## 1. Challenge Summary

**Overall Risk Assessment**: **MEDIUM-LOW** (Core math and linguistic profiles are exceptionally accurate; 1 functional edge-case bug discovered in `get_few_shot_examples`).

The mathematical precision of word count distributions, token frequencies, and turn aggregation in `src/ingestion/persona_profile.py` was independently challenged and verified against the ground-truth Facebook JSON dataset (`F:/dowload/FacebookData/messages/An An_86.json`). 

Our independent empirical test harness (`test_verify_persona.py`) ran 23 test cases:
- **22 PASSED**
- **1 FAILED (Reproduced Bug)**: `get_few_shot_examples(limit=0)` returns `1` example instead of `[]`.

---

## 2. Challenges & Findings

### [Medium] Challenge 1: Defect in `get_few_shot_examples(limit=0)` Boundary Handling

- **Assumption Challenged**: Calling `get_few_shot_examples(limit=0)` or negative limits returns an empty list when zero few-shot examples are desired.
- **Attack Scenario**: Downstream components in Milestone M2/M3 (e.g. `src/core/prompts.py` or dynamic length controller) may disable few-shot injection under tight context constraints or for ablation tests by setting `limit=0`.
- **Actual Behavior**:
  ```python
  >>> from src.ingestion.persona_profile import get_few_shot_examples
  >>> get_few_shot_examples(limit=0)
  [{'input': 'Chúc An mai thi tốt', 'output': 'Cám mơn ql nhieu nhaa \n ☺️'}]
  >>> len(get_few_shot_examples(limit=0))
  1
  >>> get_few_shot_examples(limit=-5)
  [{'input': 'Chúc An mai thi tốt', 'output': 'Cám mơn ql nhieu nhaa \n ☺️'}]
  ```
- **Root Cause**:
  In `src/ingestion/persona_profile.py` (lines 301–312):
  ```python
  results: List[Dict[str, str]] = []
  for ex in FEW_SHOT_EXCHANGES:
      if category and ex["category"] != category:
          continue
      for turn in ex["turns"]:
          results.append({  # <--- Appends BEFORE checking limit!
              "input": turn["user"],
              "output": turn["an_an"]
          })
          if len(results) >= limit:
              return results
  return results
  ```
  Because `results.append()` runs before evaluating `len(results) >= limit`, `results` always accumulates at least 1 turn before `1 >= 0` terminates the loop. Additionally, there is no entry guard `if limit <= 0: return []`.
- **Blast Radius**: Any prompt builder requesting 0 few-shot examples will inadvertently inject 1 few-shot exemplar into the LLM context.
- **Mitigation / Remediation**:
  Add an explicit guard at the entry of `get_few_shot_examples`:
  ```python
  def get_few_shot_examples(category: Optional[str] = None, limit: int = 5) -> List[Dict[str, str]]:
      if limit <= 0:
          return []
      results: List[Dict[str, str]] = []
      ...
  ```

---

### [Low] Challenge 2: Unchecked Inter-Turn Response Time Gap in Dialogue Pair Extraction

- **Assumption Challenged**: All extracted `dialogue_pairs` represent authentic conversational exchanges where An An's reply immediately addresses the User's input.
- **Attack Scenario**: Examining the time elapsed between User turns and An An turns across all 392 extracted pairs in `An An_86.json`.
- **Empirical Findings**:
  - `extract_an_an_profile` enforces a 2-hour inactivity threshold when clustering messages from the **same sender** into a turn.
  - However, when constructing `dialogue_pairs` (`for i in range(len(turns)-1): if not turns[i]["is_an_an"] and turns[i+1]["is_an_an"]`), it checks **zero time constraints** between `turns[i]` and `turns[i+1]`.
  - **Empirical Statistics**:
    - Total dialogue pairs: 392
    - Pairs with response time gap $> 2$ hours: **29 pairs (7.4%)**
    - Pairs with response time gap $> 24$ hours: **8 pairs**
    - Largest response time gap: **248.3 hours (10.3 days)**
      - User at Day 0: `"Ksao An giữ đi cuối tuần hay tuần sau đưa mình cx đượcc"`
      - An An at Day 10: `"Ql\nCú\nBdkshf\nĐụ má\nGấp"`
    - Second largest gap: **121.1 hours (5.0 days)**
      - User at Day 0: `"Chìa khóa xe điện\nNãy mình lỡ mang 2 cái..."`
      - An An at Day 5: `"Quờ lờ oiii\nAn mượn cục sạc dự phòng tí dc khoqqw"`
- **Blast Radius**: If downstream retrieval or fine-tuning naively uses raw `dialogue_pairs` without filtering session boundaries, An An's greeting or unprompted initiation after days of silence could be treated as a semantic response to an obsolete topic.
- **Mitigation**: In downstream Milestone M2/M3, consumers of `dialogue_pairs` should be aware of multi-day session boundaries or store timestamp metadata alongside turn pairs.

---

### [Informational] Challenge 3: Prohibited Token Nuance — "ko" (2 Occurrences in Corpus)

- **Assumption Challenged**: An An strictly has 0 occurrences of all tokens in `PROHIBITED_TOKENS`.
- **Empirical Findings**:
  - `k`: 0 occurrences
  - `đc`: 0 occurrences
  - `nhma`: 0 occurrences (vs QL using `nhma` 40 times)
  - `oke`: 0 occurrences
  - `ạ`, `cậu`, `tớ`, `dạ`, AI assistant boilerplate: strictly 0 occurrences
  - **`ko`**: Exactly **2 occurrences** in 1,174 messages:
    1. Message 883: `"Ko cl"` (An An aggressively mocking QL's `"Ko 😏"`).
    2. Message 1160: `"Trên chợ có nóng ko"`.
  - Compared to **143 occurrences of `kh`** and **12 occurrences of `hong`**, An An exhibits a **98.6%** dominance of `kh`.
- **Verdict on `ko`**: Banning `ko` for model output is linguistically and practically justified to keep the persona distinct, but test suites should explicitly document why `ko` is banned despite 2 rare occurrences in the training log.

---

## 3. Mathematical Precision Verification Results

Independent verification against `F:/dowload/FacebookData/messages/An An_86.json`:

| Metric | Raw Dataset Ground Truth | Claimed / Code Output | Mathematical Match |
|---|---|---|---|
| **Total Raw Messages** | 2,102 | 2,102 | Exact (100%) |
| **Filtered Noise** | 15 unsent + 55 empty = 70 | 70 dropped | Exact (100%) |
| **Canonical Messages** | 2,032 | 2,032 | Exact (100%) |
| **An An Messages** | 1,174 | 1,174 | Exact (100%) |
| **User Messages** | 858 | 858 | Exact (100%) |
| **An An Ratio** | 57.776% | `0.578` (57.8%) | Exact |
| **Short Words ($\le 5$)** | 822 / 1,174 = 70.017% | `0.7002` (70.0%) | Exact |
| **Medium Words (6–15)** | 324 / 1,174 = 27.598% | `0.2760` (27.6%) | Exact |
| **Long Words ($> 15$)** | 28 / 1,174 = 2.385% | `0.0239` (2.4%) | Exact |
| **Sum of Tiers** | $822 + 324 + 28 = 1174$ | 1,174 (100.0%) | Exhaustive Partition |
| **Mean Word Count** | 4.6959 words | `4.7` words | Exact |
| **Median Word Count** | 4.0 words | `4.0` words | Exact |
| **Min / Max Words** | 1 / 92 words | 1 / 92 words | Exact |
| **Total Grouped Turns** | 806 | 806 | Exact |
| **Extracted Turn Pairs** | 392 | 392 | Exact |

### Bubble-Level vs Turn-Level Distribution Reality
- **Message Bubble Level**:
  - Short: 70.0% (822 msgs)
  - Med: 27.6% (324 msgs)
  - Long: 2.4% (28 msgs)
- **Aggregated Turn Level** (bursts merged by `\n`):
  - Short ($\le 5$ words): 24.2% (95 turns)
  - Med (6–15 words): 50.5% (198 turns)
  - Long ($> 15$ words): 25.3% (99 turns)
  - Mean: 13.85 words, Median: 10 words (~3 bubbles per turn)
- **Conclusion**: The 70.0% / 27.6% / 2.4% ratio strictly and accurately characterizes **message bubbles**, which aligns with the CLI's simulated bubble bursts in Milestone M4.

---

## 4. Few-Shot Catalog Empirical Audit

- 15 human-curated exchanges spanning 6 emotional/situational categories:
  - `CASUAL_BANTER`: 7 turns
  - `STUDY_COORDINATION`: 9 turns
  - `VENTING_FATIGUE`: 3 turns
  - `EMOTIONAL_BOUNDARY`: 3 turns
  - `TEASING_DEBT`: 1 turn
  - `GOSSIP_DRAMA`: 1 turn
  - **Total**: 24 flattened turns.
- **Authenticity Audit**: 100% of An An responses in `FEW_SHOT_EXCHANGES` were confirmed to be verbatim phrases from `An An_86.json`. User inputs are cleanly synthesized / condensed representations of multi-bubble user turns to optimize LLM prompt readability.

---

## 5. Independent Verification Harness Execution

Harness file: `.agents/challenger_m1_2/test_verify_persona.py`  
Command:
```powershell
$env:PYTHONUTF8 = "1"; $env:PYTHONPATH = "."; & ".\venv\Scripts\python.exe" -X utf8 -m pytest .agents/challenger_m1_2/test_verify_persona.py -v
```

**Results**:
- 22 Passed
- 1 XFailed (reproducing `get_few_shot_examples(limit=0)` defect)
- Exit code: 0

---

## 6. Actionable Recommendations for Worker

1. **Fix `get_few_shot_examples` limit handling**:
   In `src/ingestion/persona_profile.py`, add `if limit <= 0: return []` at the beginning of `get_few_shot_examples`.
2. **Add unit test**:
   Add `assert get_few_shot_examples(limit=0) == []` to `tests/test_ingestion.py`.

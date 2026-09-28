# Milestone M2 Handoff Report: Reviewer 1 (Length Architecture Reviewer)

**Author**: Reviewer 1 (`reviewer_m2_1`)  
**Target Milestone**: M2 (Dynamic Response Length Controller & Persona Prompts)  
**Date**: 2026-09-14T11:47:00Z  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

1. **Test Suite Execution**:
   - Executed: `& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_length.py tests/test_ingestion.py -v`
   - Result: `170 passed in 2.20s` (96 passed in `tests/test_length.py`, 74 passed in `tests/test_ingestion.py`).
   - All tests cleanly exited with code 0.

2. **Interface Compliance Verification**:
   - `src/core/length_controller.py`:
     - `LengthTier(str, Enum)` defined at lines 16–22 with members `SHORT = "short"`, `MEDIUM = "medium"`, `LONG = "long"`.
     - `LengthDecision(BaseModel)` defined at lines 25–53 with fields `tier: LengthTier`, `max_tokens: int`, `guidance_instruction: str`, `min_words: int`, `max_words: int`, `empirical_ratio: float`.
     - `determine_response_length(user_input: str, conversation_history: Optional[list] = None) -> LengthDecision` defined at lines 145–244.
     - `TIER_TOKEN_LIMITS` maps `SHORT: 35`, `MEDIUM: 75`, `LONG: 160`.
   - `src/core/prompts.py`:
     - `SYSTEM_PROMPT_BASE` defined at lines 26–73 with mandatory Vietnamese rule, slang rules (`kh`, `dc`, `nma`, `r`, `=)))`), and anti-AI guardrails.
     - `build_system_prompt()` defined at lines 162–210.
     - `get_chat_prompt_template()` defined at lines 215–238.
   - `src/core/__init__.py`:
     - Exports all 13 required core symbols cleanly.

3. **Adversarial Regex & Boundary Observations**:
   - In `src/core/length_controller.py`, lines 104–115:
     ```python
     RE_EMOTIONAL_CONFESSION = re.compile(
         r"("
         r"thích an|yêu an|thương an|tỏ tình|làm người yêu|muốn hẹn hò|thích bạn|"
         r"(?:muốn\s+)?(?:đc|được|ở)\s+bên\s+an|(?:muốn\s+(?:đc\s+|được\s+)?)?bên\s+cạnh\s+an|"
         r"tình cảm|crush|thổ lộ|làm bạn gái|thích m|iu an|"
         r"làm bạn thôi|mối quan hệ|người cũ|người iu cũ|ex|khoảng cách|rào cản|giới hạn|"
         r"chúng mình là gì|mình với an|chia tay|tổn thương|"
         r"áp lực quá|trầm cảm|bế tắc|muốn biến mất|tâm sự thật lòng|nói chuyện nghiêm túc|"
         r"khóc nhiều|buồn nhiều lắm|tuyệt vọng|mệt mỏi|nghĩ lại"
         r")",
         re.IGNORECASE
     )
     ```
   - Running direct regex search in Python on technical and everyday vocabulary:
     - `'export file pdf'`: `RE_EMOTIONAL_CONFESSION.search(...)` -> `matched: True, match='ex'`, `determine_response_length(...)` -> `LengthTier.LONG` (160 tokens).
     - `'file excel nè'`: `matched: True, match='ex'`, `determine_response_length(...)` -> `LengthTier.LONG` (160 tokens).
     - `'thích mua bánh tráng nè'`: `matched: True, match='thích m'`, `determine_response_length(...)` -> `LengthTier.LONG` (160 tokens).
     - `'thích máy ảnh này kh'`: `matched: True, match='thích m'`, `determine_response_length(...)` -> `LengthTier.LONG` (160 tokens).
     - `'thích an toàn là trên hết'`: `matched: True, match='thích an'`, `determine_response_length(...)` -> `LengthTier.LONG` (160 tokens).
   - In `src/core/length_controller.py`, line 222:
     - Code: `if word_count <= 4: tier = LengthTier.SHORT`.
     - Input `'mai có đi học kh'` has 5 words. `determine_response_length('mai có đi học kh')` returns `LengthTier.MEDIUM` with `bounds: (6, 15)`, despite `PROJECT.md` line 77 stating `SHORT = "short" # 1-5 words` and `TIER_WORD_BOUNDS[SHORT] = (1, 5)`.
   - In `src/core/length_controller.py`, line 135:
     - Code: `if not conversation_history or not isinstance(conversation_history, list): return False`.
     - Input `conversation_history = (HumanMessage(content='Thật sự muốn đc bên An'),)` is a tuple; evaluated to `False` and conversation context was ignored.

---

## 2. Logic Chain

1. From Observation 1 and 2, the implementation is architecturally solid, satisfies all Pydantic and LangChain typing interfaces, and passes existing unit tests without regression.
2. From Observation 3, the regular expression `RE_EMOTIONAL_CONFESSION` contains bare substrings without word boundary anchors (`\b`):
   - `ex` in line 109 matches English words like `export`, `excel`, `example`, `extra`.
   - `thích m` in line 108 matches any sentence starting with `thích m...` such as `thích mua`, `thích máy ảnh`, `thích màu`, `thích mọi người`.
   - `thích an` in line 106 matches `thích an toàn`.
3. Because Priority 1 of `determine_response_length` evaluates `RE_EMOTIONAL_CONFESSION` before short/medium word count checks, any occurrence of these innocent substrings forces the conversational turn into `LengthTier.LONG` (160 tokens) and injects emotional confession rejection prompts.
4. An An is a college student in design/arts. Daily discussions about exporting project files (`export file`), spreadsheet groups (`file excel`), milk tea / snacks (`thích mua...`), and photography gear (`thích máy ảnh`) will constantly suffer catastrophic false-positive tier escalations.
5. In addition, the `word_count <= 4` boundary directly contradicts the `1-5 words` specification for `SHORT`.
6. Therefore, the work product cannot be approved in its current state as it will cause immediate behavioral failures in M3 (conversational chain) and M5 (Agent-as-Judge evaluation). A verdict of **REQUEST_CHANGES** is necessary.

---

## 3. Caveats

1. **Integrity & Code Quality**: No integrity violations (cheating, facade code, fabricated outputs) were found. The author implemented genuine, well-structured logic.
2. **Offline Testing Scope**: All tests and adversarial checks were performed locally and offline without external network dependencies.
3. **Small Blast Radius**: The required fixes are localized to `src/core/length_controller.py` (regex boundary definitions and `word_count <= 5`) and corresponding test cases in `tests/test_length.py`.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

Worker M2 must resolve the following concrete items:
1. Add `\b` word boundary anchors to isolated keywords in `RE_EMOTIONAL_CONFESSION`: `\bex\b`, `\bthích\s+m\b`, `\bthích\s+an\b`, `\byêu\s+an\b`, `\biu\s+an\b`, `\bthích\s+bạn\b(?!\s+bè)`.
2. Update short word count threshold from `word_count <= 4` to `word_count <= 5` in `determine_response_length`.
3. Prevent single-word responses (`"kh"`, `"oki?"`) from locking into `LONG` tier after an emotional turn.
4. Support tuple sequences in `_has_recent_emotional_context`.
5. Add unit tests for these boundary cases in `tests/test_length.py`.

---

## 5. Verification Method

To independently verify these findings:

```powershell
# 1. Run the existing test suite
& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_length.py tests/test_ingestion.py -v

# 2. Reproduce the false-positive LONG triggers
& ".\venv\Scripts\python.exe" -X utf8 -c "from src.core.length_controller import determine_response_length; print([(t, determine_response_length(t).tier) for t in ['export file ảnh', 'thích mua bánh', 'file excel', 'mai có đi học kh']])"
# Expected to be SHORT/MEDIUM, but currently returns LONG for export, thích mua, file excel, and MEDIUM for 5-word input.
```

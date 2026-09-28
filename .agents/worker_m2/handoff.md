# Milestone M2 Handoff Report: Dynamic Response Length Controller & Persona Prompts

**Author**: Worker Subagent M2 (`worker_m2`)  
**Date**: 2026-09-14T11:42:00Z  
**Project**: An An Persona Chatbot  
**Milestone**: M2 (Dynamic Response Length & Prompts)  
**Status**: Completed — 100% Tests Passing (170/170)

---

## 1. Observation

1. **Interface Contracts & File Ownership**:
   - Dispatched to implement core modules:
     - `src/core/__init__.py`
     - `src/core/length_controller.py`
     - `src/core/prompts.py`
     - `tests/test_length.py`
   - Verified that prior Milestone M1 tests (`tests/test_ingestion.py`) were passing with 74/74 tests.

2. **Implemented Code Invariants**:
   - `src/core/length_controller.py`:
     - `LengthTier(str, Enum)` with values `"short"`, `"medium"`, `"long"`.
     - `LengthDecision(BaseModel)` with `tier`, `max_tokens` (35, 75, 160), `guidance_instruction`, `min_words`, `max_words`, `empirical_ratio`.
     - `determine_response_length(user_input, conversation_history)` classifying greetings, affirmations, and short queries ($\le 4$ words) as `SHORT`, study/hangout banter (5–25 words) as `MEDIUM`, and emotional confessions/boundaries/word counts $> 25$ as `LONG`.
     - Verified disambiguation of romantic desires (`"muốn đc bên an"`) from physical visits (`"qua bên An lấy tiền mặt"`).
   - `src/core/prompts.py`:
     - `SYSTEM_PROMPT_BASE`: Enforces Vietnamese-only chat (`VIETNAMESE_ONLY`), An An's art student persona, close friend relationship with `ql`, mandatory slang rules (`kh`, `dc`, `nma`, `r`, `=)))`, `🤡`), and bans AI assistant disclaimers, markdown headers, and bullet points.
     - `build_system_prompt()`: Dynamically incorporates `LengthDecision.guidance_instruction` and few-shot dialogue exemplars from `FEW_SHOT_EXCHANGES`.
     - `get_chat_prompt_template()`: Produces LangChain `ChatPromptTemplate` with `SystemMessage`, `MessagesPlaceholder(variable_name="history", optional=True)`, and `HumanMessage("{input}")`.
   - `src/core/__init__.py`:
     - Exports core symbols (`LengthTier`, `LengthDecision`, `determine_response_length`, `SYSTEM_PROMPT_BASE`, `build_system_prompt`, `get_chat_prompt_template`, etc.).

3. **Test Execution Observations**:
   - Running `& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_length.py tests/test_ingestion.py -v`:
     - `tests/test_length.py`: 96 passed in 0.50s.
     - `tests/test_ingestion.py`: 74 passed.
     - Total: **170 passed in 1.75s** with 0 failures, 0 errors, 0 warnings.
   - Running `py_compile` across all created/modified files completed cleanly with exit code 0.

---

## 2. Logic Chain

1. **Dynamic Length Enforcement (F4)**:
   - Gen-Z Vietnamese chat logs exhibit an empirical distribution of 70% short, 27.6% medium, and 2.4% long messages.
   - By calculating word counts and parsing specific conversational triggers, `determine_response_length` caps generation tokens physically at generation time (`max_tokens`: 35 for `SHORT`, 75 for `MEDIUM`, 160 for `LONG`).
   - Upstream injection of `guidance_instruction` directly instructs the model to omit preambles, bullet points, or polite apologies, guaranteeing authentic brevity.

2. **Persona Authenticity & Anti-AI Shield (F3, F6)**:
   - Standard LLM behavior defaults to structured, courteous, multi-paragraph output with markdown formatting.
   - `SYSTEM_PROMPT_BASE` explicitly disables these behaviors via clear negative constraints (banning `#`, `##`, `*`, `-`, numbered lists, and assistant disclaimers like "Tôi có thể giúp gì cho bạn").
   - Slang dictionary constraints (`kh` instead of `ko`/`k`, `dc` instead of `đc`, `nma` instead of `nhma`, single `r` instead of `rồi`) and address rules (`ql`, `bạn`/`mình`, `m`/`t`) ensure exact alignment with the ingested Facebook dataset.

3. **Clean Architecture & LangChain Integration**:
   - `ChatPromptTemplate.from_messages` cleanly integrates with session memory via `MessagesPlaceholder(variable_name="history", optional=True)`.
   - This provides the necessary interface contract for Milestone M3 (`src/core/llm_factory.py` and `src/core/chain.py`).

---

## 3. Caveats

1. **Offline Zero-Cost Boundary**:
   - All tests in `tests/test_length.py` operate completely offline with zero API calls and zero cloud dependencies.
   - Live LLM calls and Agent-as-Judge validation will occur in Milestones M3 and M5.
2. **Context Continuity Heuristic**:
   - Emotional boundary context is tracked up to the last 4 turns in `conversation_history`. If a conversation shifts to a completely new topic without resetting memory, downstream logic in M3 should manage session resets.

---

## 4. Conclusion

- Milestone M2 requirements are fully satisfied:
  - `src/core/length_controller.py`, `src/core/prompts.py`, `src/core/__init__.py`, and `tests/test_length.py` are implemented and passing 100%.
  - Zero regressions introduced to Milestone M1 ingestion components (170/170 tests passing overall).
  - All constraints regarding Vietnamese-only output, anti-AI tone, and token bounds are enforced.

---

## 5. Verification Method

To independently reproduce and verify this work:

1. **Verify Python Syntax & Compilation**:
   ```powershell
   & ".\venv\Scripts\python.exe" -m py_compile src/core/__init__.py src/core/length_controller.py src/core/prompts.py tests/test_length.py
   ```

2. **Run the Full Test Suite**:
   ```powershell
   & ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_length.py tests/test_ingestion.py -v
   ```
   **Expected Result**: `170 passed in ~1.8s` with 0 failures.

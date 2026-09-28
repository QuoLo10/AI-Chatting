## 2026-09-14T11:35:47Z
You are a Worker subagent (Length Controller & Prompts Worker) for Milestone M2.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2
Project root: C:\Users\HKQL2\Documents\ExBuild

MANDATORY READ FIRST:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_1\length_design.md
4. C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2\prompt_design.md
5. C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3\test_spec.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

STRICT CONSTRAINT:
Do NOT delete or modify any files outside of the main project folder (C:\Users\HKQL2\Documents\ExBuild). All your work must be strictly contained within this directory.

EXCLUSIVE FILE OWNERSHIP:
You own and may modify:
- src/core/__init__.py
- src/core/length_controller.py
- src/core/prompts.py
- tests/test_length.py
- Files in your working directory C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2

YOUR TASKS:
1. Implement `src/core/__init__.py` exporting core symbols.
2. Implement `src/core/length_controller.py` per `length_design.md` and `PROJECT.md`:
   - `LengthTier(str, Enum)`: `SHORT="short"`, `MEDIUM="medium"`, `LONG="long"`.
   - `LengthDecision(BaseModel)`: `tier`, `max_tokens`, `guidance_instruction`, `min_words`, `max_words`, `empirical_ratio`.
   - `determine_response_length(user_input: str, conversation_history: list = None) -> LengthDecision`.
3. Implement `src/core/prompts.py` per `prompt_design.md`:
   - Strict Vietnamese language mandate (`VIETNAMESE_ONLY`).
   - Persona rules: An An art student, uses `kh`/`hong`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`.
   - Prohibitions: No AI disclaimers, no bullet points, no markdown headers, no polite assistant fluff.
   - Functions `build_system_prompt()` and `get_chat_prompt_template()`.
4. Implement `tests/test_length.py` matching `test_spec.md`.
5. Run the test suite:
   `& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_length.py tests/test_ingestion.py -v`
   Ensure 100% of all tests pass.
6. Write a detailed handoff report to `C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2\handoff.md`.
7. Notify orchestrator via send_message when complete.

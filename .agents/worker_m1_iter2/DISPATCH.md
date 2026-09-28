## 2026-09-14T11:15:38Z
You are a Worker subagent (Ingestion & Regression Remediation Worker) for Milestone M1 Iteration 2.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m1_iter2
Project root: C:\Users\HKQL2\Documents\ExBuild

MANDATORY READ FIRST:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_iter2_1\remediation_plan.md
4. C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_iter2_2\remediation_plan.md
5. C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_iter2_3\regression_test_spec.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

STRICT CONSTRAINT:
Do NOT delete or modify any files outside of the main project folder (C:\Users\HKQL2\Documents\ExBuild). All your work must be strictly contained within this directory.

EXCLUSIVE FILE OWNERSHIP:
You own and may modify:
- src/ingestion/parser.py
- src/ingestion/persona_profile.py
- src/ingestion/__init__.py
- tests/test_ingestion.py
- Files in your working directory C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m1_iter2

YOUR TASKS:
1. In `src/ingestion/parser.py`, apply the 4 fixes from `explorer_m1_iter2_1\remediation_plan.md`:
   - Open files with `encoding="utf-8-sig"` to strip UTF-8 BOM automatically.
   - Guard against null content before `str()` stringification (drop empty/null content).
   - Catch `(ValueError, TypeError, OverflowError)` when converting timestamps.
   - Use strict / word-boundary regex for An An matching (`r"^\s*an\s+an\s*$"` or word boundary `r"\ban\s+an\b"`) to prevent matching "Nguyễn Văn An".
2. In `src/ingestion/persona_profile.py`, apply the fixes from `explorer_m1_iter2_2\remediation_plan.md`:
   - Add `if limit <= 0: return []` in `get_few_shot_examples`.
   - Add optional `max_gap_hours: Optional[float] = None` parameter in `extract_an_an_profile` with gap calculation.
   - Enforce Vietnamese output: add language mandate fields to `PERSONA_PROFILE`, English assistant boilerplate to `PROHIBITED_TOKENS`, and add `format_few_shot_prompt()`.
3. Export any new public functions/constants in `src/ingestion/__init__.py`.
4. Add the regression test classes from `spec_miner_m1_iter2_3\regression_test_spec.md` into `tests/test_ingestion.py`.
5. Execute the test suite and challenger harnesses:
   - `& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_ingestion.py -v`
   - `& ".\venv\Scripts\python.exe" -X utf8 .\.agents\challenger_m1_1\challenge_harness.py`
   - `& ".\venv\Scripts\python.exe" -X utf8 -m pytest .\.agents\challenger_m1_2\test_verify_persona.py -v`
   Verify 100% of tests pass on all suites.
6. Write a comprehensive handoff report to `C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m1_iter2\handoff.md`.
7. Notify orchestrator via send_message when complete.

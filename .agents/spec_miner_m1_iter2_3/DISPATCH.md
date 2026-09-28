## 2026-09-14T11:08:03Z
You are a Spec Miner subagent (Regression Test Specifier) for Milestone M1, Iteration 2.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_iter2_3
Project root: C:\Users\HKQL2\Documents\ExBuild

MANDATORY READ FIRST:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\.agents\orchestrator_1\GATE_STATUS.md
4. C:\Users\HKQL2\Documents\ExBuild\.agents\challenger_m1_1\challenge_harness.py
5. C:\Users\HKQL2\Documents\ExBuild\.agents\challenger_m1_2\test_verify_persona.py

STRICT CONSTRAINT:
Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild. All your work must be strictly contained within this directory.
REMINDER: You are a Spec Miner; do NOT modify test files directly.

YOUR TASK:
1. Design new regression unit test cases for `tests/test_ingestion.py` covering all 5 challenger issues:
   - UTF-8 BOM JSON parsing
   - `"content": null` media messages
   - Non-finite / overflow timestamps
   - "Nguyễn Văn An" sender name discrimination (`is_an_an` should be False)
   - `get_few_shot_examples(limit=0)` returning empty list
2. Design test assertions verifying that all persona profile prompt instructions and few-shot examples enforce Vietnamese language output.
3. Write your test specification in `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_iter2_3\regression_test_spec.md` and complete your handoff.md.
4. Notify orchestrator via send_message when done.

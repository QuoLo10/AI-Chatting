## 2026-09-14T11:27:57Z
You are a Spec Miner subagent (Length & Prompt Test Specifier) for Milestone M2.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3
Project root: C:\Users\HKQL2\Documents\ExBuild

MANDATORY READ FIRST:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\TEST_INFRA.md

STRICT CONSTRAINT:
Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild. All your work must be strictly contained within this directory.
REMINDER: You are a Spec Miner; do NOT implement test files directly.

YOUR TASK:
1. Design the complete unit test specification for `tests/test_length.py`:
   - Test `determine_response_length` on short inputs (e.g. "ê", "alo", "dậy chưa", "chán quá") -> `LengthTier.SHORT` (max_tokens <= 35).
   - Test on normal conversational turns -> `LengthTier.MEDIUM` (max_tokens <= 75).
   - Test on emotional boundary / long deep inputs -> `LengthTier.LONG` (max_tokens <= 160).
   - Test boundary edge cases: empty string, whitespace, massive text, punctuation only.
   - Test prompt generation in `src/core/prompts.py`: verify that compiled system prompt contains Vietnamese language instruction, prohibited tokens list, and slang dictionary references.
2. Write your test specification to `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3\test_spec.md` and complete your handoff.md.
3. Notify orchestrator via send_message when done.

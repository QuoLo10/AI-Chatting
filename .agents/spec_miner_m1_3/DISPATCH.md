## 2026-09-14T10:49:54Z
You are a Spec Miner subagent (Ingestion Test Specifier) for Milestone M1.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_3
Project root: C:\Users\HKQL2\Documents\ExBuild
You MUST read:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\TEST_INFRA.md
4. C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_survey_3\spec_requirements.md

STRICT CONSTRAINT: Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild.
REMINDER: You are a Spec Miner; do NOT implement test files directly.

Your task:
1. Specify the comprehensive unit test suite for Milestone M1 (`tests/test_ingestion.py`).
2. Design test cases for:
   - Happy path: parsing `An An_86.json` sample file (checking message count, participants, order).
   - Safe transcoding: test strings with native UTF-8, Latin-1 double encoded, and mixed strings to ensure zero `UnicodeEncodeError`.
   - Message filtering: unsent messages, media attachments with `"Failed to download media"`.
   - Persona profiling: stats calculation, message length distributions, token frequencies (`kh`, `dc`, `nma`, `r`), dialogue pair extraction.
   - Fault tolerance: handling non-existent file, malformed JSON, empty messages array.
3. Write your test specification to C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_3\test_spec.md and complete your handoff.md.
4. Notify the orchestrator via send_message when complete.

## 2026-09-14T11:42:51Z

You are Reviewer 2 (Prompt & Vietnamese Reviewer) for Milestone M2.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\reviewer_m2_2
Project root: C:\Users\HKQL2\Documents\ExBuild

MANDATORY READ FIRST:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2\handoff.md

STRICT CONSTRAINT:
Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild. All your work must be strictly contained within this directory.

YOUR TASK:
1. Verify that `src/core/prompts.py` strictly enforces the Vietnamese language mandate.
2. Check that An An's persona rules (`kh`/`hong`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`) and prohibited tokens are rigorously implemented without leaks.
3. Run the test suite:
   `& ".\venv\Scripts\python.exe" -X utf8 -m pytest tests/test_length.py tests/test_ingestion.py -v`
4. Write your review report to C:\Users\HKQL2\Documents\ExBuild\.agents\reviewer_m2_2\review.md and handoff.md with a clear verdict (APPROVE or REQUEST_CHANGES).
5. Notify orchestrator via send_message when finished.

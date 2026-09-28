## 2026-09-14T11:42:51Z
You are Challenger 2 (Prompt Injection & Persona Challenger) for Milestone M2.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\challenger_m2_2
Project root: C:\Users\HKQL2\Documents\ExBuild

MANDATORY READ FIRST:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2\handoff.md

STRICT CONSTRAINT:
Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild. All your work must be strictly contained within this directory.

YOUR TASK:
1. Empirically challenge `src/core/prompts.py` (`build_system_prompt` and `get_chat_prompt_template`).
2. Write a challenge script in your working directory to test:
   - Prompt injection resistance (attempts to make An An speak English, switch to assistant persona, output markdown headers)
   - Template compilation with all combinations of LengthDecision and few-shot categories
   - Format string safety (no unescaped braces crashing LangChain)
3. Run your harness using `venv\Scripts\python.exe`.
4. Document findings and verdict (APPROVE or REQUEST_CHANGES) in C:\Users\HKQL2\Documents\ExBuild\.agents\challenger_m2_2\challenge.md and handoff.md.
5. Notify orchestrator via send_message when finished.

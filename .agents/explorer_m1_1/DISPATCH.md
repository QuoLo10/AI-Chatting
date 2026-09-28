## 2026-09-14T10:49:54Z
You are an Explorer subagent (Ingestion Implementation Planner) for Milestone M1.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1
Project root: C:\Users\HKQL2\Documents\ExBuild
You MUST read:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\TEST_INFRA.md
4. C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_survey_1\survey_data.md

STRICT CONSTRAINT: Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild.
REMINDER: You are an Explorer; do NOT implement production source code directly. Produce clear implementation recommendations for the Worker.

Your task:
1. Review the interface contracts in PROJECT.md for `src.ingestion.parser` and `src.ingestion.persona_profile`.
2. Design the exact architecture and code structure for:
   - `src/config.py`: loading `.env` using python-dotenv, defining paths, default JSON path `F:/dowload/FacebookData/messages/An An_86.json`, extracting `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`.
   - `src/ingestion/parser.py`: Pydantic `CanonicalMessage`, `parse_facebook_json(file_path: str)`, safe transcoding function `fix_fb_text()` with try/except UnicodeEncodeError/UnicodeDecodeError guard, filtering unsent/media messages.
   - `src/ingestion/persona_profile.py`: persona statistical extraction, profile generator, dictionary of slang terms, and verified few-shot dialogue turns extracted from survey 1.
3. Write your detailed design and recommendations to C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1\design.md and complete your handoff.md.
4. Notify the orchestrator via send_message when complete.

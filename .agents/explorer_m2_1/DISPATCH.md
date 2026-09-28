## 2026-09-14T11:28:00Z

Task from Orchestrator:
You are an Explorer subagent (Length Controller Architect) for Milestone M2.
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_1
Project root: C:\Users\HKQL2\Documents\ExBuild

MANDATORY READ FIRST:
1. C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md
2. C:\Users\HKQL2\Documents\ExBuild\PROJECT.md
3. C:\Users\HKQL2\Documents\ExBuild\TEST_INFRA.md
4. C:\Users\HKQL2\Documents\ExBuild\src\ingestion\persona_profile.py

STRICT CONSTRAINT:
Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild. All your work must be strictly contained within this directory.
REMINDER: You are an Explorer; do NOT implement production code directly.

YOUR TASK:
1. Design `src/core/length_controller.py` matching the interface contracts in `PROJECT.md`:
   - `LengthTier(str, Enum)`: `SHORT` (1-5 words, max_tokens=35), `MEDIUM` (6-15 words, max_tokens=75), `LONG` (20-50 words, max_tokens=160).
   - `LengthDecision(BaseModel)`: `tier: LengthTier`, `max_tokens: int`, `guidance_instruction: str`.
   - `determine_response_length(user_input: str, conversation_history: list = None) -> LengthDecision`:
     - Classify user input intent and length:
       - Greetings ("hi", "ê", "alo", "chào"), simple affirmations ("ừ", "ok", "đúng r"), short reactions -> `SHORT` (matches 70% of An An messages).
       - Chit-chat, casual banter, study queries, questions -> `MEDIUM` (matches 27.6% of An An messages).
       - Long inputs (>30 words) or serious emotional topics (relationship confession, boundaries, heart-to-heart) -> `LONG` (matches 2.4% of An An messages).
     - Ensure guidance instruction explicitly commands short natural messaging in Vietnamese without AI disclaimers or bullet points.
2. Write your design to `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_1\length_design.md` and complete your handoff.md.
3. Notify orchestrator via send_message when done.

# BRIEFING — 2026-09-14T11:35:00Z

## Mission
Design `src/core/prompts.py` for Milestone M2: crafting the comprehensive LangChain ChatPromptTemplate embodying An An persona, Vietnamese-only enforcement, dynamic length instruction injection, and categorized few-shot exemplar injection.

## 🔒 My Identity
- Archetype: explorer
- Roles: Persona Prompt Specialist
- Working directory: C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2
- Original parent: 30e037d6-ec66-4bba-8a82-498b94f60b80
- Milestone: M2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement production code directly
- Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild
- Write only to C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2
- CRITICAL USER MANDATE: The output language for the chatbot MUST be Vietnamese
- Strictly enforce An An persona traits, texting quirks (kh/hong, dc, nma, r, v/z, th/thui, oki/okiii), laughter/emojis (=))), 🤡, hihi, huhu), forbid AI assistant traits and markdown headers/bullet points.

## Current Parent
- Conversation ID: 30e037d6-ec66-4bba-8a82-498b94f60b80
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md`
  - `C:\Users\HKQL2\Documents\ExBuild\PROJECT.md`
  - `C:\Users\HKQL2\Documents\ExBuild\TEST_INFRA.md`
  - `C:\Users\HKQL2\Documents\ExBuild\src\ingestion\persona_profile.py`
  - `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_survey_1\survey_data.md`
  - `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_1\length_design.md`
  - `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3\test_spec.md`
- **Key findings**:
  - Persona background: An An is a female university student studying fine arts/design in Vietnam, close friends with user `ql` (classmate).
  - Crucial linguistic quirks: strict use of `kh` or `hong` (never `k` or `ko`), `dc` (never `đc`), `nma` (never `nhma`), `r` (never `rồi`), `v`/`z` (vậy), `th`/`thui` (thôi), `oki`/`okiii` (never `oke`), `=)))`, `🤡`, `hihi`, `huhu`.
  - Anti-AI shield: Strictly bans markdown headers (`#`, `##`), bullet points (`*`, `-`, `1.`), AI pleasantries, and essay structures.
  - Contract alignment: Cross-verified against `test_spec.md` Suite 7 (`TestSystemPromptGeneration`) and Suite 8 (`TestChatPromptTemplateIntegration`).
- **Unexplored areas**: None for M2 prompt design scope.

## Key Decisions Made
- Structured `src/core/prompts.py` around three core exports: `SYSTEM_PROMPT_BASE`, `build_system_prompt(...)`, and `get_chat_prompt_template(...)`.
- Designed dual injection for few-shots: formatted text block inside `build_system_prompt` and native LangChain message pairs via `get_few_shot_messages`.
- Provided a full reference implementation in `prompt_design.md` ready for Worker M2.

## Artifact Index
- `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2\DISPATCH.md` — Received instructions
- `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2\BRIEFING.md` — Situational awareness
- `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2\progress.md` — Heartbeat tracking
- `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2\prompt_design.md` — Comprehensive prompt architecture specification
- `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2\handoff.md` — Final 5-component handoff report

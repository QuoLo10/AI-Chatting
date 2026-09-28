# BRIEFING — 2026-09-14T11:42:00Z

## Mission
Implement Milestone M2: Dynamic Response Length Controller and Persona Prompts (`src/core/length_controller.py`, `src/core/prompts.py`, `src/core/__init__.py`), with comprehensive test suite in `tests/test_length.py`.

## 🔒 My Identity
- Archetype: Worker
- Roles: implementer, qa, specialist
- Working directory: C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2
- Original parent: 30e037d6-ec66-4bba-8a82-498b94f60b80
- Milestone: M2 (Dynamic Response Length & Prompts)

## 🔒 Key Constraints
- Zero-cost architecture (no paid subscriptions/APIs).
- Strict Vietnamese-only colloquial chat output.
- No AI disclaimers, no bullet points, no markdown headers, no polite assistant fluff.
- All implementations must be genuine — no cheating, hardcoded test results, or dummy facades.
- All modifications strictly within C:\Users\HKQL2\Documents\ExBuild.
- Exclusive file ownership: src/core/__init__.py, src/core/length_controller.py, src/core/prompts.py, tests/test_length.py, and .agents/worker_m2/*.

## Current Parent
- Conversation ID: 30e037d6-ec66-4bba-8a82-498b94f60b80
- Updated: not yet

## Task Summary
- **What to build**: Dynamic length controller (LengthTier, LengthDecision, determine_response_length), persona prompt builder (build_system_prompt, get_chat_prompt_template), core package exports, and test suite in tests/test_length.py.
- **Success criteria**: 100% test pass on tests/test_length.py and tests/test_ingestion.py.
- **Interface contracts**: PROJECT.md, length_design.md, prompt_design.md, test_spec.md
- **Code layout**: PROJECT.md § Code Layout

## Key Decisions Made
- LengthTier: SHORT="short" (max_tokens=35, 1-5 words), MEDIUM="medium" (max_tokens=75, 6-15 words), LONG="long" (max_tokens=160, 20-50 words).
- LengthDecision: Pydantic v2 model with required `tier`, `max_tokens`, `guidance_instruction`, and defaulted `min_words`, `max_words`, `empirical_ratio`.
- Disambiguated romantic confession "muốn đc bên an" vs physical hangout visit "qua bên An" to prevent false positive in logistics banter.
- ChatPromptTemplate constructed with SystemMessage, MessagesPlaceholder(variable_name="history", optional=True), and HumanMessage("{input}").

## Change Tracker
- **Files modified**:
  - `src/core/length_controller.py`: Dynamic length decision model, token limits, Vietnamese guidance, intent & word count classifier.
  - `src/core/prompts.py`: Base system prompt with strict Vietnamese mandate, slang rules, anti-AI formatting shield, dynamic guidance injection, few-shot injection, and LangChain ChatPromptTemplate.
  - `src/core/__init__.py`: Package exports for core primitives.
  - `tests/test_length.py`: 8 test suites (96 tests) testing enums, models, length determination, edge cases, system prompt generation, and LangChain integration.
- **Build status**: 170 passed in 1.75s (100% pass)
- **Pending issues**: None

## Quality Status
- **Build/test result**: PASS (170/170 tests passing across tests/test_length.py and tests/test_ingestion.py)
- **Lint status**: 0 syntax/compilation violations (`py_compile` succeeded)
- **Tests added/modified**: 96 tests added in tests/test_length.py

## Loaded Skills
- None requested

## Artifact Index
- C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2\DISPATCH.md — Assignment instructions
- C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2\progress.md — Liveness & task checklist
- C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2\BRIEFING.md — Situational awareness
- C:\Users\HKQL2\Documents\ExBuild\.agents\worker_m2\handoff.md — 5-Component handoff report

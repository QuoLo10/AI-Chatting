# BRIEFING — 2026-09-14T10:52:40Z

## Mission
Design exact architecture and code structure for Milestone M1 (Data Ingestion & Persona Profiling): src/config.py, src/ingestion/parser.py, and src/ingestion/persona_profile.py.

## 🔒 My Identity
- Archetype: Explorer
- Roles: Ingestion Implementation Planner, Data Profiling Analyst
- Working directory: C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1
- Original parent: 30e037d6-ec66-4bba-8a82-498b94f60b80
- Milestone: M1

## 🔒 Key Constraints
- Read-only investigation — do NOT implement production source code directly
- Strict boundary: Do NOT delete or modify any files outside C:\Users\HKQL2\Documents\ExBuild
- Only write metadata, reports, and plans to C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1\
- Produce clear, modular, unambiguous implementation specifications for Worker M1

## Current Parent
- Conversation ID: 30e037d6-ec66-4bba-8a82-498b94f60b80
- Updated: 2026-09-14T10:50:00Z

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`
  - `explorer_survey_1/survey_data.md`, `explorer_survey_2/survey_env.md`, `spec_miner_survey_3/spec_requirements.md`
  - Target dataset: `F:/dowload/FacebookData/messages/An An_86.json`
- **Key findings**:
  - `An An_86.json` is clean UTF-8 (2,102 messages). Blind `encode('latin1')` crashes with `UnicodeEncodeError` on Vietnamese diacritics. `try / except (UnicodeEncodeError, UnicodeDecodeError)` guard verified 100% safe.
  - Empirical word distribution: 70.0% short ($\le 5$ words), 27.6% medium (6-15 words), 2.4% long (>15 words), perfectly matching `PROJECT.md` length tiers.
  - Empirical slang: `kh` (143) / `hong` (12) vs `ko` (2) and `k` (0); `dc` (42) vs `đc` (0); `nma` (36) vs `nhma` (0); `=)))` (81).
  - Windows console defaults to CP1252, requiring `sys.stdout.reconfigure(encoding='utf-8')` to print Vietnamese safely.
- **Unexplored areas**: Downstream prompt templates (M2), LLM factory (M3), CLI (M4).

## Key Decisions Made
- Designed `src/config.py` with cross-fallback for `GEMINI_API_KEY` and `GOOGLE_API_KEY`, default JSON path `F:/dowload/FacebookData/messages/An An_86.json`.
- Designed `src/ingestion/parser.py` with `CanonicalMessage` adhering to `PROJECT.md` contract, safe `fix_fb_text()`, and unsent/media filtering.
- Designed `src/ingestion/persona_profile.py` with `extract_an_an_profile()`, `SLANG_DICTIONARY`, `PROHIBITED_TOKENS`, and 15 verified few-shot exchanges across 6 categories.

## Artifact Index
- DISPATCH.md — Initial task dispatch
- BRIEFING.md — Working memory and identity index
- progress.md — Liveness heartbeat and milestone checklist
- design.md — Complete architectural and code design for M1
- handoff.md — 5-Component handoff report for Worker M1

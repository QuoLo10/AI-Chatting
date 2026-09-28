# Project Plan: An An Persona Chatbot

## Objective
Build a free, CLI-based AI chatbot using LangChain that ingests Facebook messages JSON to mimic the personality, style, and dynamic response length of "An An", with automated testing and Agent-as-Judge evaluation.

## Phase 0: Survey & Discovery (Current)
- Explorer 1 (Data Analyst): Inspect `F:/dowload/FacebookData/messages/An An_86.json`, analyze encoding (UTF-8/mojibake handling), message structures, participants, dialogue turns, An An's tone, vocabulary, reaction patterns, response lengths, emojis, and conversation dynamics.
- Explorer 2 (Environment & API Analyst): Inspect workspace `C:\Users\HKQL2\Documents\ExBuild`, examine `venv` Python environment, installed packages (LangChain version, model providers like `langchain-google-genai`, `langchain-community`, `langchain-openai`, `langchain-groq`, etc.), available free-tier cloud APIs and environment keys.
- Explorer 3 / Spec Miner (Architecture & Verification Spec): Synthesize architecture requirements (ingestion pipeline, persona extraction/prompting, dynamic response length module, LangChain memory/chain, CLI interface) and design the verification framework (E2E tests, Agent-as-Judge evaluation across >=3 simulated conversations).

## Phase 1: Assessment, Decomposition & Project Index (`PROJECT.md`)
- Aggregate survey reports into Feature Inventory.
- Decompose into modular milestones (e.g. M1: Data Ingestion & Persona Modeling, M2: Core LangChain Agent with Dynamic Length & Free Cloud LLM, M3: Single-command CLI Interface, M4: E2E Test Suite & Agent-as-Judge Evaluation).
- Set up Dual Track: Implementation Track + E2E Testing Track (`TEST_INFRA.md`).

## Phase 2: Implementation & E2E Testing
- Dispatch sub-orchestrators / workers per milestone with iteration loops:
  - Explorer -> Worker -> Reviewers (2) -> Challengers (2) -> Forensic Auditor -> Gate.
- Monitor execution, manage subagent lifecycle, track progress.

## Phase 3: Final E2E Test Pass & Hardening
- Pass 100% of E2E test suite.
- Agent-as-Judge evaluation on >= 3 distinct simulated conversations.
- Adversarial coverage hardening.
- Final forensic audit verification.

## Phase 4: Delivery & Audit Verification
- Final report to parent and user.

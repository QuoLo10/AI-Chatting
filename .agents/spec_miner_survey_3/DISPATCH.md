## 2026-09-14T10:37:00Z
You are a Spec Miner subagent (Architecture & Verification Spec Miner).
Your working directory is: C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_survey_3
Project root: C:\Users\HKQL2\Documents\ExBuild
You MUST read C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md before starting work.

Your task:
1. Mine and extract detailed technical and verification requirements for:
   - Data Ingestion Module: Parsing FB JSON, decoding mojibake, extracting An An messages and conversation threads, persistent profile or dynamic few-shot retrieval.
   - Dynamic Response Length Module: Mechanism to infer target response length based on context (e.g., matching user prompt length/type, query type, historical persona distribution) and inject guidance into the prompt or generation params.
   - Core LangChain Architecture: PromptTemplate / ChatPromptTemplate, ChatModel (free-tier Google GenAI / Groq), RunnableWithMessageHistory or BaseChatMessageHistory for multi-turn CLI session.
   - CLI Interface: Single command execution via venv\Scripts\python -m ... or venv\Scripts\python main.py, interactive loop, commands (/exit, /reset, /stats), streaming or clean terminal output.
   - Agent-as-Judge Evaluation Script: Automated secondary LLM evaluation script comparing chatbot responses against An An persona in the JSON data across >= 3 distinct simulated conversations. Define exact scoring rubric (Persona Mimicry: tone/habits/humor, Dynamic Response Length matching context, Language consistency), pass/fail threshold, and output report format.
   - Automated Test Suite: Unit and integration tests for JSON parsing, length controller, prompt formatting, and CLI runner.
2. Write the specification to C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_survey_3\spec_requirements.md and complete your handoff.md.
3. Use send_message to notify the orchestrator when finished.

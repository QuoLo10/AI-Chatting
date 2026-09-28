# Handoff Report — Architecture & Verification Specification Miner (`spec_miner_survey_3`)

## 1. Observation
1. **Target Request & Constraints:**
   - Path: `C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md`
   - Requirements: R1 (Persona Mimicry from FB JSON), R2 (Dynamic Response Length avoiding AI explanations), R3 (Zero-cost architecture using free cloud APIs), R4 (LangChain Python framework), R5 (CLI chat interface).
   - Acceptance Criteria: Single-command CLI launch via `venv`, automated test suite, Agent-as-Judge evaluation on $\ge 3$ distinct simulated conversations with clear pass/fail score on persona match (humor, habits, dynamic response length).
2. **Empirical Dataset Inspection:**
   - Path: `F:/dowload/FacebookData/messages/An An_86.json` (File size: 515,161 bytes).
   - Top-level JSON schema: `{"participants": ["Hoàng Kim Quờ Lờ", "An An"], "threadName": "An An_86", "messages": [...]}`.
   - Message fields: `['isUnsent', 'media', 'reactions', 'senderName', 'text', 'timestamp', 'type']`.
   - Total messages: 2,102. Senders: An An: 1,205 messages; Hoàng Kim Quờ Lờ: 897 messages.
   - Character count of An An valid texts: min=1, max=390, mean=17.8, median=13.0.
   - Word count of An An valid texts: min=1, max=92, mean=4.7, median=4.0.
   - Distribution:
     - $\le 5$ words: 822 messages (**70.0%**).
     - $6 - 15$ words: 324 messages (**27.6%**).
     - $> 15$ words: 28 messages (**2.4%**). Max word length: 92 words.
   - Message Burst Pattern: 410 turns total for An An; mean burst size = 2.94 messages per turn; 48% of turns are 2-3 consecutive short bubbles.
3. **Linguistic & Slang Statistics:**
   - Slang occurrences in An An messages:
     - `kh` (134) vs `ko` (2) vs `k` (0).
     - `dc` (42) vs `đc` (0).
     - `nma` (34) vs `nhma` (0).
     - `r` for "rồi" (98).
     - Emoticons & Laughs: `=)))` (75), `hihi` (15), `huhu` (15), `hẹ hẹ` (4), `hehe` (3).
     - Self reference: "An", "mình", "mìn" (147); User reference: "ql" (38).
4. **Encoding & Mojibake Pitfall:**
   - Running `text.encode('latin1')` on clean Vietnamese `ơ` (`U+01A1`) in Windows Python raised:  
     `UnicodeEncodeError: 'latin-1' codec can't encode character '\u01a1' in position 1: ordinal not in range(256)`.
   - Windows PowerShell console stdout default is CP1252, causing `UnicodeEncodeError: 'charmap' codec can't encode character '\u1edd'` when printing unconfigured Vietnamese stdout.
5. **Python Environment & Dependencies:**
   - Python executable: `C:\Users\HKQL2\Documents\ExBuild\venv\Scripts\python.exe` (Version: 3.14.6 AMD64).
   - Only `pip 26.1.2` was initially installed.
   - `pip install --dry-run` successfully resolved prebuilt binary wheels for Python 3.14: `langchain-1.4.0`, `langchain-core-1.6.3`, `langchain-google-genai-4.4.0`, `langchain-groq-1.1.3`, `google-genai-2.23.0`, `groq-0.37.1`, `pydantic-2.13.5`, `pytest-9.1.1`.
   - Free-tier cloud API keys: No keys currently found in `os.environ`; system must read `GOOGLE_API_KEY`, `GEMINI_API_KEY`, or `GROQ_API_KEY` from `.env` or system environment.

## 2. Logic Chain
1. **Data Ingestion Design:**
   - From Observation 2 and 4, Facebook message dumps vary between standard exports (`sender_name`, `content`, `timestamp_ms`, Latin-1 double encoding) and modern exports (`senderName`, `text`, `timestamp`, clean UTF-8).
   - Therefore, the ingestion engine must normalize keys into a canonical Pydantic model (`CanonicalMessage`) and use a safe heuristic transcoding function that handles Latin-1 decoding errors without crashing on native UTF-8 strings.
2. **Dynamic Response Length Engine Design:**
   - From Observation 2, 70% of An An's responses are $\le 5$ words, and 97.6% are $\le 15$ words. A standard LLM generating multi-paragraph explanations completely violates the persona.
   - Therefore, a context and intent classifier must categorize incoming prompts into SHORT (1-5 words, `max_tokens=35`), MEDIUM (6-15 words, `max_tokens=75`), or LONG (20-50 words, `max_tokens=160`), injecting dynamic length guidance and hard token ceilings into the generation parameters.
3. **Core LangChain Architecture:**
   - From Observation 5, Python 3.14 supports modern LangChain (1.4.x) with official Google GenAI (`gemini-2.0-flash`) and Groq (`llama-3.3-70b-versatile`). Both offer generous free-tier quotas requiring no credit card.
   - Therefore, a unified ChatModel factory with automatic fallback between Google and Groq satisfies R3 (Zero-cost).
   - Session memory is best managed via `RunnableWithMessageHistory` and `InMemoryChatMessageHistory` with a 12-turn sliding window.
4. **CLI & Windows Encoding:**
   - From Observation 4, Windows PowerShell defaults to CP1252.
   - Therefore, the CLI entry point must explicitly call `sys.stdout.reconfigure(encoding='utf-8')` and `os.system('')` to prevent terminal crashes and enable ANSI formatting.
5. **Agent-as-Judge & Automated Testing:**
   - From Observation 1, acceptance criteria mandate automated test suites and an Agent-as-Judge evaluation on $\ge 3$ distinct simulated conversations.
   - We designed 3 concrete test conversations (Casual Banter, Study Coordination, Emotional Confession) and a 3-dimensional rubric (Persona Mimicry 40%, Dynamic Length 30%, Slang 30%) with a strict threshold (Weighted score $\ge 8.0/10.0$, hard floor of 7.0 in every category).

## 3. Caveats
1. **API Keys Not Currently Set:** Neither `GOOGLE_API_KEY` nor `GROQ_API_KEY` is present in the current process environment. The implementation must include a `.env.example` template and guide the user/orchestrator to provide at least one free API key.
2. **Offline Unit Testing:** Tests in CI/offline environments must use mock chat models (e.g. `FakeListChatModel`) so unit tests do not fail when no network or API keys are available. Live API calls should be reserved for integration tests or flagged with a pytest marker (`@pytest.mark.live_api`).
3. **Third-Party Data Variations:** While `An An_86.json` is verified, other user exports may contain photos, audio attachments, or group threads. The ingestion parser must safely ignore media attachments and group messages without crashing.

## 4. Conclusion
The architectural and verification specifications are completely defined, empirical baselines established, and documented in:
`C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_survey_3\spec_requirements.md`

All six core modules (Data Ingestion, Dynamic Response Length Controller, Core LangChain Chain, CLI Interface, Agent-as-Judge Evaluator, and Automated Test Suite) have unambiguous interfaces, mathematical bounds, Pydantic schemas, and pass/fail thresholds ready for implementation.

## 5. Verification Method
1. **Inspect Specification Document:**
   - View `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_survey_3\spec_requirements.md` to review the complete technical requirements, Pydantic schemas, prompt templates, and evaluation rubric.
2. **Verify Dataset Probing:**
   - Run: `.\venv\Scripts\python.exe -X utf8 .\.agents\spec_miner_survey_3\probe_turns.py` to confirm the dialogue turns extracted from `F:\dowload\FacebookData\messages\An An_86.json`.
3. **Verify Python 3.14 Compatibility:**
   - Run: `.\venv\Scripts\pip.exe install --dry-run langchain langchain-core langchain-community langchain-google-genai langchain-groq pydantic pytest python-dotenv` to verify all wheels resolve cleanly without compilation errors.
4. **Invalidation Conditions:**
   - If the implementation defaults to generating responses $> 25$ words for casual greetings, the dynamic length specification is violated.
   - If Latin-1 transcoding throws an uncaught `UnicodeEncodeError` on Vietnamese characters, the ingestion specification is violated.
   - If the chatbot scores $< 8.0/10$ on the Agent-as-Judge evaluation on any of the 3 simulated conversations, the verification criteria are not met.

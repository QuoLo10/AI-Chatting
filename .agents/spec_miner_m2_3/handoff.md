# Milestone M2 Handoff Report: Length Controller & Prompt Test Specification

**Agent:** `spec_miner_m2_3` (Spec Miner — Length & Prompt Test Specifier)  
**Milestone:** M2 (Dynamic Response Length & Prompts)  
**Working Directory:** `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3`  
**Handoff Type:** Hard (Task complete)  
**Date:** 2026-09-14  

---

## 1. Observation

Direct observations from authoritative specifications and environment probes:

1. **User Requirements (`ORIGINAL_REQUEST.md`)**:
   - Line 18–19: *"R1. Persona Mimicry: The chatbot must analyze the provided Facebook JSON data to extract and reflect the target person ('An An')'s habits, likes, dislikes, humor, and talking style."*
   - Line 21–22: *"R2. Dynamic Response Length: The AI must not default to long-winded AI explanations; response length (short or long) must dynamically match the context of the incoming message and the learned persona."*
   - Line 27–28: *"R4. Framework (LangChain): Use the LangChain Python framework to build the core conversation logic, memory, and persona ingestion."*

2. **Interface Contracts (`PROJECT.md`)**:
   - Lines 73–89 define the contract for `src.core.length_controller`:
     ```python
     class LengthTier(str, Enum):
         SHORT = "short"     # 1-5 words, max_tokens=35 (70% of An An messages)
         MEDIUM = "medium"   # 6-15 words, max_tokens=75 (27.6% of An An messages)
         LONG = "long"       # 20-50 words, max_tokens=160 (2.4% emotional boundary turns)

     class LengthDecision(BaseModel):
         tier: LengthTier
         max_tokens: int
         guidance_instruction: str

     def determine_response_length(user_input: str, conversation_history: list = None) -> LengthDecision:
     ```
   - Lines 134–138 define `src/core/length_controller.py` and `src/core/prompts.py`.

3. **Empirical Ground Truth (`src/ingestion/persona_profile.py`)**:
   - Lines 426–444 calculate empirical word lengths: 70.0% short ($\le 5$ words), 27.6% medium (6–15 words), 2.4% long (> 15 words); mean words = 4.7, median words = 4.0.
   - Lines 15–107 define `SLANG_DICTIONARY` containing canonical rules for `kh`, `hong`, `dc`, `nma`, `r`, `v`, `z`, `th`, `thui`, `oki`, `=)))`, `🤡`, `ql`.
   - Lines 110–133 define `PROHIBITED_TOKENS` containing forbidden slang (`ko`, `k`, `đc`, `nhma`, `oke`), overly polite pronouns (`ạ`, `dạ`, `cậu`, `tớ`), and AI boilerplate (`"Tôi là trợ lý ảo"`, `"As an AI"`, etc.).
   - Lines 143–155 and 360–365 define `language_mandate` and `VIETNAMESE_LANGUAGE_INSTRUCTION`:
     *"CRITICAL REQUIREMENT: Chatbot output MUST always be in Vietnamese (Tiếng Việt). Under NO circumstances should An An respond in English or any other foreign language..."*
   - Lines 173–327 contain 15 categorized few-shot exchanges from `An An_86.json`.

4. **Runtime Environment & Existing Tests**:
   - Executed `.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py`:
     `============================= 74 passed in 1.45s ==============================`
   - Verified LangChain prompt imports:
     `from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate` executed with exit code 0.

---

## 2. Logic Chain

1. **From Observation 1 & 3 $\rightarrow$ Length Distribution & Token Caps**:
   Because An An's empirical messaging is 70% short ($\le 5$ words) and only 2.4% long, the response length controller must default to concise turns. A token cap of 35 tokens for `SHORT` provides sufficient buffer for 1–5 Vietnamese syllables/words plus punctuation, 75 tokens for `MEDIUM` accommodates 6–15 words, and 160 tokens for `LONG` allows 20–50 words while preventing runaway AI essay generation.

2. **From Observation 2 $\rightarrow$ Data Schema & Enum Integrity**:
   `LengthTier` must inherit from `(str, Enum)` so that string comparisons (e.g. `tier == "short"`) and enum comparisons (`tier == LengthTier.SHORT`) evaluate identically. `LengthDecision` must be a Pydantic v2 `BaseModel` that enforces runtime validation, rejects invalid tiers or negative tokens, and serializes cleanly via `.model_dump()`.

3. **From Observation 1, 2 & 3 $\rightarrow$ Deterministic Intent & Length Classifier**:
   The function `determine_response_length(user_input, conversation_history)` must inspect user intent and length:
   - Greetings (`"ê"`, `"alo"`, `"hi"`, `"chào"`), confirmations (`"ừ"`, `"ok"`, `"oki"`), and inputs with $\le 4$ words must reliably output `LengthTier.SHORT`.
   - Normal chat, study coordination (`"Đề của cô mai phương..."`), and hangout planning (6–15 words) must output `LengthTier.MEDIUM`.
   - Emotional boundary keywords (e.g. `"thích An"`, `"làm người yêu"`, confession, severe stress) or long texts ($> 25$ words) must output `LengthTier.LONG`.

4. **From Observation 3 $\rightarrow$ System Prompt Compilation & Mandates**:
   The prompt builder `build_system_prompt` must combine persona background, the mandatory Vietnamese instruction (`VIETNAMESE_LANGUAGE_INSTRUCTION`), the list of forbidden tokens (`PROHIBITED_TOKENS`), slang dictionary guidelines (`SLANG_DICTIONARY`), and dynamic length guidance from `LengthDecision`. Tests must assert the presence of these core elements in the compiled output.

5. **From Observation 4 $\rightarrow$ 8-Suite Test Decomposition**:
   To ensure complete coverage exceeding Tier 1 ($\ge 45$) and Tier 2 ($\ge 25$) criteria in `TEST_INFRA.md`, the test suite is partitioned into 8 suites totaling **59 unit test cases**:
   - `TestLengthTierEnum` (5 tests)
   - `TestLengthDecisionModel` (6 tests)
   - `TestDetermineResponseLengthShort` (8 tests)
   - `TestDetermineResponseLengthMedium` (8 tests)
   - `TestDetermineResponseLengthLong` (8 tests)
   - `TestDetermineResponseLengthEdgeCases` (11 tests)
   - `TestSystemPromptGeneration` (8 tests)
   - `TestChatPromptTemplateIntegration` (6 tests)

---

## 3. Caveats

1. `src/core/length_controller.py` and `src/core/prompts.py` are planned for Milestone M2 and do not exist prior to Worker implementation. The test specification defines the exact expected behavior and contract interfaces so the Worker can implement them cleanly and pass all tests.
2. The runtime environment uses `pydantic==2.13.5` and `langchain-core==1.6.3`. All model methods in the test specification use Pydantic v2 methods (`.model_dump()`, `.model_dump_json()`).
3. No other caveats.

---

## 4. Conclusion

The unit test specification for Milestone M2 has been fully designed, verified against the authoritative specification sources, and written to:
`C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3\test_spec.md`

Key outcomes:
- **33 features discovered** across 6 categories (Length Tiering, Token Bounds, Schema Invariants, Intent Classification, Tone Guidance, Prompt Generation).
- **20 edge cases analyzed** (empty string, whitespace, punctuation, emojis, massive text stress test, foreign languages, non-string inputs).
- **59 total test cases specified** across 8 orthogonal test classes.
- Zero network calls or API keys required (100% offline, deterministic unit testing).

---

## 5. Verification Method

To independently verify this specification:

1. **Verify Artifact Existence**:
   Inspect `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3\test_spec.md`. Confirm that all 8 test suites, the Features Discovered table (33 rows), and the Edge Cases table (20 rows) are present.

2. **Verify Execution Against Implementation** (Once Worker completes M2 implementation):
   Run the pytest runner in PowerShell:
   ```powershell
   .\venv\Scripts\python.exe -m pytest tests/test_length.py -v
   ```
   - Expected: 59 passed in $< 1.5$s.
   - Invalidation condition: Any test failure, missing test cases ($< 59$), or reliance on external cloud APIs.

# Milestone M2 Handoff Report: Persona Prompt & LangChain ChatPromptTemplate Design

**Agent**: Explorer Subagent M2-2 (Persona Prompt Specialist)  
**Working Directory**: `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_2`  
**Target Milestone**: M2 (Dynamic Response Length & Prompts)  
**Deliverables**: `prompt_design.md`, `handoff.md`  
**Date**: 2026-09-14  

---

## 1. Observation

1. **Mandatory Files Inspected**:
   - `C:\Users\HKQL2\Documents\ExBuild\.agents\ORIGINAL_REQUEST.md`: Requirements R1 (Persona Mimicry), R2 (Dynamic Response Length), R4 (LangChain Framework), Vietnamese persona mimicry of "An An".
   - `C:\Users\HKQL2\Documents\ExBuild\PROJECT.md`: Architecture diagram (lines 7-21), Feature Inventory F3 (Persona Profiling) & F6 (LangChain Conversational Core), Milestones table (lines 38-46), Code Layout (lines 119-157).
   - `C:\Users\HKQL2\Documents\ExBuild\TEST_INFRA.md`: Real-World Scenarios (Casual Banter, Study Coordination, Emotional Boundary), Agent-as-Judge scoring rubric (Persona Mimicry 40%, Dynamic Length 30%, Lexical Quirks 30%).
   - `C:\Users\HKQL2\Documents\ExBuild\src\ingestion\persona_profile.py`: `SLANG_DICTIONARY` (lines 15-107), `PROHIBITED_TOKENS` (lines 110-133), `PERSONA_PROFILE` (lines 136-168), `FEW_SHOT_EXCHANGES` (lines 173-327), and helper functions `get_few_shot_examples`, `format_few_shot_prompt`.
2. **Peer Subagent Coordination**:
   - `explorer_m2_1`: Designed `src/core/length_controller.py` in `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m2_1\length_design.md` specifying `LengthTier` (`SHORT` 1-5 words max 35 tokens, `MEDIUM` 6-15 words max 75 tokens, `LONG` 20-50 words max 160 tokens) and `LengthDecision(tier, max_tokens, guidance_instruction)`.
   - `spec_miner_m2_3`: Authored unit test specification in `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m2_3\test_spec.md`. Specifically:
     - Lines 817-864 (`Suite 7: TestSystemPromptGeneration`): Verifies `build_system_prompt()` string length > 200, Vietnamese mandate ("Tiếng Việt", "tiếng Anh"), prohibited tokens (`ko`, `k`, `đc`, `nhma`, `oke`), slang rules (`kh`, `dc`, `nma`, `r`, `=)))`), anti-AI formatting rules (`bullet`, `tiêu đề`, `danh sách`, `#`), dynamic guidance interpolation, few-shot injection.
     - Lines 866-903 (`Suite 8: TestChatPromptTemplateIntegration`): Verifies `get_chat_prompt_template()` returns `ChatPromptTemplate` with input variable `input`, messages structure `[SystemMessage, MessagesPlaceholder(variable_name="history"), HumanMessage]`, valid format with empty history and with active conversation history, and custom prompt override.
3. **Environment & Runtime Verification**:
   - Python runtime: Python 3.14.6 in `.\venv\Scripts\python.exe`.
   - Tested LangChain prompt formatting and `MessagesPlaceholder` with `anyio-4.15.1` and `langchain-core-1.6.3`. Confirmed `ChatPromptTemplate.from_messages` executes cleanly without serialization errors.
   - Confirmed Windows console CP1252 vs UTF-8 encoding behavior: Vietnamese characters require safe handling / UTF-8 output streams.

---

## 2. Logic Chain

1. **From Persona Data to System Prompt Architecture**:
   - Observations show that An An has a distinct linguistic profile (134x `kh`, 12x `hong`, 0x `k`, 0x `đc`, 0x `nhma`, 98x `r`, 75x `=)))`, 14x `🤡`, 38x `ql`).
   - Therefore, `SYSTEM_PROMPT_BASE` in `src/core/prompts.py` must explicitly codify these exact positive habits and strictly forbid the anti-patterns (`k`, `ko`, `đc`, `nhma`, `oke`, `ạ`, `dạ`, `cậu-tớ`).
2. **From User Mandate to Language Hardening**:
   - The user dispatch contains the critical constraint: "The output language for the chatbot MUST be Vietnamese."
   - Under standard conditions, LLMs might translate or switch language if prompted in English.
   - Therefore, Rule 1 of `SYSTEM_PROMPT_BASE` explicitly commands 100% colloquial Vietnamese output under all circumstances, even for foreign language queries, permitting only real Gen-Z loanwords (`chill`, `bro`, `sori`, `g9`, `okiii`).
3. **From Chatbot Anti-Patterns to Anti-AI Formatting Shield**:
   - Commercial LLMs default to bullet points, markdown titles, and conversational preambles.
   - Therefore, Rule 3 of `SYSTEM_PROMPT_BASE` explicitly bans `#`, `##`, `*`, `-`, `1.`, `2.`, structured essays, and robotic pleasantries (`"Tôi có thể giúp gì cho bạn?"`).
4. **From Length Controller to Dynamic Guidance Injection**:
   - `LengthDecision.guidance_instruction` varies dynamically by turn (short 1-5 words, medium 6-15 words, long 20-50 words).
   - Therefore, `build_system_prompt(length_decision=...)` inspects the decision object, extracts `guidance_instruction`, and interpolates it into the system prompt under `[HƯỚNG DẪN ĐỘ DÀI TIN NHẮN HIỆN TẠI]`.
5. **From Few-Shot Catalog to Dual Injection Support**:
   - The system must support both static text embedding in prompts (`format_few_shot_text_block`) for Suite 7 compliance, and dynamic message conversion (`get_few_shot_messages`) into `HumanMessage` / `AIMessage` pairs for LangChain conversational execution.
   - Both functions are designed and reference verified turns from `src.ingestion.persona_profile.FEW_SHOT_EXCHANGES`.
6. **From Test Spec Invariants to Template Factory**:
   - `spec_miner_m2_3`'s Suite 8 tests call `tpl = get_chat_prompt_template()` and format with `input` and `history`.
   - Therefore, `get_chat_prompt_template(system_prompt: Optional[str] = None)` bakes the compiled system prompt into the first message and exposes `{input}` as the only required user string variable, ensuring 100% compatibility with test suites and conversational memory chains in Milestone M3.

---

## 3. Caveats

1. **Upstream Ingestion Independence**: The prompt module imports static metadata (`FEW_SHOT_EXCHANGES`, `SLANG_DICTIONARY`, `PROHIBITED_TOKENS`) from `src.ingestion.persona_profile`. It does NOT parse raw JSON at runtime, ensuring $O(1)$ instantaneous prompt generation.
2. **Model Token Truncation**: While prompt instructions command 1-5 words for SHORT and 20-50 words for LONG, physical token caps (`max_tokens`: 35, 75, 160) configured in the LLM model instance (`src/core/llm_factory.py`, Milestone M3) serve as the hard backstop.
3. **No Direct Source Modification**: As an Explorer subagent, no files outside `.agents/explorer_m2_2` were created or modified.

---

## 4. Conclusion

1. The architectural design for `src/core/prompts.py` is fully specified in `prompt_design.md`.
2. The design matches 100% of the interface contracts required by `PROJECT.md` and `spec_miner_m2_3/test_spec.md`.
3. The prompt system provides deterministic, zero-cost persona mimicry, strictly enforces Vietnamese language output, forbids AI formatting, dynamically injects length guidance, and integrates seamlessly with LangChain's `ChatPromptTemplate`.

---

## 5. Verification Method

To independently verify the prompt design against the test specifications once implemented by Worker M2:

1. **Verify Module Import and System Prompt Compilation**:
   ```powershell
   $env:PYTHONIOENCODING='utf-8'
   .\venv\Scripts\python.exe -c "
   from src.core.prompts import build_system_prompt, get_chat_prompt_template, SYSTEM_PROMPT_BASE
   p = build_system_prompt()
   assert len(p) > 200
   assert 'Tiếng Việt' in p or 'tiếng Việt' in p
   assert all(t in p for t in ['ko', 'k', 'đc', 'nhma', 'oke'])
   assert all(t in p for t in ['kh', 'dc', 'nma', 'r', '=)))'])
   print('build_system_prompt verified successfully!')
   "
   ```
2. **Verify LangChain ChatPromptTemplate Formatting**:
   ```powershell
   $env:PYTHONIOENCODING='utf-8'
   .\venv\Scripts\python.exe -c "
   from src.core.prompts import get_chat_prompt_template
   tpl = get_chat_prompt_template()
   msgs = tpl.format_messages(input='alo', history=[])
   assert len(msgs) == 2
   assert msgs[-1].content == 'alo'
   print('get_chat_prompt_template verified successfully!')
   "
   ```
3. **Execute the Full Milestone M2 Test Suite**:
   ```powershell
   .\venv\Scripts\python.exe -m pytest tests/test_length.py -v
   ```
   **Pass Semantics**: All Suite 7 (`TestSystemPromptGeneration`) and Suite 8 (`TestChatPromptTemplateIntegration`) tests exit with code 0.

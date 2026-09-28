# Review & Adversarial Challenge Report: Prompt & Vietnamese Persona (M2)

**Reviewer**: Reviewer 2 (Prompt & Vietnamese Reviewer)  
**Milestone**: M2 (Dynamic Response Length & Prompts)  
**Target Files**: `src/core/prompts.py`, `src/core/length_controller.py`, `tests/test_length.py`, `src/ingestion/persona_profile.py`  
**Date**: 2026-09-14T11:47:30Z  

---

## Review Summary

**Verdict**: **APPROVE**  
*(With 2 minor advisory recommendations for downstream Milestone M3 and 1 cross-module observation regarding length controller upstream triggers)*

The implementation of `src/core/prompts.py` demonstrates exemplary persona fidelity and rigorous prompt engineering:
1. **Vietnamese Language Mandate**: Strictly enforced. The base system prompt and all dynamic length guidance instructions explicitly mandate 100% colloquial Vietnamese and prohibit English/foreign language responses under all conditions, even when prompted in English, while allowing authentic Gen-Z loanwords (`chill`, `bro`, `sori`, `g9`, `nah nah`, `nevermind broo`, `okiii`).
2. **An An Persona Invariants**: All signature linguistic markers (`kh`/`hong`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`, `v`/`z`, `th`/`thui`, `oki`/`okiii`) are codified with explicit operational definitions and strict positive/negative constraints.
3. **Prohibited Token Shield**: All 15 tokens in `PROHIBITED_TOKENS` (`ko`, `k`, `đc`, `nhma`, `oke`, `ạ`, `cậu`, `tớ`, `dạ`, and Vietnamese/English AI assistant boilerplate) are explicitly banned in the prompt body.
4. **Anti-AI Formatting Safeguards**: Strictly forbids Markdown headings (`#`, `##`), bullet points (`*`, `-`, numbered lists), essay paragraphs, and AI polite disclaimers, directing output to natural Messenger bubble bursts (`\n`).
5. **LangChain & Dynamic Integration**: Cleanly integrates with `MessagesPlaceholder` and dynamic length decisions via `build_system_prompt()` and `get_chat_prompt_template()`.
6. **Integrity Violations Check**: Zero integrity violations detected. No hardcoded test responses, no facade classes, no bypassed tasks, and zero tautological tests. Full test suite passes 170/170 tests offline.

---

## Findings

### [Minor / Advisory] Finding 1: Unsanitized Negative-Constraint Tokens in Historical Few-Shot Catalog
- **What**: Two dialogue exemplars in the few-shot catalog (`category="VENTING_FATIGUE"` and `category="EMOTIONAL_BOUNDARY"`) contain tokens that conflict with negative constraints:
  - Turn 20 (`VENTING_FATIGUE`): An An says `Trên chợ có nóng ko` (contains banned token `ko`).
  - Turn 12 (`EMOTIONAL_BOUNDARY`): An An says `Muốn đồng ý lắm nhưng mà tiếc là không được... quen rùi nó khác lắm` (contains `không được` and banned token `rùi`).
- **Where**: `src/ingestion/persona_profile.py:305, 250` (accessed via `get_few_shot_examples()` in `src/core/prompts.py:127, 202`).
- **Why**: While this faithfully reflects raw, imperfect human typing in the real Facebook chat logs (where An An used `kh` 143 times vs `ko` 4 times), providing few-shot examples containing `ko` and `rùi` directly below instructions stating `TUYỆT ĐỐI CẤM dùng từ 'k' hoặc 'ko'` can act as a conflicting signal / distractor to an LLM, potentially inducing token leakage under specific few-shot category filters.
- **Suggestion**: In Milestone M3 (chain integration), normalize or sanitize few-shot turns before prompt injection (e.g. normalize `nóng ko` $\to$ `nóng kh`, `không được` $\to$ `kh dc`, `quen rùi` $\to$ `quen r`). Note: The default `build_system_prompt()` selects the first 3 turns (`CASUAL_BANTER`), which are 100% clean and free of prohibited tokens.

### [Minor / Advisory] Finding 2: Instruction-Level Pronoun Ambiguity in System Context Header
- **What**: In `src/core/prompts.py:27`, the introductory context line states:
  `"...với bạn thân kiêm bạn cùng lớp của mình là Hoàng Kim Quờ Lờ (bạn luôn gọi cậu ấy là "ql", chữ thường)."`
- **Where**: `src/core/prompts.py:27`.
- **Why**: Later in Rule 8 (lines 59-60), the pronoun `cậu` is strictly forbidden as a term of address (`TUYỆT ĐỐI CẤM gọi "anh", "cậu", "Quờ Lờ"`). While "cậu ấy" is used as a 3rd-person descriptive reference in the prompt instruction itself (and not as dialogue output), models can occasionally pick up on vocabulary in system instructions.
- **Suggestion**: Replace `cậu ấy` in line 27 with `người ấy` or `bạn ấy` (e.g. `(bạn luôn gọi bạn ấy là "ql", chữ thường)`) to maintain absolute lexical exclusion of `cậu` throughout the entire prompt document.

### [Cross-Module Note] Finding 3: Length Controller Regex Overmatching Triggering Excessive `LONG` Prompts
- **What**: Peer Challenger 1 identified that unanchored tokens in `RE_EMOTIONAL_CONFESSION` (e.g. bare `ex` matching `text`, `excel`, `next`, and unanchored `thích m` matching `thích màu`, `thích môn`) misclassify ordinary tech/chat messages into `LengthTier.LONG`.
- **Where**: `src/core/length_controller.py:108-109`.
- **Why**: When misclassified, `prompts.py` correctly generates the `LONG` prompt guidance (*"YÊU CẦU ĐỘ DÀI: DÀI / TÂM SỰ (20 - 50 TỪ)"*), which inadvertently suppresses An An's quick, sarcastic short-burst personality on mundane questions.
- **Suggestion**: Worker M2 should anchor regex boundaries in `length_controller.py` as detailed in Challenger 1's report. `prompts.py` itself handles dynamic injection correctly and requires no architectural changes.

---

## Adversarial Challenge Analysis

### Challenge 1: Foreign Language Prompting & Cross-Lingual Evasion
- **Assumption Challenged**: System prompt prevents the LLM from slipping into English or other languages when spoken to in English, Chinese, or mixed languages.
- **Stress-Test Analysis**:
  - Rule 1 specifically command-locks the model:
    ```
    [QUY TẮC BẮT BUỘC 1: 100% TIẾNG VIỆT (VIETNAMESE ONLY)]:
    - BẮT BUỘC PHẢI TRẢ LỜI HOÀN TOÀN BẰNG TIẾNG VIỆT TỰ NHIÊN (Tiếng Việt colloquial / đời thường).
    - Tuyệt đối KHÔNG ĐƯỢC trả lời bằng tiếng Anh (English) hay bất kỳ ngoại ngữ nào khác, KỂ CẢ KHI người dùng nhắn tin bằng tiếng Anh.
    - Nếu người dùng nhắn tiếng Anh hoặc ngôn ngữ khác, bạn vẫn trả lời bằng Tiếng Việt với thái độ bạn bè tự nhiên (ví dụ: trêu chọc sao tự nhiên nói tiếng Anh, hoặc rep bình thường bằng tiếng Việt).
    ```
  - English AI assistant patterns are explicitly enumerated and banned (`"As an AI"`, `"How can I help you"`, `"How can I assist"`, `"Sure, I can help with that"`).
  - Allowed loanwords are tightly constrained to authentic Gen-Z slang (`"chill"`, `"bro"`, `"sori"`, `"g9"`, `"nah nah"`, `"nevermind broo"`, `"okiii"`).
- **Result**: **ROBUST**. The prompt provides actionable behavioral guidance for foreign language inputs rather than a naive negative rule.

### Challenge 2: Persona Invariant Coverage & Leakage
- **Assumption Challenged**: All signature tokens (`kh`/`hong`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`) and prohibited tokens are rigorously implemented without leaks.
- **Stress-Test Analysis**:
  - Automated regex audit across `SYSTEM_PROMPT_BASE`, `DEFAULT_LENGTH_GUIDANCE`, and `build_system_prompt()` confirmed:
    - `kh`: mandated for general negation; `k`/`ko` strictly forbidden.
    - `hong`: mandated for soft/playful negation; `hông` forbidden.
    - `dc`: mandated; `đc` strictly forbidden.
    - `nma`: mandated; `nhma` strictly forbidden.
    - `r`: standalone letter `r` mandated; `rồi`/`rùi` strictly forbidden.
    - `v`/`z`: mandated; full `vậy` strictly forbidden.
    - `th`/`thui`: mandated; full `thôi` strictly forbidden.
    - `oki`/`okiii`: mandated; `oke` strictly forbidden.
    - `=)))`/`=))))`: signature laughter mandated; `haha` strictly forbidden.
    - `🤡`: mandated for clown/absurd moments.
    - `ql`: mandatory lowercase nickname; `anh`/`cậu`/`Quờ Lờ` forbidden.
    - Polite particles `dạ`/`ạ` strictly forbidden.
- **Result**: **ROBUST**. Comprehensive lexical coverage with zero rule omissions.

### Challenge 3: LangChain Prompt Formatting & Memory Compatibility
- **Assumption Challenged**: `get_chat_prompt_template()` formats correctly across diverse conversation histories (empty list, list of BaseMessages, string tuples) without dropping system instructions.
- **Stress-Test Analysis**:
  - Executed format validations across:
    - Empty history `history=[]` $\to$ correctly renders 2 messages (`SystemMessage`, `HumanMessage`).
    - Multi-turn `BaseMessage` history $\to$ correctly preserves message sequence and role attribution.
    - Custom system prompt override $\to$ successfully overrides base prompt while retaining `MessagesPlaceholder`.
- **Result**: **PASS**. Fully compliant with LangChain core prompt interfaces.

---

## Verified Claims

| Claim | Method | Result |
|---|---|---|
| `src/core/prompts.py` enforces Vietnamese-only mandate | Code inspection & regex verification of `SYSTEM_PROMPT_BASE` and `DEFAULT_LENGTH_GUIDANCE` | **PASS** |
| Persona rules (`kh`/`hong`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`) rigorously implemented | Cross-referenced against `SLANG_DICTIONARY` and tested via string search | **PASS** |
| Prohibited tokens explicitly forbidden in prompt | Audited all 15 tokens in `PROHIBITED_TOKENS` against system prompt negative rules | **PASS** |
| Anti-AI and formatting rules enforced | Verified prohibitions on Markdown headers, bullet points, numbered lists, AI apologies | **PASS** |
| Dynamic length guidance injected properly | Tested `build_system_prompt()` with `LengthDecision`, `LengthTier`, and custom string | **PASS** |
| LangChain `ChatPromptTemplate` integration | Formatted messages via `get_chat_prompt_template()` with empty and multi-turn history | **PASS** |
| Test suite execution | Ran `pytest tests/test_length.py tests/test_ingestion.py -v` (170/170 passed in 2.40s) | **PASS** |
| Python compilation cleanly succeeds | `python -m py_compile src/core/prompts.py src/core/length_controller.py src/core/__init__.py tests/test_length.py` | **PASS** |

---

## Coverage Gaps

- None within the scope of Prompt & Vietnamese persona engineering.
- Note: Live LLM inference and generation token truncation will be integrated in Milestone M3 (`src/core/llm_factory.py` & `src/core/chain.py`).

---

## Unverified Items

- Live LLM model output adherence to prompt rules (out of scope for M2; scheduled for M3 and M5 Agent-as-Judge evaluation).

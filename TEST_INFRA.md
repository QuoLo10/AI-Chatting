# E2E Test Infra: An An Persona Chatbot

## Test Philosophy
- Opaque-box and requirement-driven testing directly derived from `ORIGINAL_REQUEST.md`.
- No dependency on private implementation details; tests verify outward persona fidelity, dynamic length compliance, zero-cost API functionality, and CLI robustness.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinations + Real-World Workload Scenarios + Agent-as-Judge LLM Evaluation.

## Feature Inventory & Test Mapping
| # | Feature | Requirement | Tier 1 (Feature) | Tier 2 (Boundary) | Tier 3 (Pairwise) | Tier 4 (Real-World) |
|---|---------|-------------|:----------------:|:-----------------:|:-----------------:|:-------------------:|
| F1 | Facebook JSON Ingestion | R1 | 5 | 5 | ✓ | ✓ |
| F2 | Safe Encoding Transcoding | R1 | 5 | 5 | ✓ | ✓ |
| F3 | Persona Profiling & Few-Shot | R1 | 5 | 5 | ✓ | ✓ |
| F4 | Dynamic Response Length | R2 | 5 | 5 | ✓ | ✓ |
| F5 | Zero-Cost Cloud LLM Factory | R3 | 5 | 5 | ✓ | ✓ |
| F6 | LangChain Conversational Core | R4 | 5 | 5 | ✓ | ✓ |
| F7 | Interactive CLI Interface | R5 | 5 | 5 | ✓ | ✓ |
| F8 | Automated Test Suite | Acceptance Criteria | 5 | 5 | ✓ | ✓ |
| F9 | Agent-as-Judge Evaluation | Acceptance Criteria | 5 | 5 | ✓ | ✓ |

## Test Architecture
- **Test Runner**: `pytest` run via `.\venv\Scripts\python.exe -m pytest tests/`
- **Mock Framework**: `langchain_core.language_models.fake_chat_models.FakeListChatModel` for offline 100% deterministic unit testing without requiring external network or API keys.
- **Judge Runner**: `.\venv\Scripts\python.exe evaluation/evaluate_judge.py` calling secondary LLM (Gemini / Groq) with structured Agent-as-Judge prompt.
- **Pass/Fail Semantics**:
  - Unit/Integration tests: 100% pass rate (exit code 0).
  - Agent-as-Judge: Average weighted score $\ge 8.0/10.0$ across all 3 simulated conversations, with no single dimension scoring $< 7.0/10.0$.

## Real-World Application Scenarios (Tier 4 / Agent-as-Judge)
| # | Scenario | Features Exercised | Complexity | Target Behavior |
|---|----------|--------------------|------------|-----------------|
| 1 | Casual Banter & Late Night Chat | F3, F4, F6, F7 | Medium | Short rapid replies (1-5 words), uses `=)))`, `kh`, `ql`, tease about sleep/eating |
| 2 | Study Coordination & Deadline Stress | F3, F4, F6, F7 | Medium | Medium replies (6-15 words), practical design student slang, complaining `huhu`, `nma`, `dc` |
| 3 | Serious/Emotional Boundary & Flirting Rejection | F3, F4, F6, F7 | High | Long thoughtful replies (20-50 words), gentle but clear boundary setting, avoids verbose AI essay |

## Agent-as-Judge Scoring Rubric
1. **Persona Mimicry (Weight: 40%)**:
   - Reflects An An's witty, sarcastic yet warm art-student persona.
   - Self-reference as "An" or "mình", calls user "ql" or "bạn".
   - Appropriate reaction and teasing tone.
2. **Dynamic Response Length (Weight: 30%)**:
   - Short input -> short snappy response (1-5 words).
   - Casual chit-chat -> medium response (6-15 words).
   - Deep/serious input -> nuanced boundary response (20-50 words).
   - Strictly zero AI disclaimers, bulleted lectures, or generic assistant preambles.
3. **Lexical Quirks & Slang (Weight: 30%)**:
   - Correct usage of `kh` or `hong` (NEVER `k`, rarely `ko`).
   - Use of `dc` (never `đc`), `nma` (never `nhma`), `r` (never `rồi`), `v`/`z` (for vậy).
   - Natural laughter `=)))`, `hihi`, `huhu`, or clown emoji `🤡`.

## Coverage Thresholds
- Tier 1: $\ge 45$ feature unit test cases ($9 \times 5$).
- Tier 2: $\ge 25$ boundary and corner cases.
- Tier 3: Pairwise interaction tests covering length controller + chat chain + provider fallback.
- Tier 4: $\ge 3$ distinct multi-turn simulated conversations evaluated via Agent-as-Judge.
- Total test cases: $\ge 75$ tests across unit, integration, and E2E suites.

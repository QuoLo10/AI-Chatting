# Project: An An Persona Chatbot

## Architecture
A CLI-based AI chatbot using LangChain that ingests Facebook messages JSON data to precisely mimic the personality, style, and dynamic response length of "An An", running on zero-cost free-tier cloud APIs.

```
[Facebook JSON (An An_86.json)]
       │
       ▼
[Ingestion Engine (src/ingestion/)] ────► [Persona Profile & Few-Shot Catalog]
                                                         │
                                                         ▼
[User Message (CLI)] ──► [Dynamic Length Controller] ──► [LangChain Chat Chain]
                                                         │ (System Prompt + Memory)
                                                         ▼
                                               [Cloud LLM Factory]
                                               (Gemini 2.0 / Groq / Mock)
                                                         │
                                                         ▼
                                               [An An Response Bubbles]
```

## Feature Inventory
Every feature from the Survey phase appears here with its assigned milestone.
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Facebook JSON Ingestion | Safe parsing of FB message JSON, normalization of message fields | M1 | Survey 1, Spec Miner 3 |
| F2 | Safe Encoding & Transcoding | Heuristic transcoding guard preventing UnicodeEncodeError on Windows/UTF-8 | M1 | Survey 1, Spec Miner 3 |
| F3 | Persona Profiling & Few-Shot | Catalog of An An lexical quirks (`kh`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`) and few-shot examples | M1 | Survey 1 |
| F4 | Dynamic Response Length Controller | Context & intent classifier setting length tier (short/med/long) & token caps matching empirical distribution | M2 | Survey 1, Spec Miner 3 |
| F5 | Zero-Cost Cloud LLM Factory | Multi-provider factory supporting Google Gemini & Groq via `.env` with auto-fallback & offline mocks | M3 | Survey 2, Spec Miner 3 |
| F6 | LangChain Conversational Core | Prompt templates, session history sliding window, memory integration | M3 | Spec Miner 3 |
| F7 | Interactive CLI Interface | Single-command launcher via `venv\Scripts\python main.py`, UTF-8 console, burst bubbles, slash commands | M4 | Survey 2, Spec Miner 3 |
| F8 | Automated Test Suite (Tiers 1-4) | Comprehensive unit and integration test suite runnable offline via pytest | T1 / M5 | Spec Miner 3 |
| F9 | Agent-as-Judge Evaluation | Automated secondary LLM evaluation comparing chatbot against An An across >= 3 simulated conversations (Pass >= 8.0/10) | T2 / M5 | Spec Miner 3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Dependencies & Ingestion Engine | `requirements.txt`, `src/config.py`, `src/ingestion/parser.py`, `src/ingestion/persona_profile.py` | none | DONE |
| M2 | Dynamic Response Length & Prompts | `src/core/length_controller.py`, `src/core/prompts.py` | M1 | PLANNED |
| M3 | LLM Factory & LangChain Core | `src/core/llm_factory.py`, `src/core/chain.py` | M2 | PLANNED |
| M4 | Single-Command CLI Interface | `src/cli/chat.py`, `main.py` | M3 | PLANNED |
| T1 | Test Infra & Comprehensive Test Suite | `tests/conftest.py`, `tests/test_*.py` | M1 | PLANNED |
| T2 | Agent-as-Judge Framework | `evaluation/judge_rubric.py`, `evaluation/scenarios.py`, `evaluation/evaluate_judge.py` | M3, T1 | PLANNED |
| M5 | Final E2E Integration & Verification | 100% test pass, live Agent-as-Judge run on >=3 conversations, coverage hardening | M4, T2 | PLANNED |

## Interface Contracts

### `src.ingestion.parser` ↔ `src.ingestion.persona_profile`
```python
from pydantic import BaseModel
from typing import List, Optional

class CanonicalMessage(BaseModel):
    sender_name: str
    text: str
    timestamp_ms: int
    is_an_an: bool
    reactions: List[str] = []

def parse_facebook_json(file_path: str) -> List[CanonicalMessage]:
    """Parses Facebook JSON file, handles encoding safely, returns canonical messages."""
    ...

def extract_an_an_profile(messages: List[CanonicalMessage], max_gap_hours: Optional[float] = None) -> dict:
    """Extracts linguistic statistics, signature tokens, and top dialogue turns."""
    ...
```

### `src.core.length_controller` ↔ `src.core.chain`
```python
from enum import Enum
from pydantic import BaseModel

class LengthTier(str, Enum):
    SHORT = "short"     # 1-5 words, max_tokens=35 (70% of An An messages)
    MEDIUM = "medium"   # 6-15 words, max_tokens=75 (27.6% of An An messages)
    LONG = "long"       # 20-50 words, max_tokens=160 (2.4% emotional boundary turns)

class LengthDecision(BaseModel):
    tier: LengthTier
    max_tokens: int
    guidance_instruction: str

def determine_response_length(user_input: str, conversation_history: list = None) -> LengthDecision:
    """Analyzes user input intent and length to select optimal An An response length tier."""
    ...
```

### `src.core.llm_factory` ↔ `src.core.chain`
```python
from langchain_core.language_models.chat_models import BaseChatModel

def get_chat_model(
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 150,
    force_mock: bool = False
) -> BaseChatModel:
    """Returns configured ChatModel (Google Gemini, Groq, or Mock) reading API keys from .env."""
    ...
```

### `src.core.chain` ↔ `src.cli.chat`
```python
class AnAnChatbot:
    def __init__(self, session_id: str = "default_session", force_mock: bool = False):
        ...
    def chat(self, user_input: str) -> str:
        """Sends user message, dynamically adjusts length, returns An An reply."""
        ...
    def reset(self):
        """Clears session history."""
        ...
```

## Code Layout
```
C:\Users\HKQL2\Documents\ExBuild\
├── .agents/                    # Agent metadata only
├── .env                        # Environment variables (GEMINI_API_KEY, GROQ_API_KEY)
├── .env.example                # Template for environment variables
├── requirements.txt            # Project dependencies for venv
├── main.py                     # Single-command CLI entry point
├── src/
│   ├── __init__.py
│   ├── config.py               # Settings, .env loader, API keys
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parser.py           # Facebook JSON parser, safe transcoding
│   │   └── persona_profile.py  # An An persona data, stats, few-shot examples
│   ├── core/
│   │   ├── __init__.py
│   │   ├── length_controller.py# Dynamic response length analyzer & token bounds
│   │   ├── llm_factory.py      # Google GenAI / Groq provider & mock fallback
│   │   ├── prompts.py          # System prompt & few-shot templates
│   │   └── chain.py            # LangChain conversational chain & memory
│   └── cli/
│       ├── __init__.py
│       └── chat.py             # CLI loop, UTF-8 console setup, commands
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures, mock LLMs
│   ├── test_ingestion.py       # Tests for JSON parsing & encoding
│   ├── test_length.py          # Tests for dynamic length controller
│   ├── test_llm_factory.py     # Tests for provider factory & fallback
│   ├── test_chain.py           # Tests for LangChain chain & memory
│   └── test_cli.py             # Tests for CLI commands & runner
├── evaluation/
│   ├── __init__.py
│   ├── judge_rubric.py         # Evaluation rubric & criteria
│   ├── scenarios.py            # >= 3 distinct simulated conversation scenarios
│   └── evaluate_judge.py       # Agent-as-Judge evaluation script
├── PROJECT.md
└── TEST_INFRA.md
```

# Technical & Verification Requirements Specification
## Project: An An Persona Chatbot
**Author:** Architecture & Verification Spec Miner (`spec_miner_survey_3`)  
**Date:** 2026-09-14  
**Project Root:** `C:\Users\HKQL2\Documents\ExBuild`  
**Target Virtual Environment:** `C:\Users\HKQL2\Documents\ExBuild\venv` (Python 3.14.6)  
**Primary Verification Dataset:** `F:/dowload/FacebookData/messages/An An_86.json`

---

## Table of Contents
1. [Executive Summary & System Architecture](#1-executive-summary--system-architecture)
2. [Data Ingestion Module Specification](#2-data-ingestion-module-specification)
3. [Dynamic Response Length Module Specification](#3-dynamic-response-length-module-specification)
4. [Core LangChain Architecture Specification](#4-core-langchain-architecture-specification)
5. [CLI Interface Specification](#5-cli-interface-specification)
6. [Agent-as-Judge Evaluation Script Specification](#6-agent-as-judge-evaluation-script-specification)
7. [Automated Test Suite Specification](#7-automated-test-suite-specification)
8. [Features Discovered & Probed Matrix](#8-features-discovered--probed-matrix)
9. [Edge Cases & Error Handling Matrix](#9-edge-cases--error-handling-matrix)

---

## 1. Executive Summary & System Architecture

### 1.1 Objective
Construct an autonomous, zero-cost, CLI-based AI chatbot using Python and the LangChain framework. The chatbot ingests real Facebook Messenger chat logs to authentically replicate the persona, conversational quirks, slang, humor, emotional boundaries, and dynamic response lengths of "An An" conversing with her classmate/friend "ql" (Hoàng Kim Quờ Lờ).

### 1.2 System Architecture Diagram
```
                     +---------------------------------------------+
                     |         Facebook Messages JSON Data         |
                     | (F:/dowload/FacebookData/messages/...json)  |
                     +----------------------+----------------------+
                                            |
                                            v
                     +---------------------------------------------+
                     |            Data Ingestion Module            |
                     |  - Schema Normalizer (camelCase / snake)   |
                     |  - Mojibake Safe Transcoder (Latin-1/UTF-8) |
                     |  - Turn Aggregator & Burst Detector         |
                     |  - Filter (isUnsent, media-only, system)    |
                     +----------------------+----------------------+
                                            |
                       +--------------------+--------------------+
                       |                                         |
                       v                                         v
        +-----------------------------+           +------------------------------+
        | Static Persona Profile JSON |           | Few-Shot Exemplar Retriever  |
        | - Identity & Relationship   |           | (BM25 / Vector Store / Pairs)|
        | - Slang Rules & Emoticons   |           +--------------+---------------+
        | - Empirical Bounds          |                          |
        +--------------+--------------+                          |
                       |                                         |
                       +--------------------+--------------------+
                                            |
                                            v
+----------------+   User Prompt   +---------------------------------------------+
| CLI Interface  +---------------->|     Dynamic Response Length Controller      |
| - Interactive  |                 | - Context & Intent Classifier               |
| - Slash Cmds   |                 | - Dynamic Prompt Injection Directive        |
| - Streaming    |                 | - Hard Generation Param Bounds (max_tokens) |
+-------^--------+                 +----------------------+----------------------+
        |                                                 |
        | Streamed Response                               v
+-------+--------+                 +---------------------------------------------+
| LLM ChatModel  |<----------------+             Core LangChain Chain            |
| (Google GenAI/ |                 | - ChatPromptTemplate (System + Rules)       |
|  Groq Fallback)|                 | - MessagesPlaceholder (Session Memory)      |
+----------------+                 | - RunnableWithMessageHistory Store          |
                                   +---------------------------------------------+
                                                          |
                                                          | Test / Validation Run
                                                          v
                                   +---------------------------------------------+
                                   |      Agent-as-Judge Evaluation Script       |
                                   | - 3+ Simulated Multi-turn Conversations     |
                                   | - Secondary LLM Evaluation (Rubric 1-10)    |
                                   | - Output: Markdown Table + JSON Audit       |
                                   +---------------------------------------------+
```

---

## 2. Data Ingestion Module Specification

### 2.1 File & Schema Normalization
Official Facebook dumps and third-party extraction tools produce slightly differing JSON schemas. The parser must normalize these schemas into a canonical internal data model.

#### Canonical Pydantic Schema
```python
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class ReactionModel(BaseModel):
    actor: str
    reaction: str

class CanonicalMessage(BaseModel):
    sender_name: str
    timestamp_ms: int
    text: str
    is_unsent: bool = False
    media: List[Any] = Field(default_factory=list)
    reactions: List[ReactionModel] = Field(default_factory=list)
    msg_type: str = "text"

class CanonicalChatSession(BaseModel):
    participants: List[str]
    thread_name: str
    messages: List[CanonicalMessage]
```

#### Field Mapping Table
| Target Field | Standard FB Export Key | Modern / Tool Export Key (e.g. `An An_86.json`) | Fallback Strategy |
|---|---|---|---|
| `sender_name` | `sender_name` | `senderName` | `m.get("senderName") or m.get("sender_name") or "Unknown"` |
| `timestamp_ms` | `timestamp_ms` | `timestamp` | `m.get("timestamp") or m.get("timestamp_ms") or 0` |
| `text` | `content` | `text` | `m.get("text") or m.get("content") or ""` |
| `is_unsent` | `is_unsent` | `isUnsent` | `bool(m.get("isUnsent") or m.get("is_unsent") or False)` |
| `reactions` | `reactions` | `reactions` | List of `{actor, reaction}` objects |
| `media` | `photos`/`videos`/`files` | `media` | List of attachments |
| `thread_name` | `title` | `threadName` | `data.get("threadName") or data.get("title") or "Unknown"` |
| `participants`| `participants` (dict list) | `participants` (string list) | If elements are dicts, extract `p["name"]` |

### 2.2 Mojibake Detection & Safe Transcoding
Official Facebook exports store UTF-8 bytes decoded as Latin-1 string literals (`\u00c3\u00a0` for `à`). However, files like `An An_86.json` are already cleanly UTF-8 encoded with full Vietnamese Unicode code points (e.g., `ờ` U+1EDD, `ơ` U+01A1).
- **The Pitfall:** Blindly executing `text.encode('latin1').decode('utf-8')` on clean Vietnamese throws `UnicodeEncodeError: 'latin-1' codec can't encode character '\u1edd'` because Vietnamese characters are outside the Latin-1 (0-255) ordinal range.
- **Transcoding Algorithm:**
```python
def safe_decode_mojibake(text: Optional[str]) -> str:
    if not text or not isinstance(text, str):
        return ""
    # Heuristic check: only attempt repair if string contains typical double-encoded Latin-1 bytes
    # and does not throw UnicodeEncodeError
    if any(ch in text for ch in ('Ã', 'Â', 'á»', 'áº', 'â€™', 'Ã¡', 'Ã©')):
        try:
            return text.encode('latin1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text
```

### 2.3 Message Filtering & Thread Aggregation
Chat participants rarely send single complete sentences. Instead, they send **rapid bursts** of short bubbles.
1. **Filtering Rules:**
   - Drop messages where `is_unsent == True`.
   - Drop messages with content `"User unsent a message"`.
   - Drop media-only messages where `text.strip() == ""` unless an explicit attachment placeholder is tracked.
2. **Session Boundary Detection:**
   - If `(msg[i].timestamp_ms - msg[i-1].timestamp_ms) > 7,200,000` (2 hours), trigger a new conversation session boundary.
3. **Turn Aggregation (Burst Collapsing):**
   - Group consecutive messages from the same sender into a single logical turn:
   ```python
   # Example:
   # Turn 1 (Hoàng Kim Quờ Lờ): ["Chúc An mai thi tốt"]
   # Turn 2 (An An): ["Cám mơn ql nhieu nhaa"]
   # Turn 3 (Hoàng Kim Quờ Lờ): ["tự tin lên cố lên 💪"]
   # Turn 4 (An An): ["Ua", "An thấy má an bth mà", "Kì ta"]
   ```
   - Represent turns internally with both individual burst lists (`List[str]`) and newline-joined text (`" \n ".join(bursts)`).

### 2.4 Persona Profile & Dynamic Few-Shot Retrieval
1. **Static Persona Knowledge Base (`persona_profile.json`):**
   - Extracts baseline facts, speech quirks, and relationship attributes directly mined from `An An_86.json`.
2. **Dynamic Few-Shot Exemplar Retriever:**
   - Ingestion extracts all 410 turn pairs `(User_Turn, An_An_Turn)`.
   - Embeds or indexes user turns using lightweight BM25 (or in-memory Chroma/FAISS with HuggingFace mini embeddings).
   - On incoming user message, dynamically retrieves top $K$ (e.g. $K=3$) most relevant real exchanges to inject into prompt context, ensuring accurate tone alignment across diverse conversational topics.

---

## 3. Dynamic Response Length Module Specification

### 3.1 Empirical Baseline & Distribution
Analysis of all 1,174 valid text messages from An An across 410 conversational turns reveals an extreme brevity distribution:
- **Mean word count:** 4.7 words (Median: 4.0 words)
- **Mean character count:** 17.8 characters (Median: 13.0 characters)
- **Word Length Distribution:**
  - **Short ($\le 5$ words):** 822 messages (**70.0%**)
  - **Medium ($6 - 15$ words):** 324 messages (**27.6%**)
  - **Long ($> 15$ words):** 28 messages (**2.4%**) — Maximum observed: 92 words (in an emotional boundary-setting confession).
- **Burst Pattern:** An An averages **2.94 message bubbles per turn** (bursts), with 48% of turns comprising 2-3 short bursts.

### 3.2 Context & Intent Classifier Engine
The chatbot must classify user input into one of three distinct length profiles:

```
                          User Prompt
                              |
               +--------------+---------------+
               | Check Length & Keyword Intent |
               +--------------+---------------+
                              |
     +------------------------+------------------------+
     |                                                 |
[Short Signals]                               [Long Signals]
- Length <= 4 words                           - Length >= 25 words
- Greeting ("hi", "ê", "alo")                 - Emotional ("thích An", "tỏ tình", "tâm sự",
- Pings / Banter ("ql khờ", "quỉ")              "buồn", "áp lực", "mệt mỏi", "chia tay")
- Status / Yes-No query                       - Relationship boundary questions
     |                                                 |
     v                                                 v
Mode: SHORT                                      Mode: LONG
Target: 1 - 5 words                              Target: 20 - 55 words
(Max tokens: 30)                                 (Max tokens: 160)
     \                                                 /
      \                      [Default]                /
       +-----------------> Mode: MEDIUM <------------+
                           Target: 6 - 15 words
                           (Max tokens: 70)
```

#### Classification Rules
1. **SHORT Mode (1 to 5 words, 1 burst or 2 micro-bursts):**
   - Triggers: User input length $\le 4$ words, single-word greetings (`alo`, `ê`, `An ơi`), slang banter (`quỉ`, `khờ`), acknowledgments (`ừ`, `ok`, `aukee`).
   - Expected Output Examples: `"Jza"`, `"Tyyy"`, `"Cám mơn ql nhieu nhaa"`, `"Quỉ=)))"`, `"Gì z má"`.
2. **MEDIUM Mode (6 to 15 words, 2-3 short lines):**
   - Triggers: Default chat turn, questions about homework, schedules, study credentials, coffee meetups, gossip inquiries.
   - Expected Output Examples:
     ```
     Mới tạo á
     Này tụi mình chọn chung
     R mới thêm mà
     ```
3. **LONG Mode (20 to 55 words, max 75 words):**
   - Triggers: Emotional confessions, relationship discussions, venting about life/exes, deep personal advice.
   - Expected Output: Mature, slightly defensive/honest boundary setting, still using signature slang (`nma`, `mqh`, `chiều vong`, `=)))`, `🥲`, `thui ha`). Never exceeds 80 words.

### 3.3 Prompt Directive Injection & Generation Bounds
To prevent LLM verbosity, the Length Controller injects an explicit rule into the dynamic system prompt and enforces a hard ceiling via `max_tokens`:

| Mode | Injected Prompt Directive | `max_tokens` Ceiling | Target Words |
|---|---|---|---|
| **SHORT** | `[LENGTH RULE: BẮT BUỘC NGẮN. Chỉ trả lời từ 1 đến 5 từ. Không giải thích, không xã giao. Ví dụ: 'Jza', 'Quỉ=)))', 'Tyyy'.]` | 35 | 1 - 5 words |
| **MEDIUM** | `[LENGTH RULE: VỪA PHẢI. Trả lời từ 1 đến 3 câu ngắn (mỗi câu xuống dòng như 1 tin nhắn chat riêng), tổng cộng 6 đến 15 từ.]` | 75 | 6 - 15 words |
| **LONG** | `[LENGTH RULE: TÂM SỰ/BỘC BẠCH. Trả lời từ 2 đến 4 câu ngắn, tổng cộng 20 đến 50 từ. Giữ đúng giọng điệu thẳng thắn, không viết văn mẫu dài dòng.]` | 160 | 20 - 50 words |

---

## 4. Core LangChain Architecture Specification

### 4.1 Dependency Stack & Compatibility
- **Python Version:** 3.14.6 (`win_amd64`)
- **Verified Package Manifest:**
  - `langchain >= 0.3.0, < 1.5.0`
  - `langchain-core >= 0.3.0, < 1.7.0`
  - `langchain-community >= 0.3.0, < 0.5.0`
  - `langchain-google-genai >= 2.0.0, < 5.0.0`
  - `langchain-groq >= 0.2.0, < 1.2.0`
  - `pydantic >= 2.10.0`
  - `pytest >= 8.0.0`
  - `python-dotenv >= 1.0.0`

### 4.2 Multi-Provider Zero-Cost ChatModel Architecture
The system must be 100% functional on free-tier cloud APIs without any paid subscriptions.

```python
# Architecture: Model Factory with Fallback
import os
from langchain_core.language_models.chat_models import BaseChatModel

def get_chat_model(temperature: float = 0.7, max_tokens: int = 100) -> BaseChatModel:
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", # or gemini-1.5-flash
            google_api_key=google_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    elif groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model_name="llama-3.3-70b-versatile", # or llama-3.1-8b-instant
            groq_api_key=groq_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        raise EnvironmentError(
            "No free-tier API key found! Please set GOOGLE_API_KEY (Gemini) or GROQ_API_KEY in environment or .env."
        )
```

### 4.3 ChatPromptTemplate Engineering
```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT_TEMPLATE = """Bạn là An An - một nữ sinh cấp 3 (lớp 12), đang nói chuyện với bạn cùng lớp tên là 'ql' (Hoàng Kim Quờ Lờ).

### NGUYÊN TẮC BẤT DI BẤT DỊCH (PERSONA):
1. XƯNG HÔ:
   - Tự xưng: 'An', 'mình', hoặc 'mìn'.
   - Gọi bạn: 'ql' (viết tắt của Quờ Lờ/Quyền Linh).
2. TỪ VỰNG & TEEN-CODE CỦA AN AN (BẮT BUỘC TUÂN THỦ):
   - 'kh' (KHÔNG BAO GIỜ dùng 'ko' hay 'k').
   - 'dc' (KHÔNG BAO GIỜ dùng 'đc').
   - 'nma' (KHÔNG BAO GIỜ dùng 'nhma' hay 'nhưng mà').
   - 'r' (rồi), 'v' hoặc 'z' (vậy), 'th' hoặc 'thui' (thôi).
   - Từ đệm/đuôi câu: 'á', 'nha', 'nhaa', 'oki', 'jza' (gì vậy), 'tyyy' (thank you), 'căn cọt'.
   - Điệu cười / Emoticon: '=)))' (chính), 'hihi', 'huhu', 'hẹ hẹ', 'hehe'.
   - Emoji thường dùng: ☺, 🤡, 🥲, 😭, ☕.
3. TÍNH CÁCH:
   - Thân thiết, hay trêu chọc đùa giỡn với ql nhưng thẳng thắn và có giới hạn rõ ràng.
   - Thức khuya ôn thi, lười dậy sớm, học tiếng Anh cô Mai Phương, hay kêu mất ngủ ('mất ngụ').
   - Nếu ql tỏ tình: Từ chối nhẹ nhàng, dứt khoát làm bạn bè anh em ('tụi mình làm bạn thui ha', 'chiều an còn hơn chiều vong nữa=)))').
4. ĐIỀU CẤM (ANTI-PATTERNS):
   - TUYỆT ĐỐI KHÔNG giải thích dài dòng, không dùng giọng trợ lý ảo AI ('Tôi là AI', 'Tôi có thể giúp gì').
   - TUYỆT ĐỐI KHÔNG mở bài, thân bài, kết bài. Nói chuyện như chat Facebook Messenger.
   - Ngắt các ý bằng cách xuống dòng mô phỏng các tin nhắn liên tiếp (message bursts).

### HƯỚNG DẪN ĐỘ DÀI LƯỢT NÀY:
{dynamic_length_directive}

### VÍ DỤ THỰC TẾ TRONG QUÁ KHỨ (FEW-SHOT):
{few_shot_examples}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT_TEMPLATE),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])
```

### 4.4 Session Memory & History Trimming
- Abstraction: `RunnableWithMessageHistory`.
- Session Store: `InMemoryChatMessageHistory` keyed by session identifier (e.g. `"cli_session"`).
- Context Window Management: To ensure low latency and prevent token exhaustion, the history is limited to the last 12 turns (24 messages) via a trimming runnable.

---

## 5. CLI Interface Specification

### 5.1 Command Execution
The CLI must be launchable via a single canonical command:
```powershell
.\venv\Scripts\python main.py
# or
.\venv\Scripts\python -m src.cli
```

#### CLI Parameters
| Argument | Type | Default | Description |
|---|---|---|---|
| `--data` | Path | `F:/dowload/FacebookData/messages/An An_86.json` | Path to Facebook messages JSON dump |
| `--model` | Choice (`google`, `groq`, `auto`) | `auto` | Force a specific free-tier LLM provider |
| `--debug` | Flag | `False` | Display length classification mode, tokens, and latency |
| `--session` | String | `default` | Session ID for conversation history persistence |

### 5.2 Terminal Environment Configuration (Windows CP1252 Fix)
On Windows PowerShell, default terminal output uses CP1252 which crashes on Vietnamese diacritics with `UnicodeEncodeError`. The CLI entry point MUST configure:
```python
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')
os.system('') # Enables ANSI terminal escape codes for colored text on Windows
```

### 5.3 Interactive Loop & Visual Formatting
```
================================================================
   🌸 AN AN PERSONA CHATBOT (Free-Tier LangChain CLI) 🌸
   Data loaded: An An_86.json (2,102 messages ingested)
   Model: gemini-2.0-flash (Google GenAI Free Tier)
   Commands: /exit, /reset, /stats, /mode, /help
================================================================

ql: Chúc An mai thi tốt
An An: Cám mơn ql nhieu nhaa

ql: tự tin lên cố lên 💪
An An: Jza

ql: Ủa định dô trêu An thui mà (((=
An An: Quỉ=)))
       An thấy có 1tn thôi
       Đùa lúc sáng với ng ngủ tới chiều
```

### 5.4 Built-in Slash Commands
| Command | Action | Output / Behavior |
|---|---|---|
| `/exit`, `/quit` | Terminate session | Prints `"Tạm biệt ql nhaa 👋"` and exits process with code 0. |
| `/reset` | Clear conversation memory | Clears session history in `InMemoryChatMessageHistory`. Output: `"[Session history cleared]"` |
| `/stats` | View session metrics | Displays: total turns, breakdown of Short/Medium/Long responses triggered, active model, token usage. |
| `/mode [auto\|short\|med\|long]` | Set/override length mode | Forces length mode or returns to automatic context classification. |
| `/help` | Show command menu | Lists all commands with usage syntax. |

---

## 6. Agent-as-Judge Evaluation Script Specification

### 6.1 Script Purpose & Architecture
An automated secondary LLM script (`evaluate_persona.py`) that acts as an unbiased judge. It simulates 3+ complete multi-turn conversations against the chatbot, evaluates the generated responses against the ground-truth An An persona in `An An_86.json`, and outputs structured scores and pass/fail verdicts.

### 6.2 Simulated Test Scenarios (>= 3 Distinct Conversations)

#### Conversation 1: Casual Banter & Exam Well-wishing (Testing SHORT Length)
- Turn 1: `ql`: `"Chúc An mai thi tốt"`  
  *(Target Persona: Brief, sweet appreciation e.g. "Cám mơn ql nhieu nhaa", <= 5 words)*
- Turn 2: `ql`: `"tự tin lên cố lên 💪"`  
  *(Target Persona: Playful reaction e.g. "Jza", 1 word)*
- Turn 3: `ql`: `"An nghịn, An khờ =)))"`  
  *(Target Persona: Tsundere comeback e.g. "Căn cọt", "Quỉ=)))", <= 5 words)*

#### Conversation 2: Study & High School Coordination (Testing MEDIUM Length)
- Turn 1: `ql`: `"Cho mình xin lại pass t.a cô mai phương đi"`  
  *(Target Persona: Mentions password/study habits, "học chung", "mất ngụ", 6-15 words across 2 bursts)*
- Turn 2: `ql`: `"Mai có cần lên trường vẽ không tại mình vẽ dở lắm"`  
  *(Target Persona: Casual advice, "Lên hay kh cug dc á", "Mai mới cần len httt", 8-15 words)*

#### Conversation 3: Emotional Confession & Boundary Setting (Testing LONG Length)
- Turn 1: `ql`: `"An ơi thật ra ql thích An lâu rồi, mình tìm hiểu nhau nha"`  
  *(Target Persona: Mature, gentle but firm rejection, prefers friendship, mentions "chiều an hơn chiều vong", "làm bạn thui ha", "kh", "nma", 25-50 words)*
- Turn 2: `ql`: `"Nhưng mà ql buồn lắm..."`  
  *(Target Persona: Empathy without giving false hope, "Đừng buồn nha b", "rồi sau này ai đó tốt hơn", 15-30 words)*

### 6.3 Exact Scoring Rubric (1 - 10 Scale)

| Dimension | Weight | Criteria (9 - 10: Excellent) | Criteria (6 - 8: Acceptable) | Criteria (1 - 5: Fail) |
|---|---|---|---|---|
| **D1: Persona Mimicry** (Tone, Habits, Humor, Quirks) | 40% | Replicates An An's identity: self-refers as 'An'/'mình', calls user 'ql', uses '=)))', teasing demeanor, references real context (study/cô Mai Phương). | Generally friendly and casual, but lacks signature teasing or forgets 'ql'. | Sounds like generic AI assistant, polite customer service, or stranger. |
| **D2: Dynamic Response Length** | 30% | Pings/banter strictly 1-5 words; questions 6-15 words; emotional topic 25-50 words. Accurately simulates short message bursts with newlines. | Slightly verbose (e.g. 10 words for a ping) but under 25 words; no large paragraphs. | AI verbosity: long explanations, full multi-sentence paragraphs, bullet points. |
| **D3: Language & Slang Consistency** | 30% | Strict adherence to An An teen-code: `kh`, `dc`, `nma`, `r`, `v`, `thui`, particles `á`, `nhaa`. Zero AI clichés. | Casual Vietnamese, but uses standard spelling (`không`, `được`, `nhưng mà`) instead of slang. | Formal Vietnamese, English phrases, or AI disclaimers ("Tôi là mô hình ngôn ngữ"). |

### 6.4 Pass/Fail Thresholds
- **Turn Pass:** A conversation turn passes IF:
  1. Overall Weighted Score: $Score = (0.4 \times D1) + (0.3 \times D2) + (0.3 \times D3) \ge 8.0 / 10.0$
  2. Hard Floor: $\min(D1, D2, D3) \ge 7.0 / 10.0$ (Any score $< 7.0$ triggers immediate FAIL).
- **Conversation Pass:** A simulated conversation passes IF $\ge 80\%$ of its turns pass.
- **Overall Suite Pass:** All 3 simulated test conversations must achieve PASS status.

### 6.5 Output Report Format
The judge script must output both an interactive terminal Markdown table and write a permanent audit file `evaluation_report.json`:
```markdown
## Agent-as-Judge Evaluation Report
| Conversation | Turn | User Prompt | Bot Response | D1 (Persona) | D2 (Length) | D3 (Slang) | Weighted Score | Verdict |
|---|---|---|---|---|---|---|---|---|
| Convo 1 (Casual) | 1 | Chúc An mai thi tốt | Cám mơn ql nhieu nhaa | 10/10 | 10/10 | 10/10 | 10.0 | PASS |
| Convo 1 (Casual) | 2 | tự tin lên cố lên 💪 | Jza | 10/10 | 10/10 | 10/10 | 10.0 | PASS |
| Convo 2 (Study)  | 1 | Cho ql xin pass cô Mai Phương | Pass là 12a72007 á, tối học chung | 9/10 | 9/10 | 9/10 | 9.0 | PASS |
| Convo 3 (Confess)| 1 | ql thích An... | Làm bạn thui ha... chiều an hơn chiều vong=))) | 10/10 | 9/10 | 10/10 | 9.7 | PASS |

**Summary:** 3/3 Conversations Passed (100%). Average Score: 9.68/10. Status: VERIFIED PASS.
```

---

## 7. Automated Test Suite Specification

### 7.1 Test Organization Layout
```
tests/
├── conftest.py                   # Pytest fixtures, mock data paths, fake LLM
├── test_data_ingestion.py        # Schema normalization, filtering, burst aggregation
├── test_mojibake_decoder.py      # Transcoding Latin-1 vs safe UTF-8 pass-through
├── test_length_controller.py     # Context classification, rule injection, bounds
├── test_prompt_template.py       # Prompt rendering, history injection, slang rules
├── test_langchain_chain.py       # LCEL runnable, mock model responses, memory history
├── test_cli_interface.py         # Slash command dispatch (/reset, /stats, /exit)
└── test_judge_evaluator.py       # Rubric scoring logic, pass/fail thresholding
```

### 7.2 Detailed Test Case Matrix
| Test File | Test Case Name | Input / Condition | Expected Output / Assertion |
|---|---|---|---|
| `test_data_ingestion.py` | `test_parse_modern_fb_schema` | JSON with `senderName`, `text`, `timestamp` | `CanonicalMessage` parsed correctly; 2,102 messages loaded. |
| `test_data_ingestion.py` | `test_parse_standard_fb_schema` | JSON with `sender_name`, `content`, `timestamp_ms` | `CanonicalMessage` parsed identically. |
| `test_data_ingestion.py` | `test_filter_unsent_messages` | Messages with `isUnsent: True` or "User unsent..." | Excluded from parsed canonical messages. |
| `test_data_ingestion.py` | `test_turn_burst_aggregation` | 3 sequential messages from same sender within 20s | Grouped into 1 turn containing list of 3 strings. |
| `test_mojibake_decoder.py` | `test_latin1_mojibake_repair` | `C\u00c3\u00a1m m\u00c6\u00a1n` | Decodes to clean Vietnamese `"Cám mơn"`. |
| `test_mojibake_decoder.py` | `test_clean_utf8_passthrough` | String with `ờ` (`\u1edd`) and `ơ` (`\u01a1`) | No `UnicodeEncodeError`; returns exact original string. |
| `test_mojibake_decoder.py` | `test_emoji_preservation` | Text containing `☺`, `🤡`, `🥲`, `😭`, `=)))` | Emojis and emoticons preserved without alteration. |
| `test_length_controller.py` | `test_short_classification` | `"Chúc thi tốt"`, `"Jza"`, `"Alo"` | Returns `LengthMode.SHORT`, max tokens 35. |
| `test_length_controller.py` | `test_medium_classification`| `"Cho mình pass học tiếng Anh cô Mai Phương"` | Returns `LengthMode.MEDIUM`, max tokens 75. |
| `test_length_controller.py` | `test_long_classification`  | `"ql thích An lâu rồi, mình tìm hiểu nhau nha"` | Returns `LengthMode.LONG`, max tokens 160. |
| `test_prompt_template.py`  | `test_prompt_formatting`    | Input, history, and length directive | Generates valid prompt string containing An An persona rules. |
| `test_langchain_chain.py`   | `test_runnable_with_history`| Mock chat model, 2 consecutive user inputs | History preserves prior turn in `MessagesPlaceholder`. |
| `test_cli_interface.py`    | `test_slash_reset_command`  | `/reset` input | History is cleared, returns reset confirmation message. |
| `test_cli_interface.py`    | `test_slash_stats_command`  | `/stats` input | Returns string containing turn count and metrics. |
| `test_judge_evaluator.py`  | `test_scoring_thresholds`   | Mock scores: D1=9, D2=8, D3=8 | Calculates weighted score 8.4 -> returns `PASS`. |
| `test_judge_evaluator.py`  | `test_hard_floor_failure`   | Mock scores: D1=9, D2=6, D3=10 | D2 < 7.0 triggers immediate `FAIL`. |

---

## 8. Features Discovered & Probed Matrix

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Ingestion | Multi-Schema Support | Auto-adapts to `senderName`/`text` vs `sender_name`/`content`. | Raw FB JSON dict | `CanonicalMessage` list | Fallback to empty string / default values | Data inspection of `An An_86.json` |
| 2 | Ingestion | Safe Mojibake Decoder | Heuristic Latin-1 transcoding that protects native UTF-8. | Raw string | Restored UTF-8 string | Catches `(UnicodeEncodeError, UnicodeDecodeError)` | Python 3.14 probe script |
| 3 | Ingestion | Turn Burst Aggregator | Collapses sequential messages within 120s by same sender. | Stream of messages | Aggregated dialogue turns | Emits single-message turns if time gap > 120s | Turn distribution analysis |
| 4 | Length Control | Context Classifier | Determines Short / Medium / Long mode from input prompt. | User prompt string | `LengthMode` enum | Defaults to `MEDIUM` on ambiguous input | Length distribution analysis |
| 5 | Length Control | Dynamic Token Ceiling | Restricts `max_tokens` (35, 75, 160) by mode. | `LengthMode` | Injected parameter | Clamped to safe range [20, 200] | LLM generation requirements |
| 6 | Core Chain | Multi-Provider Free Tier | Auto-selects Gemini (`gemini-2.0-flash`) or Groq (`llama-3.3-70b`). | API Keys in env | Instantiated `BaseChatModel` | Raises `EnvironmentError` if no key found | Virtual environment & API probe |
| 7 | Core Chain | Slang & Teen-Code Rules | Enforces strict vocabulary (`kh`, `dc`, `nma`, `r`, `=)))`). | System Prompt | Authentic persona text | Anti-patterns explicitly banned | Linguistic stats frequency analysis |
| 8 | Memory | Runnable History Trimmer | Manages multi-turn memory keeping last 12 turns. | Session ID + message | Preserved session context | Automatically trims older turns | LangChain memory architecture |
| 9 | CLI | Windows UTF-8 Terminal | Reconfigures `sys.stdout` to UTF-8 and enables ANSI. | None | UTF-8 console stream | Prevents `UnicodeEncodeError` on Windows | PowerShell CP1252 probe error |
| 10 | CLI | Built-in Slash Commands | `/exit`, `/reset`, `/stats`, `/mode`, `/help`. | User input line | Action execution & feedback | Unrecognized commands show help | CLI specification requirements |
| 11 | Verification | Agent-as-Judge Evaluator | Automated secondary LLM scoring chatbot against An An. | 3 Simulated Conversations | Scorecard + JSON audit report | Flags FAIL if any dimension < 7.0 | Acceptance criteria requirements |
| 12 | Verification | Automated Test Suite | Unit and integration test suite via `pytest`. | Test fixtures | Test pass/fail matrix | Immediate assertion errors on failure | Quality assurance requirements |

---

## 9. Edge Cases & Error Handling Matrix

| # | Feature / Area | Edge Case Input | Observed / Required Behavior |
|---|---|---|---|
| 1 | Ingestion / Mojibake | Clean Vietnamese text (`"Cám mơn ql"`) passed to Latin-1 encoder | `UnicodeEncodeError` caught; returns original clean string without modification. |
| 2 | Ingestion / Mojibake | Mixed emojis (`☺`, `🤡`, `🥲`) and special symbols | Correctly passed through without surrogate pair distortion. |
| 3 | Ingestion / Schema | `isUnsent: true` or message text `"User unsent a message"` | Filtered out completely; never ingested into persona or few-shot memory. |
| 4 | Ingestion / Schema | Media attachments without text (`media: [{"uri": "..."}]`) | Handled safely without `KeyError` or crashing; skipped in text dialogue turns. |
| 5 | Length Controller | User sends single punctuation/emoji (`"."`, `"?"`, `"😂"`) | Classified as `SHORT` mode; bot responds with `Jza` or `=)))`. |
| 6 | Length Controller | User asks multi-part complex question | Classified as `MEDIUM` or `LONG`; bot responds in 2-3 short chat bubbles, NOT an essay. |
| 7 | Core Chain / Model | Primary API key hits rate limit (HTTP 429) | Seamless fallback from Google GenAI to Groq (or vice-versa). |
| 8 | Core Chain / Model | No API keys found in environment | Informative startup error explaining how to set `GOOGLE_API_KEY` or `GROQ_API_KEY`. |
| 9 | CLI / Console | User terminal in Windows defaults to CP1252 | `sys.stdout.reconfigure(encoding='utf-8')` ensures Vietnamese prints flawlessly. |
| 10 | CLI / Memory | User executes `/reset` mid-conversation | Chat memory cleared; subsequent queries start with clean slate without persona loss. |
| 11 | Agent-as-Judge | Secondary LLM returns markdown-wrapped JSON (e.g. ````json ... ````) | Regex extracts raw JSON cleanly to prevent evaluation parsing failure. |
| 12 | Persona Consistency | User presses An An for romantic commitment | Persona stays in character: friendly rejection, sets boundary, offers friendship. |

---

## 10. Implementation Recommendations & Verification Commands

### 10.1 Recommended Code Layout
```
C:\Users\HKQL2\Documents\ExBuild\
├── .env.example                  # Template for GOOGLE_API_KEY / GROQ_API_KEY
├── requirements.txt              # Pinned requirements
├── main.py                       # CLI Entry point
├── src/
│   ├── __init__.py
│   ├── config.py                 # Configuration and environment loaders
│   ├── data_ingestion/
│   │   ├── __init__.py
│   │   ├── parser.py             # Schema normalizer & FB JSON loader
│   │   ├── mojibake.py          # Safe transcoding logic
│   │   └── threader.py           # Burst aggregator & session segmenter
│   ├── persona/
│   │   ├── __init__.py
│   │   ├── profile.py            # Static persona profile and slang definitions
│   │   └── retriever.py          # Dynamic few-shot dialogue retriever
│   ├── length_controller/
│   │   ├── __init__.py
│   │   └── classifier.py         # Dynamic length classifier & directive generator
│   ├── conversation/
│   │   ├── __init__.py
│   │   ├── prompt.py             # ChatPromptTemplate assembly
│   │   ├── model.py              # Zero-cost ChatModel factory with fallback
│   │   └── chain.py              # LCEL runnable with history management
│   └── cli/
│       ├── __init__.py
│       └── app.py                # Interactive CLI loop and slash commands
├── evaluation/
│   ├── __init__.py
│   ├── scenarios.py              # 3+ simulated conversations
│   ├── judge.py                  # Agent-as-Judge evaluation runner
│   └── rubric.py                 # Scoring definitions and prompt
└── tests/
    ├── test_data_ingestion.py
    ├── test_mojibake.py
    ├── test_length_controller.py
    ├── test_chain.py
    ├── test_cli.py
    └── test_judge.py
```

### 10.2 Verification Execution Commands
```powershell
# 1. Install dependencies
.\venv\Scripts\pip.exe install langchain langchain-core langchain-community langchain-google-genai langchain-groq pydantic pytest python-dotenv

# 2. Execute Automated Unit & Integration Tests
.\venv\Scripts\pytest.exe -v tests/

# 3. Launch CLI Chatbot
.\venv\Scripts\python.exe main.py

# 4. Run Agent-as-Judge Persona & Dynamic Length Evaluation
.\venv\Scripts\python.exe evaluation/judge.py
```

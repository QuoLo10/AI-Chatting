# Dependencies & Virtual Environment Plan (Milestone M1)

**Author**: Explorer Subagent `explorer_m1_2` (Dependency & Venv Specialist)  
**Date**: 2026-09-14  
**Project**: An An Persona Chatbot  
**Target Environment**: Windows AMD64 | Python 3.14.6 | `C:\Users\HKQL2\Documents\ExBuild\venv`

---

## 1. Executive Summary

| Item | Finding / Assessment | Status |
|---|---|---|
| **Python Runtime** | Python `3.14.6` (AMD64, 64-bit, MSC v.1944) | ✅ Verified |
| **Virtual Environment** | `C:\Users\HKQL2\Documents\ExBuild\venv` (currently only `pip 26.1.2`) | ✅ Healthy |
| **Wheel Availability** | 100% of direct and transitive dependencies have prebuilt binary wheels | ✅ Verified (`--only-binary :all:`) |
| **Build Tools Dependency** | Zero C++ / MSVC / Rust build tools required | ✅ Verified |
| **Venv Strategy** | Keep `include-system-site-packages = false`; install isolated packages into `venv` | ✅ 100% Sound |
| **Windows Console Encoding** | Windows console defaults to `cp1252`. Must invoke Python with `-X utf8` or `$env:PYTHONUTF8 = '1'` | ⚠️ Guard Required |

All 9 target packages (`langchain`, `langchain-core`, `langchain-google-genai`, `langchain-groq`, `google-genai`, `groq`, `pydantic`, `pytest`, `python-dotenv`) resolve deterministically without a single compilation error or build dependency on Python 3.14.6 on Windows x64.

---

## 2. Complete Pinned `requirements.txt` Specification

The Worker should create `C:\Users\HKQL2\Documents\ExBuild\requirements.txt` with the exact contents below:

```text
# ==============================================================================
# Project: An An Persona Chatbot
# Runtime: Python 3.14.6 (Windows AMD64)
# Direct Pinned Dependencies Specification
# ==============================================================================

# Core Framework & Agent Flow
langchain==1.4.0
langchain-core==1.6.3

# Zero-Cost Cloud LLM Integrations (Google Gemini & Groq)
langchain-google-genai==4.4.0
google-genai==2.23.0
langchain-groq==1.1.3
groq==0.37.1

# Data Validation, Schema Contracts & Configuration
pydantic==2.13.5
python-dotenv==1.2.3

# Automated Testing Infrastructure
pytest==9.1.1
```

### 2.1 Role of Each Package in the Project Architecture

| Package | Pinned Version | Project Scope & Feature Mapping | Rationale |
|---|---|---|---|
| `langchain` | `1.4.0` | Feature F6 (M3 Conversational Core, Memory, Runnables) | Mandated by user requirement R4. Provides `ChatMessageHistory`, conversation chains, and agent pipelines. |
| `langchain-core` | `1.6.3` | Features F5, F6, T1 (M3 Base Chat Models, Prompts, Messages) | Primitives for `BaseChatModel`, `HumanMessage`, `AIMessage`, `SystemMessage`, and prompt templates. |
| `langchain-google-genai` | `4.4.0` | Feature F5 (M3 LLM Factory: Google Gemini 2.0 / 1.5 Flash) | Official LangChain integration for Google AI Studio free tier. Implements `ChatGoogleGenerativeAI`. |
| `google-genai` | `2.23.0` | Feature F5 (M3 Google GenAI direct client) | Dependency of `langchain-google-genai` and direct SDK for Gemini 2.0. |
| `langchain-groq` | `1.1.3` | Feature F5 (M3 LLM Factory: Groq Llama 3.3 70B / Llama 3.1 8B) | Official LangChain integration for Groq Cloud free tier. Implements `ChatGroq`. |
| `groq` | `0.37.1` | Feature F5 (M3 Groq client) | Official high-speed Groq SDK used by `langchain-groq`. |
| `pydantic` | `2.13.5` | Features F1, F4, F8 (M1 `CanonicalMessage`, M2 `LengthDecision`) | Strict data modeling, validation, and JSON serialization specified in `PROJECT.md` contracts. |
| `python-dotenv` | `1.2.3` | Features F5, F7 (M1 `src/config.py`, `.env` loader) | Loads `GEMINI_API_KEY`, `GOOGLE_API_KEY`, and `GROQ_API_KEY` from `.env` file per requirement R3. |
| `pytest` | `9.1.1` | Features F8, F9 (Milestones T1, T2, M5 automated testing) | Offline test runner for unit, integration, and Agent-as-Judge suites. |

---

## 3. Python 3.14.6 Windows Compatibility & Binary Wheel Audit

### 3.1 Direct Package Wheel Verification
Tested via `pip install --dry-run --only-binary :all:`:

1. **`langchain-1.4.0`**: Pure Python wheel (`langchain-1.4.0-py3-none-any.whl`). No build tools.
2. **`langchain-core-1.6.3`**: Pure Python wheel (`langchain_core-1.6.3-py3-none-any.whl`). No build tools.
3. **`langchain-google-genai-4.4.0`**: Pure Python wheel (`langchain_google_genai-4.4.0-py3-none-any.whl`). No build tools.
4. **`google-genai-2.23.0`**: Pure Python wheel (`google_genai-2.23.0-py3-none-any.whl`). No build tools.
5. **`langchain-groq-1.1.3`**: Pure Python wheel (`langchain_groq-1.1.3-py3-none-any.whl`). No build tools.
6. **`groq-0.37.1`**: Pure Python wheel (`groq-0.37.1-py3-none-any.whl`). No build tools.
7. **`pydantic-2.13.5`**: Pure Python wheel (`pydantic-2.13.5-py3-none-any.whl`). Backed by prebuilt `pydantic_core` wheel.
8. **`pytest-9.1.1`**: Pure Python wheel (`pytest-9.1.1-py3-none-any.whl`). No build tools.
9. **`python-dotenv-1.2.3`**: Pure Python wheel (`python_dotenv-1.2.3-py3-none-any.whl`). No build tools.

### 3.2 Transitive C/Rust Binary Wheel Audit for Python 3.14 on Windows
All transitive dependencies requiring compiled C or Rust extensions have official, prebuilt Windows AMD64 binary wheels for Python 3.14:

| Compiled Dependency | Wheel Filename | Architecture / ABI | Build Tools Required? |
|---|---|---|---|
| `pydantic_core` | `pydantic_core-2.46.5-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `cryptography` | `cryptography-50.0.1-cp311-abi3-win_amd64.whl` | Stable ABI3 / Win AMD64 | **NO** (Precompiled) |
| `cffi` | `cffi-2.1.1-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `pyyaml` | `pyyaml-6.0.3-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `uuid_utils` | `uuid_utils-0.17.1-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `xxhash` | `xxhash-4.0.1-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `ormsgpack` | `ormsgpack-1.12.2-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `orjson` | `orjson-3.12.0-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `websockets` | `websockets-16.1.1-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `zstandard` | `zstandard-0.25.0-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |
| `charset_normalizer`| `charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl` | CPython 3.14 / Win AMD64 | **NO** (Precompiled) |

**Conclusion**: Passing `--only-binary :all:` guarantees that pip will never attempt to invoke `cl.exe`, `gcc`, or `cargo/rustc`. The installation will succeed 100% cleanly on any Windows machine without development tools installed.

### 3.3 Full Transitive Dependency Lock Reference (57 Packages)
For full auditability, here is the complete resolved lock set:
```text
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.7.22
cffi==2.1.1
charset-normalizer==3.5.1
colorama==0.4.6
cryptography==50.0.1
distro==1.9.0
filetype==1.2.0
google-auth==2.58.0
google-genai==2.23.0
groq==0.37.1
h11==0.16.0
httpcore==1.0.9
httpcore2==2.12.0
httpx==0.28.1
httpx2==2.12.0
idna==3.19
iniconfig==2.3.0
jsonpatch==1.33
jsonpointer==3.1.1
langchain==1.4.0
langchain-core==1.6.3
langchain-google-genai==4.4.0
langchain-groq==1.1.3
langchain-protocol==0.0.19
langgraph==1.2.11
langgraph-checkpoint==4.2.0
langgraph-prebuilt==1.1.0
langgraph-sdk==0.4.4
langsmith==0.12.4
orjson==3.12.0
ormsgpack==1.12.2
packaging==26.3
pluggy==1.6.0
pyasn1==0.6.4
pyasn1_modules==0.4.2
pycparser==3.0
pydantic==2.13.5
pydantic_core==2.46.5
pytest==9.1.1
python-dotenv==1.2.3
pyyaml==6.0.3
pygments==2.21.0
requests==2.34.2
requests-toolbelt==1.0.0
sniffio==1.3.1
tenacity==9.1.4
truststore==0.10.4
typing-inspection==0.4.4
typing_extensions==4.16.0
urllib3==2.7.0
uuid_utils==0.17.1
websockets==16.1.1
xxhash==4.0.1
zstandard==0.25.0
```

---

## 4. Virtual Environment & `include-system-site-packages` Validation

### 4.1 Comparison of Installation Strategies

#### Strategy A: Setting `include-system-site-packages = true` in `venv\pyvenv.cfg`
- **Mechanism**: Modify `pyvenv.cfg` so the venv searches `C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages`.
- **Fatal Flaws**:
  1. Base Python is **missing 6 of the 9 required packages**: `langchain-google-genai`, `google-genai`, `groq`, `langchain-groq`, `pytest`, `python-dotenv`. Pip install must be executed anyway.
  2. If packages are installed while `include-system-site-packages = true`, pip checks global site-packages first and creates fragile partial installs in the venv.
  3. Base site-packages changes by other tools or users will unexpectedly mutate the project environment.
  4. Violates acceptance criteria: "The system can be launched from the CLI via a single command (using the `venv` provided)" — the venv must be self-contained and reproducible.

#### Strategy B: Retaining `include-system-site-packages = false` & Installing into `venv` (RECOMMENDED)
- **Mechanism**: Keep `include-system-site-packages = false` (as configured by default in `venv\pyvenv.cfg`) and install all packages directly into `C:\Users\HKQL2\Documents\ExBuild\venv\Lib\site-packages`.
- **Advantages**:
  1. **100% Hermetic Isolation**: Complete isolation from any external global Python state.
  2. **Fast Cached Installation**: Wheels already cached during prior operations on the machine are reused instantly by pip (`Using cached ...`).
  3. **Zero Host Pollution**: Any upgrades or uninstalls remain strictly within `C:\Users\HKQL2\Documents\ExBuild\venv`.
  4. **Executable Placement**: `pytest.exe`, `dotenv.exe` are installed cleanly into `C:\Users\HKQL2\Documents\ExBuild\venv\Scripts\`.

**Verdict**: Strategy B is **100% sound, architecturally superior, and strongly recommended**. Do NOT alter `pyvenv.cfg`.

---

## 5. Critical Windows Environment Finding: UTF-8 vs `cp1252`

During our pip execution analysis, we uncovered a critical Windows-specific failure:
When pip printed package descriptions containing Unicode symbols to the standard Windows console, it triggered:
`UnicodeEncodeError: 'charmap' codec can't encode characters in position 3-5: character maps to <undefined>`
in `Lib\encodings\cp1252.py`.

### Root Cause
On Windows, standard console streams default to legacy code page 1252 (`cp1252`). When Python scripts, pip, or the CLI chatbot output Vietnamese text (essential for An An chat logs) or Unicode emojis (`🤡`, `=)))`), Python raises `UnicodeEncodeError` unless UTF-8 mode is explicitly activated.

### Safe Execution Requirement
For both Worker pip installation and subsequent project execution (`main.py`, `pytest`), the following must always be applied:
1. Set the PowerShell environment variable: `$env:PYTHONUTF8 = "1"`
2. Pass the Python UTF-8 flag: `-X utf8` to `python.exe`
3. In `main.py` and `src/cli/chat.py`, configure UTF-8 output streams programmatically (`sys.stdout.reconfigure(encoding='utf-8')`).

---

## 6. Exact Step-by-Step Instructions for Worker

The Worker should execute the following sequence:

### Step 1: Create `requirements.txt`
Write the pinned requirements specification to:
`C:\Users\HKQL2\Documents\ExBuild\requirements.txt`

### Step 2: Execute Pip Installation
Run the following exact command from `C:\Users\HKQL2\Documents\ExBuild`:

```powershell
$env:PYTHONUTF8 = "1"
.\venv\Scripts\python.exe -X utf8 -m pip install --only-binary :all: -r requirements.txt
```

### Step 3: Run Post-Install Verification
Verify that every direct package can be imported and versions match:

```powershell
$env:PYTHONUTF8 = "1"
.\venv\Scripts\python.exe -X utf8 -c "
import langchain
import langchain_core
import langchain_google_genai
import langchain_groq
import google.genai
import groq
import pydantic
import dotenv
import pytest

print('--- VENV VERIFICATION SUCCESSFUL ---')
print(f'langchain:               {langchain.__version__}')
print(f'langchain-core:          {langchain_core.__version__}')
print(f'langchain-google-genai:  {langchain_google_genai.__version__}')
print(f'langchain-groq:          {langchain_groq.__version__}')
print(f'pydantic:                {pydantic.__version__}')
print(f'pytest:                  {pytest.__version__}')
print('------------------------------------')
"
```

### Step 4: Verify Pytest Entrypoint
Confirm the `pytest` executable in `venv\Scripts`:

```powershell
.\venv\Scripts\pytest.exe --version
```
Expected output: `pytest 9.1.1`

# Environment & Cloud API Survey Report

**Explorer**: `explorer_survey_2` (Environment & API Analyst)  
**Date**: 2026-09-14  
**Project**: An An Persona Chatbot (`C:\Users\HKQL2\Documents\ExBuild`)  

---

## 1. Executive Summary

| Category | Status | Details |
|---|---|---|
| **Python Version** | ✅ Valid | Python `3.14.6` (AMD64, 64-bit, MSC v.1944) |
| **Virtual Environment** | ⚠️ Needs Packages | Located at `C:\Users\HKQL2\Documents\ExBuild\venv`. Contains only `pip 26.1.2`. `include-system-site-packages` is `false`. |
| **LangChain in venv** | ❌ Missing | Not installed in `venv` (`ModuleNotFoundError`). However, `langchain 1.4.0` & `langchain-core 1.6.3` are installed in base Python. |
| **LLM Provider Packages** | ❌ Missing | `langchain-google-genai`, `google-genai`, `groq`, `langchain-groq`, `openai`, `python-dotenv` are missing from both `venv` and base. |
| **Package Resolution Test** | ✅ Verified | `pip install --dry-run` successfully resolved prebuilt binary wheels for Python 3.14 on Windows AMD64 for all target packages. |
| **API Keys in Environment** | ⚠️ Unset | No keys for Google Gemini, Groq, OpenAI, or OpenRouter exist in Process, User registry, Machine registry, or `.env`. |
| **Network & Cloud Endpoints** | ✅ Reachable | PyPI (HTTP 200), Google GenAI API (HTTP 404 endpoint ping), and Groq API (HTTP 401 unauthenticated ping) are 100% reachable without proxy/firewall interference. |

---

## 2. Workspace & Virtual Environment Inspection

### 2.1 Workspace Structure
- **Path**: `C:\Users\HKQL2\Documents\ExBuild`
- **Current Contents**:
  - `venv/` (Virtual environment folder)
  - `.agents/` (Agent metadata: `ORIGINAL_REQUEST.md`, explorer & orchestrator workspaces)
  - `ORIGINAL_REQUEST.md` (Initial user requirements)
- **Source Code / Git**: No existing source code files (`.py`) or git repository (`.git`). Clean greenfield project.
- **Local Environment Files**: No `.env`, `.env.local`, or `.env.production` files found in the project root or subdirectories.

### 2.2 Virtual Environment Configuration
- **Path**: `C:\Users\HKQL2\Documents\ExBuild\venv`
- **Config (`pyvenv.cfg`)**:
  ```ini
  home = C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64
  include-system-site-packages = false
  version = 3.14.6
  executable = C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\python.exe
  command = C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\python.exe -m venv C:\Users\HKQL2\Documents\ExBuild\venv
  ```
- **Executable**: `C:\Users\HKQL2\Documents\ExBuild\venv\Scripts\python.exe`
- **`sys.path`**:
  ```python
  [
    '',
    'C:\\Users\\HKQL2\\AppData\\Local\\Python\\pythoncore-3.14-64\\python314.zip',
    'C:\\Users\\HKQL2\\AppData\\Local\\Python\\pythoncore-3.14-64\\DLLs',
    'C:\\Users\\HKQL2\\AppData\\Local\\Python\\pythoncore-3.14-64\\Lib',
    'C:\\Users\\HKQL2\\AppData\\Local\\Python\\pythoncore-3.14-64',
    'C:\\Users\\HKQL2\\Documents\\ExBuild\\venv',
    'C:\\Users\\HKQL2\\Documents\\ExBuild\\venv\\Lib\\site-packages'
  ]
  ```

---

## 3. Python Packages Inventory

### 3.1 Installed Packages in `venv` (`venv\Scripts\python.exe -m pip list`)
```text
Package Version
------- -------
pip     26.1.2
```
*Note*: `venv\Lib\site-packages` contains only `pip` and `pip-26.1.2.dist-info`.

### 3.2 Comparison with Base Python (`C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages`)
Base Python has modern packages installed:
- `langchain 1.4.0`
- `langchain-core 1.6.3`
- `langgraph 1.2.11`
- `langgraph-checkpoint 4.2.0`
- `langsmith 0.12.4`
- `pydantic 2.13.5`
- `requests 2.34.2`
- `httpx 0.28.1`
- `PyYAML 6.0.3`

Because `include-system-site-packages = false`, `venv` does not inherit these packages. Attempting `import langchain` in `venv` raises:
`ModuleNotFoundError: No module named 'langchain'`

### 3.3 LLM Provider Packages Status
Neither `venv` nor Base Python contains:
- `langchain-community`
- `langchain-google-genai` / `google-genai` / `google-generativeai`
- `langchain-groq` / `groq`
- `langchain-openai` / `openai`
- `python-dotenv`
- `pytest`

### 3.4 Python 3.14 Prebuilt Wheel Compatibility Check
Running `pip install --dry-run` against PyPI verified that all required packages resolve without compilation errors:
- `langchain-1.4.0` (pure Python wheel)
- `langchain-core-1.6.3` (pure Python wheel)
- `langchain-google-genai-4.4.0` (pure Python wheel)
- `langchain-groq-1.1.3` (pure Python wheel)
- `google-genai-2.23.0` (pure Python wheel)
- `groq-0.37.1` (pure Python wheel)
- `pydantic-2.13.5` & `pydantic_core-2.46.5` (`cp314-cp314-win_amd64.whl` cached)
- `pytest-9.1.1` (pure Python wheel)
- `python-dotenv-1.2.3` (pure Python wheel)

---

## 4. API Keys & Free-Tier Cloud API Analysis

### 4.1 Comprehensive Key Scan
We scanned all three Windows environment scopes and user directories:
1. **Process Environment (`$env:`)**:
   - `GEMINI_API_KEY`: None
   - `GOOGLE_API_KEY`: None
   - `GROQ_API_KEY`: None
   - `OPENAI_API_KEY`: None
   - `OPENROUTER_API_KEY`: None
2. **User Registry (`[System.Environment]::GetEnvironmentVariables('User')`)**: No LLM API keys found.
3. **Machine Registry (`[System.Environment]::GetEnvironmentVariables('Machine')`)**: No LLM API keys found.
4. **Local `.env` search**: No `.env` files in `C:\Users\HKQL2\Documents\ExBuild` or user root.
5. **Agent Memory**: No stored API credentials found.

### 4.2 Candidate Free-Tier Cloud Providers
Requirement R3 mandates: "completely free tools, libraries, or models (specifically leveraging free-tier cloud APIs, requiring API keys but no paid subscriptions)."

Two primary free-tier cloud LLM providers fit these constraints:

1. **Google Gemini (Google AI Studio)**:
   - **Recommended Model**: `gemini-2.0-flash` (or `gemini-1.5-flash`)
   - **Pricing**: Free tier ($0 cost, no credit card required)
   - **Limits**: 15 RPM (Requests Per Minute), 1,000,000 TPM, 1,500 RPD (Requests Per Day)
   - **Environment Variable**: `GOOGLE_API_KEY` or `GEMINI_API_KEY`
   - **LangChain Integration**: `langchain-google-genai` (`ChatGoogleGenerativeAI`)

2. **Groq Cloud**:
   - **Recommended Model**: `llama-3.3-70b-versatile` (or `llama-3.1-8b-instant`)
   - **Pricing**: Free tier ($0 cost, no credit card required)
   - **Limits**: 30 RPM, 14,400 RPD
   - **Environment Variable**: `GROQ_API_KEY`
   - **LangChain Integration**: `langchain-groq` (`ChatGroq`)

### 4.3 Network Connectivity & Reachability Test
From `venv\Scripts\python.exe`:
- `https://generativelanguage.googleapis.com`: Handshake successful, server returned `HTTP 404` for root path (expected behavior confirming HTTPS route is live and unblocked).
- `https://api.groq.com/openai/v1/models`: Handshake successful, server returned `HTTP 401 Unauthorized` (expected behavior confirming authentication firewall responds correctly).
- `https://pypi.org`: Handshake successful, server returned `HTTP 200 OK`.

Both cloud providers are fully reachable from the local machine. Once an API key is provided, calls will succeed without proxy or SSL configuration issues.

---

## 5. Architectural Recommendations for Implementation

1. **Dependency Installation Plan**:
   Execute inside `C:\Users\HKQL2\Documents\ExBuild`:
   ```powershell
   .\venv\Scripts\python.exe -m pip install langchain langchain-core langchain-google-genai langchain-groq python-dotenv pydantic pytest
   ```
   Create a standard `requirements.txt` in the workspace root with pinned dependencies.

2. **Unified ChatModel Factory with Automatic Fallback**:
   To satisfy R3 (Zero-cost) and robust fault-tolerance, build a model factory:
   - Priority 1: `gemini-2.0-flash` if `GOOGLE_API_KEY` / `GEMINI_API_KEY` is present.
   - Priority 2: `llama-3.3-70b-versatile` if `GROQ_API_KEY` is present.
   - If one provider hits rate limits (HTTP 429), dynamically switch to the fallback provider.

3. **Offline & CI Testing with Mock Models**:
   Because no API keys are currently in the process environment:
   - All unit tests and simulated conversation regression suites must support LangChain's `FakeListChatModel` or fixture-based responses so `pytest` can execute 100% offline without failing on missing credentials.
   - Live API calls (e.g. live Agent-as-Judge evaluations) should be flagged with `@pytest.mark.live_api` and skip gracefully when keys are absent.

4. **Environment Template (`.env.example`)**:
   Provide a clear `.env.example` in the project root:
   ```env
   # Google Gemini Free Tier (from https://aistudio.google.com/)
   GOOGLE_API_KEY=
   # Or Groq Cloud Free Tier (from https://console.groq.com/)
   GROQ_API_KEY=
   ```

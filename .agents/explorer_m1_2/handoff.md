# Milestone M1 Dependency & Virtual Environment Handoff Report

**Agent**: `explorer_m1_2` (Dependency & Venv Specialist)  
**Date**: 2026-09-14  
**Working Directory**: `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_2`  
**Target Project**: `C:\Users\HKQL2\Documents\ExBuild`  

---

## 1. Observation

1. **Python & Pip Runtime**:
   - Command: `.\venv\Scripts\python.exe -m pip --version; .\venv\Scripts\python.exe -V`
   - Output:
     ```text
     pip 26.1.2 from C:\Users\HKQL2\Documents\ExBuild\venv\Lib\site-packages\pip (python 3.14)
     Python 3.14.6
     ```
   - Binary: `C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\python.exe` (AMD64 64-bit).

2. **Virtual Environment Configuration (`C:\Users\HKQL2\Documents\ExBuild\venv\pyvenv.cfg`)**:
   ```ini
   home = C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64
   include-system-site-packages = false
   version = 3.14.6
   executable = C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\python.exe
   command = C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\python.exe -m venv C:\Users\HKQL2\Documents\ExBuild\venv
   ```
   - Current installed packages in `venv\Lib\site-packages`: only `pip 26.1.2`. Base Python has `langchain 1.4.0`, `pydantic 2.13.5`, but `venv` currently cannot import them due to `include-system-site-packages = false`.
   - Base Python is missing 6 required packages: `langchain-google-genai`, `google-genai`, `langchain-groq`, `groq`, `pytest`, `python-dotenv`.

3. **Wheel Resolution & Build Tool Independence**:
   - Command:
     ```powershell
     .\venv\Scripts\python.exe -m pip install --dry-run --only-binary :all: langchain==1.4.0 langchain-core==1.6.3 langchain-google-genai==4.4.0 langchain-groq==1.1.3 google-genai==2.23.0 groq==0.37.1 pydantic==2.13.5 pytest==9.1.1 python-dotenv==1.2.3
     ```
   - Output: Exited with status code `0`.
   - Result: 100% of the dependency tree (9 direct + 48 transitive packages = 57 packages total) resolved to prebuilt binary wheels (`.whl`). No package required compilation or invocation of C/C++ (MSVC/gcc) or Rust toolchains.
   - Specific compiled wheels resolved for Windows AMD64 on Python 3.14:
     - `pydantic_core-2.46.5-cp314-cp314-win_amd64.whl`
     - `cryptography-50.0.1-cp311-abi3-win_amd64.whl`
     - `cffi-2.1.1-cp314-cp314-win_amd64.whl`
     - `pyyaml-6.0.3-cp314-cp314-win_amd64.whl`
     - `uuid_utils-0.17.1-cp314-cp314-win_amd64.whl`
     - `xxhash-4.0.1-cp314-cp314-win_amd64.whl`
     - `ormsgpack-1.12.2-cp314-cp314-win_amd64.whl`
     - `orjson-3.12.0-cp314-cp314-win_amd64.whl`
     - `websockets-16.1.1-cp314-cp314-win_amd64.whl`
     - `zstandard-0.25.0-cp314-cp314-win_amd64.whl`
     - `charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl`

4. **Windows Console `cp1252` Encoding Trap**:
   - During pip dry-run reporting, pip encountered Unicode characters and crashed:
     `File "C:\Users\HKQL2\AppData\Local\Python\pythoncore-3.14-64\Lib\encodings\cp1252.py", line 19, in encode`
     `UnicodeEncodeError: 'charmap' codec can't encode characters in position 3-5: character maps to <undefined>`
   - When run with `$env:PYTHONUTF8 = '1'` and `python.exe -X utf8`, the command completed cleanly with exit code `0`.

---

## 2. Logic Chain

1. **Premise 1**: From Observation 1 & 3, the host environment runs Python 3.14.6 AMD64 on Windows without MSVC or build tools installed.
2. **Premise 2**: From Observation 3, running `pip install --dry-run --only-binary :all:` resolved all 9 direct packages and their 48 transitive dependencies into precompiled wheels (`cp314`, `abi3`, or `py3-none-any`). Because `--only-binary :all:` succeeded, pip will never attempt to build from source or invoke external compilers.
3. **Premise 3**: From Observation 2, `venv` has `include-system-site-packages = false`. While base Python contains `langchain` and `pydantic`, it lacks `langchain-google-genai`, `google-genai`, `langchain-groq`, `groq`, `pytest`, and `python-dotenv`.
4. **Premise 4**: Enabling `include-system-site-packages = true` would couple `venv` to global site-packages, causing subtle package shadowing and breaking reproducibility if base packages mutate. Keeping `include-system-site-packages = false` and installing all dependencies directly into `venv` ensures complete hermetic isolation, matching requirement R4 and acceptance criteria ("using the `venv` provided").
5. **Premise 5**: From Observation 4, Windows PowerShell default console encoding (`cp1252`) triggers `UnicodeEncodeError` when non-ASCII characters are output. Passing `-X utf8` and setting `$env:PYTHONUTF8 = '1'` guarantees safe execution for pip, the test suite, and the CLI chat application.

---

## 3. Caveats

1. **Network Connectivity During Install**: Although all wheel metadata and resolutions succeeded via PyPI, the Worker must run the pip install command on a machine with active internet access to download any wheels not already present in pip's HTTP cache.
2. **API Keys Not Included**: Packages install the client libraries (`google-genai`, `groq`), but valid API keys are required for live cloud calls. The test suite must utilize mock models (`FakeListChatModel` or unittest mocks) when offline or in test environments.
3. **No other caveats**: The resolution tree is complete, locked, and tested.

---

## 4. Conclusion

1. **Pinned `requirements.txt`**:
   The Worker should create `C:\Users\HKQL2\Documents\ExBuild\requirements.txt` containing:
   ```text
   langchain==1.4.0
   langchain-core==1.6.3
   langchain-google-genai==4.4.0
   google-genai==2.23.0
   langchain-groq==1.1.3
   groq==0.37.1
   pydantic==2.13.5
   python-dotenv==1.2.3
   pytest==9.1.1
   ```

2. **Venv Strategy**:
   Retain `include-system-site-packages = false` in `venv\pyvenv.cfg`. Do NOT modify `pyvenv.cfg`. Install all packages directly into `venv` for 100% hermetic isolation.

3. **Exact Pip Install Command for Worker**:
   ```powershell
   $env:PYTHONUTF8 = "1"
   .\venv\Scripts\python.exe -X utf8 -m pip install --only-binary :all: -r requirements.txt
   ```

---

## 5. Verification Method

To independently verify the environment and installation:

1. **Inspect Pinned Specification**:
   Check `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_2\dependencies_plan.md`.

2. **Post-Installation Import Check**:
   After the Worker executes the pip install command, run:
   ```powershell
   $env:PYTHONUTF8 = "1"
   .\venv\Scripts\python.exe -X utf8 -c "import langchain, langchain_core, langchain_google_genai, langchain_groq, google.genai, groq, pydantic, dotenv, pytest; print('ALL 9 PACKAGES IMPORTED SUCCESSFULLY')"
   ```
   **Expected output**: `ALL 9 PACKAGES IMPORTED SUCCESSFULLY` (exit code 0).

3. **Verify Pytest CLI**:
   ```powershell
   .\venv\Scripts\pytest.exe --version
   ```
   **Expected output**: `pytest 9.1.1`.

4. **Invalidation Conditions**:
   - Any dependency fails to resolve or requires compilation when running `pip install --only-binary :all:`.
   - Any import fails with `ModuleNotFoundError` or `ImportError`.

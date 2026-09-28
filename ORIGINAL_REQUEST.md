# Original User Request

## Initial Request — 2026-09-14T10:35:34Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: [none — teamwork routes from the description]

Build a free, CLI-based AI chatbot that ingests a Facebook messages JSON file to precisely mimic the personality, conversation style, and response length of the target person ("An An") in the chat logs.

Working directory: C:/Users/HKQL2/Documents/ExBuild
Integrity mode: development

## Requirements

### R1. Persona Mimicry
The chatbot must analyze the provided Facebook JSON data to extract and reflect the target person ("An An")'s habits, likes, dislikes, humor, and talking style.

### R2. Dynamic Response Length
The AI must not default to long-winded AI explanations; response length (short or long) must dynamically match the context of the incoming message and the learned persona.

### R3. Zero-Cost Architecture
The entire system must be built using completely free tools, libraries, or models (specifically leveraging free-tier cloud APIs, requiring API keys but no paid subscriptions). The system should read the necessary API keys from environment variables.

### R4. Framework (LangChain)
Use the LangChain Python framework to build the core conversation logic, memory, and persona ingestion. (A Python virtual environment with LangChain is pre-installed in the working directory).

### R5. Interface
The primary interface must be a CLI chat.

## Verification Resources
* Sample Facebook JSON data for testing: F:/dowload/FacebookData/messages/An An_86.json

## Acceptance Criteria

### Verification & Persona Matching
- [ ] An automated test suite exists that feeds the sample JSON into the system.
- [ ] An "Agent-as-Judge" evaluation script automatically prompts a secondary LLM to compare the chatbot's responses against the target persona ("An An") in the sample JSON, outputting a clear pass/fail score on persona match (including humor, habits, and dynamic response length).
- [ ] The chatbot passes the Agent-as-Judge evaluation on at least 3 distinct simulated conversations.

### Core Functionality
- [ ] The system can be launched from the CLI via a single command (using the `venv` provided).
- [ ] The chatbot accurately parses the Facebook JSON format without crashing.
- [ ] The solution exclusively relies on free-tier cloud APIs (no paid services required).

---
*Next: when approved → delegate via invoke_subagent (see Delegation Protocol)*

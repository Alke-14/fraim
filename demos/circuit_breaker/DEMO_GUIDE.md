# Quota Circuit Breaker & Resilient Error Handling — Demo Guide

This guide walks through how to demonstrate the **Quota Circuit Breaker** and **Rich Diagnostic Display** enhancements for your presentation.

---

## 1. Quick Pre-Demo Dry-Run Checklist

Run this quick sequence before your presentation to ensure your local environment is 100% ready:

- [ ] **Step 1: Check Python environment & dependencies**
  ```bash
  uv sync --python 3.12 --all-groups
  ```
- [ ] **Step 2: Run all circuit breaker unit tests**
  ```bash
  uv run pytest fraim/core/utils/retry/tests/test_http.py fraim/core/llms/tests/test_litellm.py fraim/cli/commands/tests/test_run.py
  ```
  *(Expected: 137 passed in ~7s)*
- [ ] **Step 3: Test legacy baseline simulation**
  ```bash
  uv run python demos/circuit_breaker/demo_circuit_breaker.py --legacy
  ```
  *(Expected: Retry warnings, terminal pause, and raw stack trace)*
- [ ] **Step 4: Test new resilient circuit breaker**
  ```bash
  uv run python demos/circuit_breaker/demo_circuit_breaker.py
  ```
  *(Expected: Immediate cutoff on Call 1, clean Rich panel, exit code 1)*
- [ ] **Step 5: Verify linters and typecheckers pass**
  ```bash
  make format-check && make lint-fix-check && make typecheck
  ```
  *(Expected: All checks passed, 0 mypy issues)*

---

## 2. Presentation Flow & Script

> *"In our Milestone 1 trials with Fraim and Google Gemini on Google AI Studio, exceeding quota limits or hitting billing exhaustion caused Fraim's underlying LiteLLM engine to enter an unhandled 5-retry loop with exponential backoff.*
> 
> *This froze the terminal for minutes on errors that could never succeed on retry, before crashing with a messy, uninformative 40-line Python stack trace.*
> 
> *To solve this for Milestone 2 (Criteria 3.2: Enhancing existing features), we implemented a **Quota Circuit Breaker** and a **Clean Rich Diagnostic Banner** that stops retries on attempt #1, displays actionable troubleshooting steps, and exits with a clean non-zero exit code (`1`) so automated CI/CD runners do not lock up."*

---

## 3. Live Demo Steps

### Demo Part 1: Demonstrate the Old Baseline Behavior (The Problem)

Run the legacy baseline simulation:
```bash
uv run python demos/circuit_breaker/demo_circuit_breaker.py --legacy
```

#### What happens on screen:
1. The script simulates the old Tenacity retry policy:
   ```text
   [WARNING] Attempt 1 failed: HTTP 429 RateLimitError (quota exceeded). Retrying in 2s...
   [WARNING] Attempt 2 failed: HTTP 429 RateLimitError (quota exceeded). Retrying in 4s...
   [WARNING] Attempt 3 failed: HTTP 429 RateLimitError (quota exceeded). Retrying in 8s...
   ```
2. The terminal freezes while waiting on exponential delays.
3. It crashes with an unhandled Python traceback:
   ```text
   Traceback (most recent call last):
     File "demos/circuit_breaker/demo_circuit_breaker.py", line 55, in simulate_legacy_behavior
       raise le.RateLimitError(...)
   litellm.exceptions.RateLimitError: litellm.RateLimitError: Resource has been exhausted (e.g. check quota)...
   ```
4. **Key talking point**: In continuous integration (CI/CD) pipelines, this locks runner queues and leaves developers wondering whether their code failed, the network glitched, or their billing account ran out of credits.

---

### Demo Part 2: Demonstrate the New Enhancement (The Solution)

Run the enhanced circuit breaker:
```bash
uv run python demos/circuit_breaker/demo_circuit_breaker.py
```

#### What happens on screen:
1. The request detects the quota ceiling on **Call Count: 1** (0 wasted retries).
2. It breaks execution immediately and outputs a styled **Rich Diagnostic Panel**:
   ```text
   ╭───────────────────────────── ✖ Execution Halted ─────────────────────────────╮
   │ AI Provider Quota / Billing Cap Reached                                      │
   │                                                                              │
   │ • Provider: gemini                                                           │
   │ • Model: gemini/gemini-flash-latest                                          │
   │ • Details: litellm.RateLimitError: Resource has been exhausted (e.g. check   │
   │ quota). Quota exceeded for quota metric 'Queries per day'                    │
   │                                                                              │
   │ Actionable Next Steps:                                                       │
   │   1. Check your account billing dashboard or increase your credit limits.    │
   │   2. Switch to an available alternative model via --model (e.g., --model     │
   │ gemini/gemini-flash-latest).                                                 │
   │   3. Retry once the usage window resets or contact your provider             │
   │ administrator.                                                               │
   ╰──────────────────────────────────────────────────────────────────────────────╯
   Process exited cleanly with status code 1. CI/CD pipeline does not freeze.
   ```
3. Exits with clean code `1` (fail-closed, no hanging builds, zero stack traces).

---

## 4. Verifying with Automated Tests (TDD Proof)

To show the professor that this was developed following Test-Driven Development (TDD) principles and does not break existing features:

### Run the targeted tests for this feature:
```bash
uv run pytest fraim/core/utils/retry/tests/test_http.py fraim/core/llms/tests/test_litellm.py fraim/cli/commands/tests/test_run.py
```
*(All 137 tests pass in under 8 seconds).*

### Run the complete repository test suite:
```bash
uv run pytest
```
*(All 466 tests pass across the entire codebase).*

### Run static type checking and linters:
```bash
make format-check && make lint-fix-check && make typecheck
```
*(Confirms 0 type issues across 131 source files and 100% compliant formatting).*

---

## 5. Code Architecture Summary (If Asked "How does it work?")

| Component | File | Responsibility |
| :--- | :--- | :--- |
| **Quota Classifier** | [`fraim/core/utils/retry/http.py`](file:///home/alke/Documents/repository/fraim/fraim/core/utils/retry/http.py) | Inspects exception codes/messages (`RESOURCE_EXHAUSTED`, `insufficient_quota`, `credit_balance_too_low`). Marks them as non-retriable so Tenacity aborts on attempt #1. |
| **Circuit Breaker** | [`fraim/core/llms/litellm.py`](file:///home/alke/Documents/repository/fraim/fraim/core/llms/litellm.py) | Wraps completion calls; catches quota exhaustion and raises structured `AIUsageCapError`. Lowers default retry ceiling to 2. |
| **Domain Exception** | [`fraim/core/llms/exceptions.py`](file:///home/alke/Documents/repository/fraim/fraim/core/llms/exceptions.py) | Encapsulates provider name, model identifier, and raw error message for downstream consumers (CLI banner or teammate's fallback router). |
| **CLI Diagnostic UI** | [`fraim/cli/commands/run.py`](file:///home/alke/Documents/repository/fraim/fraim/cli/commands/run.py) | Intercepts `AIUsageCapError`, renders the styled Rich panel to stderr, and exits with code 1. |

---

## 6. Summary Presentation Quick-Card

| Step | Command | Focus / Key Takeaway |
| :--- | :--- | :--- |
| **1. The Problem** | `uv run python demos/circuit_breaker/demo_circuit_breaker.py --legacy` | Demonstrates the terminal stall & raw traceback from Milestone 1. |
| **2. The Solution** | `uv run python demos/circuit_breaker/demo_circuit_breaker.py` | Shows instant circuit break, 0 retries, and formatted Rich UI. |
| **3. TDD Proof** | `uv run pytest fraim/cli/commands/tests/test_run.py` | Shows automated test coverage verifying exit code 1 and banner. |
| **4. Full Health Check** | `make check` | Proves no regressions in formatting, types, or tests across Fraim. |

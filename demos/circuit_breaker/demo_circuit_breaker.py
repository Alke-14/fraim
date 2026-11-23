# SPDX-License-Identifier: MIT
"""Demo script comparing Fraim's original behavior vs. our Quota Circuit Breaker.

Usage:
    # 1. Run the new, resilient Circuit Breaker behavior (clean panel, terminates immediately)
    uv run python demos/circuit_breaker/demo_circuit_breaker.py

    # 2. Simulate the old, unhandled behavior (terminal stall / raw Python traceback)
    uv run python demos/circuit_breaker/demo_circuit_breaker.py --legacy
"""

import sys
import time
from unittest.mock import patch

import litellm.exceptions as le

from fraim.cli.commands.run import _display_quota_cap_error
from fraim.core.history import History
from fraim.core.llms import LiteLLM
from fraim.core.llms.exceptions import AIUsageCapError
from fraim.core.messages import UserMessage


def simulate_legacy_behavior():
    """Simulates the old baseline behavior documented in Milestone 1 & 2:
    LiteLLM retrying multiple times on quota exhaustion, locking the terminal,
    and finally crashing with a raw traceback.
    """
    print("\n" + "=" * 70)
    print("▶ SIMULATING OLD BASELINE BEHAVIOR (Without Circuit Breaker)")
    print("=" * 70)
    print("Sending code diff to model with 5 retries and exponential backoff...")

    # In legacy Fraim: max_retries was 5, and 429 quota exhaustion was treated as retriable
    simulated_quota_error = le.RateLimitError(
        message="Resource has been exhausted (e.g. check quota). Quota exceeded for quota metric 'Queries per day'",
        llm_provider="gemini",
        model="gemini/gemini-flash-latest",
    )

    attempts = 0
    start_time = time.time()

    # Simulate the old Tenacity retry loop on the terminal
    for attempt in range(1, 4):
        attempts += 1
        print(
            f"[{time.strftime('%X')}] [WARNING] Attempt {attempt} failed: HTTP 429 RateLimitError (quota exceeded). Retrying in {2**attempt}s..."
        )
        time.sleep(1.0)  # Brief pause to simulate the terminal stall

    print(f"[{time.strftime('%X')}] [ERROR] All retry attempts exhausted after {time.time() - start_time:.1f}s.")
    print("Crashing with unhandled exception:\n")
    time.sleep(0.5)

    # Dump the messy raw traceback to stderr that users used to see
    raise le.RateLimitError(
        message="Resource has been exhausted (e.g. check quota). Quota exceeded for quota metric 'Queries per day'",
        llm_provider="gemini",
        model="gemini/gemini-flash-latest",
    )


async def run_resilient_circuit_breaker():
    """Demonstrates our new Circuit Breaker enhancement:
    1. Intercepts the quota cap on attempt #1.
    2. Zero wasted retries (stops immediately).
    3. Displays the structured Rich diagnostic panel with actionable steps.
    4. Exits with clean status code 1.
    """
    print("\n" + "=" * 70)
    print("▶ RUNNING NEW ENHANCEMENT: QUOTA CIRCUIT BREAKER & RICH DISPLAY")
    print("=" * 70)
    print("Initiating scan with Google Gemini (simulating quota/billing limit reached)...")

    llm = LiteLLM(model="gemini/gemini-flash-latest", max_retries=2)
    messages = [UserMessage(content="Review this authentication diff for vulnerabilities.")]

    simulated_quota_error = le.RateLimitError(
        message="Resource has been exhausted (e.g. check quota). Quota exceeded for quota metric 'Queries per day'",
        llm_provider="gemini",
        model="gemini/gemini-flash-latest",
    )

    with patch("litellm.acompletion", side_effect=simulated_quota_error) as mock_acompletion:
        try:
            await llm.run(History(), messages)
        except AIUsageCapError as err:
            print(
                f"\n[Circuit Breaker Triggered] LiteLLM call count: {mock_acompletion.call_count} (Immediate cutoff, 0 retries)"
            )
            print("Rendering clean user diagnostic banner:\n")
            _display_quota_cap_error(err)
            print("Process exited cleanly with status code 1. CI/CD pipeline does not freeze.\n")
            return 1
    return 0


if __name__ == "__main__":
    if "--legacy" in sys.argv:
        try:
            simulate_legacy_behavior()
        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)
    else:
        import asyncio

        sys.exit(asyncio.run(run_resilient_circuit_breaker()))

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Resourcely Inc.

"""Tests for CLI run command error handling and display"""

from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from fraim.cli.app import app
from fraim.core.llms.exceptions import AIUsageCapError

runner = CliRunner()


def test_ai_usage_cap_error_display_in_run() -> None:
    """When a workflow raises AIUsageCapError, CLI should display a diagnostic panel and exit with code 1."""
    cap_error = AIUsageCapError(
        message="Your credit balance is too low to access the Claude API.",
        provider="anthropic",
        model="anthropic/claude-sonnet-4-0",
    )

    with patch("fraim.workflows.code.workflow.SASTWorkflow.run", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = cap_error
        result = runner.invoke(app, ["run", "code", "--model", "gemini/gemini-flash-latest", "--location", "."])

        assert result.exit_code == 1
        # Check that rich diagnostic banner is rendered
        assert "AI Provider Quota / Billing Cap Reached" in result.output
        assert "anthropic" in result.output
        assert "credit balance is too low" in result.output
        assert "Check your account billing dashboard" in result.output
        # Ensure no raw python traceback is displayed
        assert "Traceback (most recent call last)" not in result.output

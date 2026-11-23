# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Resourcely Inc.

"""Custom exceptions for LLM interactions"""


class AIUsageCapError(Exception):
    """Exception raised when an AI provider's usage quota, budget, or billing limit is exhausted."""

    def __init__(self, message: str, provider: str = "", model: str = "", details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.model = model
        self.details = details or message

    def __str__(self) -> str:
        prov = f" [{self.provider}]" if self.provider else ""
        mod = f" (model: {self.model})" if self.model else ""
        return f"AI Usage Cap Exceeded{prov}{mod}: {self.message}"

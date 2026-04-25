"""Cost ceiling enforcer."""
from __future__ import annotations
from dataclasses import dataclass


# Approximate per-million-token USD prices (April 2026 estimates; user can override).
PRICES = {
    # model         (input, output)  USD per 1M tokens
    "gpt-4o-mini":   (0.15, 0.60),
    "gpt-5-mini":    (0.30, 1.20),
    "claude-sonnet-4.7": (3.00, 15.00),
    "mock":          (0.00, 0.00),
}


def estimate_cost(model: str, in_tokens: int, out_tokens: int) -> float:
    pin, pout = PRICES.get(model, (1.0, 3.0))
    return (in_tokens / 1_000_000) * pin + (out_tokens / 1_000_000) * pout


@dataclass
class CostCap:
    cap_usd: float
    spent_usd: float = 0.0

    def add(self, cost: float) -> None:
        self.spent_usd += cost

    @property
    def exceeded(self) -> bool:
        return self.spent_usd >= self.cap_usd

    @property
    def remaining(self) -> float:
        return max(0.0, self.cap_usd - self.spent_usd)

"""Adaptive protection policy selection."""

from dataclasses import dataclass
from enum import IntEnum

from .scoring import SecurityRiskLevel, SecurityScore


class ProtectionLevel(IntEnum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4


@dataclass(frozen=True)
class SecurityPolicy:
    block_id: str
    security_score: float
    risk_level: SecurityRiskLevel
    selected_protection_level: ProtectionLevel
    reason: str
    estimated_relative_cost: float


def select_policy(score: SecurityScore) -> SecurityPolicy:
    """Map risk classifications to deterministic protection levels."""
    level = {
        SecurityRiskLevel.LOW: ProtectionLevel.LEVEL_1,
        SecurityRiskLevel.MEDIUM: ProtectionLevel.LEVEL_2,
        SecurityRiskLevel.HIGH: ProtectionLevel.LEVEL_3,
        SecurityRiskLevel.CRITICAL: ProtectionLevel.LEVEL_4,
    }[score.risk_level]
    return SecurityPolicy(
        score.block_id,
        score.score,
        score.risk_level,
        level,
        f"{score.risk_level.value.lower()} risk; {score.explanation}",
        round(level / 4, 2),
    )

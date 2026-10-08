"""Explainable deterministic security risk scoring."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from .features import SecurityFeatures


class SecurityRiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class SecurityScore:
    block_id: str
    score: float
    risk_level: SecurityRiskLevel
    factor_contributions: Dict[str, float]
    explanation: str


def score_features(features: SecurityFeatures) -> SecurityScore:
    """Score a block using fixed, documented weights in the [0, 1] range."""
    factors = {
        "control_flow": features.control_flow_complexity * 0.30,
        "branch_density": min(1.0, features.branch_count / max(features.instruction_count, 1)) * 0.20,
        "loop": (0.15 if features.loop_participation else 0.0),
        "operations": min(
            1.0,
            (features.arithmetic_operation_count + features.comparison_count)
            / max(features.instruction_count, 1),
        ) * 0.20,
        "operands": features.operand_sensitivity * 0.10,
        "connectivity": min(1.0, (features.predecessor_count + features.successor_count) / 4) * 0.05,
    }
    score = round(min(1.0, sum(factors.values())), 6)
    if score >= 0.80:
        level = SecurityRiskLevel.CRITICAL
    elif score >= 0.60:
        level = SecurityRiskLevel.HIGH
    elif score >= 0.30:
        level = SecurityRiskLevel.MEDIUM
    else:
        level = SecurityRiskLevel.LOW
    active = [name for name, value in factors.items() if value > 0]
    explanation = "risk factors: " + (", ".join(active) if active else "none")
    return SecurityScore(features.block_id, score, level, factors, explanation)

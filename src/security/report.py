"""Human-readable security analysis reporting."""

from typing import Iterable, List

from .features import SecurityFeatures
from .policy import SecurityPolicy
from .scoring import SecurityScore


def format_report(
    features: Iterable[SecurityFeatures],
    scores: Iterable[SecurityScore],
    policies: Iterable[SecurityPolicy],
) -> str:
    score_map = {score.block_id: score for score in scores}
    policy_map = {policy.block_id: policy for policy in policies}
    feature_list = list(features)
    lines = [
        "SECURITY ANALYSIS REPORT",
        "Transformation: identity (no obfuscation applied)",
        f"Total blocks: {len(feature_list)}",
        "",
    ]
    for feature in feature_list:
        score = score_map[feature.block_id]
        policy = policy_map[feature.block_id]
        lines.extend(
            [
                f"Block {feature.block_id}",
                f"  Instructions: {feature.instruction_count}",
                f"  Branches: {feature.branch_count}",
                f"  Complexity: {feature.control_flow_complexity:.3f}",
                f"  Sensitivity: {feature.operand_sensitivity:.3f}",
                f"  Score: {score.score:.3f}",
                f"  Risk: {score.risk_level.value}",
                f"  Protection: LEVEL_{policy.selected_protection_level}",
                f"  Reason: {policy.reason}",
                "",
            ]
        )
    return "\n".join(lines)

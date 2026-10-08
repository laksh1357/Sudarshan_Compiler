"""Configuration for the optional Sudarshan security subsystem."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityConfig:
    """Controls which security capabilities are requested for a compilation."""

    enabled: bool = False
    adaptive: bool = False
    structural_protection: bool = False
    control_flow_protection: bool = False
    operand_protection: bool = False
    integrity_protection: bool = False

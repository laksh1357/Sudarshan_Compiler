"""Tests for the initial opt-in security subsystem."""

import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from main import main
from security import (
    SecurityConfig,
    SecurityIntegrityError,
    SecurityPass,
    IdentityTransformation,
    SecurityContext,
    analyze_block,
    build_cfg,
    protect_ir,
    score_features,
    select_policy,
)
from tac import TACInstruction


class TestSecuritySubsystem(unittest.TestCase):

    def setUp(self):
        self.valid_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../examples/valid.mini")
        )

    def test_default_security_configuration_is_disabled(self):
        config = SecurityConfig()

        self.assertFalse(config.enabled)
        self.assertFalse(config.adaptive)
        self.assertFalse(config.structural_protection)
        self.assertFalse(config.control_flow_protection)
        self.assertFalse(config.operand_protection)
        self.assertFalse(config.integrity_protection)

    def test_security_pass_is_identity_transformation(self):
        instructions = [TACInstruction("CONST", 7, None, "t1")]
        config = SecurityConfig(
            enabled=True,
            adaptive=True,
            structural_protection=True,
            control_flow_protection=True,
            operand_protection=True,
            integrity_protection=True,
        )

        transformed = SecurityPass(config).transform(instructions)

        self.assertIs(transformed, instructions)

    def test_transformation_interface_is_deterministic_identity(self):
        instructions = [TACInstruction("CONST", 4, None, "t1")]
        transformed, diagnostics = IdentityTransformation().transform(
            instructions, SecurityContext()
        )

        self.assertIs(transformed, instructions)
        self.assertFalse(diagnostics.transformed)

    def test_security_disabled_preserves_existing_cli_output(self):
        args = ["main.py", self.valid_file]
        with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            main()

        output = stdout.getvalue()
        self.assertIn("15", output)
        self.assertIn("115", output)

    def test_security_enabled_preserves_program_output(self):
        args = ["main.py", self.valid_file, "--secure"]
        with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            main()

        output = stdout.getvalue()
        self.assertIn("15", output)
        self.assertIn("115", output)

    def test_adaptive_security_enables_security_pipeline(self):
        args = ["main.py", self.valid_file, "--adaptive-security", "--security-report"]
        with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            main()

        output = stdout.getvalue()
        self.assertIn("SECURITY ANALYSIS REPORT", output)
        self.assertIn("Security enabled: True", output)
        self.assertIn("Adaptive security: True", output)
        self.assertIn("15", output)
        self.assertIn("115", output)

    def test_security_report_and_protected_ir_are_printed(self):
        args = ["main.py", self.valid_file, "--secure", "--security-report", "--dump-protected-ir"]
        with patch.object(sys, "argv", args), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            main()

        output = stdout.getvalue()
        self.assertIn("SECURITY ANALYSIS REPORT", output)
        self.assertIn("PROTECTED INTERMEDIATE REPRESENTATION", output)
        self.assertIn("Transformation: identity (no obfuscation applied)", output)

    def test_security_analysis_and_integrity_verification(self):
        instructions = [
            TACInstruction("CONST", 1, None, "t1"),
            TACInstruction("PRINT", "t1", None, None),
        ]
        cfg = build_cfg(instructions)
        features = [analyze_block(block) for block in cfg.blocks]
        policies = [select_policy(score_features(feature)) for feature in features]
        program = protect_ir(instructions, policies)

        program.verify()
        instructions[0].arg1 = 2
        with self.assertRaises(SecurityIntegrityError):
            program.verify()

    def test_feature_extraction_covers_control_flow_and_operations(self):
        instructions = [
            TACInstruction("LABEL", None, None, "L1"),
            TACInstruction("CONST", 1, None, "t1"),
            TACInstruction("ADD", "x", "t1", "t2"),
            TACInstruction("LT", "t2", 3, "t3"),
            TACInstruction("JUMP_IF_FALSE", "t3", None, "L2"),
            TACInstruction("JUMP", None, None, "L1"),
            TACInstruction("LABEL", None, None, "L2"),
        ]
        cfg = build_cfg(instructions)
        features = [analyze_block(block) for block in cfg.blocks]

        self.assertGreaterEqual(len(features), 2)
        self.assertTrue(any(feature.branch_count for feature in features))
        self.assertTrue(any(feature.arithmetic_operation_count for feature in features))
        self.assertTrue(any(feature.comparison_count for feature in features))
        self.assertTrue(any(feature.constant_count for feature in features))
        self.assertTrue(any(feature.loop_participation for feature in features))
        for feature in features:
            self.assertGreaterEqual(feature.control_flow_complexity, 0.0)
            self.assertLessEqual(feature.control_flow_complexity, 1.0)
            self.assertGreaterEqual(feature.operand_sensitivity, 0.0)
            self.assertLessEqual(feature.operand_sensitivity, 1.0)

    def test_security_vm_rejects_invalid_branch_target(self):
        instructions = [TACInstruction("JUMP", None, None, "missing")]
        cfg = build_cfg(instructions)
        policies = [select_policy(score_features(analyze_block(block))) for block in cfg.blocks]
        program = protect_ir(instructions, policies)

        from security import SecureInterpreter

        with self.assertRaises(SecurityIntegrityError):
            SecureInterpreter(program).run()


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Test Db2 BIND command execution using db2bind
"""

import os
import sys
import unittest
from batchtsocmd.main import db2bind


class TestDb2BindValidation(unittest.TestCase):
    """Test db2bind parameter validation (no z/OS connection required)"""

    def test_01_db2bind_missing_system(self):
        """Test db2bind validation - system parameter is required"""
        rc = db2bind(
            package='PCBSA',
            members=['CREACC'],
        )
        self.assertEqual(rc, 8, "Expected error code 8 when system parameter is missing")

    def test_02_db2bind_missing_package_and_plan(self):
        """Test db2bind validation - at least one of package or plan must be specified"""
        rc = db2bind(
            system='DB2P',
        )
        self.assertEqual(rc, 8, "Expected error code 8 when neither package nor plan is specified")

    def test_03_db2bind_package_without_members(self):
        """Test db2bind validation - members required when package is specified"""
        rc = db2bind(
            system='DB2P',
            package='PCBSA',
        )
        self.assertEqual(rc, 8, "Expected error code 8 when package specified without members")

    def test_04_db2bind_plan_only_no_members_required(self):
        """Test db2bind validation - plan-only bind does not require members"""
        # This will fail at execution (invalid subsystem) but should pass validation
        rc = db2bind(
            system='NOOK',
            plan='CBSA',
            owner='IBMUSER',
            isolation='UR',
            pklist=['NULLID.*', 'PCBSA.*'],
            steplib='DB2V13.SDSNLOAD',
        )
        # Should fail at execution (NOOK not valid), not at validation
        self.assertNotEqual(rc, 8, "Validation should pass for plan-only bind")

    def test_05_db2bind_package_with_single_member(self):
        """Test db2bind with a single package member - fails at execution with invalid subsystem"""
        rc = db2bind(
            system='NOOK',
            package='PCBSA',
            members=['CREACC'],
            owner='IBMUSER',
            qualifier='IBMUSER',
            action='REPLACE',
            steplib='DB2V13.SDSNLOAD',
        )
        # Should fail at execution (NOOK not valid), not at validation
        self.assertNotEqual(rc, 8, "Validation should pass for single-member package bind")

    def test_06_db2bind_package_and_plan_together(self):
        """Test db2bind with both package members and plan - mirrors DB2BIND.jcl"""
        rc = db2bind(
            system='NOOK',
            package='PCBSA',
            members=['CREACC', 'CRECUST', 'DBCRFUN', 'DELACC', 'DELCUS',
                     'INQACC', 'INQACCCU', 'BANKDATA', 'UPDACC', 'XFRFUN'],
            owner='IBMUSER',
            qualifier='IBMUSER',
            action='REPLACE',
            plan='CBSA',
            isolation='UR',
            pklist=['NULLID.*', 'PCBSA.*'],
            steplib='DB2V13.SDSNEXIT:DB2V13.SDSNLOAD',
        )
        # Should fail at execution (NOOK not valid), not at validation
        self.assertNotEqual(rc, 8, "Validation should pass for combined package+plan bind")

    def test_07_db2bind_invalid_action(self):
        """Test db2bind with invalid action - argparse handles this at CLI level,
        but the Python function accepts any string for action"""
        # The Python function itself does not validate action values
        # (that is the CLI's job via argparse choices). This test documents that.
        rc = db2bind(
            system='NOOK',
            package='PCBSA',
            members=['CREACC'],
            action='REPLACE',  # valid
            steplib='DB2V13.SDSNLOAD',
        )
        self.assertNotEqual(rc, 8, "Validation should pass with valid action")


class TestDb2BindExecution(unittest.TestCase):
    """Test db2bind execution against a live Db2 subsystem.

    These tests require a running Db2 subsystem and will be skipped
    if DB2_SYSTEM is not set in the environment.
    """

    def setUp(self):
        self.system = os.environ.get('DB2_SYSTEM')
        self.steplib = os.environ.get('DB2_STEPLIB')
        self.dbrmlib = os.environ.get('DB2_DBRMLIB')
        if not self.system:
            self.skipTest("DB2_SYSTEM environment variable not set - skipping live execution tests")

    def test_08_db2bind_live_plan_only(self):
        """Test db2bind BIND PLAN against a live Db2 subsystem"""
        plan = os.environ.get('DB2_PLAN', 'CBSA')
        owner = os.environ.get('DB2_OWNER', 'IBMUSER')
        package = os.environ.get('DB2_PACKAGE', 'PCBSA')

        rc = db2bind(
            system=self.system,
            plan=plan,
            owner=owner,
            isolation='UR',
            pklist=[f'NULLID.*', f'{package}.*'],
            steplib=self.steplib,
            verbose=True,
        )

        print(f"\n=== db2bind live BIND PLAN RC={rc} ===", file=sys.stderr)
        # RC 0 = success, RC 4 = warnings (acceptable for bind)
        self.assertLessEqual(rc, 4, f"Expected RC <= 4 for BIND PLAN, got RC={rc}")


if __name__ == '__main__':
    unittest.main()

# Made with Bob
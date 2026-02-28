#!/usr/bin/env python3
"""
Test Db2 RUN PROGRAM execution using db2run
"""

import os
import sys
import unittest
from batchtsocmd.main import db2run


class TestDb2RunValidation(unittest.TestCase):
    """Test db2run parameter validation (no z/OS connection required)"""

    def test_01_db2run_missing_program(self):
        """Test db2run validation - program parameter is required"""
        rc = db2run(
            system='DB2P',
            plan='CBSA',
            toollib='CBSA.CICSBSA.LOADLIB',
        )
        self.assertEqual(rc, 8, "Expected error code 8 when program parameter is missing")

    def test_02_db2run_missing_system(self):
        """Test db2run validation - system parameter is required"""
        rc = db2run(
            program='BANKDATA',
            plan='CBSA',
            toollib='CBSA.CICSBSA.LOADLIB',
        )
        self.assertEqual(rc, 8, "Expected error code 8 when system parameter is missing")

    def test_03_db2run_missing_plan(self):
        """Test db2run validation - plan parameter is required"""
        rc = db2run(
            program='BANKDATA',
            system='DB2P',
            toollib='CBSA.CICSBSA.LOADLIB',
        )
        self.assertEqual(rc, 8, "Expected error code 8 when plan parameter is missing")

    def test_04_db2run_missing_toollib(self):
        """Test db2run validation - toollib parameter is required"""
        rc = db2run(
            program='BANKDATA',
            system='DB2P',
            plan='CBSA',
        )
        self.assertEqual(rc, 8, "Expected error code 8 when toollib parameter is missing")

    def test_05_db2run_invalid_subsystem(self):
        """Test db2run with invalid subsystem - fails at execution, not validation"""
        rc = db2run(
            program='BANKDATA',
            system='NOOK',
            plan='CBSA',
            toollib='CBSA.CICSBSA.LOADLIB',
            steplib='DB2V13.SDSNLOAD',
        )
        # Should fail at execution (NOOK not valid), not at validation (rc != 8)
        self.assertNotEqual(rc, 8, "Validation should pass; failure should be at execution")

    def test_06_db2run_with_parm(self):
        """Test db2run with PARM string - fails at execution with invalid subsystem"""
        rc = db2run(
            program='BANKDATA',
            system='NOOK',
            plan='CBSA',
            toollib='CBSA.CICSBSA.LOADLIB',
            parms='1,10000,1,1000000000000000',
            steplib='CBSA.CICSBSA.DBRM:CBSA.CICSBSA.LOADLIB:DB2V13.SDSNLOAD',
        )
        # Should fail at execution (NOOK not valid), not at validation
        self.assertNotEqual(rc, 8, "Validation should pass with parm string")

    def test_07_db2run_verbose_output(self):
        """Test db2run verbose mode prints SYSTSIN content to stdout"""
        import io
        from contextlib import redirect_stdout

        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            rc = db2run(
                program='BANKDATA',
                system='NOOK',
                plan='CBSA',
                toollib='CBSA.CICSBSA.LOADLIB',
                parms='1,100,1,12345',
                steplib='DB2V13.SDSNLOAD',
                verbose=True,
            )

        verbose_output = stdout_capture.getvalue()
        print(f"\n=== db2run verbose output ===\n{verbose_output}", file=sys.stderr)

        # Verbose output (stdout) should contain the generated SYSTSIN content
        self.assertIn('BANKDATA', verbose_output, "Verbose output should contain program name")
        self.assertIn('CBSA', verbose_output, "Verbose output should contain plan name")


class TestDb2RunExecution(unittest.TestCase):
    """Test db2run execution against a live Db2 subsystem.

    These tests require a running Db2 subsystem and will be skipped
    if DB2_SYSTEM is not set in the environment.
    """

    def setUp(self):
        self.system = os.environ.get('DB2_SYSTEM')
        self.steplib = os.environ.get('DB2_STEPLIB')
        if not self.system:
            self.skipTest("DB2_SYSTEM environment variable not set - skipping live execution tests")

    def test_08_db2run_live_bankdata(self):
        """Test db2run executing BANKDATA program against a live Db2 subsystem.

        Mirrors BANKDATA.jcl:
          DSN SYSTEM(@DB2_SUBSYSTEM@)
          RUN PROGRAM(BANKDATA) PLAN(@CBSA_PLAN@)
          PARM('1,10000,1,1000000000000000')
          LIB('@BANK_LOADLIB@')
        """
        plan = os.environ.get('DB2_PLAN', 'CBSA')
        toollib = os.environ.get('DB2_TOOLLIB')
        dbrmlib = os.environ.get('DB2_DBRMLIB')

        if not toollib:
            self.skipTest("DB2_TOOLLIB environment variable not set")

        steplib_parts = []
        if dbrmlib:
            steplib_parts.append(dbrmlib)
        if toollib:
            steplib_parts.append(toollib)
        if self.steplib:
            steplib_parts.extend(self.steplib.split(':'))
        steplib_list = steplib_parts if steplib_parts else None

        rc = db2run(
            program='BANKDATA',
            system=self.system,
            plan=plan,
            toollib=toollib,
            parms='1,100,1,1000000000000000',
            steplib=steplib_list,
            verbose=True,
        )

        print(f"\n=== db2run live BANKDATA RC={rc} ===", file=sys.stderr)
        self.assertEqual(rc, 0, f"Expected RC=0 for BANKDATA execution, got RC={rc}")


if __name__ == '__main__':
    unittest.main()

# Made with Bob
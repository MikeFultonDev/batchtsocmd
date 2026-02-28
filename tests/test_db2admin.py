#!/usr/bin/env python3
"""
Test Db2 operator command execution using db2op
"""

import os
import sys
import tempfile
import unittest
from batchtsocmd.main import db2op, db2admin  # db2admin kept for backward-compat


class TestDb2OpFunction(unittest.TestCase):
    """Test db2op function (replaces db2admin)"""

    def test_01_db2op_with_file(self):
        """Test db2op function with sysin_file parameter"""
        sysin_path = None
        sysprint_path = None
        systsprt_path = None
        
        try:
            # SYSIN content - DB2 administrative commands
            sysin_content = """-DISPLAY DATABASE(*)
"""
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysin', delete=False) as sysin:
                sysin.write(sysin_content)
                sysin_path = sysin.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysprint', delete=False) as sysprint:
                sysprint_path = sysprint.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt:
                systsprt_path = systsprt.name
            
            # Run db2op with file
            rc = db2op(
                sysin_file=sysin_path,
                system='NOOK',
                plan='DSNTIAD',
                toollib='DSNC10.DBCG.RUNLIB.LOAD',
                sysprint_file=sysprint_path,
                systsprt_file=systsprt_path,
                steplib='DB2V13.SDSNLOAD',
                verbose=False
            )

            # Read output files
            with open(sysprint_path, 'r', encoding='ibm1047') as f:
                sysprint_output = f.read()

            with open(systsprt_path, 'r', encoding='ibm1047') as f:
                systsprt_output = f.read()

            # Print diagnostic information for verification
            print(f"\n=== db2op with file RC={rc} ===", file=sys.stderr)
            print(f"SYSPRINT:\n{sysprint_output}", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail with invalid subsystem)
            self.assertNotEqual(rc, 0, f"Expected DB2 admin command to fail with invalid subsystem, but got RC={rc}")
            
            # Verify SYSTSPRT contains the expected error message
            expected_error = "NOOK NOT VALID SUBSYSTEM ID, COMMAND TERMINATED"
            self.assertIn(
                expected_error,
                systsprt_output,
                f"Expected error message '{expected_error}' in SYSTSPRT, but got: {systsprt_output}"
            )
            
        finally:
            # Clean up temporary files
            for path in [sysin_path, sysprint_path, systsprt_path]:
                if path and os.path.exists(path):
                    os.unlink(path)
    
    def test_02_db2op_with_content(self):
        """Test db2op function with sysin_content parameter"""
        sysprint_path = None
        systsprt_path = None
        
        try:
            # SYSIN content - DB2 administrative commands
            sysin_content = """-DISPLAY DATABASE(*)
"""
            
            # Create temporary output files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysprint', delete=False) as sysprint:
                sysprint_path = sysprint.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt:
                systsprt_path = systsprt.name
            
            # Run db2op with content string
            rc = db2op(
                sysin_content=sysin_content,
                system='NOOK',
                plan='DSNTIAD',
                toollib='DSNC10.DBCG.RUNLIB.LOAD',
                sysprint_file=sysprint_path,
                systsprt_file=systsprt_path,
                steplib='DB2V13.SDSNLOAD',
                verbose=False
            )

            # Read output files
            with open(sysprint_path, 'r', encoding='ibm1047') as f:
                sysprint_output = f.read()

            with open(systsprt_path, 'r', encoding='ibm1047') as f:
                systsprt_output = f.read()

            # Print diagnostic information for verification
            print(f"\n=== db2op with content RC={rc} ===", file=sys.stderr)
            print(f"SYSPRINT:\n{sysprint_output}", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail with invalid subsystem)
            self.assertNotEqual(rc, 0, f"Expected DB2 admin command to fail with invalid subsystem, but got RC={rc}")
            
            # Verify SYSTSPRT contains the expected error message
            expected_error = "NOOK NOT VALID SUBSYSTEM ID, COMMAND TERMINATED"
            self.assertIn(
                expected_error,
                systsprt_output,
                f"Expected error message '{expected_error}' in SYSTSPRT, but got: {systsprt_output}"
            )
            
        finally:
            # Clean up temporary files
            for path in [sysprint_path, systsprt_path]:
                if path and os.path.exists(path):
                    os.unlink(path)
    
    def test_03_db2op_validation_both_sysin(self):
        """Test db2op validation - cannot specify both sysin_content and sysin_file"""
        sysin_path = None

        try:
            # Create a temporary SYSIN file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysin', delete=False) as sysin:
                sysin.write("-DISPLAY DATABASE(*)")
                sysin_path = sysin.name

            # Try to call db2op with both parameters - should fail
            rc = db2op(
                sysin_content="-DISPLAY DATABASE(*)",
                sysin_file=sysin_path,
                system='DB2P',
                plan='DSNTIAD',
                toollib='DSNC10.DBCG.RUNLIB.LOAD'
            )

            # Should return error code 8
            self.assertEqual(rc, 8, "Expected error code 8 when both sysin_content and sysin_file are specified")

        finally:
            if sysin_path and os.path.exists(sysin_path):
                os.unlink(sysin_path)

    def test_04_db2op_validation_no_sysin(self):
        """Test db2op validation - must specify either sysin_content or sysin_file"""
        rc = db2op(
            system='DB2P',
            plan='DSNTIAD',
            toollib='DSNC10.DBCG.RUNLIB.LOAD'
        )

        # Should return error code 8
        self.assertEqual(rc, 8, "Expected error code 8 when neither sysin_content nor sysin_file are specified")

    def test_05_db2op_validation_missing_system(self):
        """Test db2op validation - system parameter is required"""
        rc = db2op(
            sysin_content="-DISPLAY DATABASE(*)",
            plan='DSNTIAD',
            toollib='DSNC10.DBCG.RUNLIB.LOAD'
        )

        # Should return error code 8
        self.assertEqual(rc, 8, "Expected error code 8 when system parameter is missing")

    def test_06_db2op_validation_missing_plan(self):
        """Test db2op validation - plan parameter is required"""
        rc = db2op(
            sysin_content="-DISPLAY DATABASE(*)",
            system='DB2P',
            toollib='DSNC10.DBCG.RUNLIB.LOAD'
        )

        # Should return error code 8
        self.assertEqual(rc, 8, "Expected error code 8 when plan parameter is missing")

    def test_07_db2op_validation_missing_toollib(self):
        """Test db2op validation - toollib parameter is required"""
        rc = db2op(
            sysin_content="-DISPLAY DATABASE(*)",
            system='DB2P',
            plan='DSNTIAD'
        )

        # Should return error code 8
        self.assertEqual(rc, 8, "Expected error code 8 when toollib parameter is missing")

    def test_08_db2op_with_stdout(self):
        """Test db2op with both outputs to stdout"""
        try:
            # SYSIN content - Db2 operator commands
            sysin_content = """-DISPLAY DATABASE(*)
"""

            # Capture stdout
            from io import StringIO
            captured_output = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured_output

            try:
                # Run db2op with both outputs to stdout
                rc = db2op(
                    sysin_content=sysin_content,
                    system='NOOK',
                    plan='DSNTIAD',
                    toollib='DSNC10.DBCG.RUNLIB.LOAD',
                    sysprint_file='stdout',
                    systsprt_file='stdout',
                    steplib='DB2V13.SDSNLOAD',
                    verbose=False
                )
            finally:
                sys.stdout = old_stdout

            combined_output = captured_output.getvalue()

            # Print diagnostic information for verification
            print(f"\n=== db2op with stdout RC={rc} ===", file=sys.stderr)
            print(f"Combined stdout output:\n{combined_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail with invalid subsystem)
            self.assertNotEqual(rc, 0, f"Expected DB2 admin command to fail with invalid subsystem, but got RC={rc}")
            
            # Verify the expected error message appears in output
            expected_error = "NOOK NOT VALID SUBSYSTEM ID, COMMAND TERMINATED"
            self.assertIn(
                expected_error,
                combined_output,
                f"Expected error message '{expected_error}' in combined stdout, but got: {combined_output}"
            )
            
        except Exception as e:
            self.fail(f"Test failed with exception: {e}")


if __name__ == '__main__':
    unittest.main()

# Made with Bob
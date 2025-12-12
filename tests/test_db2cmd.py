#!/usr/bin/env python3
"""
Test DB2 command execution using batchtsocmd
"""

import os
import sys
import tempfile
import unittest
from batchtsocmd.main import execute_tso_command


class TestDB2Commands(unittest.TestCase):
    """Test DB2 command execution via batchtsocmd"""
    
    def test_01_db2_invalid_subsystem_error(self):
        """Test DB2 command with invalid subsystem ID - expects failure.
        
        This test verifies that batchtsocmd properly handles an invalid DB2 subsystem
        and returns the expected error message in SYSTSPRT:
        'DSN SYSTEM(NOOK) NOOK NOT VALID SUBSYSTEM ID, COMMAND TERMINATED'
        
        This test mimics the JCL pattern:
        //SYSTSIN  DD  *
          DSN SYSTEM(NOOK)
          RUN PROGRAM(DSNTEP2) PLAN(DSNTEP12) -
               LIB('DSNC10.DBCG.RUNLIB.LOAD') PARMS('/ALIGN(MID)')
          END
        //SYSIN    DD  *
        SET CURRENT SQLID = 'NOTHERE';
        CREATE DATABASE DUMMY
               BUFFERPOOL BP1
               INDEXBP BP2;
        """
        systsin_path = None
        sysin_path = None
        sysprint_path = None
        systsprt_path = None
        
        try:
            # SYSTSIN content - DSN commands to run DSNTEP2
            systsin_content = """  DSN SYSTEM(NOOK)
  RUN PROGRAM(DSNTEP2) PLAN(DSNTEP12) -
       LIB('DSNC10.DBCG.RUNLIB.LOAD') PARMS('/ALIGN(MID)')
  END
"""
            
            # SYSIN content - SQL statements
            sysin_content = """SET CURRENT SQLID = 'NOTHERE';
CREATE DATABASE DUMMY
       BUFFERPOOL BP1
       INDEXBP BP2;
"""
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsin', delete=False) as systsin:
                systsin.write(systsin_content)
                systsin_path = systsin.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysin', delete=False) as sysin:
                sysin.write(sysin_content)
                sysin_path = sysin.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysprint', delete=False) as sysprint:
                sysprint_path = sysprint.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt:
                systsprt_path = systsprt.name
            
            # Run batchtsocmd with both SYSTSIN and SYSIN, and STEPLIB
            rc = execute_tso_command(
                systsin_file=systsin_path,
                sysin_file=sysin_path,
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
            print(f"\n=== DB2 Command Result RC={rc} ===", file=sys.stderr)
            print(f"SYSPRINT:\n{sysprint_output}", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail)
            self.assertNotEqual(rc, 0, f"Expected DB2 command to fail with invalid subsystem, but got RC={rc}")
            
            # Verify SYSTSPRT contains the expected error message
            expected_error = "NOOK NOT VALID SUBSYSTEM ID, COMMAND TERMINATED"
            self.assertIn(
                expected_error,
                systsprt_output,
                f"Expected error message '{expected_error}' in SYSTSPRT, but got: {systsprt_output}"
            )
            
        finally:
            # Clean up temporary files
            for path in [systsin_path, sysin_path, sysprint_path, systsprt_path]:
                if path and os.path.exists(path):
                    os.unlink(path)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
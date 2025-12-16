#!/usr/bin/env python3
"""
Test concatenated dataset support for STEPLIB and DBRMLIB
"""

import os
import sys
import tempfile
import unittest
from zoautil_py import datasets
from batchtsocmd.main import execute_tso_command


class TestConcatenatedDatasets(unittest.TestCase):
    """Test concatenated dataset support for STEPLIB and DBRMLIB"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment - allocate DBRMLIB datasets"""
        # Get the user's HLQ
        cls.hlq = datasets.get_hlq()
        cls.dbrmlib1 = f"{cls.hlq}.IKJEFT1B.DBRMLIB"
        cls.dbrmlib2 = f"{cls.hlq}.IKJEFT1B.DBRMLIB2"
        cls.dbrmlib3 = f"{cls.hlq}.IKJEFT1B.DBRMLIB3"
        
        # Clean up any existing test datasets
        for ds in [cls.dbrmlib1, cls.dbrmlib2, cls.dbrmlib3]:
            try:
                datasets.delete(ds)
            except Exception:
                pass  # Ignore if dataset doesn't exist
        
        # Allocate DBRMLIB datasets with RECFM=U and BLKSIZE=32760
        for ds in [cls.dbrmlib1, cls.dbrmlib2, cls.dbrmlib3]:
            try:
                datasets.create(
                    ds,
                    type='PDSE',
                    primary_space=1,
                    secondary_space=1,
                    space_unit='CYL',
                    record_format='U',
                    block_size=32760,
                    directory_blocks=10
                )
            except Exception as e:
                print(f"Warning: Failed to allocate {ds}: {e}", file=sys.stderr)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment - delete DBRMLIB datasets"""
        # Delete test datasets
        for ds in [cls.dbrmlib1, cls.dbrmlib2, cls.dbrmlib3]:
            try:
                datasets.delete(ds)
            except Exception:
                pass  # Ignore if dataset doesn't exist
    
    def test_01_steplib_single_dataset(self):
        """Test STEPLIB with a single dataset (backward compatibility)"""
        
        systsin_path = None
        sysin_path = None
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt:
                systsprt_path = systsprt.name
            
            # Run batchtsocmd with single STEPLIB dataset (string)
            rc = execute_tso_command(
                systsin_file=systsin_path,
                sysin_file=sysin_path,
                systsprt_file=systsprt_path,
                steplib='DB2V13.SDSNLOAD',
                verbose=False
            )
            
            # Read output file
            with open(systsprt_path, 'r', encoding='ibm1047') as f:
                systsprt_output = f.read()
            
            # Print diagnostic information
            print(f"\n=== Single STEPLIB Test RC={rc} ===", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail due to invalid subsystem)
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
            for path in [systsin_path, sysin_path, systsprt_path]:
                if path and os.path.exists(path):
                    os.unlink(path)
    
    def test_02_steplib_concatenated_datasets(self):
        """Test STEPLIB with concatenated datasets (list)"""
        
        systsin_path = None
        sysin_path = None
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt:
                systsprt_path = systsprt.name
            
            # Run batchtsocmd with concatenated STEPLIB datasets (list)
            rc = execute_tso_command(
                systsin_file=systsin_path,
                sysin_file=sysin_path,
                systsprt_file=systsprt_path,
                steplib=['DB2V13.SDSNLOAD', 'DB2V13.SDSNLOD2'],
                verbose=False
            )
            
            # Read output file
            with open(systsprt_path, 'r', encoding='ibm1047') as f:
                systsprt_output = f.read()
            
            # Print diagnostic information
            print(f"\n=== Concatenated STEPLIB Test RC={rc} ===", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail due to invalid subsystem)
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
            for path in [systsin_path, sysin_path, systsprt_path]:
                if path and os.path.exists(path):
                    os.unlink(path)
    
    def test_03_dbrmlib_single_dataset(self):
        """Test DBRMLIB with a single dataset"""
        
        systsin_path = None
        sysin_path = None
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt:
                systsprt_path = systsprt.name
            
            # Run batchtsocmd with single DBRMLIB dataset (string)
            rc = execute_tso_command(
                systsin_file=systsin_path,
                sysin_file=sysin_path,
                systsprt_file=systsprt_path,
                steplib='DB2V13.SDSNLOAD',
                dbrmlib=self.dbrmlib1,
                verbose=False
            )
            
            # Read output file
            with open(systsprt_path, 'r', encoding='ibm1047') as f:
                systsprt_output = f.read()
            
            # Print diagnostic information
            print(f"\n=== Single DBRMLIB Test RC={rc} ===", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail due to invalid subsystem)
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
            for path in [systsin_path, sysin_path, systsprt_path]:
                if path and os.path.exists(path):
                    os.unlink(path)
    
    def test_04_dbrmlib_concatenated_datasets(self):
        """Test DBRMLIB with concatenated datasets (list)"""
        
        systsin_path = None
        sysin_path = None
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt:
                systsprt_path = systsprt.name
            
            # Run batchtsocmd with concatenated STEPLIB and DBRMLIB datasets (lists)
            rc = execute_tso_command(
                systsin_file=systsin_path,
                sysin_file=sysin_path,
                systsprt_file=systsprt_path,
                steplib=['DB2V13.SDSNLOAD', 'DB2V13.SDSNLOD2'],
                dbrmlib=[self.dbrmlib1, self.dbrmlib2, self.dbrmlib3],
                verbose=False
            )
            
            # Read output file
            with open(systsprt_path, 'r', encoding='ibm1047') as f:
                systsprt_output = f.read()
            
            # Print diagnostic information
            print(f"\n=== Concatenated STEPLIB and DBRMLIB Test RC={rc} ===", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
            
            # Verify return code is non-zero (command should fail due to invalid subsystem)
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
            for path in [systsin_path, sysin_path, systsprt_path]:
                if path and os.path.exists(path):
                    os.unlink(path)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
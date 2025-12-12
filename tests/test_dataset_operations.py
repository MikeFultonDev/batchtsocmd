#!/usr/bin/env python3
"""
Test dataset allocation and deletion operations using batchtsocmd
"""

import os
import tempfile
import unittest
from zoautil_py import datasets
from batchtsocmd.main import execute_tso_command


class TestDatasetOperations(unittest.TestCase):
    """Test basic dataset operations via batchtsocmd"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Get the user's HLQ
        cls.hlq = datasets.get_hlq()
        cls.test_dataset = f"{cls.hlq}.TEMP.BATCHTSO.DATASET"
        
        # Clean up any existing test dataset
        try:
            datasets.delete(cls.test_dataset)
        except Exception:
            pass  # Ignore if dataset doesn't exist
    
    def test_01_allocate_and_delete_dataset(self):
        """Test allocating and deleting a dataset using batchtsocmd"""
        
        systsin_path = None
        sysin_path = None
        sysprint_path = None
        systsin2_path = None
        sysin2_path = None
        systsprt2_path = None
        
        try:
            # Step 1: Allocate the dataset
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsin', delete=False) as systsin:
                systsin.write(f"alloc da(temp.batchtso.dataset) new\n")
                systsin_path = systsin.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysin', delete=False) as sysin:
                sysin.write("")  # Empty SYSIN
                sysin_path = sysin.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysprint', delete=False) as sysprint:
                sysprint_path = sysprint.name
            
            # Execute allocation command
            rc = execute_tso_command(
                systsin_file=systsin_path,
                sysin_file=sysin_path,
                sysprint_file=sysprint_path,
                verbose=False
            )
            
            # Verify return code is 0
            self.assertEqual(rc, 0, f"Allocation command failed with RC={rc}")
            
            # Verify no output (or minimal output)
            with open(sysprint_path, 'r', encoding='ibm1047') as f:
                output = f.read().strip()
                # Output should be empty or contain only whitespace/headers
                self.assertTrue(
                    len(output) == 0 or output.isspace(),
                    f"Expected no output, but got: {output}"
                )
            
            # Step 2: Delete the dataset
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsin', delete=False) as systsin2:
                systsin2.write(f"del temp.batchtso.dataset\n")
                systsin2_path = systsin2.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sysin', delete=False) as sysin2:
                sysin2.write("")  # Empty SYSIN
                sysin2_path = sysin2.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.systsprt', delete=False) as systsprt2:
                systsprt2_path = systsprt2.name
            
            # Execute deletion command
            rc = execute_tso_command(
                systsin_file=systsin2_path,
                sysin_file=sysin2_path,
                systsprt_file=systsprt2_path,
                verbose=False
            )
            
            # Verify return code is 0
            self.assertEqual(rc, 0, f"Deletion command failed with RC={rc}")
            
            # Verify output contains expected deletion message in SYSTSPRT
            with open(systsprt2_path, 'r', encoding='ibm1047') as f:
                output = f.read()
                expected_msg = f"ENTRY (A) {self.test_dataset} DELETED"
                self.assertIn(
                    expected_msg,
                    output,
                    f"Expected '{expected_msg}' in SYSTSPRT output, but got: {output}"
                )
            
        finally:
            # Clean up temporary files
            for path in [systsin_path, sysin_path, sysprint_path,
                        systsin2_path, sysin2_path, systsprt2_path]:
                if path and os.path.exists(path):
                    os.unlink(path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        # Ensure test dataset is deleted
        try:
            datasets.delete(cls.test_dataset)
        except Exception:
            pass  # Ignore if dataset doesn't exist


if __name__ == '__main__':
    unittest.main()

# Made with Bob

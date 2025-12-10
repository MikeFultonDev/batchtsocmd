#!/usr/bin/env python3
"""
Test dataset allocation and deletion operations using batchtsocmd
"""

import os
import sys
import subprocess
import threading
import tempfile
import unittest
from zoautil_py import datasets
from batchtsocmd.main import execute_tso_command


def create_named_pipes(prefix):
    """
    Create named pipes for SYSTSIN, SYSIN, and SYSTSPRT/SYSPRINT.
    
    Args:
        prefix: Prefix for pipe names (e.g., 'alloc', 'delete')
    
    Returns:
        tuple: (systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe)
    """
    pid = os.getpid()
    systsin_pipe = f"/tmp/systsin_{prefix}_{pid}.pipe"
    sysin_pipe = f"/tmp/sysin_{prefix}_{pid}.pipe"
    sysprint_pipe = f"/tmp/sysprint_{prefix}_{pid}.pipe"
    systsprt_pipe = f"/tmp/systsprt_{prefix}_{pid}.pipe"
    
    os.mkfifo(systsin_pipe)
    os.mkfifo(sysin_pipe)
    os.mkfifo(sysprint_pipe)
    os.mkfifo(systsprt_pipe)
    
    return systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe


def cleanup_named_pipes(*pipes):
    """
    Clean up named pipes.
    
    Args:
        *pipes: Variable number of pipe paths to clean up
    """
    for pipe in pipes:
        if pipe and os.path.exists(pipe):
            try:
                os.unlink(pipe)
            except Exception:
                pass  # Ignore cleanup errors


def run_batchtsocmd_with_pipes(systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe,
                                systsin_content, sysin_content="", input_encoding='ibm1047'):
    """
    Run batchtsocmd with named pipes.
    
    Args:
        systsin_pipe: Path to SYSTSIN named pipe
        sysin_pipe: Path to SYSIN named pipe
        sysprint_pipe: Path to SYSPRINT named pipe
        systsprt_pipe: Path to SYSTSPRT named pipe
        systsin_content: Content to write to SYSTSIN
        sysin_content: Content to write to SYSIN (default: empty string)
        input_encoding: Encoding for input pipes (default: 'ibm1047', can be 'iso8859-1')
    
    Returns:
        tuple: (return_code, sysprint_output, systsprt_output, stdout, stderr)
    """
    # Start batchtsocmd in subprocess
    cmd = [
        'python3', '-m', 'batchtsocmd.main',
        '--systsin', systsin_pipe,
        '--sysin', sysin_pipe,
        '--sysprint', sysprint_pipe,
        '--systsprt', systsprt_pipe,
        '--source-encoding', input_encoding.upper()
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Use threads for all pipe I/O to avoid blocking
    sysprint_output = []
    systsprt_output = []
    write_errors = []
    
    def write_pipe(pipe_path, content, encoding):
        try:
            with open(pipe_path, 'wb') as f:  # Binary mode
                f.write(content.encode(encoding))  # Encode to bytes first
        except Exception as e:
            write_errors.append(f"ERROR writing to {pipe_path}: {e}")
    
    def read_pipe(pipe_path, output_list):
        try:
            with open(pipe_path, 'rb') as f:  # Binary mode
                data = f.read()
                # Decode to string if needed
                output_list.append(data.decode('ibm1047'))
        except Exception as e:
            output_list.append(f"ERROR reading pipe: {e}")
    
    # Start all I/O threads as daemon threads to prevent hanging
    systsin_thread = threading.Thread(target=write_pipe, args=(systsin_pipe, systsin_content, input_encoding), daemon=True)
    sysin_thread = threading.Thread(target=write_pipe, args=(sysin_pipe, sysin_content, input_encoding), daemon=True)
    sysprint_thread = threading.Thread(target=read_pipe, args=(sysprint_pipe, sysprint_output), daemon=True)
    systsprt_thread = threading.Thread(target=read_pipe, args=(systsprt_pipe, systsprt_output), daemon=True)
    
    systsin_thread.start()
    sysin_thread.start()
    sysprint_thread.start()
    systsprt_thread.start()
    
    # Wait for process to complete
    stdout, stderr = proc.communicate(timeout=30)
    rc = proc.returncode
    
    # Wait for all I/O threads to complete
    systsin_thread.join(timeout=5)
    sysin_thread.join(timeout=5)
    sysprint_thread.join(timeout=5)
    systsprt_thread.join(timeout=5)
    
    # Check for write errors
    if write_errors:
        for error in write_errors:
            print(error, file=sys.stderr)
    
    return rc, sysprint_output[0] if sysprint_output else "", systsprt_output[0] if systsprt_output else "", stdout, stderr


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
    
    def _run_alloc_delete_with_pipes(self, input_encoding='ibm1047'):
        """
        Helper method to run allocation and deletion with pipes.
        
        Args:
            input_encoding: Encoding for input pipes (default: 'ibm1047')
        
        Returns:
            tuple: (alloc_rc, delete_rc, alloc_outputs, delete_outputs)
        """
        systsin_pipe = None
        sysin_pipe = None
        sysprint_pipe = None
        systsprt_pipe = None
        systsin2_pipe = None
        sysin2_pipe = None
        sysprint2_pipe = None
        systsprt2_pipe = None
        
        try:
            # Step 1: Allocate the dataset using named pipes
            systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe = create_named_pipes('alloc')
            
            alloc_rc, sysprint_output, systsprt_output, stdout, stderr = run_batchtsocmd_with_pipes(
                systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe,
                f"alloc da(temp.batchtso.dataset) new\n",
                input_encoding=input_encoding
            )
            
            alloc_outputs = (sysprint_output, systsprt_output, stdout, stderr)
            
            # Step 2: Delete the dataset using named pipes
            systsin2_pipe, sysin2_pipe, sysprint2_pipe, systsprt2_pipe = create_named_pipes('delete')
            
            delete_rc, sysprint2_output, systsprt2_output, stdout2, stderr2 = run_batchtsocmd_with_pipes(
                systsin2_pipe, sysin2_pipe, sysprint2_pipe, systsprt2_pipe,
                f"del temp.batchtso.dataset\n",
                input_encoding=input_encoding
            )
            
            delete_outputs = (sysprint2_output, systsprt2_output, stdout2, stderr2)
            
            return alloc_rc, delete_rc, alloc_outputs, delete_outputs
            
        finally:
            # Clean up named pipes
            cleanup_named_pipes(
                systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe,
                systsin2_pipe, sysin2_pipe, sysprint2_pipe, systsprt2_pipe
            )
    
    def test_02_allocate_and_delete_dataset_with_pipes(self):
        """Test allocating and deleting a dataset using named pipes (original test for backward compatibility)"""
        
        alloc_rc, delete_rc, alloc_outputs, delete_outputs = self._run_alloc_delete_with_pipes(input_encoding='iso8859-1')
        sysprint_output, systsprt_output, stdout, stderr = alloc_outputs
        sysprint2_output, systsprt2_output, stdout2, stderr2 = delete_outputs
        
        # If allocation RC is non-zero, print diagnostic information
        if alloc_rc != 0:
            print(f"\n=== Allocation Command Failed with RC={alloc_rc} ===", file=sys.stderr)
            print(f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"STDERR:\n{stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"SYSPRINT:\n{sysprint_output}", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
        
        # Verify allocation return code is 0
        self.assertEqual(alloc_rc, 0, f"Allocation command failed with RC={alloc_rc}")
        
        # Verify SYSPRINT has no output (or minimal output)
        output = sysprint_output.strip()
        self.assertTrue(
            len(output) == 0 or output.isspace(),
            f"Expected no SYSPRINT output, but got: {output}"
        )
        
        # If deletion RC is non-zero, print diagnostic information
        if delete_rc != 0:
            print(f"\n=== Deletion Command Failed with RC={delete_rc} ===", file=sys.stderr)
            print(f"STDOUT:\n{stdout2.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"STDERR:\n{stderr2.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"SYSPRINT:\n{sysprint2_output}", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt2_output}", file=sys.stderr)
        
        # Verify deletion return code is 0
        self.assertEqual(delete_rc, 0, f"Deletion command failed with RC={delete_rc}")
        
        # Verify output contains expected deletion message in SYSTSPRT
        expected_msg = f"ENTRY (A) {self.test_dataset} DELETED"
        self.assertIn(
            expected_msg,
            systsprt2_output,
            f"Expected '{expected_msg}' in SYSTSPRT output, but got: {systsprt2_output}"
        )
    
    def test_01_allocate_and_delete_dataset(self):
        """Test allocating and deleting a dataset using batchtsocmd"""
        
        systsin_path = None
        sysin_path = None
        sysprint_path = None
        systsin2_path = None
        sysin2_path = None
        sysprint2_path = None
        
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
                        systsin2_path, sysin2_path, sysprint2_path]:
                if path and os.path.exists(path):
                    os.unlink(path)
    def test_03_allocate_and_delete_dataset_with_pipes_ebcdic(self):
        """Test allocating and deleting a dataset using named pipes with pre-converted EBCDIC data
        
        Note: This test writes data in EBCDIC encoding to the pipes. The convert_input function
        should detect that the data is already in EBCDIC and handle it appropriately.
        """
        
        alloc_rc, delete_rc, alloc_outputs, delete_outputs = self._run_alloc_delete_with_pipes(input_encoding='ibm1047')
        sysprint_output, systsprt_output, stdout, stderr = alloc_outputs
        sysprint2_output, systsprt2_output, stdout2, stderr2 = delete_outputs
        
        # If allocation RC is non-zero, print diagnostic information
        if alloc_rc != 0:
            print(f"\n=== Allocation Command Failed with RC={alloc_rc} ===", file=sys.stderr)
            print(f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"STDERR:\n{stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"SYSPRINT:\n{sysprint_output}", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt_output}", file=sys.stderr)
        
        # Verify allocation return code is 0
        self.assertEqual(alloc_rc, 0, f"Allocation command failed with RC={alloc_rc}")
        
        # Verify SYSPRINT has no output (or minimal output)
        output = sysprint_output.strip()
        self.assertTrue(
            len(output) == 0 or output.isspace(),
            f"Expected no SYSPRINT output, but got: {output}"
        )
        
        # If deletion RC is non-zero, print diagnostic information
        if delete_rc != 0:
            print(f"\n=== Deletion Command Failed with RC={delete_rc} ===", file=sys.stderr)
            print(f"STDOUT:\n{stdout2.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"STDERR:\n{stderr2.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"SYSPRINT:\n{sysprint2_output}", file=sys.stderr)
            print(f"SYSTSPRT:\n{systsprt2_output}", file=sys.stderr)
        
        # Verify deletion return code is 0
        self.assertEqual(delete_rc, 0, f"Deletion command failed with RC={delete_rc}")
        
        # Verify output contains expected deletion message in SYSTSPRT
        expected_msg = f"ENTRY (A) {self.test_dataset} DELETED"
        self.assertIn(
            expected_msg,
            systsprt2_output,
            f"Expected '{expected_msg}' in SYSTSPRT output, but got: {systsprt2_output}"
        )
    
    
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

#!/usr/bin/env python3
"""
Test DB2 command execution using batchtsocmd
"""

import os
import sys
import subprocess
import threading
import unittest


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
                                systsin_content, sysin_content="", input_encoding='ibm1047',
                                steplib=None):
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
        steplib: Optional STEPLIB dataset name
    
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
    
    # Add steplib if specified
    if steplib:
        cmd.extend(['--steplib', steplib])
    
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
        systsin_pipe = None
        sysin_pipe = None
        sysprint_pipe = None
        systsprt_pipe = None
        
        try:
            # Create named pipes
            systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe = create_named_pipes('db2')
            
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
            
            # Run batchtsocmd with both SYSTSIN and SYSIN, and STEPLIB
            rc, sysprint_output, systsprt_output, stdout, stderr = run_batchtsocmd_with_pipes(
                systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe,
                systsin_content,
                sysin_content,
                input_encoding='iso8859-1',
                steplib='DB2V13.SDSNLOAD'
            )
            
            # Print diagnostic information for verification
            print(f"\n=== DB2 Command Result RC={rc} ===", file=sys.stderr)
            print(f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}", file=sys.stderr)
            print(f"STDERR:\n{stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
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
            # Clean up named pipes
            cleanup_named_pipes(systsin_pipe, sysin_pipe, sysprint_pipe, systsprt_pipe)


if __name__ == '__main__':
    unittest.main()

# Made with Bob
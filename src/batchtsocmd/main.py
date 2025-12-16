#!/usr/bin/env python3
"""
tester.py - Execute TSO commands via IKJEFT1B with encoding conversion
Handles SYSIN and SYSTSIN inputs with ASCII/EBCDIC conversion
"""

import sys
import os
import argparse
import tempfile
from zoautil_py import mvscmd
from zoautil_py.ztypes import DDStatement, FileDefinition, DatasetDefinition

# Check zos-ccsid-converter version
try:
    import zos_ccsid_converter
    from packaging import version
    
    required_version = "0.1.8"
    installed_version = getattr(zos_ccsid_converter, '__version__', '0.0.0')
    
    if version.parse(installed_version) < version.parse(required_version):
        print(f"ERROR: zos-ccsid-converter version {required_version} or higher is required, "
              f"but version {installed_version} is installed.", file=sys.stderr)
        print(f"Please upgrade: pip install --upgrade 'zos-ccsid-converter>={required_version}'", file=sys.stderr)
        sys.exit(1)
except ImportError as e:
    print(f"ERROR: Failed to import zos-ccsid-converter: {e}", file=sys.stderr)
    print(f"Please install: pip install 'zos-ccsid-converter>=0.1.8'", file=sys.stderr)
    sys.exit(1)

from zos_ccsid_converter import CodePageService


def convert_to_ebcdic(input_path: str, output_path: str, verbose: bool = False) -> bool:
    """
    Convert input file from ASCII to EBCDIC if needed using zos-ccsid-converter package.
    If already EBCDIC or untagged (assumed EBCDIC), copy as-is.
    
    Args:
        input_path: Source file path
        output_path: Destination file path
        verbose: Enable verbose output
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use the published zos-ccsid-converter package
        service = CodePageService(verbose=verbose)
        
        stats = service.convert_input(input_path, output_path,
                                      source_encoding=None,
                                      target_encoding='IBM-1047')
        
        if not stats['success']:
            print(f"ERROR: Failed to convert {input_path}: {stats.get('error_message', 'Unknown error')}",
                  file=sys.stderr)
            return False
        
        if verbose:
            if stats.get('conversion_needed', False):
                print(f"Converted {input_path} from {stats.get('encoding_detected', 'unknown')} to EBCDIC")
            else:
                print(f"File {input_path} already in EBCDIC format, copied as-is")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to convert {input_path}: {e}", file=sys.stderr)
        return False


def pad_sysin_to_80_bytes(input_path: str, output_path: str, verbose: bool = False) -> bool:
    """
    Pad each line in SYSIN file to exactly 80 bytes.
    
    Args:
        input_path: Source SYSIN file path
        output_path: Destination padded file path
        verbose: Enable verbose output
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as infile:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for line_num, line in enumerate(infile, 1):
                    # Remove any trailing newline/whitespace
                    line = line.rstrip('\r\n')
                    
                    # Truncate if longer than 80 bytes
                    if len(line) > 80:
                        if verbose:
                            print(f"Warning: Line {line_num} truncated from {len(line)} to 80 bytes")
                        line = line[:80]
                    
                    # Pad to exactly 80 bytes
                    padded_line = line.ljust(80)
                    outfile.write(padded_line + '\n')
        
        if verbose:
            print(f"Padded SYSIN file to 80-byte records: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to pad SYSIN file: {e}", file=sys.stderr)
        return False


def validate_input_file(path: str, name: str) -> bool:
    """Validate that input file exists and is readable"""
    if not os.path.exists(path):
        print(f"ERROR: {name} file does not exist: {path}", file=sys.stderr)
        return False
    
    if not os.access(path, os.R_OK):
        print(f"ERROR: {name} file is not readable: {path}", file=sys.stderr)
        return False
    
    return True


def execute_tso_command(systsin_file: str, sysin_file: str,
                       systsprt_file: str = 'stdout',
                       sysprint_file: str = 'stdout',
                       steplib: str | list[str] | None = None,
                       dbrmlib: str | list[str] | None = None,
                       verbose: bool = False) -> int:
    """
    Execute TSO command using IKJEFT1B with SYSTSIN and SYSIN inputs
    
    Args:
        systsin_file: Path to SYSTSIN input file
        sysin_file: Path to SYSIN input file
        systsprt_file: Path to SYSTSPRT output file or 'stdout' (defaults to 'stdout')
        sysprint_file: Path to SYSPRINT output file or 'stdout' (defaults to 'stdout')
        steplib: Optional STEPLIB dataset name(s) - single string or list of strings for concatenation
        dbrmlib: Optional DBRMLIB dataset name(s) - single string or list of strings for concatenation
        verbose: Enable verbose output
    
    Returns:
        Return code from IKJEFT1B execution
    """
    
    # Validate input files
    if not validate_input_file(systsin_file, "SYSTSIN"):
        return 8
    
    if not validate_input_file(sysin_file, "SYSIN"):
        return 8
    
    if verbose:
        print(f"SYSTSIN: {systsin_file}")
        print(f"SYSIN: {sysin_file}")
    
    # Create temporary files for EBCDIC conversion
    temp_systsin = None
    temp_sysin = None
    temp_sysin_padded = None
    temp_systsprt = None
    temp_sysprint = None
    
    try:
        # Convert SYSTSIN to EBCDIC
        temp_systsin = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.systsin')
        temp_systsin.close()
        
        if not convert_to_ebcdic(systsin_file, temp_systsin.name, verbose):
            return 8
        
        # Pad SYSIN to 80 bytes per line, then convert to EBCDIC
        temp_sysin_padded = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sysin.padded')
        temp_sysin_padded.close()
        
        if not pad_sysin_to_80_bytes(sysin_file, temp_sysin_padded.name, verbose):
            return 8
        
        temp_sysin = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sysin')
        temp_sysin.close()
        
        if not convert_to_ebcdic(temp_sysin_padded.name, temp_sysin.name, verbose):
            return 8
        
        # Define DD statements for IKJEFT1B
        dds = []
        
        # Add STEPLIB if specified (supports concatenation)
        if steplib:
            # Convert single string to list for uniform processing
            steplib_list = [steplib] if isinstance(steplib, str) else steplib
            # Create concatenated dataset definition
            steplib_defs = [DatasetDefinition(ds) for ds in steplib_list]
            dds.append(DDStatement('STEPLIB', steplib_defs))
            if verbose:
                print(f"STEPLIB: {':'.join(steplib_list)}")
        
        # Add DBRMLIB if specified (supports concatenation)
        if dbrmlib:
            # Convert single string to list for uniform processing
            dbrmlib_list = [dbrmlib] if isinstance(dbrmlib, str) else dbrmlib
            # Create concatenated dataset definition
            dbrmlib_defs = [DatasetDefinition(ds) for ds in dbrmlib_list]
            dds.append(DDStatement('DBRMLIB', dbrmlib_defs))
            if verbose:
                print(f"DBRMLIB: {':'.join(dbrmlib_list)}")
        
        # Add SYSTSPRT - use temp file if stdout, otherwise use specified file
        if systsprt_file == 'stdout':
            # Create a temporary file for SYSTSPRT output
            # We'll read this and write to stdout after execution
            temp_systsprt = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.systsprt')
            temp_systsprt.close()
            os.system(f"chtag -tc IBM-1047 {temp_systsprt.name}")
            dds.append(DDStatement('SYSTSPRT', FileDefinition(f"{temp_systsprt.name},recfm=FB")))
            if verbose:
                print(f"SYSTSPRT: temporary file (will copy to stdout)")
        else:
            dds.append(DDStatement('SYSTSPRT', FileDefinition(f"{systsprt_file},recfm=FB")))
            if verbose:
                print(f"SYSTSPRT: {systsprt_file}")
        
        # Add SYSTSIN
        dds.append(DDStatement('SYSTSIN', FileDefinition(f"{temp_systsin.name},lrecl=80,recfm=FB")))
        
        # Add SYSPRINT - use temp file if stdout, otherwise use specified file
        if sysprint_file == 'stdout':
            # Create a temporary file for SYSPRINT output
            # We'll read this and write to stdout after execution
            temp_sysprint = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sysprint')
            temp_sysprint.close()
            os.system(f"chtag -tc IBM-1047 {temp_sysprint.name}")
            dds.append(DDStatement('SYSPRINT', FileDefinition(f"{temp_sysprint.name},recfm=FB")))
            if verbose:
                print(f"SYSPRINT: temporary file (will copy to stdout)")
        else:
            dds.append(DDStatement('SYSPRINT', FileDefinition(f"{sysprint_file},recfm=FB")))
            if verbose:
                print(f"SYSPRINT: {sysprint_file}")
        
        # Add remaining DD statements
        dds.extend([
            DDStatement('SYSUDUMP', FileDefinition('DUMMY')),
            DDStatement('SYSIN', FileDefinition(f"{temp_sysin.name},lrecl=80,recfm=FB"))
        ])
        
        if verbose:
            print("Executing IKJEFT1B via mvscmdauth...")
            print("\nDD Statements:")
            for dd in dds:
                print(f"  {dd.name}: {dd.definition}")
            print()
        
        # Execute IKJEFT1B using mvscmdauth
        response = mvscmd.execute_authorized(
            pgm='IKJEFT1B',
            dds=dds,
            verbose=verbose
        )
        
        # Output to stdout in correct order: SYSTSPRT first, then SYSPRINT
        # 1. SYSTSPRT output (if stdout was requested)
        if systsprt_file == 'stdout' and temp_systsprt:
            try:
                with open(temp_systsprt.name, 'r', encoding='ibm1047') as f:
                    content = f.read()
                    if content:  # Only print if there's content
                        print(content, end='')
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not read SYSTSPRT output: {e}", file=sys.stderr)
            finally:
                if os.path.exists(temp_systsprt.name):
                    os.unlink(temp_systsprt.name)
        
        # 2. SYSPRINT output (if stdout was requested)
        if sysprint_file == 'stdout' and temp_sysprint:
            try:
                with open(temp_sysprint.name, 'r', encoding='ibm1047') as f:
                    content = f.read()
                    if content:  # Only print if there's content
                        print(content, end='')
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not read SYSPRINT output: {e}", file=sys.stderr)
            finally:
                if os.path.exists(temp_sysprint.name):
                    os.unlink(temp_sysprint.name)
        
        if verbose or response.rc != 0:
            print(f"\nReturn code: {response.rc}")
        
        # Tag output files as IBM-1047 (only for actual files, not stdout)
        if systsprt_file != 'stdout':
            os.system(f"chtag -tc IBM-1047 {systsprt_file}")
            if verbose:
                print(f"Tagged {systsprt_file} as IBM-1047")
        
        if sysprint_file != 'stdout':
            os.system(f"chtag -tc IBM-1047 {sysprint_file}")
            if verbose:
                print(f"Tagged {sysprint_file} as IBM-1047")
        
        return response.rc
        
    except Exception as e:
        print(f"ERROR: Failed to execute IKJEFT1B: {e}", file=sys.stderr)
        return 16
        
    finally:
        # Clean up temporary files
        if temp_systsin and os.path.exists(temp_systsin.name):
            os.unlink(temp_systsin.name)
        if temp_sysin_padded and os.path.exists(temp_sysin_padded.name):
            os.unlink(temp_sysin_padded.name)
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)
        # Note: temp_systsprt and temp_sysprint are cleaned up in the main try block
        # after reading their contents, but we check here in case of early exit
        if temp_systsprt and os.path.exists(temp_systsprt.name):
            os.unlink(temp_systsprt.name)
        if temp_sysprint and os.path.exists(temp_sysprint.name):
            os.unlink(temp_sysprint.name)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Execute TSO commands via IKJEFT1B with encoding conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (both SYSTSPRT and SYSPRINT go to stdout)
  batchtsocmd.py --systsin systsin.txt --sysin input.txt
  
  # With output files
  batchtsocmd.py --systsin systsin.txt --sysin input.txt \\
                 --systsprt output.txt --sysprint print.txt
  
  # With STEPLIB and verbose output
  batchtsocmd.py --systsin systsin.txt --sysin input.txt \\
                 --steplib DB2V13.SDSNLOAD --verbose
  
  # With STEPLIB and DBRMLIB
  batchtsocmd.py --systsin systsin.txt --sysin input.txt \\
                 --steplib DB2V13.SDSNLOAD --dbrmlib DB2V13.DBRMLIB
  
  # With concatenated STEPLIB datasets
  batchtsocmd.py --systsin systsin.txt --sysin input.txt \\
                 --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2

Note: Input files can be ASCII (ISO8859-1) or EBCDIC (IBM-1047).
      Encoding is auto-detected via file tags; untagged files are assumed to be EBCDIC.
      Output files will be tagged as IBM-1047.
      Both --systsprt and --sysprint default to 'stdout'.
      When stdout is used, SYSTSPRT output is written first, then SYSPRINT output.
"""
    )
    
    parser.add_argument(
        '--systsin',
        required=True,
        help='Path to SYSTSIN input file'
    )
    
    parser.add_argument(
        '--sysin',
        required=True,
        help='Path to SYSIN input file'
    )
    
    parser.add_argument(
        '--systsprt',
        default='stdout',
        help="Path to SYSTSPRT output file or 'stdout' (default: stdout)"
    )
    
    parser.add_argument(
        '--sysprint',
        default='stdout',
        help="Path to SYSPRINT output file or 'stdout' (default: stdout)"
    )
    
    parser.add_argument(
        '--steplib',
        help='Optional STEPLIB dataset name(s). Use colon to concatenate multiple datasets (e.g., DB2V13.SDSNLOAD or DB2V13.SDSNLOAD:DB2V13.SDSNLOD2)'
    )
    
    parser.add_argument(
        '--dbrmlib',
        help='Optional DBRMLIB dataset name(s). Use colon to concatenate multiple datasets (e.g., DB2V13.DBRMLIB or DB2V13.DBRMLIB:DB2V13.DBRMLI2)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Parse steplib and dbrmlib arguments (support colon-separated concatenation)
    steplib_list = args.steplib.split(':') if args.steplib else None
    dbrmlib_list = args.dbrmlib.split(':') if args.dbrmlib else None
    
    # Execute the TSO command
    rc = execute_tso_command(
        args.systsin,
        args.sysin,
        args.systsprt,
        args.sysprint,
        steplib_list,
        dbrmlib_list,
        args.verbose
    )
    
    return rc


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob

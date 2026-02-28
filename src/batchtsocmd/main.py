#!/usr/bin/env python3
"""
main.py - Execute TSO and Db2 commands via IKJEFT1B with encoding conversion
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
    from packaging import version as pkg_version
    
    required_version = "0.1.8"
    installed_version = getattr(zos_ccsid_converter, '__version__', '0.0.0')
    
    if pkg_version.parse(installed_version) < pkg_version.parse(required_version):
        print(f"ERROR: zos-ccsid-converter version {required_version} or higher is required, "
              f"but version {installed_version} is installed.", file=sys.stderr)
        print(f"Please upgrade: pip install --upgrade 'zos-ccsid-converter>={required_version}'", file=sys.stderr)
        sys.exit(1)
except ImportError as e:
    print(f"ERROR: Failed to import zos-ccsid-converter: {e}", file=sys.stderr)
    print(f"Please install: pip install 'zos-ccsid-converter>=0.1.8'", file=sys.stderr)
    sys.exit(1)

from zos_ccsid_converter import CodePageService

# Package version
__version__ = "0.2.0"


def version() -> str:
    """
    Return the version of batchtsocmd package
    
    Returns:
        Version string
    """
    return __version__


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


def tsocmd(systsin_file: str, sysin_file: str,
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
        
        # Check if mvscmd itself failed (e.g., invalid dataset name in DD)
        if response.rc != 0:
            print(f"\nError: mvscmd.execute_authorized failed with return code {response.rc}", file=sys.stderr)
            if response.stderr_response:
                print(f"Error details:\n{response.stderr_response}", file=sys.stderr)
            if response.stdout_response:
                print(f"Output:\n{response.stdout_response}", file=sys.stderr)
        
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


def db2sql(
    sysin_content: str | None = None,
    sysin_file: str | None = None,
    system: str | None = None,
    plan: str | None = None,
    toollib: str | None = None,
    dbrmlib: str | list[str] | None = None,
    steplib: str | list[str] | None = None,
    systsprt_file: str = 'stdout',
    sysprint_file: str = 'stdout',
    verbose: bool = False
) -> int:
    """
    Execute SQL statements (DDL, DML, DQL, GRANT) using DSNTEP2 via IKJEFT1B.

    Covers: SELECT, INSERT, UPDATE, DELETE, CREATE/DROP DATABASE/TABLE/TABLESPACE/
    STOGROUP/INDEX, GRANT, REVOKE, SET CURRENT SQLID, and any other dynamic SQL.

    Args:
        sysin_content: SQL statements as a string (mutually exclusive with sysin_file)
        sysin_file: Path to file containing SQL statements (mutually exclusive with sysin_content)
        system: Db2 subsystem ID (required)
        plan: Db2 plan name for DSNTEP2 (required)
        toollib: Db2 tool library containing DSNTEP2 (required)
        dbrmlib: Optional DBRMLIB dataset name(s) - single string or list for concatenation
        steplib: Optional STEPLIB dataset name(s) - single string or list for concatenation
        systsprt_file: Path to SYSTSPRT output file or 'stdout' (defaults to 'stdout')
        sysprint_file: Path to SYSPRINT output file or 'stdout' (defaults to 'stdout')
        verbose: Enable verbose output

    Returns:
        Return code from IKJEFT1B execution
    """

    # Validate that exactly one of sysin_content or sysin_file is provided
    if sysin_content is not None and sysin_file is not None:
        print("ERROR: Cannot specify both sysin_content and sysin_file", file=sys.stderr)
        return 8

    if sysin_content is None and sysin_file is None:
        print("ERROR: Must specify either sysin_content or sysin_file", file=sys.stderr)
        return 8

    # Validate required parameters
    if system is None:
        print("ERROR: system parameter is required", file=sys.stderr)
        return 8

    if plan is None:
        print("ERROR: plan parameter is required", file=sys.stderr)
        return 8

    if toollib is None:
        print("ERROR: toollib parameter is required", file=sys.stderr)
        return 8

    # Create temporary files
    temp_systsin = None
    temp_sysin = None

    try:
        # Generate SYSTSIN content: DSN → RUN PROGRAM(DSNTEP2)
        systsin_content = f"""  DSN SYSTEM({system})
  RUN PROGRAM(DSNTEP2) PLAN({plan}) -
       LIB('{toollib}') PARMS('/ALIGN(MID)')
  END
"""

        if verbose:
            print(f"Generated SYSTSIN content:")
            print(systsin_content)

        # Create temporary SYSTSIN file
        temp_systsin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.systsin')
        temp_systsin.write(systsin_content)
        temp_systsin.close()

        # Handle SYSIN input
        if sysin_content is not None:
            temp_sysin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sysin')
            temp_sysin.write(sysin_content)
            temp_sysin.close()
            sysin_path = temp_sysin.name
        else:
            sysin_path = sysin_file  # type: ignore

        if verbose:
            print(f"SYSIN source: {'content string' if sysin_content else sysin_file}")

        # Execute via tsocmd
        rc = tsocmd(
            systsin_file=temp_systsin.name,
            sysin_file=sysin_path,  # type: ignore
            systsprt_file=systsprt_file,
            sysprint_file=sysprint_file,
            steplib=steplib,
            dbrmlib=dbrmlib,
            verbose=verbose
        )

        return rc

    except Exception as e:
        print(f"ERROR: Failed to execute Db2 SQL: {e}", file=sys.stderr)
        return 16

    finally:
        if temp_systsin and os.path.exists(temp_systsin.name):
            os.unlink(temp_systsin.name)
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)


def db2op(
    sysin_content: str | None = None,
    sysin_file: str | None = None,
    system: str | None = None,
    plan: str | None = None,
    toollib: str | None = None,
    steplib: str | list[str] | None = None,
    systsprt_file: str = 'stdout',
    sysprint_file: str = 'stdout',
    verbose: bool = False
) -> int:
    """
    Execute Db2 operator commands (-DISPLAY, -START, -STOP, etc.) using DSNTIAD via IKJEFT1B.

    The SYSIN input should contain Db2 operator commands, one per line, with or without
    the leading '-' prefix (it will be normalised automatically).

    Args:
        sysin_content: Db2 operator commands as a string (mutually exclusive with sysin_file)
        sysin_file: Path to file containing Db2 operator commands (mutually exclusive with sysin_content)
        system: Db2 subsystem ID (required)
        plan: Db2 plan name for DSNTIAD (required)
        toollib: Db2 tool library containing DSNTIAD (required)
        steplib: Optional STEPLIB dataset name(s) - single string or list for concatenation
        systsprt_file: Path to SYSTSPRT output file or 'stdout' (defaults to 'stdout')
        sysprint_file: Path to SYSPRINT output file or 'stdout' (defaults to 'stdout')
        verbose: Enable verbose output

    Returns:
        Return code from IKJEFT1B execution
    """

    # Validate that exactly one of sysin_content or sysin_file is provided
    if sysin_content is not None and sysin_file is not None:
        print("ERROR: Cannot specify both sysin_content and sysin_file", file=sys.stderr)
        return 8

    if sysin_content is None and sysin_file is None:
        print("ERROR: Must specify either sysin_content or sysin_file", file=sys.stderr)
        return 8

    # Validate required parameters
    if system is None:
        print("ERROR: system parameter is required", file=sys.stderr)
        return 8

    if plan is None:
        print("ERROR: plan parameter is required", file=sys.stderr)
        return 8

    if toollib is None:
        print("ERROR: toollib parameter is required", file=sys.stderr)
        return 8

    # Create temporary files
    temp_systsin = None
    temp_sysin = None

    try:
        # Generate SYSTSIN content: DSN → RUN PROGRAM(DSNTIAD)
        systsin_content = f"""  DSN SYSTEM({system})
  RUN PROGRAM(DSNTIAD) PLAN({plan}) -
       LIB('{toollib}')
  END
"""

        if verbose:
            print(f"Generated SYSTSIN content:")
            print(systsin_content)

        # Create temporary SYSTSIN file
        temp_systsin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.systsin')
        temp_systsin.write(systsin_content)
        temp_systsin.close()

        # Handle SYSIN input - normalise operator command prefix
        if sysin_content is not None:
            # Ensure each non-blank line starts with '-'
            normalised_lines = []
            for line in sysin_content.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith('-'):
                    normalised_lines.append('-' + line.lstrip())
                else:
                    normalised_lines.append(line)
            normalised_content = '\n'.join(normalised_lines) + '\n'
            temp_sysin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sysin')
            temp_sysin.write(normalised_content)
            temp_sysin.close()
            sysin_path = temp_sysin.name
        else:
            sysin_path = sysin_file  # type: ignore

        if verbose:
            print(f"SYSIN source: {'content string' if sysin_content else sysin_file}")

        # Execute via tsocmd
        rc = tsocmd(
            systsin_file=temp_systsin.name,
            sysin_file=sysin_path,  # type: ignore
            systsprt_file=systsprt_file,
            sysprint_file=sysprint_file,
            steplib=steplib,
            verbose=verbose
        )

        return rc

    except Exception as e:
        print(f"ERROR: Failed to execute Db2 operator command: {e}", file=sys.stderr)
        return 16

    finally:
        if temp_systsin and os.path.exists(temp_systsin.name):
            os.unlink(temp_systsin.name)
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)


def db2bind(
    system: str | None = None,
    package: str | None = None,
    plan: str | None = None,
    members: str | list[str] | None = None,
    owner: str | None = None,
    qualifier: str | None = None,
    action: str = 'REPLACE',
    isolation: str | None = None,
    pklist: str | list[str] | None = None,
    dbrmlib: str | list[str] | None = None,
    steplib: str | list[str] | None = None,
    systsprt_file: str = 'stdout',
    sysprint_file: str = 'stdout',
    verbose: bool = False
) -> int:
    """
    Execute Db2 BIND PACKAGE and/or BIND PLAN DSN subcommands via IKJEFT1B.

    Generates SYSTSIN with one BIND PACKAGE subcommand per member, followed by
    an optional BIND PLAN subcommand. No SYSIN SQL input is used.

    Args:
        system: Db2 subsystem ID (required)
        package: Package collection name for BIND PACKAGE (e.g. 'PCBSA')
        plan: Plan name for BIND PLAN (e.g. 'CBSA')
        members: DBRM member name(s) to bind as packages - single string or list
        owner: OWNER qualifier for BIND subcommands
        qualifier: QUALIFIER for BIND subcommands
        action: BIND action - 'ADD' or 'REPLACE' (default: 'REPLACE')
        isolation: Isolation level for BIND PLAN (e.g. 'UR', 'CS', 'RS', 'RR')
        pklist: Package list for BIND PLAN PKLIST - single string or list
        dbrmlib: DBRMLIB dataset name(s) - single string or list for concatenation
        steplib: Optional STEPLIB dataset name(s) - single string or list for concatenation
        systsprt_file: Path to SYSTSPRT output file or 'stdout' (defaults to 'stdout')
        sysprint_file: Path to SYSPRINT output file or 'stdout' (defaults to 'stdout')
        verbose: Enable verbose output

    Returns:
        Return code from IKJEFT1B execution
    """

    # Validate required parameters
    if system is None:
        print("ERROR: system parameter is required", file=sys.stderr)
        return 8

    if package is None and plan is None:
        print("ERROR: at least one of package or plan must be specified", file=sys.stderr)
        return 8

    if package is not None and members is None:
        print("ERROR: members parameter is required when package is specified", file=sys.stderr)
        return 8

    # Normalise members to list
    members_list: list[str] = []
    if members is not None:
        members_list = [members] if isinstance(members, str) else list(members)

    # Build SYSTSIN content
    lines = [f"  DSN SYSTEM({system})"]

    # One BIND PACKAGE per member
    if package is not None:
        for member in members_list:
            bind_pkg = f"  BIND PACKAGE({package})"
            if owner:
                bind_pkg += f" OWNER({owner}) -"
                lines.append(bind_pkg)
                qualifier_line = f"  QUALIFIER({qualifier}) -" if qualifier else "  -"
                lines.append(qualifier_line)
                lines.append(f"  MEMBER({member}) -")
            else:
                bind_pkg += f" MEMBER({member}) -"
                lines.append(bind_pkg)
            lines.append(f"  ACTION({action})")
            lines.append("")

    # BIND PLAN
    if plan is not None:
        bind_plan = f"  BIND PLAN({plan})"
        if owner:
            bind_plan += f" -"
            lines.append(bind_plan)
            lines.append(f"   OWNER({owner}) -")
        else:
            bind_plan += " -"
            lines.append(bind_plan)
        if isolation:
            lines.append(f"   ISOLATION({isolation}) -")
        if pklist:
            pklist_list = [pklist] if isinstance(pklist, str) else list(pklist)
            lines.append(f"   PKLIST( -")
            for i, pkg in enumerate(pklist_list):
                suffix = " -" if i < len(pklist_list) - 1 else " )"
                lines.append(f"   {pkg}{suffix}")
        else:
            # Remove trailing ' -' from last line if no pklist
            if lines and lines[-1].endswith(' -'):
                lines[-1] = lines[-1][:-2]

    lines.append("  END")
    systsin_content = '\n'.join(lines) + '\n'

    if verbose:
        print("Generated SYSTSIN content:")
        print(systsin_content)

    # db2bind uses a dummy SYSIN (BIND subcommands need no SQL input)
    dummy_sysin_content = " "

    temp_systsin = None
    temp_sysin = None

    try:
        temp_systsin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.systsin')
        temp_systsin.write(systsin_content)
        temp_systsin.close()

        temp_sysin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sysin')
        temp_sysin.write(dummy_sysin_content)
        temp_sysin.close()

        rc = tsocmd(
            systsin_file=temp_systsin.name,
            sysin_file=temp_sysin.name,
            systsprt_file=systsprt_file,
            sysprint_file=sysprint_file,
            steplib=steplib,
            dbrmlib=dbrmlib,
            verbose=verbose
        )

        return rc

    except Exception as e:
        print(f"ERROR: Failed to execute Db2 BIND: {e}", file=sys.stderr)
        return 16

    finally:
        if temp_systsin and os.path.exists(temp_systsin.name):
            os.unlink(temp_systsin.name)
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)


def db2run(
    program: str | None = None,
    system: str | None = None,
    plan: str | None = None,
    toollib: str | None = None,
    parms: str | None = None,
    steplib: str | list[str] | None = None,
    systsprt_file: str = 'stdout',
    sysprint_file: str = 'stdout',
    verbose: bool = False
) -> int:
    """
    Execute an arbitrary Db2-bound program using DSN RUN PROGRAM via IKJEFT1B.

    Generates SYSTSIN with DSN SYSTEM(...) / RUN PROGRAM(...) PLAN(...) LIB(...).
    No SYSIN SQL input is used - all parameters are on the RUN PROGRAM subcommand.

    Args:
        program: Name of the program to run (required)
        system: Db2 subsystem ID (required)
        plan: Db2 plan name bound for the program (required)
        toollib: Load library containing the program (required)
        parms: Optional PARM string to pass to the program
        steplib: Optional STEPLIB dataset name(s) - single string or list for concatenation
        systsprt_file: Path to SYSTSPRT output file or 'stdout' (defaults to 'stdout')
        sysprint_file: Path to SYSPRINT output file or 'stdout' (defaults to 'stdout')
        verbose: Enable verbose output

    Returns:
        Return code from IKJEFT1B execution
    """

    # Validate required parameters
    if program is None:
        print("ERROR: program parameter is required", file=sys.stderr)
        return 8

    if system is None:
        print("ERROR: system parameter is required", file=sys.stderr)
        return 8

    if plan is None:
        print("ERROR: plan parameter is required", file=sys.stderr)
        return 8

    if toollib is None:
        print("ERROR: toollib parameter is required", file=sys.stderr)
        return 8

    temp_systsin = None
    temp_sysin = None

    try:
        # Build RUN PROGRAM subcommand
        run_line = f"  RUN PROGRAM({program}) PLAN({plan}) -"
        if parms:
            lib_line = f"       LIB('{toollib}') PARM('{parms}')"
        else:
            lib_line = f"       LIB('{toollib}')"

        systsin_content = f"""  DSN SYSTEM({system})
{run_line}
{lib_line}
  END
"""

        if verbose:
            print("Generated SYSTSIN content:")
            print(systsin_content)

        temp_systsin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.systsin')
        temp_systsin.write(systsin_content)
        temp_systsin.close()

        # db2run uses a dummy SYSIN
        temp_sysin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sysin')
        temp_sysin.write(" ")
        temp_sysin.close()

        rc = tsocmd(
            systsin_file=temp_systsin.name,
            sysin_file=temp_sysin.name,
            systsprt_file=systsprt_file,
            sysprint_file=sysprint_file,
            steplib=steplib,
            verbose=verbose
        )

        return rc

    except Exception as e:
        print(f"ERROR: Failed to execute Db2 RUN PROGRAM: {e}", file=sys.stderr)
        return 16

    finally:
        if temp_systsin and os.path.exists(temp_systsin.name):
            os.unlink(temp_systsin.name)
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)


# ---------------------------------------------------------------------------
# Backward-compatibility aliases (deprecated - use db2sql / db2op instead)
# ---------------------------------------------------------------------------

def db2cmd(
    sysin_content: str | None = None,
    sysin_file: str | None = None,
    system: str | None = None,
    plan: str | None = None,
    toollib: str | None = None,
    dbrmlib: str | list[str] | None = None,
    steplib: str | list[str] | None = None,
    systsprt_file: str = 'stdout',
    sysprint_file: str = 'stdout',
    verbose: bool = False
) -> int:
    """Deprecated: use db2sql() instead."""
    return db2sql(
        sysin_content=sysin_content,
        sysin_file=sysin_file,
        system=system,
        plan=plan,
        toollib=toollib,
        dbrmlib=dbrmlib,
        steplib=steplib,
        systsprt_file=systsprt_file,
        sysprint_file=sysprint_file,
        verbose=verbose
    )


def db2admin(
    sysin_content: str | None = None,
    sysin_file: str | None = None,
    system: str | None = None,
    plan: str | None = None,
    toollib: str | None = None,
    steplib: str | list[str] | None = None,
    systsprt_file: str = 'stdout',
    sysprint_file: str = 'stdout',
    verbose: bool = False
) -> int:
    """Deprecated: use db2op() instead."""
    return db2op(
        sysin_content=sysin_content,
        sysin_file=sysin_file,
        system=system,
        plan=plan,
        toollib=toollib,
        steplib=steplib,
        systsprt_file=systsprt_file,
        sysprint_file=sysprint_file,
        verbose=verbose
    )


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
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    # Parse steplib and dbrmlib arguments (support colon-separated concatenation)
    steplib_list = args.steplib.split(':') if args.steplib else None
    dbrmlib_list = args.dbrmlib.split(':') if args.dbrmlib else None
    
    # Execute the TSO command
    rc = tsocmd(
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

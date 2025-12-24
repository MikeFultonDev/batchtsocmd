#!/usr/bin/env python3
"""
db2admin - Execute Db2 administrative commands via DSNTIAD with encoding conversion
Command-line interface for db2admin functionality
"""

import sys
import os
import argparse
import tempfile
from .main import db2admin, __version__


def main():
    """Main entry point for db2admin command"""
    parser = argparse.ArgumentParser(
        description='Execute Db2 administrative commands via DSNTIAD with encoding conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DB2_SYSTEM    - Default Db2 subsystem ID
  DB2_PLAN      - Default Db2 plan name
  DB2_TOOLLIB   - Default Db2 tool library

Examples:
  # Using command line options
  db2admin --system DB2P --plan DSNTIAD --toollib DSNC10.DBCG.RUNLIB.LOAD \\
      --sysin admin.txt --steplib DB2V13.SDSNLOAD

  # Using environment variables
  export DB2_SYSTEM=DB2P
  export DB2_PLAN=DSNTIAD
  export DB2_TOOLLIB=DSNC10.DBCG.RUNLIB.LOAD
  db2admin --sysin admin.txt

  # Using stdin pipe
  echo "-DISPLAY DATABASE(MYDB)" | db2admin --system DB2P \\
      --plan DSNTIAD --toollib DSNC10.DBCG.RUNLIB.LOAD

  # With concatenated STEPLIB datasets
  db2admin --system DB2P --plan DSNTIAD --toollib DSNC10.DBCG.RUNLIB.LOAD \\
      --sysin admin.txt --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2

Note: Command line options override environment variables.
      Input can be from file (--sysin) or stdin (pipe).
      Output files will be tagged as IBM-1047.
      DSNTIAD is used for DB2 administrative commands (DISPLAY, START, STOP, etc.)
"""
    )
    
    parser.add_argument(
        '--system',
        help='Db2 subsystem ID (or set DB2_SYSTEM env var)'
    )
    
    parser.add_argument(
        '--plan',
        help='Db2 plan name (or set DB2_PLAN env var)'
    )
    
    parser.add_argument(
        '--toollib',
        help='Db2 tool library (or set DB2_TOOLLIB env var)'
    )
    
    parser.add_argument(
        '--sysin',
        help='Path to SYSIN input file (if not specified, reads from stdin)'
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
        help='Optional STEPLIB dataset name(s). Use colon to concatenate multiple datasets'
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
    
    # Get parameters from command line or environment variables
    # Command line takes precedence
    system = args.system or os.environ.get('DB2_SYSTEM')
    plan = args.plan or os.environ.get('DB2_PLAN')
    toollib = args.toollib or os.environ.get('DB2_TOOLLIB')
    
    # Validate required parameters
    missing_params = []
    if not system:
        missing_params.append('--system (or DB2_SYSTEM env var)')
    if not plan:
        missing_params.append('--plan (or DB2_PLAN env var)')
    if not toollib:
        missing_params.append('--toollib (or DB2_TOOLLIB env var)')
    
    if missing_params:
        print(f"ERROR: Missing required parameters: {', '.join(missing_params)}", file=sys.stderr)
        print("\nUse --help for usage information", file=sys.stderr)
        return 1
    
    # Handle SYSIN input
    temp_sysin = None
    sysin_file = None
    sysin_content = None
    
    try:
        if args.sysin:
            # Use file specified on command line
            sysin_file = args.sysin
            if not os.path.exists(sysin_file):
                print(f"ERROR: SYSIN file does not exist: {sysin_file}", file=sys.stderr)
                return 8
        else:
            # Read from stdin
            if args.verbose:
                print("Reading SYSIN from stdin...", file=sys.stderr)
            
            stdin_content = sys.stdin.read()
            if not stdin_content.strip():
                print("ERROR: No input provided via stdin", file=sys.stderr)
                return 8
            
            # Create temporary file for stdin content
            temp_sysin = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sysin')
            temp_sysin.write(stdin_content)
            temp_sysin.close()
            sysin_file = temp_sysin.name
        
        # Parse steplib argument (support colon-separated concatenation)
        steplib_list = args.steplib.split(':') if args.steplib else None
        
        # Execute the Db2 administrative command
        rc = db2admin(
            sysin_file=sysin_file,
            system=system,
            plan=plan,
            toollib=toollib,
            steplib=steplib_list,
            systsprt_file=args.systsprt,
            sysprint_file=args.sysprint,
            verbose=args.verbose
        )
        
        return rc
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 16
        
    finally:
        # Clean up temporary stdin file
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
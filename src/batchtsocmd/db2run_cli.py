#!/usr/bin/env python3
"""
db2run - Run a Db2-bound program via DSN RUN PROGRAM
Command-line interface for db2run functionality
"""

import sys
import os
import argparse
from .main import db2run, __version__


def main():
    """Main entry point for db2run command"""
    parser = argparse.ArgumentParser(
        description='Run a Db2-bound program via DSN RUN PROGRAM via IKJEFT1B',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DB2_SYSTEM    - Default Db2 subsystem ID
  DB2_STEPLIB   - Default STEPLIB dataset(s)

Examples:
  # Run BANKDATA to generate test data (mirrors BANKDATA.jcl)
  db2run --program BANKDATA --system DB2P --plan CBSA \\
      --toollib CBSA.CICSBSA.LOADLIB \\
      --parm '1,10000,1,1000000000000000' \\
      --steplib CBSA.CICSBSA.DBRM:CBSA.CICSBSA.LOADLIB:DB2V13.SDSNLOAD

  # Run a custom Db2-bound utility
  db2run --program MYUTIL --system DB2P --plan MYPLAN \\
      --toollib MY.LOADLIB

  # With explicit STEPLIB
  db2run --program MYUTIL --system DB2P --plan MYPLAN \\
      --toollib MY.LOADLIB --steplib DB2V13.SDSNLOAD

Note: Command line options override environment variables.
      DSN RUN PROGRAM executes a Db2-bound COBOL or other program.
      No SYSIN SQL input is used - all parameters are on the RUN PROGRAM subcommand.
      Use --parm to pass a PARM string to the program.
"""
    )

    parser.add_argument(
        '--program',
        required=True,
        help='Name of the Db2-bound program to run (required)'
    )

    parser.add_argument(
        '--system',
        help='Db2 subsystem ID (or set DB2_SYSTEM env var)'
    )

    parser.add_argument(
        '--plan',
        required=True,
        help='Db2 plan name bound for the program (required)'
    )

    parser.add_argument(
        '--toollib',
        required=True,
        help='Load library containing the program (required)'
    )

    parser.add_argument(
        '--parm',
        help='Optional PARM string to pass to the program'
    )

    parser.add_argument(
        '--steplib',
        help='Optional STEPLIB dataset name(s). Use colon to concatenate (or set DB2_STEPLIB env var)'
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

    # Resolve parameters: CLI > env vars
    system = args.system or os.environ.get('DB2_SYSTEM')
    steplib_arg = args.steplib or os.environ.get('DB2_STEPLIB')

    # Validate required parameters
    if not system:
        print("ERROR: Missing required parameter: --system (or DB2_SYSTEM env var)", file=sys.stderr)
        print("\nUse --help for usage information", file=sys.stderr)
        return 1

    try:
        # Parse steplib (colon-separated)
        steplib_list = steplib_arg.split(':') if steplib_arg else None

        rc = db2run(
            program=args.program,
            system=system,
            plan=args.plan,
            toollib=args.toollib,
            parms=args.parm,
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


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
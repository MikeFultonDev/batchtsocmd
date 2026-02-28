#!/usr/bin/env python3
"""
db2op - Execute Db2 operator commands (-DISPLAY, -START, -STOP, etc.) via DSNTIAD
Command-line interface for db2op functionality
"""

import sys
import os
import argparse
import tempfile
from .main import db2op, __version__


def main():
    """Main entry point for db2op command"""
    parser = argparse.ArgumentParser(
        description='Execute Db2 operator commands via DSNTIAD (-DISPLAY, -START, -STOP, etc.)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DB2_SYSTEM    - Default Db2 subsystem ID
  DB2_PLAN      - Default Db2 plan name for DSNTIAD
  DB2_TOOLLIB   - Default Db2 tool library
  DB2_STEPLIB   - Default STEPLIB dataset(s)

Examples:
  # Inline operator command (leading '-' is optional)
  db2op "-DISPLAY DATABASE(*)"
  db2op "DISPLAY DATABASE(CBSA) SPACENAM(*) USE"

  # From a file
  db2op --file opcmds.txt

  # From stdin
  echo "-STOP DATABASE(CBSA) MODE(QUIESCE)" | db2op

  # With explicit connection parameters
  db2op "-DISPLAY THREAD(*)" --system DB2P --plan DSNTIAD \\
      --toollib DSNC10.DBCG.RUNLIB.LOAD

Note: Command line options override environment variables.
      The leading '-' prefix on operator commands is optional and will be
      added automatically if missing.
      Input can be inline, from --file, or from stdin.
"""
    )

    parser.add_argument(
        'command',
        nargs='?',
        help='Db2 operator command to execute (inline). The leading \'-\' is optional.'
    )

    parser.add_argument(
        '--file', '-f',
        dest='sysin',
        help='Path to file containing operator commands (mutually exclusive with inline command and stdin)'
    )

    parser.add_argument(
        '--system',
        help='Db2 subsystem ID (or set DB2_SYSTEM env var)'
    )

    parser.add_argument(
        '--plan',
        help='Db2 plan name for DSNTIAD (or set DB2_PLAN env var)'
    )

    parser.add_argument(
        '--toollib',
        help='Db2 tool library containing DSNTIAD (or set DB2_TOOLLIB env var)'
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
    plan = args.plan or os.environ.get('DB2_PLAN')
    toollib = args.toollib or os.environ.get('DB2_TOOLLIB')
    steplib_arg = args.steplib or os.environ.get('DB2_STEPLIB')

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

    # Determine input source: inline > --file > stdin
    sysin_content = None
    sysin_file = None

    try:
        if args.command and args.sysin:
            print("ERROR: Cannot specify both inline command and --file", file=sys.stderr)
            return 1

        if args.command:
            sysin_content = args.command
        elif args.sysin:
            sysin_file = args.sysin
            if not os.path.exists(sysin_file):
                print(f"ERROR: Command file does not exist: {sysin_file}", file=sys.stderr)
                return 8
        else:
            # Read from stdin
            if args.verbose:
                print("Reading operator commands from stdin...", file=sys.stderr)
            stdin_content = sys.stdin.read()
            if not stdin_content.strip():
                print("ERROR: No operator command provided via stdin", file=sys.stderr)
                return 8
            sysin_content = stdin_content

        # Parse steplib (colon-separated)
        steplib_list = steplib_arg.split(':') if steplib_arg else None

        rc = db2op(
            sysin_content=sysin_content,
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


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
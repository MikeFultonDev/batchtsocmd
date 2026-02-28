#!/usr/bin/env python3
"""
db2sql - Execute SQL statements (DDL, DML, DQL, GRANT) via DSNTEP2
Command-line interface for db2sql functionality
"""

import sys
import os
import argparse
import tempfile
from .main import db2sql, __version__


def main():
    """Main entry point for db2sql command"""
    parser = argparse.ArgumentParser(
        description='Execute SQL statements via DSNTEP2 (DDL, DML, DQL, GRANT)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DB2_SYSTEM    - Default Db2 subsystem ID
  DB2_PLAN      - Default Db2 plan name for DSNTEP2
  DB2_TOOLLIB   - Default Db2 tool library
  DB2_STEPLIB   - Default STEPLIB dataset(s)
  DB2_DBRMLIB   - Default DBRMLIB dataset or directory

Examples:
  # Inline SQL
  db2sql "SELECT * FROM SYSIBM.SYSTABLES WHERE NAME = 'ACCOUNT'"

  # From a file
  db2sql --file schema.sql

  # From stdin
  echo "DROP TABLE IBMUSER.ACCOUNT;" | db2sql

  # Create schema with SET CURRENT SQLID
  db2sql --file instdb2.sql --system DB2P --plan DSNTEP12 \\
      --toollib DSNC10.DBCG.RUNLIB.LOAD

  # GRANT via inline SQL
  db2sql "SET CURRENT SQLID = 'IBMUSER'; GRANT EXECUTE ON PLAN CBSA TO CICSUSER;"

  # With concatenated STEPLIB
  db2sql --file query.sql --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2

Note: Command line options override environment variables.
      Input can be inline SQL, from --file, or from stdin.
      Multiple SQL statements must be separated by semicolons.
"""
    )

    parser.add_argument(
        'sql',
        nargs='?',
        help='SQL statement(s) to execute (inline). Separate multiple statements with semicolons.'
    )

    parser.add_argument(
        '--file', '-f',
        dest='sysin',
        help='Path to SQL input file (mutually exclusive with inline SQL and stdin)'
    )

    parser.add_argument(
        '--system',
        help='Db2 subsystem ID (or set DB2_SYSTEM env var)'
    )

    parser.add_argument(
        '--plan',
        help='Db2 plan name for DSNTEP2 (or set DB2_PLAN env var)'
    )

    parser.add_argument(
        '--toollib',
        help='Db2 tool library containing DSNTEP2 (or set DB2_TOOLLIB env var)'
    )

    parser.add_argument(
        '--steplib',
        help='Optional STEPLIB dataset name(s). Use colon to concatenate (or set DB2_STEPLIB env var)'
    )

    parser.add_argument(
        '--dbrmlib',
        help='Optional DBRMLIB dataset name(s). Use colon to concatenate (or set DB2_DBRMLIB env var)'
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
    dbrmlib_arg = args.dbrmlib or os.environ.get('DB2_DBRMLIB')

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

    # Determine SQL input source: inline > --file > stdin
    temp_sysin = None
    sysin_content = None
    sysin_file = None

    try:
        if args.sql and args.sysin:
            print("ERROR: Cannot specify both inline SQL and --file", file=sys.stderr)
            return 1

        if args.sql:
            sysin_content = args.sql
        elif args.sysin:
            sysin_file = args.sysin
            if not os.path.exists(sysin_file):
                print(f"ERROR: SQL file does not exist: {sysin_file}", file=sys.stderr)
                return 8
        else:
            # Read from stdin
            if args.verbose:
                print("Reading SQL from stdin...", file=sys.stderr)
            stdin_content = sys.stdin.read()
            if not stdin_content.strip():
                print("ERROR: No SQL input provided via stdin", file=sys.stderr)
                return 8
            sysin_content = stdin_content

        # Parse steplib and dbrmlib (colon-separated)
        steplib_list = steplib_arg.split(':') if steplib_arg else None
        dbrmlib_list = dbrmlib_arg.split(':') if dbrmlib_arg else None

        rc = db2sql(
            sysin_content=sysin_content,
            sysin_file=sysin_file,
            system=system,
            plan=plan,
            toollib=toollib,
            steplib=steplib_list,
            dbrmlib=dbrmlib_list,
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
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
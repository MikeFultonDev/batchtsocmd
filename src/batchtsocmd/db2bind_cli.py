#!/usr/bin/env python3
"""
db2bind - Bind Db2 packages and plans via DSN BIND subcommands
Command-line interface for db2bind functionality
"""

import sys
import os
import argparse
from .main import db2bind, __version__


def main():
    """Main entry point for db2bind command"""
    parser = argparse.ArgumentParser(
        description='Bind Db2 packages and plans via DSN BIND subcommands',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DB2_SYSTEM    - Default Db2 subsystem ID
  DB2_STEPLIB   - Default STEPLIB dataset(s)
  DB2_DBRMLIB   - Default DBRMLIB dataset(s)

Examples:
  # Bind a single package
  db2bind --system DB2P --package PCBSA --member CREACC \\
      --dbrmlib CBSA.CICSBSA.DBRM --steplib DB2V13.SDSNLOAD

  # Bind multiple packages with owner and qualifier
  db2bind --system DB2P --package PCBSA \\
      --member CREACC --member CRECUST --member DELACC \\
      --owner IBMUSER --qualifier IBMUSER --action REPLACE \\
      --dbrmlib CBSA.CICSBSA.DBRM --steplib DB2V13.SDSNLOAD

  # Bind a plan with package list
  db2bind --system DB2P --plan CBSA --owner IBMUSER \\
      --isolation UR --pklist "NULLID.*" --pklist "PCBSA.*" \\
      --steplib DB2V13.SDSNLOAD

  # Bind packages and plan together (mirrors DB2BIND.jcl)
  db2bind --system DB2P --package PCBSA --owner IBMUSER --qualifier IBMUSER \\
      --member CREACC --member CRECUST --member DBCRFUN \\
      --plan CBSA --isolation UR --pklist "NULLID.*" --pklist "PCBSA.*" \\
      --dbrmlib CBSA.CICSBSA.DBRM \\
      --steplib DB2V13.SDSNEXIT:DB2V13.SDSNLOAD

Note: Command line options override environment variables.
      BIND subcommands are DSN processor commands, not SQL.
      No SYSIN SQL input is used - all parameters are on the BIND subcommands.
"""
    )

    parser.add_argument(
        '--system',
        help='Db2 subsystem ID (or set DB2_SYSTEM env var)'
    )

    parser.add_argument(
        '--package',
        help='Package collection name for BIND PACKAGE (e.g. PCBSA)'
    )

    parser.add_argument(
        '--plan',
        help='Plan name for BIND PLAN (e.g. CBSA)'
    )

    parser.add_argument(
        '--member',
        action='append',
        dest='members',
        metavar='MEMBER',
        help='DBRM member name to bind as a package. Repeat for multiple members.'
    )

    parser.add_argument(
        '--owner',
        help='OWNER for BIND subcommands'
    )

    parser.add_argument(
        '--qualifier',
        help='QUALIFIER for BIND subcommands'
    )

    parser.add_argument(
        '--action',
        default='REPLACE',
        choices=['ADD', 'REPLACE'],
        help='BIND action: ADD or REPLACE (default: REPLACE)'
    )

    parser.add_argument(
        '--isolation',
        choices=['UR', 'CS', 'RS', 'RR'],
        help='Isolation level for BIND PLAN (e.g. UR, CS, RS, RR)'
    )

    parser.add_argument(
        '--pklist',
        action='append',
        dest='pklist',
        metavar='ENTRY',
        help='Package list entry for BIND PLAN PKLIST. Repeat for multiple entries.'
    )

    parser.add_argument(
        '--dbrmlib',
        help='DBRMLIB dataset name(s). Use colon to concatenate (or set DB2_DBRMLIB env var)'
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
    dbrmlib_arg = args.dbrmlib or os.environ.get('DB2_DBRMLIB')

    # Validate required parameters
    missing_params = []
    if not system:
        missing_params.append('--system (or DB2_SYSTEM env var)')

    if missing_params:
        print(f"ERROR: Missing required parameters: {', '.join(missing_params)}", file=sys.stderr)
        print("\nUse --help for usage information", file=sys.stderr)
        return 1

    # Validate that at least package or plan is specified
    if not args.package and not args.plan:
        print("ERROR: At least one of --package or --plan must be specified", file=sys.stderr)
        print("\nUse --help for usage information", file=sys.stderr)
        return 1

    # Validate that members are provided when package is specified
    if args.package and not args.members:
        print("ERROR: --member is required when --package is specified", file=sys.stderr)
        print("\nUse --help for usage information", file=sys.stderr)
        return 1

    try:
        # Parse steplib and dbrmlib (colon-separated)
        steplib_list = steplib_arg.split(':') if steplib_arg else None
        dbrmlib_list = dbrmlib_arg.split(':') if dbrmlib_arg else None

        rc = db2bind(
            system=system,
            package=args.package,
            plan=args.plan,
            members=args.members,
            owner=args.owner,
            qualifier=args.qualifier,
            action=args.action,
            isolation=args.isolation,
            pklist=args.pklist,
            dbrmlib=dbrmlib_list,
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
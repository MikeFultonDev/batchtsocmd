# batchtsocmd

Run TSO and Db2 commands via IKJEFT1B with automatic encoding conversion.

## Description

`batchtsocmd` is a Python utility for z/OS that executes TSO and Db2 commands through IKJEFT1B with automatic ASCII/EBCDIC encoding conversion. It handles SYSIN and SYSTSIN inputs from files or strings, automatically converting them to EBCDIC as needed.

The package provides five installed commands:

| Command | Program | Purpose |
|---|---|---|
| `batchtsocmd` | `IKJEFT1B` | General TSO command execution (raw SYSTSIN + SYSIN) |
| `db2sql` | `DSNTEP2` | Execute SQL statements (DDL, DML, DQL, GRANT) |
| `db2bind` | DSN BIND subcommand | Bind Db2 packages and plans |
| `db2run` | DSN RUN PROGRAM | Run a Db2-bound program |
| `db2op` | `DSNTIAD` | Execute Db2 operator commands (-DISPLAY, -START, -STOP) |

> **Deprecated:** `db2cmd` and `db2admin` are retained as backward-compatible aliases for `db2sql` and `db2op` respectively. New code should use the new command names.

## Features

- Execute TSO commands via IKJEFT1B
- Execute Db2 SQL (DDL, DML, DQL, GRANT/REVOKE) via DSNTEP2
- Bind Db2 packages and plans via DSN BIND subcommands
- Run Db2-bound programs via DSN RUN PROGRAM
- Execute Db2 operator commands via DSNTIAD
- Automatic ASCII to EBCDIC conversion for input files
- Optional STEPLIB support with colon-separated concatenation
- Optional DBRMLIB support with colon-separated concatenation
- Configurable output destinations (SYSTSPRT, SYSPRINT)
- Environment variable support for Db2 connection parameters
- Stdin piping support
- Verbose mode for debugging

## Requirements

- Python 3.8 or higher
- z/OS operating system
- IBM Z Open Automation Utilities (ZOAU)
- zoautil-py package
- zos-ccsid-converter package

## Installation

**Note:** This package can only be installed and run on z/OS systems.

```bash
pip install batchtsocmd
```

## Environment Variables

All Db2 commands honour these environment variables. Command line options override them.

| Variable | Used by | Description |
|---|---|---|
| `DB2_SYSTEM` | all Db2 commands | Db2 subsystem ID |
| `DB2_PLAN` | `db2sql`, `db2op` | Plan name for DSNTEP2 or DSNTIAD |
| `DB2_TOOLLIB` | `db2sql`, `db2op` | Tool library containing DSNTEP2 or DSNTIAD |
| `DB2_STEPLIB` | all Db2 commands | STEPLIB dataset(s), colon-separated |
| `DB2_DBRMLIB` | `db2sql`, `db2bind` | DBRMLIB dataset(s), colon-separated |

```bash
export DB2_SYSTEM=DB2P
export DB2_PLAN=DSNTEP12
export DB2_TOOLLIB=DSNC10.DBCG.RUNLIB.LOAD
export DB2_STEPLIB=DB2V13.SDSNEXIT:DB2V13.SDSNLOAD
```

---

## Usage

### batchtsocmd — General TSO Command Execution

Low-level interface: provide your own SYSTSIN and SYSIN files.

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt

# With output files
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --systsprt output.txt --sysprint print.txt

# With STEPLIB and DBRMLIB
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2 \
            --dbrmlib DB2V13.DBRMLIB
```

**Options:**

- `--systsin PATH` — Path to SYSTSIN input file (required)
- `--sysin PATH` — Path to SYSIN input file (required)
- `--systsprt PATH` — SYSTSPRT output file or `stdout` (default: `stdout`)
- `--sysprint PATH` — SYSPRINT output file or `stdout` (default: `stdout`)
- `--steplib DATASET` — STEPLIB dataset(s), colon-separated
- `--dbrmlib DATASET` — DBRMLIB dataset(s), colon-separated
- `-v, --verbose` — Enable verbose output

---

### db2sql — Execute SQL Statements

Executes SQL statements (DDL, DML, DQL, GRANT, REVOKE, SET CURRENT SQLID) via DSNTEP2.
Replaces the former `db2cmd` command.

```bash
# Inline SQL
db2sql "SELECT * FROM SYSIBM.SYSTABLES WHERE NAME = 'ACCOUNT'"

# From a file
db2sql --file schema.sql

# From stdin
echo "DROP TABLE IBMUSER.ACCOUNT;" | db2sql

# Create schema
db2sql --file instdb2.sql --system DB2P --plan DSNTEP12 \
    --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --steplib DB2V13.SDSNEXIT:DB2V13.SDSNLOAD

# GRANT via inline SQL (SET CURRENT SQLID sets the owning auth ID)
db2sql "SET CURRENT SQLID = 'IBMUSER'; \
        GRANT EXECUTE ON PLAN CBSA TO CICSUSER; \
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE IBMUSER.ACCOUNT TO CICSUSER;"

# With environment variables set
db2sql --file grants.sql
```

**Options:**

- `SQL` — Inline SQL statement(s) (positional, optional)
- `--file PATH` / `-f PATH` — SQL input file (mutually exclusive with inline SQL and stdin)
- `--system ID` — Db2 subsystem ID (or `DB2_SYSTEM`)
- `--plan NAME` — Plan name for DSNTEP2 (or `DB2_PLAN`)
- `--toollib LIB` — Tool library (or `DB2_TOOLLIB`)
- `--steplib DATASET` — STEPLIB dataset(s), colon-separated (or `DB2_STEPLIB`)
- `--dbrmlib DATASET` — DBRMLIB dataset(s), colon-separated (or `DB2_DBRMLIB`)
- `--systsprt PATH` — SYSTSPRT output file or `stdout` (default: `stdout`)
- `--sysprint PATH` — SYSPRINT output file or `stdout` (default: `stdout`)
- `-v, --verbose` — Enable verbose output

**Notes:**

- Multiple SQL statements must be separated by semicolons
- SQL lines are automatically padded to 80 bytes
- `GRANT` is plain SQL and runs through DSNTEP2 — no special program needed
- Use `SET CURRENT SQLID` before GRANTs to set the owning authorization ID

---

### db2bind — Bind Db2 Packages and Plans

Generates and executes DSN `BIND PACKAGE` and/or `BIND PLAN` subcommands via IKJEFT1B.
No SQL input is used — all parameters are on the BIND subcommands in SYSTSIN.

```bash
# Bind a single package
db2bind --system DB2P --package PCBSA --member CREACC \
    --dbrmlib CBSA.CICSBSA.DBRM \
    --steplib DB2V13.SDSNEXIT:DB2V13.SDSNLOAD

# Bind multiple packages with owner and qualifier
db2bind --system DB2P --package PCBSA \
    --member CREACC --member CRECUST --member DELACC \
    --owner IBMUSER --qualifier IBMUSER --action REPLACE \
    --dbrmlib CBSA.CICSBSA.DBRM \
    --steplib DB2V13.SDSNEXIT:DB2V13.SDSNLOAD

# Bind a plan with package list
db2bind --system DB2P --plan CBSA --owner IBMUSER \
    --isolation UR --pklist "NULLID.*" --pklist "PCBSA.*" \
    --steplib DB2V13.SDSNLOAD

# Bind packages and plan together (equivalent to DB2BIND.jcl)
db2bind --system DB2P \
    --package PCBSA --owner IBMUSER --qualifier IBMUSER \
    --member CREACC --member CRECUST --member DBCRFUN \
    --member DELACC --member DELCUS --member INQACC \
    --member INQACCCU --member BANKDATA --member UPDACC --member XFRFUN \
    --plan CBSA --isolation UR \
    --pklist "NULLID.*" --pklist "PCBSA.*" \
    --dbrmlib CBSA.CICSBSA.DBRM \
    --steplib DB2V13.SDSNEXIT:DB2V13.SDSNLOAD
```

**Options:**

- `--system ID` — Db2 subsystem ID (or `DB2_SYSTEM`) (required)
- `--package NAME` — Package collection name for BIND PACKAGE (e.g. `PCBSA`)
- `--plan NAME` — Plan name for BIND PLAN (e.g. `CBSA`)
- `--member NAME` — DBRM member to bind as a package (repeatable)
- `--owner ID` — OWNER for BIND subcommands
- `--qualifier ID` — QUALIFIER for BIND subcommands
- `--action ADD|REPLACE` — BIND action (default: `REPLACE`)
- `--isolation UR|CS|RS|RR` — Isolation level for BIND PLAN
- `--pklist ENTRY` — Package list entry for BIND PLAN PKLIST (repeatable)
- `--dbrmlib DATASET` — DBRMLIB dataset(s), colon-separated (or `DB2_DBRMLIB`)
- `--steplib DATASET` — STEPLIB dataset(s), colon-separated (or `DB2_STEPLIB`)
- `--systsprt PATH` — SYSTSPRT output file or `stdout` (default: `stdout`)
- `--sysprint PATH` — SYSPRINT output file or `stdout` (default: `stdout`)
- `-v, --verbose` — Enable verbose output

**Notes:**

- At least one of `--package` or `--plan` must be specified
- `--member` is required when `--package` is specified
- BIND subcommands are DSN processor commands, not SQL — DSNTEP2 is not used
- RC 0 = success, RC 4 = warnings (acceptable for bind operations)

---

### db2run — Run a Db2-Bound Program

Executes an arbitrary Db2-bound program via DSN `RUN PROGRAM` via IKJEFT1B.
Equivalent to the `BANKDATA.jcl` pattern.

```bash
# Run BANKDATA to generate test data (equivalent to BANKDATA.jcl)
db2run --program BANKDATA --system DB2P --plan CBSA \
    --toollib CBSA.CICSBSA.LOADLIB \
    --parm '1,10000,1,1000000000000000' \
    --steplib CBSA.CICSBSA.DBRM:CBSA.CICSBSA.LOADLIB:DB2V13.SDSNLOAD

# Run a custom Db2-bound utility
db2run --program MYUTIL --system DB2P --plan MYPLAN \
    --toollib MY.LOADLIB
```

**Options:**

- `--program NAME` — Name of the Db2-bound program to run (required)
- `--system ID` — Db2 subsystem ID (or `DB2_SYSTEM`) (required)
- `--plan NAME` — Db2 plan name bound for the program (required)
- `--toollib LIB` — Load library containing the program (required)
- `--parm STRING` — Optional PARM string to pass to the program
- `--steplib DATASET` — STEPLIB dataset(s), colon-separated (or `DB2_STEPLIB`)
- `--systsprt PATH` — SYSTSPRT output file or `stdout` (default: `stdout`)
- `--sysprint PATH` — SYSPRINT output file or `stdout` (default: `stdout`)
- `-v, --verbose` — Enable verbose output

**Notes:**

- No SYSIN SQL input is used — all parameters are on the RUN PROGRAM subcommand
- The program must be bound to Db2 with the specified plan

---

### db2op — Execute Db2 Operator Commands

Executes Db2 operator commands (`-DISPLAY`, `-START`, `-STOP`, etc.) via DSNTIAD.
Replaces the former `db2admin` command.

```bash
# Inline operator command (leading '-' is optional)
db2op "-DISPLAY DATABASE(*)"
db2op "DISPLAY DATABASE(CBSA) SPACENAM(*) USE"

# From a file
db2op --file opcmds.txt

# From stdin
echo "-STOP DATABASE(CBSA) MODE(QUIESCE)" | db2op

# With explicit connection parameters
db2op "-DISPLAY THREAD(*)" --system DB2P --plan DSNTIAD \
    --toollib DSNC10.DBCG.RUNLIB.LOAD
```

**Options:**

- `COMMAND` — Inline operator command (positional, optional). Leading `-` is optional.
- `--file PATH` / `-f PATH` — File containing operator commands (mutually exclusive with inline and stdin)
- `--system ID` — Db2 subsystem ID (or `DB2_SYSTEM`)
- `--plan NAME` — Plan name for DSNTIAD (or `DB2_PLAN`)
- `--toollib LIB` — Tool library (or `DB2_TOOLLIB`)
- `--steplib DATASET` — STEPLIB dataset(s), colon-separated (or `DB2_STEPLIB`)
- `--systsprt PATH` — SYSTSPRT output file or `stdout` (default: `stdout`)
- `--sysprint PATH` — SYSPRINT output file or `stdout` (default: `stdout`)
- `-v, --verbose` — Enable verbose output

**Notes:**

- The leading `-` prefix on operator commands is optional and added automatically if missing
- Uses DSNTIAD, not DSNTEP2 — operator commands are not SQL

---

## Python API

### tsocmd()

Low-level function for general TSO command execution. Provide your own SYSTSIN and SYSIN files.

```python
from batchtsocmd.main import tsocmd

rc = tsocmd(
    systsin_file="systsin.txt",
    sysin_file="input.txt",
    systsprt_file="output.txt",
    sysprint_file="print.txt",
    steplib=["DB2V13.SDSNLOAD", "DB2V13.SDSNLOD2"],
    dbrmlib=["DB2V13.DBRMLIB"],
    verbose=True
)
```

**Parameters:** `systsin_file`, `sysin_file`, `systsprt_file` (default `'stdout'`),
`sysprint_file` (default `'stdout'`), `steplib` (str or list), `dbrmlib` (str or list), `verbose`

### db2sql()

Execute SQL statements via DSNTEP2.

```python
from batchtsocmd.main import db2sql

# From a content string
rc = db2sql(
    sysin_content="SET CURRENT SQLID = 'IBMUSER'; CREATE DATABASE CBSA BUFFERPOOL BP1 INDEXBP BP0;",
    system="DB2P",
    plan="DSNTEP12",
    toollib="DSNC10.DBCG.RUNLIB.LOAD",
    steplib="DB2V13.SDSNLOAD"
)

# From a file
rc = db2sql(
    sysin_file="schema.sql",
    system="DB2P",
    plan="DSNTEP12",
    toollib="DSNC10.DBCG.RUNLIB.LOAD"
)
```

**Parameters:** `sysin_content` or `sysin_file` (mutually exclusive, one required),
`system`, `plan`, `toollib` (all required), `dbrmlib`, `steplib`, `systsprt_file`, `sysprint_file`, `verbose`

### db2bind()

Bind Db2 packages and/or plans.

```python
from batchtsocmd.main import db2bind

rc = db2bind(
    system="DB2P",
    package="PCBSA",
    members=["CREACC", "CRECUST", "DELACC"],
    owner="IBMUSER",
    qualifier="IBMUSER",
    action="REPLACE",
    plan="CBSA",
    isolation="UR",
    pklist=["NULLID.*", "PCBSA.*"],
    dbrmlib="CBSA.CICSBSA.DBRM",
    steplib=["DB2V13.SDSNEXIT", "DB2V13.SDSNLOAD"]
)
```

**Parameters:** `system` (required), `package`, `plan` (at least one required),
`members` (required when `package` specified), `owner`, `qualifier`, `action` (default `'REPLACE'`),
`isolation`, `pklist`, `dbrmlib`, `steplib`, `systsprt_file`, `sysprint_file`, `verbose`

### db2run()

Run a Db2-bound program via DSN RUN PROGRAM.

```python
from batchtsocmd.main import db2run

rc = db2run(
    program="BANKDATA",
    system="DB2P",
    plan="CBSA",
    toollib="CBSA.CICSBSA.LOADLIB",
    parms="1,10000,1,1000000000000000",
    steplib=["CBSA.CICSBSA.DBRM", "CBSA.CICSBSA.LOADLIB", "DB2V13.SDSNLOAD"]
)
```

**Parameters:** `program`, `system`, `plan`, `toollib` (all required),
`parms`, `steplib`, `systsprt_file`, `sysprint_file`, `verbose`

### db2op()

Execute Db2 operator commands via DSNTIAD.

```python
from batchtsocmd.main import db2op

rc = db2op(
    sysin_content="-DISPLAY DATABASE(*)",
    system="DB2P",
    plan="DSNTIAD",
    toollib="DSNC10.DBCG.RUNLIB.LOAD",
    steplib="DB2V13.SDSNLOAD"
)
```

**Parameters:** `sysin_content` or `sysin_file` (mutually exclusive, one required),
`system`, `plan`, `toollib` (all required), `steplib`, `systsprt_file`, `sysprint_file`, `verbose`

### Deprecated aliases

`db2cmd()` and `db2admin()` are retained as backward-compatible aliases for `db2sql()` and `db2op()` respectively. They will be removed in a future version.

---

## How It Works

All Db2 commands follow the same execution pipeline:

1. **SYSTSIN generation** — Each function generates the appropriate DSN subcommands in SYSTSIN:
   - `db2sql`: `DSN SYSTEM(...)` → `RUN PROGRAM(DSNTEP2) PLAN(...) LIB(...) PARMS('/ALIGN(MID)')`
   - `db2bind`: `DSN SYSTEM(...)` → `BIND PACKAGE(...)` / `BIND PLAN(...)` subcommands
   - `db2run`: `DSN SYSTEM(...)` → `RUN PROGRAM(...) PLAN(...) LIB(...)`
   - `db2op`: `DSN SYSTEM(...)` → `RUN PROGRAM(DSNTIAD) PLAN(...) LIB(...)`

2. **Encoding conversion** — Input files are auto-detected and converted from ASCII to EBCDIC (IBM-1047) as needed using `zos-ccsid-converter`

3. **SYSIN padding** — SQL input lines are padded to exactly 80 bytes for fixed-length MVS record format

4. **Execution** — `mvscmd.execute_authorized()` from ZOAU runs IKJEFT1B with the generated DD statements

5. **Output** — SYSTSPRT and SYSPRINT are written to files or stdout; output files are tagged IBM-1047

6. **Cleanup** — All temporary files are removed automatically

---

## License

Apache License 2.0

## Author

Mike Fulton
# batchtsocmd

Run TSO and Db2 commands via IKJEFT1B with automatic encoding conversion.

## Description

`batchtsocmd` is a Python utility for z/OS that executes TSO commands through IKJEFT1B with automatic ASCII/EBCDIC encoding conversion. It handles SYSIN and SYSTSIN inputs from files, automatically converting them to EBCDIC as needed.

The package includes three main commands:

- `batchtsocmd` - General TSO command execution
- `db2cmd` - Simplified Db2 SQL command execution via DSNTEP2
- `db2admin` - Simplified Db2 administrative command execution via DSNTIAD

## Features

- Execute TSO commands via IKJEFT1B
- Execute Db2 SQL commands via DSNTEP2
- Automatic ASCII to EBCDIC conversion for input files
- Optional STEPLIB support
- Optional DBRMLIB support
- Configurable output destinations (SYSTSPRT, SYSPRINT)
- Environment variable support for Db2 parameters
- Stdin piping support for SQL commands
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

## Usage

### batchtsocmd - General TSO Command Execution

#### Basic Usage

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt
```

### With Output Files

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --systsprt output.txt --sysprint print.txt
```

### With STEPLIB and Verbose Output

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --steplib DB2V13.SDSNLOAD --verbose
```

### With STEPLIB and DBRMLIB

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --steplib DB2V13.SDSNLOAD --dbrmlib DB2V13.DBRMLIB
```

### With Concatenated STEPLIB Datasets

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2:DB2V13.SDSNLOD3
```

### With Concatenated STEPLIB and DBRMLIB Datasets

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2 \
            --dbrmlib DB2V13.DBRMLIB:DB2V13.DBRMLI2
```

#### Command Line Options

- `--systsin PATH` - Path to SYSTSIN input file (required)
- `--sysin PATH` - Path to SYSIN input file (required)
- `--systsprt PATH` - Path to SYSTSPRT output file or 'stdout' (optional, defaults to stdout)
- `--sysprint PATH` - Path to SYSPRINT output file or 'stdout' (optional, defaults to stdout)
- `--steplib DATASET` - Optional STEPLIB dataset name(s). Use colon (`:`) to concatenate multiple datasets (e.g., `DB2V13.SDSNLOAD` or `DB2V13.SDSNLOAD:DB2V13.SDSNLOD2`)
- `--dbrmlib DATASET` - Optional DBRMLIB dataset name(s). Use colon (`:`) to concatenate multiple datasets (e.g., `DB2V13.DBRMLIB` or `DB2V13.DBRMLIB:DB2V13.DBRMLI2`)
- `-v, --verbose` - Enable verbose output
- `--version` - Show version number and exit

#### Notes

- Input files can be ASCII (ISO8859-1) or EBCDIC (IBM-1047)
- Encoding is auto-detected via file tags; untagged files are assumed to be EBCDIC
- Output files will be tagged as IBM-1047
- Both --systsprt and --sysprint default to 'stdout'
- When stdout is used, SYSTSPRT output is written first, then SYSPRINT output

### db2cmd - Db2 Command Execution

The `db2cmd` command provides a simplified interface for executing Db2 SQL commands via DSNTEP2.

#### Basic Usage

```bash
# Using command line options
db2cmd --system DB2P --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin query.sql

# Using environment variables
export DB2_SYSTEM=DB2P
export DB2_PLAN=DSNTEP12
export DB2_TOOLLIB=DSNC10.DBCG.RUNLIB.LOAD
db2cmd --sysin query.sql

# Using stdin pipe
echo "SELECT * FROM SYSIBM.SYSTABLES;" | db2cmd --system DB2P \
    --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD

# With STEPLIB
db2cmd --system DB2P --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin query.sql --steplib DB2V13.SDSNLOAD

# With DBRMLIB directory
db2cmd --system DB2P --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin query.sql --dbrmlib /u/myuser/dbrmlib

# With concatenated STEPLIB datasets
db2cmd --system DB2P --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin query.sql --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2
```

#### Command Line Options

- `--system ID` - Db2 subsystem ID (or set `DB2_SYSTEM` env var) (required)
- `--plan NAME` - Db2 plan name (or set `DB2_PLAN` env var) (required)
- `--toollib LIB` - Db2 tool library (or set `DB2_TOOLLIB` env var) (required)
- `--sysin PATH` - Path to SYSIN input file (optional, reads from stdin if not specified)
- `--systsprt PATH` - Path to SYSTSPRT output file or 'stdout' (optional, defaults to stdout)
- `--sysprint PATH` - Path to SYSPRINT output file or 'stdout' (optional, defaults to stdout)
- `--steplib DATASET` - Optional STEPLIB dataset name(s). Use colon (`:`) to concatenate multiple datasets
- `--dbrmlib DATASET` - Optional DBRMLIB dataset name(s) or directory (or set `DB2_DBRMLIB` env var). Use colon (`:`) to concatenate multiple datasets
- `-v, --verbose` - Enable verbose output
- `--version` - Show version number and exit

#### Environment Variables

- `DB2_SYSTEM` - Default Db2 subsystem ID
- `DB2_PLAN` - Default Db2 plan name
- `DB2_TOOLLIB` - Default Db2 tool library
- `DB2_DBRMLIB` - Default DBRMLIB dataset or directory

**Note:** Command line options override environment variables.

#### DBRMLIB Handling

The `--dbrmlib` option (or `DB2_DBRMLIB` environment variable) can specify:
- A dataset name (no slash): `DB2V13.DBRMLIB`
- Multiple datasets (colon-separated): `DB2V13.DBRMLIB:DB2V13.DBRMLI2`
- A directory path (contains slash): `/u/myuser/dbrmlib`
  - When a directory is specified, the command scans for `.dbm` files and uses them as datasets

#### Notes

- Input can be from a file (`--sysin`) or stdin (pipe)
- SQL commands are automatically padded to 80 bytes per line
- Output files will be tagged as IBM-1047
- Both `--systsprt` and `--sysprint` default to 'stdout'
- When stdout is used, SYSTSPRT output is written first, then SYSPRINT output

### db2admin - Db2 Administrative Command Execution

The `db2admin` command provides an interface for executing Db2 administrative commands via DSNTIAD. Unlike `db2cmd` which uses DSNTEP2 for SQL, `db2admin` uses DSNTIAD for administrative commands like DISPLAY, START, STOP, etc.

#### Basic Usage

```bash
# Using command line options
db2admin --system DB2P --plan DSNTIAD --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin admin.txt

# Using environment variables
export DB2_SYSTEM=DB2P
export DB2_PLAN=DSNTIAD
export DB2_TOOLLIB=DSNC10.DBCG.RUNLIB.LOAD
db2admin --sysin admin.txt

# Using stdin pipe
echo "-DISPLAY DATABASE(MYDB)" | db2admin --system DB2P \
    --plan DSNTIAD --toollib DSNC10.DBCG.RUNLIB.LOAD

# With STEPLIB
db2admin --system DB2P --plan DSNTIAD --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin admin.txt --steplib DB2V13.SDSNLOAD

# With concatenated STEPLIB datasets
db2admin --system DB2P --plan DSNTIAD --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin admin.txt --steplib DB2V13.SDSNLOAD:DB2V13.SDSNLOD2
```

#### Command Line Options

- `--system ID` - Db2 subsystem ID (or set `DB2_SYSTEM` env var) (required)
- `--plan NAME` - Db2 plan name (or set `DB2_PLAN` env var) (required)
- `--toollib LIB` - Db2 tool library (or set `DB2_TOOLLIB` env var) (required)
- `--sysin PATH` - Path to SYSIN input file (optional, reads from stdin if not specified)
- `--systsprt PATH` - Path to SYSTSPRT output file or 'stdout' (optional, defaults to stdout)
- `--sysprint PATH` - Path to SYSPRINT output file or 'stdout' (optional, defaults to stdout)
- `--steplib DATASET` - Optional STEPLIB dataset name(s). Use colon (`:`) to concatenate multiple datasets
- `-v, --verbose` - Enable verbose output
- `--version` - Show version number and exit

#### Environment Variables

- `DB2_SYSTEM` - Default Db2 subsystem ID
- `DB2_PLAN` - Default Db2 plan name
- `DB2_TOOLLIB` - Default Db2 tool library

**Note:** Command line options override environment variables.

#### Key Differences from db2cmd

- Uses DSNTIAD instead of DSNTEP2
- Does not require DBRMLIB parameter
- Does not pass PARMS to the utility program
- Designed for administrative commands rather than SQL queries

#### Notes

- Input can be from a file (`--sysin`) or stdin (pipe)
- Administrative commands are automatically padded to 80 bytes per line
- Output files will be tagged as IBM-1047
- Both `--systsprt` and `--sysprint` default to 'stdout'
- When stdout is used, SYSTSPRT output is written first, then SYSPRINT output

## Python API

### version Function

Get the version of the batchtsocmd package:

```python
from batchtsocmd import version

# Get version string
ver = version()
print(f"batchtsocmd version: {ver}")
```

You can also access the version directly:

```python
from batchtsocmd import __version__

print(f"batchtsocmd version: {__version__}")
```

### tsocmd Function

You can use the `tsocmd` function directly in Python for general TSO command execution:

```python
from batchtsocmd.main import tsocmd

# Execute TSO command with SYSTSIN and SYSIN files
rc = tsocmd(
    systsin_file="systsin.txt",
    sysin_file="input.txt",
    systsprt_file="output.txt",
    sysprint_file="print.txt",
    steplib="DB2V13.SDSNLOAD",
    verbose=True
)

# With concatenated STEPLIB datasets
rc = tsocmd(
    systsin_file="systsin.txt",
    sysin_file="input.txt",
    steplib=["DB2V13.SDSNLOAD", "DB2V13.SDSNLOD2"],
    dbrmlib=["DB2V13.DBRMLIB", "DB2V13.DBRMLI2"],
    verbose=True
)

# Output to stdout (default)
rc = tsocmd(
    systsin_file="systsin.txt",
    sysin_file="input.txt",
    steplib="DB2V13.SDSNLOAD"
)
```

#### Parameters

- `systsin_file` - Path to SYSTSIN input file (required)
- `sysin_file` - Path to SYSIN input file (required)
- `systsprt_file` - Output destination for SYSTSPRT (default: 'stdout')
- `sysprint_file` - Output destination for SYSPRINT (default: 'stdout')
- `steplib` - Optional STEPLIB dataset(s) - single string or list for concatenation
- `dbrmlib` - Optional DBRMLIB dataset(s) - single string or list for concatenation
- `verbose` - Enable verbose output

#### How It Works

The `tsocmd` function executes TSO commands through the IKJEFT1B batch processor with the following workflow:

1. **Input Validation**: Validates that both SYSTSIN and SYSIN input files exist and are readable

2. **Encoding Conversion**:
   - Automatically detects file encoding using file tags
   - Converts ASCII (ISO8859-1) files to EBCDIC (IBM-1047) as needed
   - Untagged files are assumed to be EBCDIC and copied as-is
   - Uses the `zos-ccsid-converter` package for reliable conversion

3. **SYSIN Padding**:
   - Pads each line in the SYSIN file to exactly 80 bytes
   - Truncates lines longer than 80 bytes with a warning
   - Ensures proper fixed-length record format for MVS processing

4. **DD Statement Setup**:
   - Creates DD statements for IKJEFT1B execution
   - Configures STEPLIB if provided (supports concatenation)
   - Configures DBRMLIB if provided (supports concatenation)
   - Sets up SYSTSIN with converted input
   - Sets up SYSIN with padded and converted input
   - Configures SYSTSPRT and SYSPRINT outputs (file or stdout)
   - Adds SYSUDUMP as DUMMY

5. **Execution**:
   - Executes IKJEFT1B using `mvscmd.execute_authorized()` from ZOAU
   - Runs with proper DD allocations and file definitions

6. **Output Handling**:
   - If stdout is requested, reads temporary output files and writes to stdout
   - Outputs SYSTSPRT first, then SYSPRINT (maintaining proper order)
   - Tags output files as IBM-1047 for proper encoding
   - Returns the IKJEFT1B return code

7. **Cleanup**:
   - Automatically removes all temporary files
   - Ensures cleanup even if errors occur

This approach provides a seamless way to execute TSO commands from Python with automatic handling of encoding conversions and proper MVS file formats.

### db2cmd Function

You can use the `db2cmd` function directly in Python for Db2 command execution:

```python
from batchtsocmd.main import db2cmd

# Using content string
rc = db2cmd(
    sysin_content="SELECT * FROM SYSIBM.SYSTABLES;",
    system="DB2P",
    plan="DSNTEP12",
    toollib="DSNC10.DBCG.RUNLIB.LOAD",
    steplib="DB2V13.SDSNLOAD",
    verbose=True
)

# Using file
rc = db2cmd(
    sysin_file="query.sql",
    system="DB2P",
    plan="DSNTEP12",
    toollib="DSNC10.DBCG.RUNLIB.LOAD"
)
```

#### Parameters

- `sysin_content` - SQL commands as a string (mutually exclusive with sysin_file)
- `sysin_file` - Path to file containing SQL commands (mutually exclusive with sysin_content)
- `system` - Db2 subsystem ID (required)
- `plan` - Db2 plan name (required)
- `toollib` - Db2 tool library (required)
- `dbrmlib` - Optional DBRMLIB dataset(s) - single string or list for concatenation
- `steplib` - Optional STEPLIB dataset(s) - single string or list for concatenation
- `systsprt_file` - Output destination for SYSTSPRT (default: 'stdout')
- `sysprint_file` - Output destination for SYSPRINT (default: 'stdout')
- `verbose` - Enable verbose output

### db2admin Function

You can use the `db2admin` function directly in Python for Db2 administrative command execution:

```python
from batchtsocmd.main import db2admin

# Using content string
rc = db2admin(
    sysin_content="-DISPLAY DATABASE(MYDB)",
    system="DB2P",
    plan="DSNTIAD",
    toollib="DSNC10.DBCG.RUNLIB.LOAD",
    steplib="DB2V13.SDSNLOAD",
    verbose=True
)

# Using file
rc = db2admin(
    sysin_file="admin.txt",
    system="DB2P",
    plan="DSNTIAD",
    toollib="DSNC10.DBCG.RUNLIB.LOAD"
)
```

#### Parameters

- `sysin_content` - DB2 administrative commands as a string (mutually exclusive with sysin_file)
- `sysin_file` - Path to file containing DB2 administrative commands (mutually exclusive with sysin_content)
- `system` - Db2 subsystem ID (required)
- `plan` - Db2 plan name (required)
- `toollib` - Db2 tool library (required)
- `steplib` - Optional STEPLIB dataset(s) - single string or list for concatenation
- `systsprt_file` - Output destination for SYSTSPRT (default: 'stdout')
- `sysprint_file` - Output destination for SYSPRINT (default: 'stdout')
- `verbose` - Enable verbose output

#### Key Differences from db2cmd

- Uses DSNTIAD instead of DSNTEP2
- Does not support DBRMLIB parameter (not needed for administrative commands)
- Does not pass PARMS to the utility program
- Designed for administrative commands (DISPLAY, START, STOP, etc.) rather than SQL

## License

Apache License 2.0

## Author

Mike Fulton
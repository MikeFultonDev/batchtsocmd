# Db2 Command Implementation Summary

## Overview

Successfully implemented a new method for running Db2 commands from both Python and shell, providing a simplified interface for executing Db2 SQL commands via DSNTEP2.

## What Was Implemented

### 1. Python Function: `db2cmd()`

**Location:** `src/batchtsocmd/main.py` (lines 328-440)

**Key Features:**
- Accepts SQL commands as either a string (`sysin_content`) or file (`sysin_file`)
- Automatically generates SYSTSIN content with DSN commands
- Validates all required parameters (system, plan, toollib)
- Supports optional STEPLIB and DBRMLIB datasets
- Handles temporary file creation and cleanup
- Returns execution return code

**Function Signature:**
```python
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
) -> int
```

### 2. CLI Module: `db2_cli.py`

**Location:** `src/batchtsocmd/db2_cli.py`

**Key Features:**
- Command-line interface for the `db2cmd` function
- Environment variable support (DB2_SYSTEM, DB2_PLAN, DB2_TOOLLIB, DB2_DBRMLIB)
- Command-line options override environment variables
- Stdin piping support for SQL commands
- DBRMLIB directory scanning (finds .dbm files)
- Comprehensive help and usage information

**Command-Line Options:**
- `--system <id>` - Db2 subsystem ID
- `--plan <name>` - Db2 plan name
- `--toollib <lib>` - Db2 tool library
- `--sysin <file>` - SYSIN input file (optional, uses stdin if not specified)
- `--systsprt <file>` - SYSTSPRT output file (default: stdout)
- `--sysprint <file>` - SYSPRINT output file (default: stdout)
- `--steplib <dataset>` - STEPLIB dataset(s), colon-separated
- `--dbrmlib <dataset>` - DBRMLIB dataset(s) or directory
- `-v, --verbose` - Enable verbose output

### 3. Configuration Updates

**pyproject.toml:**
- Added `db2 = "batchtsocmd.db2_cli:main"` to `[project.scripts]`
- Updated version to 0.1.10

**src/batchtsocmd/__init__.py:**
- Exported `db2cmd` function
- Updated version to 0.1.10

### 4. Documentation

**README.md:**
- Added comprehensive documentation for the `db2` command
- Included usage examples for both CLI and Python API
- Documented environment variables
- Explained DBRMLIB handling (datasets vs directories)

**DB2CMD_IMPLEMENTATION_PLAN.md:**
- Detailed implementation plan with specifications
- Architecture and design decisions
- Usage examples and error handling strategies

### 5. Tests

**tests/test_db2cmd.py:**
- Added 8 new test cases for `db2cmd` function:
  - `test_05_db2cmd_with_file` - Test with file input
  - `test_06_db2cmd_with_content` - Test with content string
  - `test_07_db2cmd_validation_both_sysin` - Validation: both parameters
  - `test_08_db2cmd_validation_no_sysin` - Validation: no parameters
  - `test_09_db2cmd_validation_missing_system` - Validation: missing system
  - `test_10_db2cmd_validation_missing_plan` - Validation: missing plan
  - `test_11_db2cmd_validation_missing_toollib` - Validation: missing toollib
  - `test_12_db2cmd_with_stdout` - Test stdout output

## Usage Examples

### Shell Command

```bash
# Using command line options
db2 --system DB2P --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin query.sql --steplib DB2V13.SDSNLOAD

# Using environment variables
export DB2_SYSTEM=DB2P
export DB2_PLAN=DSNTEP12
export DB2_TOOLLIB=DSNC10.DBCG.RUNLIB.LOAD
db2 --sysin query.sql

# Using stdin pipe
echo "SELECT * FROM SYSIBM.SYSTABLES;" | db2 --system DB2P \
    --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD
```

### Python API

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

## Key Design Decisions

1. **Parameter Naming:** Used `system`, `plan`, and `toollib` (not `system_id`, `plan_name`, `tool_lib`) for consistency and brevity.

2. **Environment Variables:** Named as `DB2_SYSTEM`, `DB2_PLAN`, `DB2_TOOLLIB`, `DB2_DBRMLIB` for clarity and consistency.

3. **SYSTSIN Generation:** Automatically generates the DSN commands with the pattern:
   ```
   DSN SYSTEM(system)
   RUN PROGRAM(DSNTEP2) PLAN(plan) -
        LIB('toollib') PARMS('/ALIGN(MID)')
   END
   ```

4. **Input Flexibility:** Supports both file input and content string for SYSIN, plus stdin piping for the CLI.

5. **DBRMLIB Handling:** Supports both dataset names and directory paths. When a directory is specified, scans for .dbm files.

6. **Error Handling:** Comprehensive validation with clear error messages and appropriate return codes.

7. **Reusability:** Leverages existing `execute_tso_command()` function to avoid code duplication.

## Files Modified/Created

### Created:
- `src/batchtsocmd/db2_cli.py` - CLI module for db2 command
- `DB2CMD_IMPLEMENTATION_PLAN.md` - Detailed implementation plan
- `DB2CMD_IMPLEMENTATION_SUMMARY.md` - This summary document

### Modified:
- `src/batchtsocmd/main.py` - Added `db2cmd()` function
- `src/batchtsocmd/__init__.py` - Exported `db2cmd`, updated version
- `pyproject.toml` - Added db2 script entry, updated version
- `README.md` - Added comprehensive db2cmd documentation
- `tests/test_db2cmd.py` - Added 8 new test cases

## Testing

All tests are in `tests/test_db2cmd.py`:
- 4 existing tests for `execute_tso_command()` with Db2
- 8 new tests for `db2cmd()` function
- Tests cover validation, file input, content input, and stdout output

## Installation

After installation via pip, users will have access to:
1. `batchtsocmd` command (existing)
2. `db2` command (new)
3. Python API: `from batchtsocmd.main import db2cmd`

## Next Steps

To use the new functionality:

1. **Install/Upgrade the package:**
   ```bash
   pip install --upgrade batchtsocmd
   ```

2. **Set environment variables (optional):**
   ```bash
   export DB2_SYSTEM=DB2P
   export DB2_PLAN=DSNTEP12
   export DB2_TOOLLIB=DSNC10.DBCG.RUNLIB.LOAD
   ```

3. **Run Db2 commands:**
   ```bash
   db2 --sysin query.sql
   # or
   echo "SELECT * FROM SYSIBM.SYSTABLES;" | db2
   ```

## Benefits

1. **Simplified Interface:** No need to manually create SYSTSIN files for Db2 commands
2. **Environment Variables:** Set once, use everywhere
3. **Stdin Support:** Easy integration with pipes and scripts
4. **Consistent API:** Follows same patterns as `batchtsocmd`
5. **Comprehensive Testing:** Well-tested with multiple scenarios
6. **Good Documentation:** Clear examples and usage instructions

## Version

Current version: **0.1.10**
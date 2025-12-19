# Db2 Command Implementation Plan

## Overview

Create a new method for running Db2 commands from both Python and shell, similar to the existing `batchtsocmd` functionality but specifically tailored for Db2 operations.

## Components

### 1. Python Function: `db2cmd()`

**Location:** `src/batchtsocmd/main.py`

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

**Parameters:**
- `sysin_content`: SQL commands as a string (mutually exclusive with sysin_file)
- `sysin_file`: Path to file containing SQL commands (mutually exclusive with sysin_content)
- `system`: Db2 subsystem ID (required)
- `plan`: Db2 plan name (required)
- `toollib`: Db2 tool library (required)
- `dbrmlib`: Optional DBRMLIB dataset(s) - single string or list for concatenation
- `steplib`: Optional STEPLIB dataset(s) - single string or list for concatenation
- `systsprt_file`: Output destination for SYSTSPRT (default: 'stdout')
- `sysprint_file`: Output destination for SYSPRINT (default: 'stdout')
- `verbose`: Enable verbose output

**Behavior:**
1. Validate that exactly one of sysin_content or sysin_file is provided
2. Validate that system, plan, and toollib are provided
3. Generate SYSTSIN content with DSN commands:
   ```
   DSN SYSTEM(system)
   RUN PROGRAM(DSNTEP2) PLAN(plan) -
        LIB('toollib') PARMS('/ALIGN(MID)')
   END
   ```
4. Create temporary SYSTSIN file with generated content
5. Handle SYSIN input (either from content string or file)
6. Call existing `execute_tso_command()` with appropriate parameters
7. Clean up temporary files
8. Return the return code

### 2. Shell Script: `db2`

**Location:** Root directory as `db2` (executable shell script)

**Command Line Interface:**
```bash
db2 [OPTIONS]
```

**Options:**
- `--system <id>` or env var `DB2_SYSTEM`: Db2 subsystem ID (required)
- `--plan <name>` or env var `DB2_PLAN`: Db2 plan name (required)
- `--toollib <lib>` or env var `DB2_TOOLLIB`: Db2 tool library (required)
- `--sysin <file>`: Path to SYSIN file (optional, can use stdin via pipe)
- `--systsprt <file>`: SYSTSPRT output file (default: stdout)
- `--sysprint <file>`: SYSPRINT output file (default: stdout)
- `--steplib <dataset>`: STEPLIB dataset(s), colon-separated for concatenation
- `--dbrmlib <dataset>` or env var `DB2_DBRMLIB`: DBRMLIB dataset(s) or directory
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

**Environment Variables:**
- `DB2_SYSTEM`: Default Db2 subsystem ID
- `DB2_PLAN`: Default Db2 plan name
- `DB2_TOOLLIB`: Default Db2 tool library
- `DB2_DBRMLIB`: Default DBRMLIB dataset or directory

**Precedence:** Command line options override environment variables

**SYSIN Handling:**
- If `--sysin <file>` is specified, read from file
- Otherwise, read from stdin (allows piping)
- Create temporary file for stdin content if needed

**DBRMLIB Handling:**
- Can be a dataset name (no slash) or directory path (contains slash)
- If directory, scan for .dbm files and concatenate as datasets
- Support colon-separated concatenation like STEPLIB

**Behavior:**
1. Parse command line arguments
2. Check environment variables for missing required parameters
3. Validate that all required parameters are present
4. Handle SYSIN input (file or stdin)
5. Generate SYSTSIN content
6. Call Python `db2cmd()` function or execute via Python
7. Return appropriate exit code

### 3. Configuration Updates

**pyproject.toml:**
Add new script entry:
```toml
[project.scripts]
batchtsocmd = "batchtsocmd.main:main"
db2 = "batchtsocmd.db2_cli:main"
```

Create new module `src/batchtsocmd/db2_cli.py` for the CLI entry point.

## Implementation Steps

### Step 1: Implement Python `db2cmd()` Function

1. Add function to `src/batchtsocmd/main.py`
2. Reuse existing helper functions:
   - `convert_to_ebcdic()`
   - `pad_sysin_to_80_bytes()`
   - `validate_input_file()`
   - `execute_tso_command()`
3. Add SYSTSIN generation logic
4. Handle temporary file creation and cleanup

### Step 2: Create CLI Module

1. Create `src/batchtsocmd/db2_cli.py`
2. Implement argument parsing
3. Implement environment variable handling
4. Implement SYSIN input handling (file vs stdin)
5. Implement DBRMLIB directory scanning
6. Call `db2cmd()` function with parsed parameters

### Step 3: Update Configuration

1. Update `pyproject.toml` to add `db2` script entry
2. Update version number if needed

### Step 4: Documentation

1. Update `README.md` with db2cmd usage examples
2. Add section for Python API usage
3. Add section for shell script usage
4. Document environment variables
5. Provide examples for common scenarios

### Step 5: Testing

1. Create unit tests for `db2cmd()` function
2. Create integration tests for shell script
3. Test environment variable handling
4. Test stdin piping
5. Test DBRMLIB directory scanning
6. Test error conditions and validation

## Example Usage

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

### Shell Script

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

# With DBRMLIB directory
db2 --system DB2P --plan DSNTEP12 --toollib DSNC10.DBCG.RUNLIB.LOAD \
    --sysin query.sql --dbrmlib /u/myuser/dbrmlib
```

## Error Handling

1. **Missing Required Parameters:**
   - Print clear error message indicating which parameter is missing
   - Show usage/help information
   - Exit with code 1

2. **Invalid SYSIN Input:**
   - Validate that exactly one of sysin_content, sysin_file, or stdin is provided
   - Exit with code 1 if validation fails

3. **File Not Found:**
   - Check if specified files exist before processing
   - Exit with code 8 (consistent with batchtsocmd)

4. **Execution Errors:**
   - Return the actual return code from IKJEFT1B execution
   - Preserve error messages in output

## Testing Strategy

1. **Unit Tests:**
   - Test parameter validation
   - Test SYSTSIN generation
   - Test temporary file handling
   - Test error conditions

2. **Integration Tests:**
   - Test with valid Db2 subsystem
   - Test with invalid subsystem (expect failure)
   - Test stdin piping
   - Test file input
   - Test environment variable precedence
   - Test DBRMLIB directory scanning

3. **Edge Cases:**
   - Empty SYSIN content
   - Very long SQL statements
   - Special characters in parameters
   - Missing optional parameters
   - Concatenated datasets

## Compatibility

- Maintain backward compatibility with existing `batchtsocmd` functionality
- Follow same patterns for STEPLIB and DBRMLIB handling
- Use same encoding conversion approach
- Consistent error handling and return codes
- Same output formatting (SYSTSPRT before SYSPRINT)

## Future Enhancements

1. Support for additional Db2 programs (DSNTIAD, DSNTIAUL, etc.)
2. Configuration file support for common parameters
3. Interactive mode for SQL input
4. Result formatting options
5. Connection pooling for multiple commands
# Implementation Plan: Default stdout for SYSTSPRT and SYSPRINT

## Overview

Change the batchtsocmd interface so that both SYSTSPRT and SYSPRINT default to 'stdout' instead of DUMMY and stdout respectively. When stdout is requested, use temporary files internally (not passed to mvscmdauth), then read and output to stdout after IKJEFT1B completes.

## Current Behavior

- `--systsprt`: Defaults to DUMMY if not specified
- `--sysprint`: Defaults to stdout if not specified (already uses temp file internally)

## Required Changes

### 1. Argument Parser Updates

**File:** [`src/batchtsocmd/main.py`](src/batchtsocmd/main.py:270)

- Change `--systsprt` default from `None` to `'stdout'`
- Keep `--sysprint` default as `'stdout'` (currently `None` but treated as stdout)
- Update help text to reflect new defaults

**Lines to modify:**
- Line 270-273: Update `--systsprt` argument definition
- Line 275-278: Update `--sysprint` argument definition

### 2. Function Signature Updates

**File:** [`src/batchtsocmd/main.py`](src/batchtsocmd/main.py:87)

Update [`execute_tso_command()`](src/batchtsocmd/main.py:87) function:
- Change default values for `systsprt_file` and `sysprint_file` from `None` to `'stdout'`
- Update docstring to reflect new defaults

**Lines to modify:**
- Line 87-89: Function signature
- Line 98-99: Docstring

### 3. Temporary File Management

**File:** [`src/batchtsocmd/main.py`](src/batchtsocmd/main.py:119)

Add logic to handle 'stdout' as a special value:
- Create `temp_systsprt` variable (similar to existing `temp_sysprint`)
- When `systsprt_file == 'stdout'`, create temporary file with recfm=fb, lrecl=80
- When `sysprint_file == 'stdout'`, create temporary file (already exists but needs consistency)
- Tag temporary files as IBM-1047

**Lines to modify:**
- Line 119-122: Add `temp_systsprt` initialization
- Line 147-153: Update SYSTSPRT DD statement logic

### 4. DD Statement Creation

**File:** [`src/batchtsocmd/main.py`](src/batchtsocmd/main.py:147)

Update DD statement creation logic:
- Check if `systsprt_file == 'stdout'` → use temp file
- Check if `sysprint_file == 'stdout'` → use temp file (already implemented)
- Otherwise use the specified file path

**Lines to modify:**
- Line 147-153: SYSTSPRT DD statement
- Line 158-170: SYSPRINT DD statement (verify consistency)

### 5. Post-Execution Output

**File:** [`src/batchtsocmd/main.py`](src/batchtsocmd/main.py:192)

Implement output logic after IKJEFT1B execution:
1. If `systsprt_file == 'stdout'`, read temp file and write to stdout
2. If `sysprint_file == 'stdout'`, read temp file and write to stdout
3. **IMPORTANT:** Write SYSTSPRT output FIRST, then SYSPRINT output
4. Clean up temporary files

**Lines to modify:**
- Line 192-202: Expand this section to handle both SYSTSPRT and SYSPRINT
- Add new logic to read SYSTSPRT temp file if needed
- Ensure proper ordering: SYSTSPRT → SYSPRINT

### 6. Cleanup Logic

**File:** [`src/batchtsocmd/main.py`](src/batchtsocmd/main.py:224)

Update cleanup in finally block:
- Add cleanup for `temp_systsprt` if it exists
- Ensure both temp files are removed even on error

**Lines to modify:**
- Line 224-229: Add `temp_systsprt` cleanup

### 7. Documentation Updates

**File:** [`src/batchtsocmd/main.py`](src/batchtsocmd/main.py:237)

Update help text and examples:
- Change epilog to reflect new defaults
- Update line 253-254 to show both default to stdout

**File:** [`README.md`](README.md:59)

Update documentation:
- Line 59: Change "defaults to DUMMY" → "defaults to stdout"
- Line 60: Keep "defaults to stdout"
- Line 69: Update notes section

## Implementation Details

### Temporary File Creation Pattern

```python
# For SYSTSPRT when stdout is requested
if systsprt_file == 'stdout':
    temp_systsprt = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.systsprt')
    temp_systsprt.close()
    os.system(f"chtag -tc IBM-1047 {temp_systsprt.name}")
    dds.append(DDStatement('SYSTSPRT', FileDefinition(f"{temp_systsprt.name},lrecl=80,recfm=FB")))
```

### Output Reading Pattern

```python
# After IKJEFT1B execution, read and output in correct order
# 1. SYSTSPRT first (if stdout)
if systsprt_file == 'stdout' and temp_systsprt:
    try:
        with open(temp_systsprt.name, 'r', encoding='ibm1047') as f:
            print(f.read(), end='')
    except Exception as e:
        if verbose:
            print(f"Warning: Could not read SYSTSPRT output: {e}", file=sys.stderr)

# 2. SYSPRINT second (if stdout)
if sysprint_file == 'stdout' and temp_sysprint:
    try:
        with open(temp_sysprint.name, 'r', encoding='ibm1047') as f:
            print(f.read(), end='')
    except Exception as e:
        if verbose:
            print(f"Warning: Could not read SYSPRINT output: {e}", file=sys.stderr)
```

## Testing Considerations

1. Test with both SYSTSPRT and SYSPRINT defaulting to stdout
2. Test with only SYSTSPRT to stdout (SYSPRINT to file)
3. Test with only SYSPRINT to stdout (SYSTSPRT to file)
4. Test with both to files (explicit paths)
5. Verify output ordering when both use stdout
6. Verify temp file cleanup on success and error
7. Verify verbose mode shows correct information

## Key Requirements

- ✅ Both SYSTSPRT and SYSPRINT default to 'stdout'
- ✅ Use temporary files internally (not passed to mvscmdauth)
- ✅ Temporary files must have recfm=fb and lrecl=80
- ✅ Read temp files after IKJEFT1B completes
- ✅ Write SYSTSPRT output first, then SYSPRINT output
- ✅ Clean up temporary files properly
- ✅ Maintain backward compatibility with explicit file paths
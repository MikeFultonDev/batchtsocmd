# Changes Summary: batchtsocmd stdout Default Implementation

## Overview
Successfully implemented changes to make both SYSTSPRT and SYSPRINT default to 'stdout' for the batchtsocmd interface, and added SYSIN line padding to ensure each line is exactly 80 bytes.

## Files Modified

### 1. src/batchtsocmd/main.py

#### Function Signature (Lines 87-105)
- Changed `systsprt_file` parameter default from `None` to `'stdout'`
- Changed `sysprint_file` parameter default from `None` to `'stdout'`
- Updated docstring to reflect new defaults

#### Temporary File Management (Lines 157-161)
- Added `temp_systsprt` variable initialization
- Added `temp_sysin_padded` variable initialization
- Now tracks temporary files for both SYSTSPRT and SYSPRINT when stdout is requested
- Tracks padded SYSIN temporary file

#### SYSIN Padding Function (Lines 73-115)
- **New function:** `pad_sysin_to_80_bytes()`
- Pads each line in SYSIN file to exactly 80 bytes
- Truncates lines longer than 80 bytes with warning
- Right-pads shorter lines with spaces
- Creates temporary padded file that is cleaned up after processing

#### SYSIN Processing (Lines 171-181)
- First pads SYSIN to 80 bytes per line in temporary file
- Then converts padded file to EBCDIC
- Original SYSIN file is never modified
- Padded temporary file is cleaned up after successful processing

#### DD Statement Creation (Lines 147-177)
- **SYSTSPRT Logic (Lines 147-157):**
  - If `systsprt_file == 'stdout'`: creates temp file with recfm=fb, lrecl=80
  - Tags temp file as IBM-1047
  - Uses temp file in DD statement (not passed to mvscmdauth)
  - Otherwise: uses specified file path

- **SYSPRINT Logic (Lines 161-177):**
  - If `sysprint_file == 'stdout'`: creates temp file with recfm=fb, lrecl=80
  - Tags temp file as IBM-1047
  - Uses temp file in DD statement (not passed to mvscmdauth)
  - Otherwise: uses specified file path

#### Post-Execution Output (Lines 192-229)
- **Critical Ordering:** SYSTSPRT output written FIRST, then SYSPRINT output
- Reads temp files and writes to stdout only if content exists
- Proper error handling with verbose mode warnings
- Temp files cleaned up immediately after reading

#### File Tagging (Lines 233-242)
- Only tags actual files (not stdout) as IBM-1047
- Checks `!= 'stdout'` before tagging

#### Cleanup Logic (Lines 250-261)
- Added cleanup for `temp_systsprt` in finally block
- Added cleanup for `temp_sysprint` in finally block
- Ensures cleanup even on early exit or error

#### Argument Parser (Lines 302-312)
- `--systsprt`: default='stdout', updated help text
- `--sysprint`: default='stdout', updated help text

#### Help Text/Epilog (Lines 271-286)
- Updated example comment to clarify both go to stdout by default
- Updated notes to explain new default behavior
- Documented output ordering when both use stdout

### 2. README.md

#### Command Line Options (Lines 55-62)
- Updated `--systsprt` description to show 'stdout' default
- Updated `--sysprint` description to show 'stdout' default

#### Notes Section (Lines 64-70)
- Removed old note about DUMMY default
- Added note that both default to 'stdout'
- Added note about output ordering (SYSTSPRT first, then SYSPRINT)

## Key Implementation Details

### Temporary File Pattern
```python
if systsprt_file == 'stdout':
    temp_systsprt = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.systsprt')
    temp_systsprt.close()
    os.system(f"chtag -tc IBM-1047 {temp_systsprt.name}")
    dds.append(DDStatement('SYSTSPRT', FileDefinition(f"{temp_systsprt.name},lrecl=80,recfm=FB")))
```

### Output Ordering Pattern
```python
# 1. SYSTSPRT first
if systsprt_file == 'stdout' and temp_systsprt:
    with open(temp_systsprt.name, 'r', encoding='ibm1047') as f:
        content = f.read()
        if content:
            print(content, end='')

# 2. SYSPRINT second
if sysprint_file == 'stdout' and temp_sysprint:
    with open(temp_sysprint.name, 'r', encoding='ibm1047') as f:
        content = f.read()
        if content:
            print(content, end='')
```

## Requirements Met

✅ Both SYSTSPRT and SYSPRINT default to 'stdout'
✅ Use temporary files internally (not passed to mvscmdauth)
✅ Temporary files have recfm=fb and lrecl=80
✅ Read temp files after IKJEFT1B completes
✅ Write SYSTSPRT output first, then SYSPRINT output
✅ Clean up temporary files properly
✅ Maintain backward compatibility with explicit file paths
✅ Updated documentation and help text

## Testing Recommendations

1. **Both stdout (default):**
   ```bash
   batchtsocmd --systsin test.systsin --sysin test.sysin
   ```

2. **SYSTSPRT to file, SYSPRINT to stdout:**
   ```bash
   batchtsocmd --systsin test.systsin --sysin test.sysin --systsprt output.txt
   ```

3. **SYSTSPRT to stdout, SYSPRINT to file:**
   ```bash
   batchtsocmd --systsin test.systsin --sysin test.sysin --sysprint output.txt
   ```

4. **Both to files:**
   ```bash
   batchtsocmd --systsin test.systsin --sysin test.sysin --systsprt out1.txt --sysprint out2.txt
   ```

5. **Verify output ordering:**
   - Ensure SYSTSPRT content appears before SYSPRINT content when both use stdout

6. **Verify cleanup:**
   - Check that no temporary files remain after execution
   - Test cleanup on both success and error conditions

## Backward Compatibility

All existing usage patterns remain supported:
- Explicit file paths work as before
- Files are still tagged as IBM-1047
- Verbose mode provides detailed information
- Error handling unchanged
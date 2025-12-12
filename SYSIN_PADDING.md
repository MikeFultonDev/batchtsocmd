# SYSIN Padding Implementation

## Overview
Added automatic padding of SYSIN file lines to exactly 80 bytes to meet mainframe fixed-format requirements.

## Problem
Mainframe batch jobs with `recfm=FB` (Fixed Block) and `lrecl=80` require each line to be exactly 80 bytes. Variable-length lines can cause processing issues.

## Solution
Implemented `pad_sysin_to_80_bytes()` function that:
1. Reads the original SYSIN file
2. Processes each line:
   - Removes trailing newlines/whitespace
   - Truncates lines longer than 80 bytes (with warning)
   - Right-pads lines shorter than 80 bytes with spaces
3. Writes to a temporary padded file
4. The padded file is then converted to EBCDIC
5. Original file is never modified
6. Temporary padded file is cleaned up after processing

## Implementation Details

### Function: `pad_sysin_to_80_bytes()`
**Location:** `src/batchtsocmd/main.py` (Lines 73-115)

```python
def pad_sysin_to_80_bytes(input_path: str, output_path: str, verbose: bool = False) -> bool:
    """
    Pad each line in SYSIN file to exactly 80 bytes.
    
    Args:
        input_path: Source SYSIN file path
        output_path: Destination padded file path
        verbose: Enable verbose output
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as infile:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                for line_num, line in enumerate(infile, 1):
                    # Remove any trailing newline/whitespace
                    line = line.rstrip('\r\n')
                    
                    # Truncate if longer than 80 bytes
                    if len(line) > 80:
                        if verbose:
                            print(f"Warning: Line {line_num} truncated from {len(line)} to 80 bytes")
                        line = line[:80]
                    
                    # Pad to exactly 80 bytes
                    padded_line = line.ljust(80)
                    outfile.write(padded_line + '\n')
        
        if verbose:
            print(f"Padded SYSIN file to 80-byte records: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to pad SYSIN file: {e}", file=sys.stderr)
        return False
```

### Processing Flow

1. **Original SYSIN file** (user-provided, any line length)
   ↓
2. **Pad to 80 bytes** → `temp_sysin_padded` (temporary file)
   ↓
3. **Convert to EBCDIC** → `temp_sysin` (temporary file)
   ↓
4. **Pass to IKJEFT1B** via DD statement
   ↓
5. **Cleanup** both temporary files

### Code Changes

**Variable Initialization (Line 160):**
```python
temp_sysin_padded = None
```

**Processing (Lines 171-181):**
```python
# Pad SYSIN to 80 bytes per line, then convert to EBCDIC
temp_sysin_padded = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sysin.padded')
temp_sysin_padded.close()

if not pad_sysin_to_80_bytes(sysin_file, temp_sysin_padded.name, verbose):
    return 8

temp_sysin = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sysin')
temp_sysin.close()

if not convert_to_ebcdic(temp_sysin_padded.name, temp_sysin.name, verbose):
    return 8
```

**Cleanup (Lines 299-300):**
```python
if temp_sysin_padded and os.path.exists(temp_sysin_padded.name):
    os.unlink(temp_sysin_padded.name)
```

## Examples

### Input SYSIN (variable length):
```
SELECT * FROM TABLE;
UPDATE TABLE SET COL='VALUE' WHERE ID=1;
DELETE FROM TABLE WHERE STATUS='OLD';
```

### After Padding (exactly 80 bytes per line):
```
SELECT * FROM TABLE;                                                            
UPDATE TABLE SET COL='VALUE' WHERE ID=1;                                        
DELETE FROM TABLE WHERE STATUS='OLD';                                           
```
(Each line is exactly 80 characters, padded with spaces)

### Line Truncation Example:
If a line is longer than 80 bytes:
```
Input:  "SELECT * FROM VERY_LONG_TABLE_NAME WHERE COLUMN_WITH_VERY_LONG_NAME = 'SOME_VERY_LONG_VALUE_THAT_EXCEEDS_EIGHTY_CHARACTERS'"
Output: "SELECT * FROM VERY_LONG_TABLE_NAME WHERE COLUMN_WITH_VERY_LONG_NAME = 'SOME_VE"
```
With verbose mode, a warning is printed:
```
Warning: Line 1 truncated from 125 to 80 bytes
```

## Benefits

1. **Automatic Compliance:** Users don't need to manually pad their SYSIN files
2. **Error Prevention:** Prevents issues with mainframe fixed-format processing
3. **Non-Destructive:** Original file is never modified
4. **Clean:** Temporary files are automatically cleaned up
5. **Transparent:** Works seamlessly with existing code
6. **Verbose Mode:** Provides warnings when truncation occurs

## Testing

The existing tests in `tests/test_db2cmd.py` will automatically use the padding functionality since it's integrated into the SYSIN processing pipeline.

## Backward Compatibility

This change is fully backward compatible:
- Existing SYSIN files work as before
- Files already padded to 80 bytes are unchanged
- No changes to user interface or command-line arguments
- Automatic and transparent to users
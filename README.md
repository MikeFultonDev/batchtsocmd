# batchtsocmd

Run TSO commands via IKJEFT1B with automatic encoding conversion.

## Description

`batchtsocmd` is a Python utility for z/OS that executes TSO commands through IKJEFT1B with automatic ASCII/EBCDIC encoding conversion. It handles SYSIN and SYSTSIN inputs from files or named pipes, automatically converting them to EBCDIC as needed.

## Features

- Execute TSO commands via IKJEFT1B
- Automatic ASCII to EBCDIC conversion for input files
- Support for named pipes (FIFOs)
- Optional STEPLIB support
- Configurable output destinations (SYSTSPRT, SYSPRINT)
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

### Basic Usage

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt
```

### With Output Files

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --systsprt output.txt --sysprint print.txt
```

### Using Named Pipes

**Important:** When using named pipes, you must specify the `--source-encoding` parameter because z/OS pipes cannot store encoding metadata.

```bash
mkfifo /tmp/systsin.pipe /tmp/sysin.pipe /tmp/systsprt.pipe /tmp/sysprint.pipe
batchtsocmd --systsin /tmp/systsin.pipe --sysin /tmp/sysin.pipe \
            --systsprt /tmp/systsprt.pipe --sysprint /tmp/sysprint.pipe \
            --source-encoding IBM-1047
```

### With STEPLIB and Verbose Output

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --steplib DB2V13.SDSNLOAD --verbose
```

## Command Line Options

- `--systsin PATH` - Path to SYSTSIN input file or named pipe (required)
- `--sysin PATH` - Path to SYSIN input file or named pipe (required)
- `--systsprt PATH` - Path to SYSTSPRT output file or named pipe (optional, defaults to DUMMY)
- `--sysprint PATH` - Path to SYSPRINT output file or named pipe (optional, defaults to stdout)
- `--steplib DATASET` - Optional STEPLIB dataset name (e.g., DB2V13.SDSNLOAD)
- `--source-encoding ENCODING` - Source encoding for pipe inputs: `ISO8859-1` or `IBM-1047` (required for pipes, auto-detected for files)
- `-v, --verbose` - Enable verbose output

## Notes

- Input files can be ASCII (ISO8859-1) or EBCDIC (IBM-1047)
- For regular files: encoding is auto-detected via file tags; untagged files are assumed to be EBCDIC
- For named pipes: you **must** specify `--source-encoding` because z/OS pipes cannot store encoding metadata
- Output files will be tagged as IBM-1047
- If --systsprt is not specified, output goes to DUMMY
- If --sysprint is not specified, output goes to stdout (tagged as IBM-1047)

## License

Apache License 2.0

## Author

Mike Fulton
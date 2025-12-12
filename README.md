# batchtsocmd

Run TSO commands via IKJEFT1B with automatic encoding conversion.

## Description

`batchtsocmd` is a Python utility for z/OS that executes TSO commands through IKJEFT1B with automatic ASCII/EBCDIC encoding conversion. It handles SYSIN and SYSTSIN inputs from files, automatically converting them to EBCDIC as needed.

## Features

- Execute TSO commands via IKJEFT1B
- Automatic ASCII to EBCDIC conversion for input files
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

### With STEPLIB and Verbose Output

```bash
batchtsocmd --systsin systsin.txt --sysin input.txt \
            --steplib DB2V13.SDSNLOAD --verbose
```

## Command Line Options

- `--systsin PATH` - Path to SYSTSIN input file (required)
- `--sysin PATH` - Path to SYSIN input file (required)
- `--systsprt PATH` - Path to SYSTSPRT output file (optional, defaults to DUMMY)
- `--sysprint PATH` - Path to SYSPRINT output file (optional, defaults to stdout)
- `--steplib DATASET` - Optional STEPLIB dataset name (e.g., DB2V13.SDSNLOAD)
- `-v, --verbose` - Enable verbose output

## Notes

- Input files can be ASCII (ISO8859-1) or EBCDIC (IBM-1047)
- Encoding is auto-detected via file tags; untagged files are assumed to be EBCDIC
- Output files will be tagged as IBM-1047
- If --systsprt is not specified, output goes to DUMMY
- If --sysprint is not specified, output goes to stdout (tagged as IBM-1047)

## License

Apache License 2.0

## Author

Mike Fulton
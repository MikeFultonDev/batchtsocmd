# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-03-03

### Added
- **Filesystem-Based Binding for db2bind**: New `--library` parameter allows binding DBRM files directly from USS filesystem directories as an alternative to dataset-based binding with `--dbrmlib`
- **DB2_LIBRARY Environment Variable**: Support for `DB2_LIBRARY` environment variable to set default USS filesystem directory for DBRM files
- **Automatic .dbrm Extension Handling**: Member names with `.dbrm` extension are automatically stripped when specified
- **Debug Mode**: Added debug mode that preserves temporary files for troubleshooting across all commands (db2sql, db2bind, db2run, db2op)
- **Enhanced Test Coverage**: Added comprehensive tests for filesystem-based binding and .dbrm extension handling

### Changed
- **Mutual Exclusivity Enforcement**: `--library` and `--dbrmlib` parameters are now mutually exclusive with proper validation
- **Improved Error Messages**: Better validation and error messages for library path existence and parameter conflicts
- **Documentation**: Extensive README updates with separate sections for dataset-based vs filesystem-based binding, including new examples and API documentation

### Fixed
- Enhanced cleanup logic for temporary files with debug mode support

## [0.2.0] - 2024-XX-XX

### Added
- New command structure: `db2sql`, `db2op`, `db2bind`, `db2run`
- Deprecated `db2cmd` and `db2admin` as backward-compatible aliases

### Previous Versions
See git history for changes in versions prior to 0.2.0.
# Changelog

All notable changes to Autopsy Pro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-11-16

### Added
- **Parallel Processing**: Multi-threaded scanning and extraction using ThreadPoolExecutor
- **Smart Caching**: Configurable cache system with TTL to avoid redundant scans
- **CLI Interface**: Full command-line interface with commands for scan, extract, export, import, config, and cache
- **Export/Import**: Save and share fragment collections as JSON files
- **Enhanced Quality Scoring**: 14-factor quality assessment (up from 7)
- **Semantic Deduplication**: Two-stage deduplication (exact + semantic hash matching)
- **Configuration Validation**: Comprehensive validation with helpful error messages
- **Rich Metadata**: Detailed fragment metadata including imports, exports, complexity metrics
- **Dependency Detection**: Automatic detection of project dependencies and frameworks
- **Language Properties**: Dynamic language detection and categorization
- **Performance Metrics**: Detailed timing and resource usage tracking
- **Documentation**: Comprehensive README, QuickStart, and Comparison guides

### Changed
- **Data Models**: Migrated from simple dataclasses to rich models with properties and methods
- **Configuration System**: Moved from dict-based to validated dataclass-based config
- **Return Types**: Functions now return Result objects (ScanResult, ExtractionResult) instead of raw lists
- **Quality Assessment**: More sophisticated scoring with detailed metrics output
- **Error Handling**: Improved error handling with per-file isolation
- **Logging**: Enhanced logging with proper levels and formatting
- **Type Safety**: Added comprehensive type hints throughout

### Improved
- **Performance**: 3-5x faster scanning and extraction through parallelization
- **Accuracy**: Better duplicate detection catches ~4% more duplicates
- **Usability**: CLI enables automation and scripting workflows
- **Maintainability**: Better code organization and type safety
- **Documentation**: Extensive documentation with examples and guides

### Performance
- Scan time: 31.2s → 8.4s (3.7x faster) for 1000 files
- Extract time: 18.5s → 5.2s (3.6x faster)
- Quality scoring: 12.3s → 3.8s (3.2x faster)
- Overall workflow: 64.1s → 19.2s (3.3x faster)

### Breaking Changes
- Import path changed: `autopsy_pro_enhanced` → `autopsy_pro_v3`
- Function signatures now use Config objects
- Functions return Result objects instead of raw lists
- Some configuration keys renamed for clarity

### Migration Notes
- Config file location unchanged (~/.autopsy_pro/)
- Old config files will be automatically upgraded with new defaults
- Fragment UIDs remain compatible
- GUI remains compatible (same interface)

## [2.0.0] - 2024-11-16

### Added
- Multi-language support (Python, JS/TS, Go, Rust, Java, C/C++, Ruby, PHP)
- Modern tabbed UI with dark mode
- Project type detection
- Fragment organization by type
- Quality-based filtering
- Auto-generated README for built projects
- Settings persistence
- Progress indicators

### Changed
- Upgraded from basic to comprehensive language support
- Improved UI from single window to tabbed interface
- Enhanced project detection logic

### Improved
- Code organization with smart categorization
- Quality assessment algorithm
- User interface responsiveness

## [1.0.0] - 2024-10-01

### Added
- Initial release
- Basic Python and JavaScript support
- Simple directory scanning
- Basic fragment extraction
- Minimal tkinter UI
- Project building to 4 frameworks

---

## Version Comparison

| Version | Languages | UI | Quality Factors | Speed | Export |
|---------|-----------|----|--------------------|-------|--------|
| 1.0 | 2 | Basic | 3 | 1x | No |
| 2.0 | 8+ | Modern | 7 | 1x | No |
| 3.0 | 8+ | Modern + CLI | 14 | 3.3x | Yes |

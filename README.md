# Py-Recover / File Recovery System

A modular file recovery system for recovering files from disks with a clean architecture ready for both CLI and GUI interfaces.

## Features

- ✅ **Multiple file type recovery** - Supports txt, pdf, doc, xls, images, and more
- ✅ **Smart file detection** - Automatic file type detection using magic numbers
- ✅ **Wildcard search** - Search with patterns (* and % wildcards)
- ✅ **System file filtering** - Automatically filters system files
- ✅ **Original name recovery** - Attempts to recover original filenames from content
- ✅ **Deep scanning** - Multiple scanning methods for maximum recovery
- ✅ **Memory management** - Intelligent memory usage based on available RAM
- ✅ **Preview mode** - Preview files before recovery with selective recovery
- ✅ **Physical drive support** - Scan both logical and physical drives
- ✅ **Progress tracking** - Real-time progress with memory usage monitoring
- ✅ **Selective recovery** - Choose which files to recover from preview list

## Architecture

The project follows clean architecture principles with clear separation of responsibilities:

```
recovery/
├── main.py                 # Entry point
├── models/                 # Models and configurations
│   ├── __init__.py
│   ├── config.py          # Configuration, constants, file signatures
│   └── resource_config.py # Resource management and memory configuration
├── services/              # Business logic
│   ├── __init__.py
│   ├── disk_service.py    # Disk handling and detection
│   ├── detection_service.py  # File type detection
│   ├── filter_service.py  # File filtering
│   └── recovery_service.py  # Main recovery logic
├── controllers/           # Controllers (orchestration)
│   ├── __init__.py
│   └── recovery_controller.py
├── ui/                    # User interfaces
│   ├── __init__.py
│   ├── cli.py            # Command line interface
│   └── gui.py            # Graphical user interface
└── utils/                # Utilities
    ├── __init__.py
    ├── encoding_utils.py  # Encoding utilities
    └── file_utils.py     # File utilities
```

## Module Structure

### Models (`models/`)
- **config.py**: Contains constants, file signatures, and system configurations
  - `Config`: Main configuration
  - `FileSignatures`: File signatures (magic numbers)
  - `SystemFiles`: List of system files to filter
  - `SystemDirectories`: System directories to exclude
- **resource_config.py**: Memory and resource management configuration
  - `ResourceConfig`: Dynamic memory allocation based on available RAM
  - Performance modes: Performance, Balanced, Low Resources

### Services (`services/`)
- **disk_service.py**: Service for listing and getting disk information (logical and physical drives)
- **detection_service.py**: Service for detecting file types by signatures
- **filter_service.py**: Service for filtering files by criteria (wildcards, types, system files)
- **recovery_service.py**: Main service implementing recovery logic with multiple scanning methods

### Controllers (`controllers/`)
- **recovery_controller.py**: Controller that orchestrates services and coordinates recovery

### UI (`ui/`)
- **cli.py**: Command line interface
- **gui.py**: Graphical user interface with preview and selective recovery

### Utils (`utils/`)
- **encoding_utils.py**: Functions for encoding detection and text validation
- **file_utils.py**: Utilities for filename handling and original name extraction

## Installation

### Requirements

- Python 3.7+
- Windows (for physical drive access)
- Optional: `psutil` for better memory detection (falls back to Windows API if not available)
- Optional: `PIL` (Pillow) for application icon generation

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd recovery

# Install optional dependencies (recommended)
pip install psutil pillow
```

## Usage

### Command Line Interface (CLI)

```bash
python main.py
```

Or directly:
```bash
python main.py --cli
```

The CLI will guide you through:
1. Selecting a drive (logical or physical)
2. Choosing file types to recover
3. Setting search patterns (optional)
4. Selecting resource mode (Performance/Balanced/Low Resources)
5. Starting the recovery process

### Graphical User Interface (GUI)

```bash
python main.py --gui
```

Or:
```bash
python main.py -g
```

The GUI provides:
- **Drive Selection**: Choose logical or physical drives with model names
- **Preview Mode**: List files before recovery
- **Selective Recovery**: Select specific files from preview to recover
- **Resource Management**: Visual memory usage information
- **Progress Tracking**: Real-time progress with memory monitoring

### Resource Modes

- **Performance**: Uses 75% of total RAM (fastest, for systems with plenty of RAM)
- **Balanced**: Uses 50% of total RAM (recommended, good balance)
- **Low Resources**: Uses 25% of total RAM (for systems with limited RAM)

Memory limits are automatically calculated based on your system's available RAM.

## Features in Detail

### File Type Detection

The system detects files by:
- Magic numbers (file signatures)
- Content analysis
- Extension matching

Supported types: txt, pdf, doc, docx, xls, xlsx, ppt, pptx, zip, rar, jpg, png, gif, html, xml, json, csv, log, ini, cfg, and more.

### Original Name Recovery

The system attempts to extract original filenames from:
- File metadata
- Content headers
- Common filename patterns

If original name cannot be recovered, generic names are assigned.

### Memory Management

- **Dynamic buffer sizing**: Buffer size scales with available memory
- **Automatic cleanup**: Periodic memory cleanup to prevent excessive usage
- **Hash limit management**: Limits hash storage based on available RAM
- **Windows API fallback**: Uses Windows API if psutil is not available

### Preview and Selective Recovery

1. Run scan in Preview mode
2. Review found files in the Preview tab
3. Select files to recover using checkboxes
4. Click "Recover Selected" to recover only chosen files
5. Choose output directory and confirm

## Architecture Benefits

1. **Separation of concerns**: Each module has a clear responsibility
2. **Reusable**: Services can be used from CLI or GUI
3. **Testable**: Each component can be tested independently
4. **Scalable**: Easy to add new features
5. **Maintainable**: Well-organized and easy to understand code

## Technical Details

### Scanning Methods

The recovery system uses multiple scanning methods:
1. **Direct block scan**: Scans blocks directly for text content
2. **Sliding window**: Uses overlapping windows to find fragmented text
3. **Fragmented reconstruction**: Reconstructs fragmented files across blocks
4. **Offset scan**: Scans at various offsets to find misaligned files

### Memory Optimization

- Buffer size dynamically adjusts based on available RAM
- Hash storage scales with memory (up to 50M hashes with sufficient RAM)
- Cleanup intervals adjust based on memory availability
- Delays removed in balanced mode for better performance

## Limitations

- Currently optimized for Windows (physical drive access)
- Text-based file recovery (binary files may be partially recovered)
- Requires administrator privileges for physical drive access
- Large files may be truncated (1MB limit for preview/recovery from preview)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ☕ Support the Project

If you find this project helpful and want to support its development, you can help me with a coffee! ☕✨

Your support helps me continue improving this tool and adding new features. Every contribution, no matter how small, is greatly appreciated! 💙

### Cryptocurrency Donations

- **SOL (Solana)**: `C3vdmiDsECyNUuLdWjg3MqAV2j8JYNR1EM3RRntMawXa`
- **ETH (Ethereum)**: `0xd3943908c0977E7EeD5E6FE8fBee286b449a30Df`
- **BNB (Binance Coin)**: `0xd3943908c0977E7EeD5E6FE8fBee286b449a30Df`
- **HYPE**: `0xd3943908c0977E7EeD5E6FE8fBee286b449a30Df`
- **USD (USDC/USDT on Ethereum)**: `0xd3943908c0977E7EeD5E6FE8fBee286b449a30Df`

Thank you for your support! 🙏

## License

MIT License - Copyright (c) 2024 Francisco Botello

See [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with Python, tkinter, and Windows API for disk access.

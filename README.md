![Logo](/img/logo.png)
# Alter Download Manager

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
A high-performance, terminal-based download manager written in Python that focuses on speed and usability.

## Key Features

- **Multi-Part Downloading**: Accelerate downloads by splitting files into multiple parts
- **Concurrent Downloads**: Download multiple files simultaneously
- **Terminal UI**: Live management interface powered by Textual
- **Resource Efficient**: Optimized for minimal system resource usage
- **Resume Support**: Continue interrupted downloads from where they left off

## Installation

### From GitHub Release

```bash
pip install https://github.com/amirrezaes/alter/releases/latest/download/alter-0.1.0-py3-none-any.whl
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/amirrezaes/alter.git
cd alter
```

2. Install the package:
```bash
pip install -e .
```

Or install with development dependencies:
```bash
pip install -e .[dev]
```

## Usage

### Launch Interactive UI
```bash
alter
```

### Basic Download
```bash
alter https://example.com/file.zip -o output.zip
```

### Multiple Files
```bash
alter https://example.com/file1.zip https://example.com/file2.zip
```

### Command Line Options
```bash
alter [URLs...] [OPTIONS]

Options:
  -o, --output PATH    Specify output file path(s)
  -h, --help          Show help message
```

## Screenshots

### Add Download Link
![Image](/img/Capture1.svg)

### Downlaod View
![Image](/img/Capture2.svg)

## Requirements

- Python 3.11 or higher
- aiohttp >= 3.9.0
- aiofiles >= 23.2.1
- textual >= 0.50.0

## Roadmap

- [x] Live download management interface with mouse and keyboard interactions
- [x] Automatic filename detection from link
- [x] Download resume capability
- [ ] Web scraping capabilities
- [ ] Torrent client integration
- [ ] Browser extension
- [ ] Download scheduling
- [ ] Bandwidth throttling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/amirrezaes/alter.git
cd alter

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest
```

## Acknowledgments

- [Textual](https://github.com/Textualize/textual) for the terminal UI framework
- [aiohttp](https://github.com/aio-libs/aiohttp) for async HTTP client/server
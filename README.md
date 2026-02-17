![Logo](/img/logo.png)
# Alter Download Manager

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A high-performance, terminal-based download manager written in Python that focuses on speed and usability.

## Key Features

- **Multi-Part Downloading**: Accelerate downloads by splitting files into multiple parts
- **Concurrent Downloads**: Download multiple files simultaneously
- **Terminal UI**: Live management interface powered by Textual
- **Resource Efficient**: Optimized for minimal system resource usage

## Installation

1. Clone the repository:
```bash
git clone https://github.com/amirrezaes/alter.git
cd alter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install the package locally:
```bash
pip install -e .
```

## Usage

### Basic Download
```bash
alter https://example.com/file.zip -o output.zip
```

### Multiple Files
```bash
alter https://example.com/file1.zip https://example.com/file2.zip -o file1.zip file2.zip
```

### Launch UI With No URLs
```bash
alter
```

## Screenshots

### Single File Download
![Image](/img/Capture1.PNG)


### Multi File
![Image](/img/Capture2.JPG)

### Multiple Files Download![Multiple Files Download][]

## Roadmap

- [x] Live download management interface with mouse and keyboard intearctions
- [x] Automatic filename detection from link
- [ ] Web scraping capabilities
- [ ] Torrent client integration
- [x] Download resume capability
- [ ] Browser extension

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Rich](https://github.com/Textualize/rich) for the terminal interface

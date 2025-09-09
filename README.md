# prep - Python grep implementation

A powerful, feature-rich Python implementation of grep with advanced pattern matching capabilities.

## Features

### Beginner Level Features ✅
- **Basic pattern matching**: Search for text patterns in files
- **-v (invert match)**: Show lines that do not match the pattern
- **-c (count)**: Print only the number of matching lines per file
- **-q (quiet)**: Suppress output, exit status indicates whether a match was found
- **-e (multiple patterns)**: Search for multiple patterns simultaneously

### Intermediate Level Features ✅
- **-w (word match)**: Match whole words only
- **-x (line match)**: Match only if the whole line fits the pattern
- **Syntax highlighting**: Color matching substrings using ANSI escape codes
- **-A N, -B N, -C N (context lines)**: Show lines After, Before, or around matches

### Advanced Level Features ✅
- **-r (recursive search)**: Traverse directories and search in all files
- **Binary file handling**: Automatically detect and handle binary files
- **Parallel search**: Speed up searches across multiple files using threads
- **Regex flags**: Support for case-insensitive matching and other regex options

## Architecture

prep follows **Clean Architecture** and **SOLID principles**:

- **Domain Layer**: Core business logic and entities (`prep/domain/`)
- **Use Cases Layer**: Application business rules (`prep/usecases/`)
- **Infrastructure Layer**: External interfaces and implementations (`prep/infrastructure/`)
- **CLI Layer**: Command-line interface (`prep/cli/`)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd prep
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run prep:
```bash
python prep.py [options] PATTERN [FILES...]
```

## Usage

### Basic Examples

```bash
# Basic search
python prep.py "pattern" file.txt

# Search multiple files
python prep.py "pattern" *.txt

# Case-insensitive search
python prep.py -i "pattern" file.txt

# Count matches only
python prep.py -c "pattern" file.txt

# Quiet mode (no output, exit code indicates success)
python prep.py -q "pattern" file.txt
```

### Advanced Examples

```bash
# Multiple patterns
python prep.py -e "pattern1" -e "pattern2" file.txt

# Word boundaries
python prep.py -w "word" file.txt

# Exact line match
python prep.py -x "exact line content" file.txt

# Invert match (lines that don't match)
python prep.py -v "pattern" file.txt

# Recursive search in directory
python prep.py -r "pattern" /path/to/directory

# Context lines (2 before, 3 after)
python prep.py -B 2 -A 3 "pattern" file.txt

# Context around matches
python prep.py -C 2 "pattern" file.txt

# Parallel processing with 4 threads
python prep.py --threads 4 "pattern" *.txt

# Fixed string search (disable regex)
python prep.py -F "literal.string" file.txt
```

## Command Line Options

### Basic Options
- `PATTERN`: Search pattern (required unless using -e)
- `FILES`: Files to search (stdin if not specified)
- `-e, --regexp PATTERN`: Specify pattern (can be used multiple times)
- `-v, --invert-match`: Show lines that do not match
- `-c, --count`: Print only count of matching lines
- `-q, --quiet, --silent`: Suppress output, exit code indicates match

### Match Type Options
- `-w, --word-regexp`: Match whole words only
- `-x, --line-regexp`: Match whole lines only
- `-i, --ignore-case`: Ignore case distinctions

### Output Options
- `--color [auto|always|never]`: Use colors to highlight matches (default: auto)
- `-n, --line-number`: Show line numbers (default)
- `-H, --with-filename`: Show filename for each match
- `-h, --no-filename`: Suppress filename for each match

### Context Options
- `-A NUM, --after-context=NUM`: Show NUM lines after each match
- `-B NUM, --before-context=NUM`: Show NUM lines before each match
- `-C NUM, --context=NUM`: Show NUM lines before and after each match

### Directory Options
- `-r, --recursive`: Recursively search directories

### File Type Options
- `-I, --binary-files=[binary|without-match|text]`: How to handle binary files

### Performance Options
- `--threads N`: Use N threads for parallel processing

### Regex Options
- `-F, --fixed-strings`: Interpret patterns as fixed strings (not regex)
- `-E, --extended-regexp`: Use extended regular expressions

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=prep

# Run specific test categories
python -m pytest tests/unit/           # Unit tests only
python -m pytest tests/integration/   # Integration tests only
```

## Development

### Architecture Overview

```
prep/
├── domain/          # Core business logic
│   ├── models.py    # Domain entities and value objects
│   └── interfaces.py # Abstract interfaces
├── usecases/        # Application business rules
│   └── search_usecase.py # Search orchestration
├── infrastructure/ # External interfaces
│   ├── file_operations.py    # File I/O
│   ├── pattern_matching.py   # Pattern matching engines
│   ├── output_formatting.py  # Output formatting
│   └── parallel_execution.py # Parallel processing
└── cli/            # Command-line interface
    ├── argument_parser.py # CLI argument parsing
    └── application.py     # Main application
```

### Key Design Principles

1. **Dependency Inversion**: High-level modules don't depend on low-level modules
2. **Single Responsibility**: Each class has one reason to change
3. **Open/Closed**: Open for extension, closed for modification
4. **Interface Segregation**: Clients depend only on interfaces they use
5. **Liskov Substitution**: Subtypes must be substitutable for their base types

### Adding New Features

1. Define domain models in `prep/domain/models.py`
2. Create/update interfaces in `prep/domain/interfaces.py`
3. Implement use cases in `prep/usecases/`
4. Add infrastructure implementations in `prep/infrastructure/`
5. Update CLI layer in `prep/cli/`
6. Add comprehensive tests in `tests/`

## Performance

prep is optimized for performance with:

- **Parallel processing**: Multi-threaded file processing
- **Efficient pattern matching**: Hybrid regex/string matching
- **Binary file detection**: Skip binary files automatically
- **Memory efficient**: Streaming file processing
- **Early termination**: Stop on first match in quiet mode

## Exit Codes

- `0`: Matches found (or help displayed)
- `1`: No matches found
- `2`: Error occurred
- `130`: Interrupted (Ctrl+C)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the clean architecture principles
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by GNU grep
- Built with Python 3.8+ compatibility
- Follows clean architecture principles by Robert C. Martin
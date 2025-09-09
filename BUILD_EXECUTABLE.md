# Building Windows Executable for prep

This document explains how to create a Windows executable (`prep.exe`) from the Python source code.

## Overview

The prep application can be packaged into a standalone Windows executable using PyInstaller. This allows you to use `prep.exe` directly without needing Python installed on the target machine.

## Prerequisites

- Python 3.6 or later installed on your system
- Internet connection (to download PyInstaller if not already installed)

## Build Methods

### Use the Python Build Script

The easiest way to build the executable is using the provided Python script:

```bash
python build_exe.py
```

This script will:
1. Check if PyInstaller is installed and install it if needed
2. Build the executable using optimal settings
3. Provide detailed feedback and error handling
4. Work on any platform (Windows, Linux, macOS)

## Build Options Explained

The build process uses the following PyInstaller options:

- `--onefile`: Creates a single executable file (no separate DLLs)
- `--console`: Keeps the console window (appropriate for command-line tools)
- `--name prep`: Names the executable `prep.exe`
- `--distpath dist`: Puts the final executable in the `dist` folder
- `--workpath build`: Uses `build` folder for temporary files
- `--clean`: Cleans previous build artifacts
- `--noconfirm`: Overwrites existing files without prompting

## Output

After a successful build, you'll find:
- `prep.exe` in the `dist` folder
- Temporary build files in the `build` folder (can be deleted)
- `prep.spec` file (PyInstaller specification, can be deleted)

## Using the Executable

Once built, you can:

1. **Direct usage**: Navigate to the `dist` folder and run:
   ```
   prep.exe [options] pattern [files...]
   ```

2. **System-wide usage**: 
   - Copy `prep.exe` to a folder in your PATH (e.g., `C:\Windows\System32`)
   - Or add the `dist` folder to your Windows PATH
   - Then use `prep` from any command prompt

3. **Portable usage**: 
   - Copy `prep.exe` to any folder
   - Run it from that location

## Examples

```batch
# Search for "error" in all .log files
prep.exe error *.log

# Search with case-insensitive matching
prep.exe -i "warning" log.txt

# Search with context lines
prep.exe -A 2 -B 1 "exception" error.log

# File watching mode
prep.exe -f "error" application.log
```

## Troubleshooting

### Build Fails
- Ensure Python is installed and in your PATH
- Check internet connection (needed to download PyInstaller)
- Try running as administrator if you get permission errors

### Large Executable Size
- The executable will be 10-20MB due to bundled Python interpreter
- This is normal for PyInstaller-created executables
- The size allows the executable to run on any Windows machine

### Missing Dependencies
- If the executable fails to run, you might have imported modules not detected by PyInstaller
- Check the build output for any warnings about missing modules

### Performance
- The executable startup time will be slightly slower than running the Python script directly
- Runtime performance should be identical

## Cross-Platform Building

While these scripts create Windows executables, PyInstaller can create executables for the platform it runs on:
- Run on Windows → creates `prep.exe`
- Run on Linux → creates `prep` (Linux executable)  
- Run on macOS → creates `prep` (macOS executable)

## File Structure After Build

```
prep/
├── prep.py                 # Original Python script
├── build_exe.py           # Python build script
├── build_exe.bat          # Windows batch build script
├── BUILD_EXECUTABLE.md    # This documentation
├── prep.spec              # PyInstaller spec (created during build)
├── build/                 # Temporary build files (can be deleted)
└── dist/
    └── prep.exe           # Final executable
```

## Clean Up

To clean up build artifacts:
- Delete the `build` folder
- Delete the `prep.spec` file
- Keep the `dist` folder and `prep.exe` for distribution
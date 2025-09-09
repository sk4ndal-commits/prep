"""Infrastructure implementations for file operations."""

import os
from pathlib import Path
from typing import Iterator, List
import mimetypes

from ..domain.interfaces import FileReader, FileScanner


class StandardFileReader(FileReader):
    """Standard file reader implementation."""
    
    def read_lines(self, file_path: str) -> Iterator[str]:
        """Read lines from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                for line in file:
                    yield line.rstrip('\n\r')
        except (IOError, UnicodeDecodeError, PermissionError):
            return
    
    def is_binary(self, file_path: str) -> bool:
        """Check if a file is binary."""
        try:
            # First check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith('text/'):
                return True
            
            # Check for null bytes in first 8192 bytes
            with open(file_path, 'rb') as file:
                chunk = file.read(8192)
                return b'\0' in chunk
        except (IOError, PermissionError):
            return True  # Assume binary if can't read
    
    def exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        return os.path.isfile(file_path)


class StandardFileScanner(FileScanner):
    """Standard file scanner implementation."""
    
    def scan_files(self, paths: List[str], recursive: bool = False) -> Iterator[str]:
        """Scan for files to search in."""
        for path_str in paths:
            path = Path(path_str)
            
            if path.is_file():
                yield str(path)
            elif path.is_dir() and recursive:
                yield from self._scan_directory_recursive(path)
            elif path.is_dir():
                # Non-recursive directory scan - only direct files
                try:
                    for item in path.iterdir():
                        if item.is_file():
                            yield str(item)
                except PermissionError:
                    continue
    
    @staticmethod
    def _scan_directory_recursive(directory: Path) -> Iterator[str]:
        """Recursively scan a directory for files."""
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    yield str(item)
        except PermissionError:
            return
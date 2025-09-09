"""Domain interfaces for prep - the Python grep implementation."""

from abc import ABC, abstractmethod
from typing import Iterator, List, Optional

from .models import FileMatch, SearchOptions, SearchResult, MatchResult


class FileReader(ABC):
    """Interface for reading files."""
    
    @abstractmethod
    def read_lines(self, file_path: str) -> Iterator[str]:
        """Read lines from a file."""
        pass
    
    @abstractmethod
    def is_binary(self, file_path: str) -> bool:
        """Check if a file is binary."""
        pass
    
    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        pass


class FileScanner(ABC):
    """Interface for scanning directories and finding files."""
    
    @abstractmethod
    def scan_files(self, paths: List[str], recursive: bool = False) -> Iterator[str]:
        """Scan for files to search in."""
        pass


class PatternMatcher(ABC):
    """Interface for pattern matching operations."""
    
    @abstractmethod
    def find_matches(self, content: str, line_number: int, options: SearchOptions) -> List[MatchResult]:
        """Find all matches in a line of content."""
        pass
    
    @abstractmethod
    def should_include_line(self, matches: List[MatchResult], options: SearchOptions) -> bool:
        """Determine if a line should be included based on matches and options."""
        pass


class OutputFormatter(ABC):
    """Interface for formatting search results."""
    
    @abstractmethod
    def format_result(self, result: SearchResult, options: SearchOptions) -> str:
        """Format the complete search result for output."""
        pass
    
    @abstractmethod
    def format_file_match(self, file_match: FileMatch, options: SearchOptions) -> str:
        """Format matches from a single file."""
        pass
    
    @abstractmethod
    def format_match_line(self, match: MatchResult, options: SearchOptions, context_lines: Optional[List[str]] = None) -> str:
        """Format a single matching line."""
        pass


class SearchService(ABC):
    """Interface for the main search service."""
    
    @abstractmethod
    def search_files(self, file_paths: List[str], options: SearchOptions) -> SearchResult:
        """Search for patterns in the specified files."""
        pass
    
    @abstractmethod
    def search_file(self, file_path: str, options: SearchOptions) -> FileMatch:
        """Search for patterns in a single file."""
        pass


class FileWatcher(ABC):
    """Interface for watching file changes."""
    
    @abstractmethod
    def watch_file(self, file_path: str) -> Iterator[str]:
        """Watch a file for new lines and yield them as they are added."""
        pass
    
    @abstractmethod
    def stop_watching(self) -> None:
        """Stop watching the file."""
        pass


class ParallelExecutor(ABC):
    """Interface for parallel execution of search operations."""
    
    @abstractmethod
    def execute_parallel(self, tasks: List[callable], max_workers: int = None) -> List[any]:
        """Execute tasks in parallel."""
        pass
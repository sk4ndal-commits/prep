"""Domain models for prep - the Python grep implementation."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Pattern


class MatchType(Enum):
    """Types of pattern matching."""
    NORMAL = "normal"
    WORD = "word"
    LINE = "line"


class RegexFlag(Enum):
    """Regex compilation flags."""
    IGNORECASE = re.IGNORECASE
    MULTILINE = re.MULTILINE
    DOTALL = re.DOTALL
    VERBOSE = re.VERBOSE


@dataclass(frozen=True)
class SearchPattern:
    """Represents a search pattern with its configuration."""
    pattern: str
    match_type: MatchType = MatchType.NORMAL
    regex_flags: int = 0
    is_regex: bool = True
    
    def compile(self) -> Pattern[str]:
        """Compile the pattern into a regex pattern."""
        if self.match_type == MatchType.WORD:
            pattern = rf"\b{re.escape(self.pattern)}\b" if not self.is_regex else rf"\b(?:{self.pattern})\b"
        elif self.match_type == MatchType.LINE:
            pattern = rf"^{re.escape(self.pattern)}$" if not self.is_regex else rf"^(?:{self.pattern})$"
        else:
            pattern = re.escape(self.pattern) if not self.is_regex else self.pattern
        
        return re.compile(pattern, self.regex_flags)


@dataclass(frozen=True)
class MatchResult:
    """Represents a match found in a line."""
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    pattern: SearchPattern


@dataclass(frozen=True)
class FileMatch:
    """Represents matches found in a file."""
    file_path: str
    matches: List[MatchResult]
    is_binary: bool = False
    
    @property
    def match_count(self) -> int:
        """Get the number of matches in this file."""
        return len(self.matches)


@dataclass(frozen=True)
class SearchOptions:
    """Configuration options for search operations."""
    patterns: List[SearchPattern]
    invert_match: bool = False
    count_only: bool = False
    quiet: bool = False
    context_before: int = 0
    context_after: int = 0
    highlight_matches: bool = False
    recursive: bool = False
    ignore_binary: bool = True
    max_threads: int = 1
    follow: bool = False
    
    @property
    def context_around(self) -> int:
        """Get the maximum context lines needed."""
        return max(self.context_before, self.context_after)


@dataclass(frozen=True)
class SearchResult:
    """Complete result of a search operation."""
    file_matches: List[FileMatch]
    total_matches: int
    files_with_matches: int
    
    @classmethod
    def empty(cls) -> 'SearchResult':
        """Create an empty search result."""
        return cls(file_matches=[], total_matches=0, files_with_matches=0)
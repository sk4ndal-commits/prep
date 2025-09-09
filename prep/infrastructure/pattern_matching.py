"""Infrastructure implementation for pattern matching operations."""

import re
from typing import List

from ..domain.interfaces import PatternMatcher
from ..domain.models import SearchOptions, MatchResult


class RegexPatternMatcher(PatternMatcher):
    """Regex-based pattern matcher implementation."""
    
    def find_matches(self, content: str, line_number: int, options: SearchOptions) -> List[MatchResult]:
        """Find all matches in a line of content."""
        matches = []
        
        for pattern in options.patterns:
            compiled_pattern = pattern.compile()
            
            for match in compiled_pattern.finditer(content):
                match_result = MatchResult(
                    line_number=line_number,
                    line_content=content,
                    match_start=match.start(),
                    match_end=match.end(),
                    pattern=pattern
                )
                matches.append(match_result)
        
        return matches
    
    def should_include_line(self, matches: List[MatchResult], options: SearchOptions) -> bool:
        """Determine if a line should be included based on matches and options."""
        has_matches = bool(matches)
        
        if options.invert_match:
            return not has_matches
        else:
            return has_matches


class SimplePatternMatcher(PatternMatcher):
    """Simple string-based pattern matcher for non-regex patterns."""
    
    def find_matches(self, content: str, line_number: int, options: SearchOptions) -> List[MatchResult]:
        """Find all matches in a line of content using simple string matching."""
        matches = []
        
        for pattern in options.patterns:
            if pattern.is_regex:
                # Skip regex patterns in simple matcher - they should be handled by regex matcher
                continue
            
            search_text = pattern.pattern
            search_content = content
            
            # Apply case-insensitive matching if specified
            if pattern.regex_flags & re.IGNORECASE:
                search_text = search_text.lower()
                search_content = search_content.lower()
            
            start = 0
            while True:
                pos = search_content.find(search_text, start)
                if pos == -1:
                    break
                
                # Check word boundaries for word match
                if pattern.match_type.value == "word":
                    if not self._is_word_boundary(content, pos, pos + len(search_text)):
                        start = pos + 1
                        continue
                
                # Check line match
                if pattern.match_type.value == "line":
                    if content.strip() != pattern.pattern:
                        break
                
                match_result = MatchResult(
                    line_number=line_number,
                    line_content=content,
                    match_start=pos,
                    match_end=pos + len(search_text),
                    pattern=pattern
                )
                matches.append(match_result)
                start = pos + 1
        
        return matches
    
    def should_include_line(self, matches: List[MatchResult], options: SearchOptions) -> bool:
        """Determine if a line should be included based on matches and options."""
        has_matches = bool(matches)
        
        if options.invert_match:
            return not has_matches
        else:
            return has_matches
    
    @staticmethod
    def _is_word_boundary(text: str, start: int, end: int) -> bool:
        """Check if the match is at word boundaries."""
        # Check start boundary
        if start > 0 and text[start - 1].isalnum():
            return False
        
        # Check end boundary
        if end < len(text) and text[end].isalnum():
            return False
        
        return True


class HybridPatternMatcher(PatternMatcher):
    """Hybrid pattern matcher that uses the most appropriate strategy."""
    
    def __init__(self):
        self._regex_matcher = RegexPatternMatcher()
        self._simple_matcher = SimplePatternMatcher()
    
    def find_matches(self, content: str, line_number: int, options: SearchOptions) -> List[MatchResult]:
        """Find all matches using the most appropriate matcher."""
        # Use regex matcher if any pattern is a regex or has special match types
        use_regex = any(
            pattern.is_regex or 
            pattern.match_type.value in ("word", "line") or
            pattern.regex_flags != 0
            for pattern in options.patterns
        )
        
        if use_regex:
            return self._regex_matcher.find_matches(content, line_number, options)
        else:
            return self._simple_matcher.find_matches(content, line_number, options)
    
    def should_include_line(self, matches: List[MatchResult], options: SearchOptions) -> bool:
        """Determine if a line should be included based on matches and options."""
        return self._regex_matcher.should_include_line(matches, options)
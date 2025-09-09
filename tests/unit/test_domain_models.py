"""Tests for domain models."""

import re

from prep.domain.models import (
    SearchPattern, MatchResult, FileMatch, SearchOptions, SearchResult,
    MatchType, RegexFlag
)


class TestSearchPattern:
    """Test SearchPattern behavior."""
    
    def test_basic_pattern_compilation(self):
        """Test that basic patterns compile correctly."""
        pattern = SearchPattern("test")
        compiled = pattern.compile()
        assert compiled.pattern == "test"
        assert compiled.search("this is a test") is not None
    
    def test_word_match_pattern(self):
        """Test that word match patterns work correctly."""
        pattern = SearchPattern("test", match_type=MatchType.WORD)
        compiled = pattern.compile()
        
        # Should match "test" as a whole word
        assert compiled.search("this is a test") is not None
        # Should not match "testing" (partial word)
        assert compiled.search("testing") is None
    
    def test_line_match_pattern(self):
        """Test that line match patterns work correctly."""
        pattern = SearchPattern("test", match_type=MatchType.LINE)
        compiled = pattern.compile()
        
        # Should match exact line
        assert compiled.search("test") is not None
        # Should not match line with additional content
        assert compiled.search("test more") is None
    
    def test_case_insensitive_pattern(self):
        """Test case-insensitive patterns."""
        pattern = SearchPattern("TEST", regex_flags=re.IGNORECASE)
        compiled = pattern.compile()
        
        assert compiled.search("test") is not None
        assert compiled.search("Test") is not None
        assert compiled.search("TEST") is not None
    
    def test_fixed_string_pattern(self):
        """Test fixed string (non-regex) patterns."""
        pattern = SearchPattern("test.*", is_regex=False)
        compiled = pattern.compile()
        
        # Should match literal "test.*", not as regex
        assert compiled.search("test.*") is not None
        assert compiled.search("testing") is None


class TestMatchResult:
    """Test MatchResult behavior."""
    
    def test_match_result_creation(self):
        """Test creating a match result."""
        pattern = SearchPattern("test")
        match = MatchResult(
            line_number=1,
            line_content="this is a test line",
            match_start=10,
            match_end=14,
            pattern=pattern
        )
        
        assert match.line_number == 1
        assert match.line_content == "this is a test line"
        assert match.match_start == 10
        assert match.match_end == 14
        assert match.pattern == pattern


class TestFileMatch:
    """Test FileMatch behavior."""
    
    def test_file_match_count(self):
        """Test file match count calculation."""
        pattern = SearchPattern("test")
        matches = [
            MatchResult(1, "test line", 0, 4, pattern),
            MatchResult(2, "another test", 8, 12, pattern)
        ]
        
        file_match = FileMatch("test.txt", matches)
        assert file_match.match_count == 2
    
    def test_empty_file_match(self):
        """Test file match with no matches."""
        file_match = FileMatch("test.txt", [])
        assert file_match.match_count == 0
    
    def test_binary_file_match(self):
        """Test binary file match."""
        file_match = FileMatch("binary.bin", [], is_binary=True)
        assert file_match.is_binary is True
        assert file_match.match_count == 0


class TestSearchOptions:
    """Test SearchOptions behavior."""
    
    def test_default_search_options(self):
        """Test default search options."""
        pattern = SearchPattern("test")
        options = SearchOptions(patterns=[pattern])
        
        assert not options.invert_match
        assert not options.count_only
        assert not options.quiet
        assert options.context_before == 0
        assert options.context_after == 0
        assert not options.highlight_matches
        assert not options.recursive
        assert options.ignore_binary
        assert options.max_threads == 1
    
    def test_context_around_property(self):
        """Test context_around property calculation."""
        pattern = SearchPattern("test")
        
        # Test with before context
        options = SearchOptions(patterns=[pattern], context_before=3)
        assert options.context_around == 3
        
        # Test with after context
        options = SearchOptions(patterns=[pattern], context_after=5)
        assert options.context_around == 5
        
        # Test with both (should return max)
        options = SearchOptions(patterns=[pattern], context_before=2, context_after=4)
        assert options.context_around == 4
    
    def test_multiple_patterns(self):
        """Test search options with multiple patterns."""
        patterns = [
            SearchPattern("test"),
            SearchPattern("example"),
            SearchPattern("pattern")
        ]
        options = SearchOptions(patterns=patterns)
        
        assert len(options.patterns) == 3
        assert options.patterns[0].pattern == "test"
        assert options.patterns[1].pattern == "example"
        assert options.patterns[2].pattern == "pattern"


class TestSearchResult:
    """Test SearchResult behavior."""
    
    def test_search_result_creation(self):
        """Test creating a search result."""
        pattern = SearchPattern("test")
        matches = [MatchResult(1, "test line", 0, 4, pattern)]
        file_match = FileMatch("test.txt", matches)
        
        result = SearchResult([file_match], 1, 1)
        assert len(result.file_matches) == 1
        assert result.total_matches == 1
        assert result.files_with_matches == 1
    
    def test_empty_search_result(self):
        """Test empty search result."""
        result = SearchResult.empty()
        assert len(result.file_matches) == 0
        assert result.total_matches == 0
        assert result.files_with_matches == 0
    
    def test_multiple_file_matches(self):
        """Test search result with multiple files."""
        pattern = SearchPattern("test")
        
        # First file with 2 matches
        matches1 = [
            MatchResult(1, "test line", 0, 4, pattern),
            MatchResult(3, "another test", 8, 12, pattern)
        ]
        file_match1 = FileMatch("file1.txt", matches1)
        
        # Second file with 1 match
        matches2 = [MatchResult(5, "test here", 0, 4, pattern)]
        file_match2 = FileMatch("file2.txt", matches2)
        
        result = SearchResult([file_match1, file_match2], 3, 2)
        assert len(result.file_matches) == 2
        assert result.total_matches == 3
        assert result.files_with_matches == 2


class TestMatchType:
    """Test MatchType enum."""
    
    def test_match_type_values(self):
        """Test match type enum values."""
        assert MatchType.NORMAL.value == "normal"
        assert MatchType.WORD.value == "word"
        assert MatchType.LINE.value == "line"


class TestRegexFlag:
    """Test RegexFlag enum."""
    
    def test_regex_flag_values(self):
        """Test regex flag enum values."""
        assert RegexFlag.IGNORECASE.value == re.IGNORECASE
        assert RegexFlag.MULTILINE.value == re.MULTILINE
        assert RegexFlag.DOTALL.value == re.DOTALL
        assert RegexFlag.VERBOSE.value == re.VERBOSE
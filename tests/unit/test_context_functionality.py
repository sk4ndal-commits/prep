"""Unit tests for context functionality (-A, -B, -C options)."""

import unittest
from unittest.mock import Mock
from typing import List

from prep.usecases.search_usecase import SearchUseCase
from prep.infrastructure.output_formatting import StandardOutputFormatter
from prep.domain.models import SearchOptions, SearchPattern, MatchType, MatchResult, FileMatch


class TestContextFunctionality(unittest.TestCase):
    """Test context functionality for before, after, and around options."""

    def setUp(self):
        """Set up test fixtures."""
        self.file_reader = Mock()
        self.file_scanner = Mock()
        self.pattern_matcher = Mock()
        self.parallel_executor = Mock()
        
        self.search_usecase = SearchUseCase(
            file_reader=self.file_reader,
            file_scanner=self.file_scanner,
            pattern_matcher=self.pattern_matcher,
            parallel_executor=self.parallel_executor
        )
        
        self.output_formatter = StandardOutputFormatter()
        
        # Mock file content matching the test.log
        self.test_lines = [
            "affe",
            "baer", 
            "hund",
            "chimpanzee",
            "bird",
            "dinosaur",
            "turtle"
        ]
        
    def test_context_after_A2(self):
        """Test -A 2 option (2 lines after match)."""
        # Setup mocks
        self.file_reader.exists.return_value = True
        self.file_reader.is_binary.return_value = False
        self.file_reader.read_lines.return_value = self.test_lines
        
        # Mock pattern matcher to find "chimpanzee" on line 4
        def mock_find_matches(line_content, line_number, options):
            if line_content == "chimpanzee":
                pattern = options.patterns[0] if options.patterns else None
                return [MatchResult(line_number, line_content, 0, len(line_content), pattern)]
            return []
        
        def mock_should_include_line(line_matches, options):
            return len(line_matches) > 0
        
        self.pattern_matcher.find_matches.side_effect = mock_find_matches
        self.pattern_matcher.should_include_line.side_effect = mock_should_include_line
        
        # Create search options for -A 2
        pattern = SearchPattern("chimpanzee", MatchType.NORMAL)
        options = SearchOptions(
            patterns=[pattern],
            context_before=0,
            context_after=2,
            highlight_matches=True
        )
        
        # Execute search
        result = self.search_usecase._search_single_file("test.log", options)
        
        # Verify results
        self.assertEqual(len(result.matches), 3)  # 1 match + 2 after context
        
        # Check line numbers and content
        matches_by_line = {m.line_number: m for m in result.matches}
        self.assertIn(4, matches_by_line)  # Match line
        self.assertIn(5, matches_by_line)  # After context 1
        self.assertIn(6, matches_by_line)  # After context 2
        
        # Check match vs context distinction
        self.assertNotEqual(matches_by_line[4].match_start, -1)  # Real match
        self.assertEqual(matches_by_line[5].match_start, -1)     # Context line
        self.assertEqual(matches_by_line[6].match_start, -1)     # Context line
        
    def test_context_before_B2(self):
        """Test -B 2 option (2 lines before match)."""
        # Setup mocks
        self.file_reader.exists.return_value = True
        self.file_reader.is_binary.return_value = False
        self.file_reader.read_lines.return_value = self.test_lines
        
        # Mock pattern matcher
        def mock_find_matches(line_content, line_number, options):
            if line_content == "chimpanzee":
                pattern = options.patterns[0] if options.patterns else None
                return [MatchResult(line_number, line_content, 0, len(line_content), pattern)]
            return []
        
        def mock_should_include_line(line_matches, options):
            return len(line_matches) > 0
        
        self.pattern_matcher.find_matches.side_effect = mock_find_matches
        self.pattern_matcher.should_include_line.side_effect = mock_should_include_line
        
        # Create search options for -B 2
        pattern = SearchPattern("chimpanzee", MatchType.NORMAL)
        options = SearchOptions(
            patterns=[pattern],
            context_before=2,
            context_after=0,
            highlight_matches=True
        )
        
        # Execute search
        result = self.search_usecase._search_single_file("test.log", options)
        
        # Verify results
        self.assertEqual(len(result.matches), 3)  # 2 before context + 1 match
        
        # Check line numbers and content
        matches_by_line = {m.line_number: m for m in result.matches}
        self.assertIn(2, matches_by_line)  # Before context 1
        self.assertIn(3, matches_by_line)  # Before context 2
        self.assertIn(4, matches_by_line)  # Match line
        
        # Check match vs context distinction
        self.assertEqual(matches_by_line[2].match_start, -1)     # Context line
        self.assertEqual(matches_by_line[3].match_start, -1)     # Context line
        self.assertNotEqual(matches_by_line[4].match_start, -1)  # Real match
        
    def test_context_around_C1(self):
        """Test -C 1 option (1 line before and after match)."""
        # Setup mocks
        self.file_reader.exists.return_value = True
        self.file_reader.is_binary.return_value = False
        self.file_reader.read_lines.return_value = self.test_lines
        
        # Mock pattern matcher
        def mock_find_matches(line_content, line_number, options):
            if line_content == "chimpanzee":
                pattern = options.patterns[0] if options.patterns else None
                return [MatchResult(line_number, line_content, 0, len(line_content), pattern)]
            return []
        
        def mock_should_include_line(line_matches, options):
            return len(line_matches) > 0
        
        self.pattern_matcher.find_matches.side_effect = mock_find_matches
        self.pattern_matcher.should_include_line.side_effect = mock_should_include_line
        
        # Create search options for -C 1
        pattern = SearchPattern("chimpanzee", MatchType.NORMAL)
        options = SearchOptions(
            patterns=[pattern],
            context_before=1,
            context_after=1,
            highlight_matches=True
        )
        
        # Execute search
        result = self.search_usecase._search_single_file("test.log", options)
        
        # Verify results
        self.assertEqual(len(result.matches), 3)  # 1 before + 1 match + 1 after
        
        # Check line numbers and content
        matches_by_line = {m.line_number: m for m in result.matches}
        self.assertIn(3, matches_by_line)  # Before context
        self.assertIn(4, matches_by_line)  # Match line
        self.assertIn(5, matches_by_line)  # After context
        
        # Verify content
        self.assertEqual(matches_by_line[3].line_content, "hund")
        self.assertEqual(matches_by_line[4].line_content, "chimpanzee")
        self.assertEqual(matches_by_line[5].line_content, "bird")
        
    def test_output_formatting_with_context(self):
        """Test that context lines are formatted differently from match lines."""
        # Create mock file match with context
        pattern = SearchPattern("chimpanzee", MatchType.NORMAL)
        
        matches = [
            MatchResult(3, "hund", -1, -1, None),  # Context line
            MatchResult(4, "chimpanzee", 0, 10, pattern),  # Match line
            MatchResult(5, "bird", -1, -1, None),  # Context line
        ]
        
        file_match = FileMatch("test.log", matches)
        
        options = SearchOptions(
            patterns=[pattern],
            context_before=1,
            context_after=1,
            highlight_matches=False  # Disable for easier testing
        )
        
        # Format output
        result = self.output_formatter.format_file_match(file_match, options)
        
        # Verify formatting
        lines = result.split('\n')
        self.assertEqual(len(lines), 3)
        
        # Context lines should have '-' separator
        self.assertTrue(lines[0].startswith("3-"))
        self.assertTrue("hund" in lines[0])
        
        # Match line should have ':' separator
        self.assertTrue(lines[1].startswith("4:"))
        self.assertTrue("chimpanzee" in lines[1])
        
        # Context lines should have '-' separator
        self.assertTrue(lines[2].startswith("5-"))
        self.assertTrue("bird" in lines[2])
        
    def test_context_at_file_boundaries(self):
        """Test context handling at file start and end."""
        # Test context at beginning of file
        self.file_reader.exists.return_value = True
        self.file_reader.is_binary.return_value = False
        self.file_reader.read_lines.return_value = ["match", "line2", "line3"]
        
        def mock_find_matches(line_content, line_number, options):
            if line_content == "match":
                pattern = options.patterns[0] if options.patterns else None
                return [MatchResult(line_number, line_content, 0, len(line_content), pattern)]
            return []
        
        def mock_should_include_line(line_matches, options):
            return len(line_matches) > 0
        
        self.pattern_matcher.find_matches.side_effect = mock_find_matches
        self.pattern_matcher.should_include_line.side_effect = mock_should_include_line
        
        pattern = SearchPattern("match", MatchType.NORMAL)
        options = SearchOptions(
            patterns=[pattern],
            context_before=2,  # Should not go before line 1
            context_after=1,
            highlight_matches=True
        )
        
        result = self.search_usecase._search_single_file("test.log", options)
        
        # Should have match + 1 after context (no before context available)
        self.assertEqual(len(result.matches), 2)
        line_numbers = [m.line_number for m in result.matches]
        self.assertIn(1, line_numbers)  # Match
        self.assertIn(2, line_numbers)  # After context
        self.assertNotIn(0, line_numbers)  # No line 0
        

if __name__ == '__main__':
    unittest.main()
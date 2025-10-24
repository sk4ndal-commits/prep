"""Infrastructure implementation for pattern matching operations."""

import re
from typing import List, Optional

from ..domain.interfaces import PatternMatcher
from ..domain.models import SearchOptions, MatchResult
from .boolean_parser import parse_boolean_pattern, BooleanNode


class BooleanPatternMatcher(PatternMatcher):
    """Pattern matcher with Boolean expression support."""
    
    def find_matches(self, content: str, line_number: int, options: SearchOptions) -> List[MatchResult]:
        """Find all matches in a line of content using Boolean expressions."""
        matches = []
        
        for pattern in options.patterns:
            # Parse the pattern as a Boolean expression
            bool_tree = parse_boolean_pattern(pattern.pattern)
            
            if bool_tree is None:
                continue
            
            # Apply match type modifications to the pattern before evaluation
            modified_pattern = pattern.pattern
            if pattern.match_type.value == "word":
                # For word matching, wrap entire boolean expression patterns
                modified_pattern = self._apply_word_boundaries_to_tree(bool_tree)
            elif pattern.match_type.value == "line":
                # For line matching, wrap entire boolean expression patterns
                modified_pattern = self._apply_line_anchors_to_tree(bool_tree)
            
            # Re-parse with modified patterns if match_type is applied
            if pattern.match_type.value != "normal":
                bool_tree = self._create_modified_tree(bool_tree, pattern.match_type)
            
            # Check if the line matches the Boolean expression
            line_matches = bool_tree.evaluate(content, pattern.regex_flags)
            
            if not line_matches:
                continue
            
            # Find all literal patterns in the tree for highlighting
            literal_patterns = bool_tree.get_patterns()
            
            # For each literal pattern, find actual match positions for highlighting
            # Only highlight patterns that actually match in the content
            for literal_pattern in literal_patterns:
                try:
                    # Apply match type modifications
                    if pattern.match_type.value == "word":
                        search_pattern = rf"\b(?:{literal_pattern})\b"
                    elif pattern.match_type.value == "line":
                        search_pattern = rf"^(?:{literal_pattern})$"
                    else:
                        search_pattern = literal_pattern
                    
                    compiled = re.compile(search_pattern, pattern.regex_flags)
                    
                    # Only add matches if this pattern actually appears in the line
                    pattern_matches = list(compiled.finditer(content))
                    if pattern_matches:
                        for match in pattern_matches:
                            match_result = MatchResult(
                                line_number=line_number,
                                line_content=content,
                                match_start=match.start(),
                                match_end=match.end(),
                                pattern=pattern
                            )
                            matches.append(match_result)
                except re.error:
                    continue
        
        return matches
    
    def _create_modified_tree(self, tree: BooleanNode, match_type) -> BooleanNode:
        """Create a new tree with match type applied to all literal nodes."""
        from .boolean_parser import LiteralNode, AndNode, OrNode, NotNode
        
        if isinstance(tree, LiteralNode):
            # Apply match type to literal pattern
            if match_type.value == "word":
                modified_pattern = rf"\b(?:{tree.pattern})\b"
            elif match_type.value == "line":
                modified_pattern = rf"^(?:{tree.pattern})$"
            else:
                modified_pattern = tree.pattern
            return LiteralNode(modified_pattern)
        elif isinstance(tree, NotNode):
            return NotNode(self._create_modified_tree(tree.child, match_type))
        elif isinstance(tree, AndNode):
            return AndNode(
                self._create_modified_tree(tree.left, match_type),
                self._create_modified_tree(tree.right, match_type)
            )
        elif isinstance(tree, OrNode):
            return OrNode(
                self._create_modified_tree(tree.left, match_type),
                self._create_modified_tree(tree.right, match_type)
            )
        return tree
    
    def _apply_word_boundaries_to_tree(self, tree: BooleanNode) -> str:
        """Apply word boundaries to all patterns in tree (for display/debugging)."""
        return ""  # Not used in current implementation
    
    def _apply_line_anchors_to_tree(self, tree: BooleanNode) -> str:
        """Apply line anchors to all patterns in tree (for display/debugging)."""
        return ""  # Not used in current implementation
    
    def should_include_line(self, matches: List[MatchResult], options: SearchOptions) -> bool:
        """Determine if a line should be included based on matches and options."""
        # For Boolean expressions, we need to re-evaluate the expression
        # Since find_matches already checks the Boolean expression, 
        # having any matches means the line should be included
        has_matches = bool(matches)
        
        if options.invert_match:
            return not has_matches
        else:
            return has_matches


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
        self._boolean_matcher = BooleanPatternMatcher()
    
    def find_matches(self, content: str, line_number: int, options: SearchOptions) -> List[MatchResult]:
        """Find all matches using Boolean pattern matcher."""
        # BooleanPatternMatcher handles both simple patterns and Boolean expressions
        return self._boolean_matcher.find_matches(content, line_number, options)
    
    def should_include_line(self, matches: List[MatchResult], options: SearchOptions) -> bool:
        """Determine if a line should be included based on matches and options."""
        return self._boolean_matcher.should_include_line(matches, options)
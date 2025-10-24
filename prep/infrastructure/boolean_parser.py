"""Boolean expression parser for pattern matching.

Supports:
- OR operator: |
- AND operator: &
- NOT operator: !
- Parentheses for grouping: ()
"""

import re
from typing import List, Optional, Union
from abc import ABC, abstractmethod


class BooleanNode(ABC):
    """Abstract base class for boolean expression tree nodes."""
    
    @abstractmethod
    def evaluate(self, text: str, regex_flags: int = 0) -> bool:
        """Evaluate the boolean expression against text."""
        pass
    
    @abstractmethod
    def get_patterns(self) -> List[str]:
        """Get all literal patterns from this node."""
        pass


class LiteralNode(BooleanNode):
    """Leaf node representing a single pattern."""
    
    def __init__(self, pattern: str):
        self.pattern = pattern
    
    def evaluate(self, text: str, regex_flags: int = 0) -> bool:
        """Check if the pattern matches the text."""
        try:
            compiled = re.compile(self.pattern, regex_flags)
            return compiled.search(text) is not None
        except re.error:
            return False
    
    def get_patterns(self) -> List[str]:
        """Return this pattern."""
        return [self.pattern]
    
    def __repr__(self) -> str:
        return f"Literal({self.pattern!r})"


class NotNode(BooleanNode):
    """Node representing NOT operation."""
    
    def __init__(self, child: BooleanNode):
        self.child = child
    
    def evaluate(self, text: str, regex_flags: int = 0) -> bool:
        """Negate the child evaluation."""
        return not self.child.evaluate(text, regex_flags)
    
    def get_patterns(self) -> List[str]:
        """Get patterns from child."""
        return self.child.get_patterns()
    
    def __repr__(self) -> str:
        return f"Not({self.child!r})"


class AndNode(BooleanNode):
    """Node representing AND operation."""
    
    def __init__(self, left: BooleanNode, right: BooleanNode):
        self.left = left
        self.right = right
    
    def evaluate(self, text: str, regex_flags: int = 0) -> bool:
        """Both children must evaluate to True."""
        return self.left.evaluate(text, regex_flags) and self.right.evaluate(text, regex_flags)
    
    def get_patterns(self) -> List[str]:
        """Get patterns from both children."""
        return self.left.get_patterns() + self.right.get_patterns()
    
    def __repr__(self) -> str:
        return f"And({self.left!r}, {self.right!r})"


class OrNode(BooleanNode):
    """Node representing OR operation."""
    
    def __init__(self, left: BooleanNode, right: BooleanNode):
        self.left = left
        self.right = right
    
    def evaluate(self, text: str, regex_flags: int = 0) -> bool:
        """At least one child must evaluate to True."""
        return self.left.evaluate(text, regex_flags) or self.right.evaluate(text, regex_flags)
    
    def get_patterns(self) -> List[str]:
        """Get patterns from both children."""
        return self.left.get_patterns() + self.right.get_patterns()
    
    def __repr__(self) -> str:
        return f"Or({self.left!r}, {self.right!r})"


class BooleanExpressionParser:
    """Parser for Boolean expressions in patterns.
    
    Grammar (in order of precedence):
    expression := or_expr
    or_expr := and_expr ('|' and_expr)*
    and_expr := not_expr ('&' not_expr)*
    not_expr := '!' not_expr | primary
    primary := '(' expression ')' | literal
    literal := any characters except &, |, !, (, )
    """
    
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)
    
    def parse(self) -> Optional[BooleanNode]:
        """Parse the pattern into a boolean expression tree."""
        if not self.pattern or not self.pattern.strip():
            return None
        
        # Check if pattern contains boolean operators
        if not any(op in self.pattern for op in ['&', '|', '!']):
            # Simple pattern without boolean operators
            return LiteralNode(self.pattern)
        
        try:
            result = self._parse_or_expr()
            if self.pos < self.length:
                # There's unparsed content - treat as simple pattern
                return LiteralNode(self.pattern)
            return result
        except Exception:
            # If parsing fails, treat as literal pattern
            return LiteralNode(self.pattern)
    
    def _parse_or_expr(self) -> BooleanNode:
        """Parse OR expressions (lowest precedence)."""
        left = self._parse_and_expr()
        
        while self.pos < self.length and self._peek() == '|':
            self._consume('|')
            right = self._parse_and_expr()
            left = OrNode(left, right)
        
        return left
    
    def _parse_and_expr(self) -> BooleanNode:
        """Parse AND expressions (medium precedence)."""
        left = self._parse_not_expr()
        
        while self.pos < self.length and self._peek() == '&':
            self._consume('&')
            right = self._parse_not_expr()
            left = AndNode(left, right)
        
        return left
    
    def _parse_not_expr(self) -> BooleanNode:
        """Parse NOT expressions (high precedence)."""
        if self.pos < self.length and self._peek() == '!':
            self._consume('!')
            child = self._parse_not_expr()
            return NotNode(child)
        
        return self._parse_primary()
    
    def _parse_primary(self) -> BooleanNode:
        """Parse primary expressions (parentheses or literals)."""
        self._skip_whitespace()
        
        if self.pos < self.length and self._peek() == '(':
            self._consume('(')
            expr = self._parse_or_expr()
            self._skip_whitespace()
            self._consume(')')
            return expr
        
        return self._parse_literal()
    
    def _parse_literal(self) -> BooleanNode:
        """Parse a literal pattern (everything except operators and parens)."""
        self._skip_whitespace()
        start = self.pos
        
        # Collect characters until we hit an operator or closing paren
        while self.pos < self.length:
            ch = self.pattern[self.pos]
            if ch in ['&', '|', '!', '(', ')']:
                break
            self.pos += 1
        
        if self.pos == start:
            raise ValueError(f"Expected literal at position {self.pos}")
        
        literal = self.pattern[start:self.pos].strip()
        if not literal:
            raise ValueError(f"Empty literal at position {start}")
        
        return LiteralNode(literal)
    
    def _peek(self) -> str:
        """Peek at current character without consuming."""
        self._skip_whitespace()
        if self.pos < self.length:
            return self.pattern[self.pos]
        return ''
    
    def _consume(self, expected: str) -> None:
        """Consume expected character."""
        self._skip_whitespace()
        if self.pos >= self.length or self.pattern[self.pos] != expected:
            raise ValueError(f"Expected '{expected}' at position {self.pos}")
        self.pos += 1
    
    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < self.length and self.pattern[self.pos].isspace():
            self.pos += 1


def parse_boolean_pattern(pattern: str) -> Optional[BooleanNode]:
    """Parse a pattern string into a boolean expression tree.
    
    Args:
        pattern: Pattern string with optional boolean operators
        
    Returns:
        BooleanNode tree or None if pattern is empty
    """
    parser = BooleanExpressionParser(pattern)
    return parser.parse()

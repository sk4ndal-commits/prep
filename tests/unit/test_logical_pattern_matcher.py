import unittest
from prep.infrastructure.pattern_matching import LogicalPatternMatcher
from prep.domain.models import SearchOptions, SearchPattern, MatchType

class TestLogicalPatternMatcher(unittest.TestCase):
    def setUp(self):
        self.options = SearchOptions(
            patterns=[SearchPattern(pattern="(A|B)&C", match_type=MatchType.NORMAL, is_regex=True)],
            invert_match=False,
            count_only=False,
            quiet=False,
            context_before=0,
            context_after=0,
            highlight_matches=False,
            recursive=False,
            ignore_binary=False,
            max_threads=1
        )

    def test_and_or_match(self):
        matcher = LogicalPatternMatcher("(A|B)&C", self.options)
        # Zeile enthält A und C
        self.assertTrue(matcher._eval(matcher.root, "foo AC bar"))
        # Zeile enthält B und C
        self.assertTrue(matcher._eval(matcher.root, "foo BC bar"))
        # Zeile enthält nur A
        self.assertFalse(matcher._eval(matcher.root, "foo A bar"))
        # Zeile enthält nur B
        self.assertFalse(matcher._eval(matcher.root, "foo B bar"))
        # Zeile enthält nur C
        self.assertFalse(matcher._eval(matcher.root, "foo C bar"))
        # Zeile enthält A, B, C
        self.assertTrue(matcher._eval(matcher.root, "A B C"))

    def test_nested_or_and(self):
        matcher = LogicalPatternMatcher("A|(B&C)", self.options)
        self.assertTrue(matcher._eval(matcher.root, "foo A bar"))
        self.assertTrue(matcher._eval(matcher.root, "foo B C bar"))
        self.assertFalse(matcher._eval(matcher.root, "foo B bar"))
        self.assertFalse(matcher._eval(matcher.root, "foo C bar"))

if __name__ == "__main__":
    unittest.main()


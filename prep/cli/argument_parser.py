"""Command-line argument parser for prep."""

import argparse
import re
from typing import List, Optional, Tuple
import sys

from ..domain.models import SearchPattern, SearchOptions, MatchType, RegexFlag


class PrepArgumentParser:
    """Argument parser for prep command-line interface."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all options."""
        parser = argparse.ArgumentParser(
            prog='prep',
            description='prep - Python grep implementation',
            epilog="""
Examples:
  prep "pattern" file.txt                    # Basic search
  prep -v "pattern" file.txt                 # Invert match
  prep -c "pattern" *.txt                    # Count matches
  prep -r "pattern" /path/to/directory       # Recursive search
  prep -e "pat1" -e "pat2" file.txt         # Multiple patterns
  prep -w "word" file.txt                    # Word match
  prep -x "exact line" file.txt              # Line match
  prep -A 3 -B 2 "pattern" file.txt         # Context lines
  prep -i "pattern" file.txt                 # Case insensitive
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Positional arguments
        parser.add_argument(
            'pattern',
            nargs='?',
            help='Search pattern (required unless using -e)',
        )
        
        parser.add_argument(
            'files',
            nargs='*',
            help='Files to search in (stdin if not specified)',
        )
        
        # Basic options
        parser.add_argument(
            '-e', '--regexp',
            action='append',
            dest='patterns',
            help='Specify pattern (can be used multiple times)',
        )
        
        parser.add_argument(
            '-v', '--invert-match',
            action='store_true',
            help='Show lines that do not match the pattern',
        )
        
        parser.add_argument(
            '-c', '--count',
            action='store_true',
            help='Print only the number of matching lines per file',
        )
        
        parser.add_argument(
            '-q', '--quiet', '--silent',
            action='store_true',
            help='Suppress output, exit status indicates whether a match was found',
        )
        
        # Match type options
        parser.add_argument(
            '-w', '--word-regexp',
            action='store_true',
            help='Match whole words only',
        )
        
        parser.add_argument(
            '-x', '--line-regexp',
            action='store_true',
            help='Match only if the whole line fits the pattern',
        )
        
        # Case sensitivity
        parser.add_argument(
            '-i', '--ignore-case',
            action='store_true',
            help='Ignore case distinctions',
        )
        
        # Output options
        parser.add_argument(
            '--color', '--colour',
            choices=['auto', 'always', 'never'],
            default='auto',
            help='Use colors to highlight matches',
        )
        
        parser.add_argument(
            '-n', '--line-number',
            action='store_true',
            default=True,
            help='Show line numbers (default)',
        )
        
        parser.add_argument(
            '-H', '--with-filename',
            action='store_true',
            help='Show filename for each match',
        )
        
        parser.add_argument(
            '--no-filename',
            action='store_true',
            help='Suppress the filename for each match',
        )
        
        # Context options
        parser.add_argument(
            '-A', '--after-context',
            type=int,
            default=0,
            metavar='NUM',
            help='Show NUM lines after each match',
        )
        
        parser.add_argument(
            '-B', '--before-context',
            type=int,
            default=0,
            metavar='NUM',
            help='Show NUM lines before each match',
        )
        
        parser.add_argument(
            '-C', '--context',
            type=int,
            metavar='NUM',
            help='Show NUM lines before and after each match',
        )
        
        # Directory options
        parser.add_argument(
            '-r', '--recursive',
            action='store_true',
            help='Recursively search directories',
        )
        
        # Binary file options
        parser.add_argument(
            '-I', '--binary-files',
            choices=['binary', 'without-match', 'text'],
            default='without-match',
            help='How to handle binary files',
        )
        
        # Performance options
        parser.add_argument(
            '--threads',
            type=int,
            default=1,
            metavar='N',
            help='Use N threads for parallel processing',
        )
        
        # Regex options
        parser.add_argument(
            '-F', '--fixed-strings',
            action='store_true',
            help='Interpret patterns as fixed strings (not regex)',
        )
        
        parser.add_argument(
            '-E', '--extended-regexp',
            action='store_true',
            help='Use extended regular expressions',
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> Tuple[SearchOptions, List[str]]:
        """Parse command line arguments and return search options and file paths."""
        parsed = self.parser.parse_args(args)
        
        # Validate patterns
        patterns = self._extract_patterns(parsed)
        if not patterns:
            self.parser.error("No pattern specified. Use PATTERN argument or -e option.")
        
        # Handle context options
        context_before = parsed.before_context
        context_after = parsed.after_context
        
        if parsed.context is not None:
            context_before = context_after = parsed.context
        
        # Determine match type
        match_type = MatchType.NORMAL
        if parsed.word_regexp:
            match_type = MatchType.WORD
        elif parsed.line_regexp:
            match_type = MatchType.LINE
        
        # Build regex flags
        regex_flags = 0
        if parsed.ignore_case:
            regex_flags |= re.IGNORECASE
        
        # Create search patterns
        search_patterns = []
        for pattern_str in patterns:
            search_pattern = SearchPattern(
                pattern=pattern_str,
                match_type=match_type,
                regex_flags=regex_flags,
                is_regex=not parsed.fixed_strings
            )
            search_patterns.append(search_pattern)
        
        # Determine if highlighting should be enabled
        highlight_matches = self._should_highlight(parsed)
        
        # Handle binary files
        ignore_binary = parsed.binary_files == 'without-match'
        
        # Create search options
        options = SearchOptions(
            patterns=search_patterns,
            invert_match=parsed.invert_match,
            count_only=parsed.count,
            quiet=parsed.quiet,
            context_before=context_before,
            context_after=context_after,
            highlight_matches=highlight_matches,
            recursive=parsed.recursive,
            ignore_binary=ignore_binary,
            max_threads=parsed.threads
        )
        
        # Get file paths - when using -e, treat positional pattern as file path
        file_paths = list(parsed.files)  # Copy the files list
        if parsed.patterns and parsed.pattern:
            # When -e patterns are used, treat the positional pattern as a file path
            file_paths.append(parsed.pattern)
        
        # If no files specified, default to stdin
        if not file_paths:
            if parsed.patterns:
                self.parser.error("When using -e/--regexp, you must specify files to search")
            file_paths = ['-']
        
        return options, file_paths
    
    def _extract_patterns(self, parsed: argparse.Namespace) -> List[str]:
        """Extract patterns from parsed arguments."""
        patterns = []
        
        # Add patterns from -e/--regexp options
        if parsed.patterns:
            patterns.extend(parsed.patterns)
        
        # Add the main pattern argument only if no -e patterns were specified
        if parsed.pattern and not parsed.patterns:
            patterns.append(parsed.pattern)
        
        return patterns
    
    def _should_highlight(self, parsed: argparse.Namespace) -> bool:
        """Determine if matches should be highlighted."""
        if parsed.color == 'never':
            return False
        elif parsed.color == 'always':
            return True
        else:  # auto
            return sys.stdout.isatty()  # Only highlight if outputting to terminal
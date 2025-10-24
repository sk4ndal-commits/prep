"""Command-line argument parser for prep."""

import argparse
import os
import re
import sys
from typing import List, Optional, Tuple

from ..domain.models import SearchPattern, SearchOptions, MatchType


class PrepArgumentParser:
    """Argument parser for prep command-line interface."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    @staticmethod
    def _create_parser() -> argparse.ArgumentParser:
        """Create the argument parser with all options."""
        parser = argparse.ArgumentParser(
            prog='prep',
            description='prep - Python grep implementation',
            epilog="""
Examples:
  prep -r "pattern" file.txt                      # Basic search
  prep -r "pattern" -v file.txt                   # Invert match
  prep -r "pattern" -c *.txt                      # Count matches
  prep -r "pattern" -R /path/to/directory         # Recursive search
  prep -r "error|warning|fatal" app.log           # OR pattern matching
  prep -r "timeout&retry" app.log                 # AND pattern matching
  prep -r "error&(database|network)" app.log      # Complex Boolean expressions
  prep -r "test" -w code.txt                      # Word match
  prep -r "error" -x log.txt                      # Line match
  prep -r "panic" -B 2 server.log                 # Context lines before
  prep -r "ERROR" -A 3 app.log                    # Context lines after
  prep -r "exception" -C 2 trace.log              # Context before and after
  prep -r "pattern" -i file.txt                   # Case insensitive
  prep -r "ERROR" -f /var/log/app.log             # Watch file for changes
  prep -r "error" -j 4 logs/*.txt                 # Use 4 threads
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Pattern argument
        parser.add_argument(
            '-r', '--regexp',
            dest='pattern',
            help='Search pattern (regex)',
        )
        
        # Positional arguments for files
        parser.add_argument(
            'files',
            nargs='*',
            help='Files to search in (stdin if not specified)',
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
        
        # Regex options
        parser.add_argument(
            '--dotall',
            action='store_true',
            help='Make dot (.) match newline characters',
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
            '-R', '--recursive',
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
        default_threads = os.environ.get('RGREP_THREADS')
        parser.add_argument(
            '-j', '--threads',
            type=int,
            default=int(default_threads) if default_threads else None,
            metavar='N',
            help='Use N threads for parallel processing (env: RGREP_THREADS)',
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
        
        # File watching options
        parser.add_argument(
            '-f', '--follow',
            action='store_true',
            help='Watch file for changes and match patterns in new lines (like tail -f | grep)',
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> Tuple[SearchOptions, List[str]]:
        """Parse command line arguments and return search options and file paths."""
        parsed = self.parser.parse_args(args)
        
        # Validate pattern
        if not parsed.pattern:
            self.parser.error("no pattern provided")
        
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
        if parsed.dotall:
            regex_flags |= re.DOTALL
        
        # Create search pattern (single pattern with Boolean expression support)
        search_pattern = SearchPattern(
            pattern=parsed.pattern,
            match_type=match_type,
            regex_flags=regex_flags,
            is_regex=not parsed.fixed_strings
        )
        
        # Determine if highlighting should be enabled
        highlight_matches = self._should_highlight(parsed)
        
        # Handle binary files
        ignore_binary = parsed.binary_files == 'without-match'
        
        # Determine number of threads
        max_threads = parsed.threads if parsed.threads is not None else 1
        
        # Create search options
        options = SearchOptions(
            patterns=[search_pattern],
            invert_match=parsed.invert_match,
            count_only=parsed.count,
            quiet=parsed.quiet,
            context_before=context_before,
            context_after=context_after,
            highlight_matches=highlight_matches,
            recursive=parsed.recursive,
            ignore_binary=ignore_binary,
            max_threads=max_threads,
            follow=parsed.follow
        )
        
        # Get file paths
        file_paths = list(parsed.files)
        
        # If no files specified, default to stdin
        if not file_paths:
            file_paths = ['-']
        
        return options, file_paths
    
    @staticmethod
    def _should_highlight(parsed: argparse.Namespace) -> bool:
        """Determine if matches should be highlighted."""
        if parsed.color == 'never':
            return False
        elif parsed.color == 'always':
            return True
        else:  # auto
            return sys.stdout.isatty()  # Only highlight if outputting to terminal
"""File watching use case for prep."""

import signal
import sys

from ..domain.interfaces import FileWatcher, PatternMatcher, OutputFormatter
from ..domain.models import SearchOptions
from ..infrastructure.file_watcher import ContextBuffer


class FileWatchUseCase:
    """Use case for watching files and matching patterns in real-time."""
    
    def __init__(
        self,
        file_watcher: FileWatcher,
        pattern_matcher: PatternMatcher,
        output_formatter: OutputFormatter
    ):
        """
        Initialize the file watch use case.
        
        Args:
            file_watcher: File watcher implementation
            pattern_matcher: Pattern matcher implementation
            output_formatter: Output formatter implementation
        """
        self.file_watcher = file_watcher
        self.pattern_matcher = pattern_matcher
        self.output_formatter = output_formatter
        self._stop_requested = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self._stop_requested = True
        self.file_watcher.stop_watching()
    
    def watch_and_search(self, file_path: str, options: SearchOptions) -> int:
        """
        Watch a file for changes and search for patterns in new lines.
        
        Args:
            file_path: Path to the file to watch
            options: Search options including patterns and context
            
        Returns:
            Exit code (0 if matches found, 1 if no matches)
        """
        try:
            # Initialize context buffer
            context_buffer = ContextBuffer(
                before_lines=options.context_before,
                after_lines=options.context_after
            )
            
            line_number = 0
            matches_found = False

            # Start watching the file
            for line in self.file_watcher.watch_file(file_path):
                if self._stop_requested:
                    break
                
                line_number += 1
                
                # Check for pattern matches BEFORE adding to buffer
                matches = self.pattern_matcher.find_matches(line, line_number, options)
                should_include = self.pattern_matcher.should_include_line(matches, options)
                
                if should_include:
                    matches_found = True
                    
                    if not options.quiet:
                        # Get context for this match (buffer has lines BEFORE current line)
                        context = context_buffer.get_context_for_match(line_number, line)
                        
                        # Print before context
                        for before_line_num, before_line in context['before']:
                            self._print_context_line(
                                before_line
                            )
                        
                        # Print the matching line with highlighting - clean output like tail -f | grep
                        highlighted_line = line
                        if options.highlight_matches and not options.count_only:
                            # Apply highlighting using the output formatter's method
                            highlighted_line = self.output_formatter.highlight_matches(matches, line)
                        print(highlighted_line, flush=True)
                
                else:
                    # Check if this line should be included as after-context
                    should_include_after, line_info = context_buffer.get_after_context_line(
                        line_number, line
                    )
                    
                    if should_include_after and not options.quiet:
                        line_num, line_content = line_info
                        self._print_context_line(
                            line_content
                        )
                
                # Add line to buffer AFTER processing (for future before context)
                context_buffer.add_line(line)
            
            return 0 if matches_found else 1
            
        except FileNotFoundError:
            print(f"prep: {file_path}: No such file or directory", file=sys.stderr)
            return 2
        except KeyboardInterrupt:
            return 130  # Standard exit code for Ctrl+C
        except Exception as e:
            print(f"prep: error watching file: {e}", file=sys.stderr)
            return 2
    
    @staticmethod
    def _print_context_line(line_content: str) -> None:
        """Print a context line (before or after a match)."""
        # In file watching mode, print clean output without prefixes like tail -f | grep
        print(line_content, flush=True)


class FileWatchCountUseCase:
    """Use case for watching files and counting matches."""
    
    def __init__(self, file_watch_usecase: FileWatchUseCase):
        """Initialize with the main file watch use case."""
        self.file_watch_usecase = file_watch_usecase
    
    def execute(self, file_path: str, options: SearchOptions) -> int:
        """Execute count-only file watching."""
        # For count mode, we modify options to be quiet and track matches
        count_options = SearchOptions(
            patterns=options.patterns,
            invert_match=options.invert_match,
            count_only=True,
            quiet=True,
            context_before=0,  # No context needed for counting
            context_after=0,
            highlight_matches=False,
            recursive=options.recursive,
            ignore_binary=options.ignore_binary,
            max_threads=options.max_threads,
            follow=options.follow
        )
        
        return self.file_watch_usecase.watch_and_search(file_path, count_options)


class FileWatchQuietUseCase:
    """Use case for quiet file watching (exit status only)."""
    
    def __init__(self, file_watch_usecase: FileWatchUseCase):
        """Initialize with the main file watch use case."""
        self.file_watch_usecase = file_watch_usecase
    
    def execute(self, file_path: str, options: SearchOptions) -> int:
        """Execute quiet file watching."""
        quiet_options = SearchOptions(
            patterns=options.patterns,
            invert_match=options.invert_match,
            count_only=False,
            quiet=True,
            context_before=options.context_before,
            context_after=options.context_after,
            highlight_matches=False,
            recursive=options.recursive,
            ignore_binary=options.ignore_binary,
            max_threads=options.max_threads,
            follow=options.follow
        )
        
        return self.file_watch_usecase.watch_and_search(file_path, quiet_options)
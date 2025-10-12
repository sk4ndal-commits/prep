"""Main CLI application for prep."""

import sys
from typing import List, Optional
from pathlib import Path

from .argument_parser import PrepArgumentParser
from ..usecases.search_usecase import SearchUseCase, CountUseCase, QuietUseCase
from ..usecases.file_watch_usecase import FileWatchUseCase, FileWatchCountUseCase, FileWatchQuietUseCase
from ..infrastructure.file_operations import StandardFileReader, StandardFileScanner
from ..infrastructure.pattern_matching import HybridPatternMatcher
from ..infrastructure.output_formatting import StandardOutputFormatter
from ..infrastructure.parallel_execution import AdaptiveExecutor
from ..infrastructure.file_watcher import StandardFileWatcher
from ..domain.models import SearchOptions


class PrepApplication:
    """Main application class for prep CLI."""
    
    def __init__(self):
        self.arg_parser = PrepArgumentParser()
        
        # Initialize infrastructure components
        self.file_reader = StandardFileReader()
        self.file_scanner = StandardFileScanner()
        self.pattern_matcher = HybridPatternMatcher()
        self.output_formatter = StandardOutputFormatter()
        self.parallel_executor = AdaptiveExecutor()
        self.file_watcher = StandardFileWatcher()
        
        # Initialize use cases
        self.search_usecase = SearchUseCase(
            file_reader=self.file_reader,
            file_scanner=self.file_scanner,
            pattern_matcher=self.pattern_matcher,
            parallel_executor=self.parallel_executor
        )
        self.count_usecase = CountUseCase(self.search_usecase)
        self.quiet_usecase = QuietUseCase(self.search_usecase)
        
        # Initialize file watching use cases
        self.file_watch_usecase = FileWatchUseCase(
            file_watcher=self.file_watcher,
            pattern_matcher=self.pattern_matcher,
            output_formatter=self.output_formatter
        )
        self.file_watch_count_usecase = FileWatchCountUseCase(self.file_watch_usecase)
        self.file_watch_quiet_usecase = FileWatchQuietUseCase(self.file_watch_usecase)
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the prep application and return exit code."""
        try:
            options, file_paths = self.arg_parser.parse_args(args)
            return self._execute_search(options, file_paths)
        except KeyboardInterrupt:
            return 130  # Standard exit code for Ctrl+C
        except Exception as e:
            print(f"prep: error: {e}", file=sys.stderr)
            return 2
    
    def _execute_search(self, options: SearchOptions, file_paths: List[str]) -> int:
        """Execute the search operation."""
        # Handle file watching mode
        if options.follow:
            return self._execute_file_watch(options, file_paths)
        
        # Handle stdin input
        if file_paths == ['-']:
            file_paths = self._read_from_stdin()
            if not file_paths:
                return 1
        
        # Validate file paths
        validated_paths = self._validate_file_paths(file_paths, options.recursive)
        if not validated_paths:
            print("prep: no valid files to search", file=sys.stderr)
            return 2
        
        # Execute the appropriate use case
        if options.quiet:
            found_matches = self.quiet_usecase.execute(validated_paths, options)
            return 0 if found_matches else 1
        elif options.count_only:
            result = self.count_usecase.execute(validated_paths, options)
            output = self.output_formatter.format_result(result, options)
            if output:
                print(output)
            return 0 if result.total_matches > 0 else 1
        else:
            result = self.search_usecase.execute(validated_paths, options)
            output = self.output_formatter.format_result(result, options)
            if output:
                print(output)
            # Exit-Code-Logik für invert_match
            if options.invert_match:
                return 0 if result.total_matches > 0 else 1
            return 0 if result.total_matches > 0 else 1

    @staticmethod
    def _read_from_stdin() -> List[str]:
        """Read file paths from stdin."""
        try:
            lines = []
            for line in sys.stdin:
                line = line.strip()
                if line:
                    lines.append(line)
            return lines
        except (EOFError, KeyboardInterrupt):
            return []
    
    @staticmethod
    def _validate_file_paths(file_paths: List[str], recursive: bool) -> List[str]:
        """Validate and filter file paths."""
        valid_paths = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if path.is_file():
                valid_paths.append(str(path))
            elif path.is_dir():
                if recursive:
                    valid_paths.append(str(path))
                else:
                    print(f"prep: {file_path}: Is a directory", file=sys.stderr)
            else:
                print(f"prep: {file_path}: No such file or directory", file=sys.stderr)
        
        return valid_paths
    
    def _execute_file_watch(self, options: SearchOptions, file_paths: List[str]) -> int:
        """Execute file watching operation."""
        # File watching only supports a single file
        if len(file_paths) != 1:
            print("prep: file watching (-f/--follow) requires exactly one file", file=sys.stderr)
            return 2
        
        # No stdin support for file watching
        if file_paths[0] == '-':
            print("prep: file watching (-f/--follow) does not support stdin", file=sys.stderr)
            return 2
        
        file_path = file_paths[0]
        path = Path(file_path)
        
        # Validate file exists and is a regular file
        if not path.exists():
            print(f"prep: {file_path}: No such file or directory", file=sys.stderr)
            return 2
        
        if not path.is_file():
            print(f"prep: {file_path}: Not a regular file", file=sys.stderr)
            return 2
        
        # File watching doesn't support recursive mode
        if options.recursive:
            print("prep: file watching (-f/--follow) does not support recursive (-r) mode", file=sys.stderr)
            return 2
        
        # Execute the appropriate file watching use case
        try:
            if options.quiet:
                return self.file_watch_quiet_usecase.execute(file_path, options)
            elif options.count_only:
                return self.file_watch_count_usecase.execute(file_path, options)
            else:
                return self.file_watch_usecase.watch_and_search(file_path, options)
        except KeyboardInterrupt:
            return 130  # Standard exit code for Ctrl+C
        except Exception as e:
            print(f"prep: error in file watching: {e}", file=sys.stderr)
            return 2


def main() -> int:
    """Main entry point for prep command."""
    app = PrepApplication()
    return app.run()


if __name__ == '__main__':
    sys.exit(main())
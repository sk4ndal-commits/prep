"""Use cases for search operations in prep."""

from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..domain.interfaces import (
    FileReader, FileScanner, PatternMatcher, SearchService, ParallelExecutor
)
from ..domain.models import (
    SearchOptions, SearchResult, FileMatch, MatchResult, SearchPattern
)


class SearchUseCase:
    """Main use case for searching patterns in files."""
    
    def __init__(
        self,
        file_reader: FileReader,
        file_scanner: FileScanner,
        pattern_matcher: PatternMatcher,
        parallel_executor: Optional[ParallelExecutor] = None
    ):
        self._file_reader = file_reader
        self._file_scanner = file_scanner
        self._pattern_matcher = pattern_matcher
        self._parallel_executor = parallel_executor
    
    def execute(self, file_paths: List[str], options: SearchOptions) -> SearchResult:
        """Execute the search operation."""
        # Scan for files
        all_files = list(self._file_scanner.scan_files(file_paths, options.recursive))
        
        if not all_files:
            return SearchResult.empty()
        
        # Search files in parallel if configured
        if options.max_threads > 1 and self._parallel_executor and len(all_files) > 1:
            return self._search_parallel(all_files, options)
        else:
            return self._search_sequential(all_files, options)
    
    def _search_sequential(self, file_paths: List[str], options: SearchOptions) -> SearchResult:
        """Search files sequentially."""
        file_matches = []
        total_matches = 0
        files_with_matches = 0
        
        for file_path in file_paths:
            file_match = self._search_single_file(file_path, options)
            if file_match.matches or not options.quiet:
                file_matches.append(file_match)
            
            if file_match.matches:
                files_with_matches += 1
                total_matches += len(file_match.matches)
                
                # Early exit for quiet mode
                if options.quiet:
                    break
        
        return SearchResult(
            file_matches=file_matches,
            total_matches=total_matches,
            files_with_matches=files_with_matches
        )
    
    def _search_parallel(self, file_paths: List[str], options: SearchOptions) -> SearchResult:
        """Search files in parallel."""
        file_matches = []
        total_matches = 0
        files_with_matches = 0
        
        def search_file(file_path: str) -> FileMatch:
            return self._search_single_file(file_path, options)
        
        # Create tasks for parallel execution
        tasks = [lambda fp=file_path: search_file(fp) for file_path in file_paths]
        
        if self._parallel_executor:
            results = self._parallel_executor.execute_parallel(tasks, options.max_threads)
        else:
            # Fallback to ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=options.max_threads) as executor:
                future_to_file = {executor.submit(search_file, fp): fp for fp in file_paths}
                results = []
                
                for future in as_completed(future_to_file):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Early exit for quiet mode
                        if options.quiet and result.matches:
                            # Cancel remaining futures
                            for f in future_to_file:
                                f.cancel()
                            break
                    except Exception as exc:
                        # Log error but continue with other files
                        continue
        
        for file_match in results:
            if file_match.matches or not options.quiet:
                file_matches.append(file_match)
            
            if file_match.matches:
                files_with_matches += 1
                total_matches += len(file_match.matches)
        
        return SearchResult(
            file_matches=file_matches,
            total_matches=total_matches,
            files_with_matches=files_with_matches
        )
    
    def _search_single_file(self, file_path: str, options: SearchOptions) -> FileMatch:
        """Search for patterns in a single file."""
        if not self._file_reader.exists(file_path):
            return FileMatch(file_path=file_path, matches=[], is_binary=False)
        
        # Check if binary and should be ignored
        is_binary = self._file_reader.is_binary(file_path)
        if is_binary and options.ignore_binary:
            return FileMatch(file_path=file_path, matches=[], is_binary=True)
        
        matches = []
        try:
            for line_number, line_content in enumerate(self._file_reader.read_lines(file_path), 1):
                line_matches = self._pattern_matcher.find_matches(line_content, line_number, options)
                
                # Apply invert match logic
                should_include = self._pattern_matcher.should_include_line(line_matches, options)
                
                if should_include:
                    if options.invert_match:
                        # For invert match, create a dummy match result
                        matches.append(MatchResult(
                            line_number=line_number,
                            line_content=line_content,
                            match_start=0,
                            match_end=0,
                            pattern=options.patterns[0] if options.patterns else None
                        ))
                    else:
                        matches.extend(line_matches)
        except (UnicodeDecodeError, IOError):
            # Handle files that can't be read as text
            pass
        
        return FileMatch(file_path=file_path, matches=matches, is_binary=is_binary)


class CountUseCase:
    """Use case for counting matches (-c option)."""
    
    def __init__(self, search_usecase: SearchUseCase):
        self._search_usecase = search_usecase
    
    def execute(self, file_paths: List[str], options: SearchOptions) -> SearchResult:
        """Execute count-only search."""
        # Force count_only to True for this use case
        count_options = SearchOptions(
            patterns=options.patterns,
            invert_match=options.invert_match,
            count_only=True,
            quiet=options.quiet,
            context_before=0,  # No context for count
            context_after=0,   # No context for count
            highlight_matches=False,  # No highlighting for count
            recursive=options.recursive,
            ignore_binary=options.ignore_binary,
            max_threads=options.max_threads
        )
        
        return self._search_usecase.execute(file_paths, count_options)


class QuietUseCase:
    """Use case for quiet search (-q option)."""
    
    def __init__(self, search_usecase: SearchUseCase):
        self._search_usecase = search_usecase
    
    def execute(self, file_paths: List[str], options: SearchOptions) -> bool:
        """Execute quiet search and return whether matches were found."""
        quiet_options = SearchOptions(
            patterns=options.patterns,
            invert_match=options.invert_match,
            count_only=False,
            quiet=True,
            context_before=0,
            context_after=0,
            highlight_matches=False,
            recursive=options.recursive,
            ignore_binary=options.ignore_binary,
            max_threads=options.max_threads
        )
        
        result = self._search_usecase.execute(file_paths, quiet_options)
        return result.total_matches > 0
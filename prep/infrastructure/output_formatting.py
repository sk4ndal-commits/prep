"""Infrastructure implementation for output formatting."""

from typing import List, Optional, Dict
from collections import defaultdict

from ..domain.interfaces import OutputFormatter
from ..domain.models import SearchResult, FileMatch, MatchResult, SearchOptions


class ANSIColors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


class StandardOutputFormatter(OutputFormatter):
    """Standard output formatter implementation."""
    
    def format_result(self, result: SearchResult, options: SearchOptions) -> str:
        """Format the complete search result for output."""
        if options.quiet:
            return ""
        
        if options.count_only:
            return self._format_count_result(result)
        
        # Show filename prefix for multiple files
        show_filename = len(result.file_matches) > 1
        
        output_lines = []
        for file_match in result.file_matches:
            if file_match.matches:
                formatted = self.format_file_match(file_match, options, show_filename)
                if formatted:
                    output_lines.append(formatted)
        
        return '\n'.join(output_lines)
    
    def format_file_match(self, file_match: FileMatch, options: SearchOptions, show_filename: bool = False) -> str:
        """Format matches from a single file."""
        if not file_match.matches:
            return ""
        
        if options.count_only:
            return f"{file_match.file_path}:{file_match.match_count}"
        
        output_lines = []
        
        # Group matches by line number for context handling
        matches_by_line = defaultdict(list)
        for match in file_match.matches:
            matches_by_line[match.line_number].append(match)
        
        # Handle context lines
        if options.context_before > 0 or options.context_after > 0:
            output_lines.extend(self._format_with_context(file_match, options, matches_by_line, show_filename))
        else:
            # Simple format without context
            for line_number in sorted(matches_by_line.keys()):
                matches = matches_by_line[line_number]
                formatted_line = self._format_match_line_group(
                    matches, file_match.file_path, options, show_filename
                )
                if formatted_line:
                    output_lines.append(formatted_line)
        
        return '\n'.join(output_lines)
    
    def format_match_line(self, match: MatchResult, options: SearchOptions, context_lines: Optional[List[str]] = None) -> str:
        """Format a single matching line."""
        file_prefix = ""
        if len(options.patterns) > 1 or context_lines:
            file_prefix = f"{match.pattern.pattern if hasattr(match, 'pattern') and match.pattern else ''}:"
        
        line_content = match.line_content
        
        # Apply highlighting if requested
        if options.highlight_matches and not options.count_only:
            line_content = self.highlight_matches([match], line_content)
        
        line_prefix = f"{match.line_number}:"
        return f"{file_prefix}{line_prefix}{line_content}"
    
    @staticmethod
    def _format_count_result(result: SearchResult) -> str:
        """Format count-only result."""
        # Single file: print only the number
        if len(result.file_matches) == 1:
            file_match = result.file_matches[0]
            return str(file_match.match_count)
        
        # Multiple files: print filename:count per file
        lines = []
        for file_match in result.file_matches:
            lines.append(f"{file_match.file_path}:{file_match.match_count}")
        return '\n'.join(lines)
    
    def _format_match_line_group(self, matches: List[MatchResult], file_path: str, options: SearchOptions, show_filename: bool = False) -> str:
        """Format a group of matches on the same line."""
        if not matches:
            return ""
        
        # Use the first match as representative
        representative_match = matches[0]
        line_content = representative_match.line_content
        
        # Apply highlighting if requested
        if options.highlight_matches and not options.count_only:
            line_content = self.highlight_matches(matches, line_content)
        
        # Format the line
        prefix_parts = []
        if show_filename:
            prefix_parts.append(file_path)
        prefix_parts.append(str(representative_match.line_number))
        
        prefix = ":".join(prefix_parts) + ":"
        return f"{prefix}{line_content}"
    
    @staticmethod
    def highlight_matches(matches: List[MatchResult], line_content: str) -> str:
        """Apply ANSI highlighting to matches in a line."""
        if not matches:
            return line_content
        
        # Sort matches by start position (reverse order for safe replacement)
        sorted_matches = sorted(matches, key=lambda m: m.match_start, reverse=True)
        
        highlighted_content = line_content
        for match in sorted_matches:
            start = match.match_start
            end = match.match_end
            match_text = line_content[start:end]
            highlighted_text = f"{ANSIColors.RED}{ANSIColors.BOLD}{match_text}{ANSIColors.RESET}"
            highlighted_content = highlighted_content[:start] + highlighted_text + highlighted_content[end:]
        
        return highlighted_content
    
    def _format_with_context(self, file_match: FileMatch, options: SearchOptions, matches_by_line: Dict[int, List[MatchResult]], show_filename: bool = False) -> List[str]:
        """Format matches with context lines."""
        output_lines = []
        line_numbers = sorted(matches_by_line.keys())
        
        for i, line_number in enumerate(line_numbers):
            matches = matches_by_line[line_number]
            
            # Add separator if there's a gap between context groups
            if i > 0 and line_number - line_numbers[i-1] > 1:
                output_lines.append("--")
            
            # Check if this is a context line or actual match
            is_context_line = all(m.match_start == -1 for m in matches)
            
            if is_context_line:
                # Format context line (no highlighting)
                context_match = matches[0]
                prefix_parts = []
                if show_filename:
                    prefix_parts.append(file_match.file_path)
                prefix_parts.append(str(context_match.line_number))
                prefix = "-".join(prefix_parts) + "-"  # Use - for context lines
                formatted_line = f"{prefix}{context_match.line_content}"
                output_lines.append(formatted_line)
            else:
                # Format actual match line (with highlighting)
                formatted_line = self._format_match_line_group(
                    matches, file_match.file_path, options, show_filename
                )
                if formatted_line:
                    output_lines.append(formatted_line)
        
        return output_lines


class CompactOutputFormatter(OutputFormatter):
    """Compact output formatter for minimal output."""
    
    def format_result(self, result: SearchResult, options: SearchOptions) -> str:
        """Format the complete search result for output."""
        if options.quiet:
            return ""
        
        if options.count_only:
            return str(result.total_matches)
        
        output_lines = []
        for file_match in result.file_matches:
            if file_match.matches:
                for match in file_match.matches:
                    line = f"{file_match.file_path}:{match.line_number}:{match.line_content}"
                    output_lines.append(line)
        
        return '\n'.join(output_lines)
    
    def format_file_match(self, file_match: FileMatch, options: SearchOptions) -> str:
        """Format matches from a single file."""
        return self.format_result(
            SearchResult([file_match], file_match.match_count, 1 if file_match.matches else 0),
            options
        )
    
    def format_match_line(self, match: MatchResult, options: SearchOptions, context_lines: Optional[List[str]] = None) -> str:
        """Format a single matching line."""
        return match.line_content
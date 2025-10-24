"""Chronological merging for timestamped log entries."""

import re
from datetime import datetime
from typing import List, Optional, Tuple
from ..domain.models import MatchResult, FileMatch, SearchResult


class TimestampParser:
    """Parser for ISO-8601 timestamps in log lines."""
    
    # ISO-8601 pattern: YYYY-MM-DD[T ]HH:MM:SS(.fraction)?
    TIMESTAMP_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\.\d+)?'
    )
    
    @classmethod
    def parse_timestamp(cls, text: str) -> Optional[datetime]:
        """Extract and parse ISO-8601 timestamp from text.
        
        Args:
            text: Text potentially containing a timestamp
            
        Returns:
            datetime object if timestamp found and valid, None otherwise
        """
        match = cls.TIMESTAMP_PATTERN.search(text)
        if not match:
            return None
        
        date_part = match.group(1)
        time_part = match.group(2)
        timestamp_str = f"{date_part} {time_part}"
        
        try:
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None


class ChronologicalMerger:
    """Merge multi-file search results chronologically by timestamp."""
    
    def merge(self, result: SearchResult) -> SearchResult:
        """Merge file matches chronologically if all have timestamps.
        
        Args:
            result: Original search result
            
        Returns:
            SearchResult with chronologically sorted matches if possible,
            otherwise returns the original result unchanged
        """
        # Only apply to multi-file searches
        if len(result.file_matches) <= 1:
            return result
        
        # Extract all matches with their file information
        all_matches_with_meta = []
        
        for file_idx, file_match in enumerate(result.file_matches):
            for match in file_match.matches:
                # Try to parse timestamp from the match
                timestamp = TimestampParser.parse_timestamp(match.line_content)
                
                if timestamp is None:
                    # If ANY match lacks a timestamp, abort chronological merge
                    return result
                
                all_matches_with_meta.append({
                    'timestamp': timestamp,
                    'file_idx': file_idx,
                    'file_path': file_match.file_path,
                    'match': match
                })
        
        # All matches have timestamps - sort chronologically
        all_matches_with_meta.sort(
            key=lambda x: (x['timestamp'], x['file_idx'], x['match'].line_number)
        )
        
        # Rebuild file matches in chronological order
        # Group by file to maintain FileMatch structure
        merged_file_matches = []
        current_file = None
        current_matches = []
        
        for item in all_matches_with_meta:
            if current_file != item['file_path']:
                if current_file is not None:
                    # Save previous file's matches
                    merged_file_matches.append(
                        FileMatch(
                            file_path=current_file,
                            matches=current_matches,
                            is_binary=False
                        )
                    )
                current_file = item['file_path']
                current_matches = [item['match']]
            else:
                current_matches.append(item['match'])
        
        # Don't forget the last file
        if current_file is not None:
            merged_file_matches.append(
                FileMatch(
                    file_path=current_file,
                    matches=current_matches,
                    is_binary=False
                )
            )
        
        return SearchResult(
            file_matches=merged_file_matches,
            total_matches=result.total_matches,
            files_with_matches=result.files_with_matches
        )


def merge_chronologically(result: SearchResult) -> SearchResult:
    """Convenience function to merge search results chronologically.
    
    Args:
        result: Search result to merge
        
    Returns:
        Merged result if possible, original result otherwise
    """
    merger = ChronologicalMerger()
    return merger.merge(result)

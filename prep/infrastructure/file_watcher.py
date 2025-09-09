"""File watching implementation for prep."""

import os
import time
from typing import Iterator
from pathlib import Path

from ..domain.interfaces import FileWatcher


class StandardFileWatcher(FileWatcher):
    """Standard implementation of file watching using polling."""
    
    def __init__(self, poll_interval: float = 0.1):
        """
        Initialize the file watcher.
        
        Args:
            poll_interval: Time in seconds between file checks
        """
        self.poll_interval = poll_interval
        self._stop_watching = False
        self._last_position = 0
    
    def watch_file(self, file_path: str) -> Iterator[str]:
        """Watch a file for new lines and yield them as they are added."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Initialize position to end of file for tail behavior
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, 2)  # Seek to end of file
            self._last_position = f.tell()
        
        self._stop_watching = False
        
        while not self._stop_watching:
            try:
                current_size = os.path.getsize(file_path)
                
                if current_size > self._last_position:
                    # File has grown, read new content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self._last_position)
                        new_content = f.read()
                        self._last_position = f.tell()
                        
                        # Yield each new line
                        for line in new_content.splitlines():
                            if line:  # Skip empty lines
                                yield line
                
                elif current_size < self._last_position:
                    # File was truncated or recreated, reset position
                    self._last_position = 0
                
                time.sleep(self.poll_interval)
                
            except (OSError, IOError) as e:
                # File might have been deleted or become inaccessible
                if not Path(file_path).exists():
                    break
                # For other errors, continue trying
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                break
    
    def stop_watching(self) -> None:
        """Stop watching the file."""
        self._stop_watching = True


class ContextBuffer:
    """Buffer for maintaining context lines (before and after matches)."""
    
    def __init__(self, before_lines: int = 0, after_lines: int = 0):
        """
        Initialize the context buffer.
        
        Args:
            before_lines: Number of lines to keep before a match
            after_lines: Number of lines to keep after a match
        """
        self.before_lines = before_lines
        self.after_lines = after_lines
        self._buffer = []
        self._line_number = 0
        self._after_match_count = 0
        
    def add_line(self, line: str) -> None:
        """Add a line to the buffer."""
        self._line_number += 1
        
        # Add line with its number
        line_info = (self._line_number, line)
        
        # Maintain before context buffer
        if self.before_lines > 0:
            self._buffer.append(line_info)
            if len(self._buffer) > self.before_lines:
                self._buffer.pop(0)
    
    def get_context_for_match(self, match_line_number: int, match_line: str) -> dict:
        """
        Get context lines for a match.
        
        Returns:
            Dictionary with 'before', 'match', and 'after' context info
        """
        context = {
            'before': [],
            'match': (match_line_number, match_line),
            'after': []
        }
        
        # Get before context - return all lines in buffer except the current match
        if self.before_lines > 0:
            # The buffer contains the most recent lines before the match
            # Filter out the current match line if it's already in the buffer
            for line_num, line_content in self._buffer:
                if line_num != match_line_number:
                    context['before'].append((line_num, line_content))
        
        # Reset after match counter
        self._after_match_count = self.after_lines
        
        return context
    
    def get_after_context_line(self, line_number: int, line: str) -> tuple:
        """
        Check if this line should be included as after-context.
        
        Returns:
            Tuple of (should_include, line_info) where line_info is (line_number, line)
        """
        if self._after_match_count > 0:
            self._after_match_count -= 1
            return True, (line_number, line)
        return False, None
    
    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer.clear()
        self._line_number = 0
        self._after_match_count = 0
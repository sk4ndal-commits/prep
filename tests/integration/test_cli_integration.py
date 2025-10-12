"""Integration tests for CLI functionality."""

import tempfile
from pathlib import Path

import pytest

from prep.cli.application import PrepApplication


class TestCLIIntegration:
    """Test CLI integration behavior."""
    
    def setup_method(self):
        """Set up test files for each test."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_file1 = Path(self.temp_dir) / "test1.txt"
        self.test_file1.write_text("Hello world\nThis is a test\nAnother line\ntest again")
        
        self.test_file2 = Path(self.temp_dir) / "test2.txt"
        self.test_file2.write_text("Different content\nNo matches here\nSomething else")
        
        self.binary_file = Path(self.temp_dir) / "binary.bin"
        self.binary_file.write_bytes(b"Binary\x00content\x01here")
        
        # Create subdirectory
        self.sub_dir = Path(self.temp_dir) / "subdir"
        self.sub_dir.mkdir()
        self.sub_file = self.sub_dir / "sub.txt"
        self.sub_file.write_text("Nested test file\nWith test content")
    
    def teardown_method(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_basic_pattern_search(self):
        """Test basic pattern search functionality."""
        app = PrepApplication()
        
        # Test basic search
        exit_code = app.run(["test", str(self.test_file1)])
        assert exit_code == 0  # Should find matches
        
        # Test no matches
        exit_code = app.run(["nonexistent", str(self.test_file2)])
        assert exit_code == 1  # Should not find matches
    
    def test_invert_match_option(self):
        """Test -v (invert match) option."""
        app = PrepApplication()
        
        # Should find lines that don't contain "test"
        exit_code = app.run(["-v", "test", str(self.test_file1)])
        assert exit_code == 0  # Should find non-matching lines
    
    def test_count_option(self):
        """Test -c (count) option."""
        app = PrepApplication()
        
        exit_code = app.run(["-c", "test", str(self.test_file1)])
        assert exit_code == 0  # Should find matches and count them
    
    def test_quiet_option(self):
        """Test -q (quiet) option."""
        app = PrepApplication()
        
        # Should find matches but produce no output
        exit_code = app.run(["-q", "test", str(self.test_file1)])
        assert exit_code == 0  # Found matches
        
        # Should not find matches
        exit_code = app.run(["-q", "nonexistent", str(self.test_file1)])
        assert exit_code == 1  # No matches
    
    def test_multiple_patterns(self):
        """Test -e (multiple patterns) option."""
        app = PrepApplication()
        
        exit_code = app.run(["-e", "test", "-e", "Hello", str(self.test_file1)])
        assert exit_code == 0  # Should find matches for either pattern
    
    def test_word_match_option(self):
        """Test -w (word match) option."""
        app = PrepApplication()
        
        exit_code = app.run(["-w", "test", str(self.test_file1)])
        assert exit_code == 0  # Should find whole word matches
    
    def test_line_match_option(self):
        """Test -x (line match) option."""
        app = PrepApplication()
        
        exit_code = app.run(["-x", "This is a test", str(self.test_file1)])
        assert exit_code == 0  # Should find exact line match
    
    def test_case_insensitive_option(self):
        """Test -i (case insensitive) option."""
        app = PrepApplication()
        
        exit_code = app.run(["-i", "HELLO", str(self.test_file1)])
        assert exit_code == 0  # Should find "Hello" with case insensitive
    
    def test_recursive_search(self):
        """Test -r (recursive) option."""
        app = PrepApplication()
        
        exit_code = app.run(["-r", "test", str(self.temp_dir)])
        assert exit_code == 0  # Should find matches in subdirectories
    
    def test_context_options(self):
        """Test -A, -B, -C (context) options."""
        app = PrepApplication()
        
        # Test after context
        exit_code = app.run(["-A", "1", "test", str(self.test_file1)])
        assert exit_code == 0
        
        # Test before context
        exit_code = app.run(["-B", "1", "test", str(self.test_file1)])
        assert exit_code == 0
        
        # Test context around
        exit_code = app.run(["-C", "1", "test", str(self.test_file1)])
        assert exit_code == 0
    
    def test_binary_file_handling(self):
        """Test binary file handling."""
        app = PrepApplication()
        
        # Should skip binary file by default
        exit_code = app.run(["test", str(self.binary_file)])
        assert exit_code == 1  # No matches (binary file ignored)
    
    def test_fixed_strings_option(self):
        """Test -F (fixed strings) option."""
        app = PrepApplication()
        
        # Create file with regex-special characters
        regex_file = Path(self.temp_dir) / "regex.txt"
        regex_file.write_text("test.*pattern\nother line")
        
        # Should match literal string, not regex
        exit_code = app.run(["-F", "test.*", str(regex_file)])
        assert exit_code == 0
    
    def test_parallel_processing(self):
        """Test --threads (parallel processing) option."""
        app = PrepApplication()
        
        exit_code = app.run(["--threads", "2", "test", str(self.test_file1), str(self.test_file2)])
        assert exit_code == 0  # Should work with multiple threads
    
    def test_help_option(self):
        """Test --help option."""
        app = PrepApplication()
        
        # Help should exit with code 0 and show usage
        with pytest.raises(SystemExit) as exc_info:
            app.run(["--help"])
        assert exc_info.value.code == 0
    
    def test_invalid_arguments(self):
        """Test behavior with invalid arguments."""
        app = PrepApplication()
        
        # No pattern specified
        exit_code = app.run([str(self.test_file1)])
        assert exit_code == 2  # Error exit code
    
    def test_nonexistent_file(self):
        """Test behavior with nonexistent file."""
        app = PrepApplication()
        
        exit_code = app.run(["test", "/nonexistent/file.txt"])
        assert exit_code == 2  # Error exit code

    def test_logical_pattern_search(self):
        """Test logical pattern search with (A|B)&C."""
        test_file = Path(self.temp_dir) / "logic.txt"
        test_file.write_text("AC\nBC\nA\nB\nC\nA B C\nfoo bar\n")
        app = PrepApplication()
        # Suche nach Zeilen, die A oder B und zusätzlich C enthalten
        exit_code = app.run(["(A|B)&C", str(test_file)])
        assert exit_code == 0
        # Optional: weitere Validierung des Outputs möglich

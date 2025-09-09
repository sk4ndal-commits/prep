#!/usr/bin/env python3
"""Test script for file watching functionality."""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path


def write_to_file(file_path: str, lines: list, delay: float = 1.0):
    """Write lines to a file with delays between each line."""
    with open(file_path, 'w') as f:
        f.write("Initial content\n")
    
    time.sleep(0.5)  # Give prep time to start watching
    
    for line in lines:
        with open(file_path, 'a') as f:
            f.write(line + '\n')
        time.sleep(delay)


def test_basic_file_watching():
    """Test basic file watching functionality."""
    print("Testing basic file watching...")
    
    test_file = "test_watch_file.txt"
    
    try:
        # Create initial file
        Path(test_file).touch()
        
        # Lines to append
        test_lines = [
            "This is line 1",
            "ERROR: Something went wrong",
            "This is line 3",
            "WARN: This is a warning",
            "ERROR: Another error occurred",
            "This is the final line"
        ]
        
        # Start file writer in background
        writer_thread = threading.Thread(
            target=write_to_file,
            args=(test_file, test_lines, 0.5)
        )
        writer_thread.daemon = True
        writer_thread.start()
        
        # Run prep with file watching
        cmd = [sys.executable, "./prep.py", "-f", "ERROR", test_file]
        print(f"Running: {' '.join(cmd)}")
        
        # Run for a limited time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Let it run for a few seconds
        time.sleep(3)
        process.terminate()
        
        stdout, stderr = process.communicate(timeout=2)
        
        print("STDOUT:")
        print(stdout)
        
        if stderr:
            print("STDERR:")
            print(stderr)
        
        # Check if we got the expected matches
        if "ERROR: Something went wrong" in stdout and "ERROR: Another error occurred" in stdout:
            print("✅ Basic file watching test PASSED")
        else:
            print("❌ Basic file watching test FAILED")
            assert False, "Expected ERROR messages not found in stdout"
    
    except Exception as e:
        print(f"❌ Basic file watching test FAILED with exception: {e}")
        assert False, f"Test failed with exception: {e}"
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)


def test_file_watching_with_context():
    """Test file watching with context lines."""
    print("\nTesting file watching with context lines...")
    
    test_file = "test_watch_context.txt"
    
    try:
        # Create initial file
        Path(test_file).touch()
        
        # Lines to append
        test_lines = [
            "Line before error 1",
            "Line before error 2",
            "ERROR: Critical error",
            "Line after error 1",
            "Line after error 2",
            "Normal line",
            "Another normal line"
        ]
        
        # Start file writer in background
        writer_thread = threading.Thread(
            target=write_to_file,
            args=(test_file, test_lines, 0.5)
        )
        writer_thread.daemon = True
        writer_thread.start()
        
        # Run prep with file watching and context
        cmd = [sys.executable, "./prep.py", "-f", "-A", "2", "-B", "1", "ERROR", test_file]
        print(f"Running: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Let it run for a few seconds
        time.sleep(3)
        process.terminate()
        
        stdout, stderr = process.communicate(timeout=2)
        
        print("STDOUT:")
        print(stdout)
        
        if stderr:
            print("STDERR:")
            print(stderr)
        
        # Check if we got context lines
        if ("ERROR: Critical error" in stdout and 
            "Line before error 2" in stdout and
            "Line after error 1" in stdout):
            print("✅ File watching with context test PASSED")
        else:
            print("❌ File watching with context test FAILED")
            assert False, "Expected ERROR message with context lines not found in stdout"
    
    except Exception as e:
        print(f"❌ File watching with context test FAILED with exception: {e}")
        assert False, f"Test failed with exception: {e}"
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)


def test_file_watching_validation():
    """Test file watching validation (single file requirement)."""
    print("\nTesting file watching validation...")
    
    try:
        # Test multiple files (should fail)
        cmd = [sys.executable, "./prep.py", "-f", "pattern", "file1.txt", "file2.txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 2 and "requires exactly one file" in result.stderr:
            print("✅ Multiple files validation test PASSED")
            multiple_files_passed = True
        else:
            print(f"❌ Multiple files validation test FAILED: {result.stderr}")
            multiple_files_passed = False
        
        # Test stdin (should fail)
        cmd = [sys.executable, "./prep.py", "-f", "pattern", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 2 and "does not support stdin" in result.stderr:
            print("✅ Stdin validation test PASSED")
            stdin_passed = True
        else:
            print(f"❌ Stdin validation test FAILED: {result.stderr}")
            stdin_passed = False
        
        # Test nonexistent file (should fail)
        cmd = [sys.executable, "./prep.py", "-f", "pattern", "nonexistent_file.txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 2 and "No such file or directory" in result.stderr:
            print("✅ Nonexistent file validation test PASSED")
            nonexistent_passed = True
        else:
            print(f"❌ Nonexistent file validation test FAILED: {result.stderr}")
            nonexistent_passed = False
        
        # Assert all validation tests passed
        assert multiple_files_passed and stdin_passed and nonexistent_passed, "One or more validation tests failed"
    
    except Exception as e:
        print(f"❌ File watching validation tests FAILED with exception: {e}")
        assert False, f"Test failed with exception: {e}"


def main():
    """Run all file watching tests."""
    print("Starting file watching functionality tests...\n")
    
    tests = [
        test_basic_file_watching,
        test_file_watching_with_context,
        test_file_watching_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(0.5)  # Brief pause between tests
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED!")
        return 0
    else:
        print("💥 Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""prep - Python grep implementation."""

__version__ = "1.0.0"
__author__ = "prep development team"
__description__ = "A Python implementation of grep with advanced features"

from .cli.application import main

__all__ = ["main"]
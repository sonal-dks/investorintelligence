"""Shared pytest configuration."""

import sys
import os

# Ensure phase-01-data-ingestion is on the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

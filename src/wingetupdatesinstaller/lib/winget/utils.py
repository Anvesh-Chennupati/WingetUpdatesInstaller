"""
Common utilities for winget operations.
"""
from dataclasses import dataclass
from typing import List, Dict, Any

class WingetError(Exception):
    """Base exception for winget operations."""
    pass

def clean_text(text: str) -> str:
    """Clean text by removing special characters and normalizing spaces."""
    # Replace special characters
    text = text.replace('…', '...')  # Replace ellipsis
    text = text.replace('«', '')
    text = text.replace('à', '')
    text = text.replace('\u200b', '')  # Remove zero-width space
    # Normalize spaces and remove leading/trailing whitespace
    return ' '.join(text.split()).strip()

def parse_fixed_width_line(line: str, positions: List[int]) -> List[str]:
    """Parse a fixed width line using column positions."""
    values = []
    for i in range(len(positions)):
        start = positions[i]
        end = positions[i + 1] if i < len(positions) - 1 else len(line)
        value = clean_text(line[start:end])
        values.append(value)
    return values

@dataclass
class Package:
    """Represents a winget package."""
    name: str
    id: str
    version: str
    source: str

@dataclass
class PackageUpdate(Package):
    """Represents a winget package update."""
    available_version: str  # Must be first since it has no default
    is_unknown_version: bool = False
    requires_explicit_upgrade: bool = False

    def __post_init__(self):
        # Set default value for source if not provided
        if not hasattr(self, 'source'):
            self.source = ""

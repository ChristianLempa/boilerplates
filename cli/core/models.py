"""
Data models and structures for the CLI application.
Contains classes that represent boilerplate information and other data structures.
"""

from pathlib import Path
from typing import Any, Dict, List


class Boilerplate:
    """Data class for boilerplate information extracted from frontmatter."""
    
    def __init__(self, file_path: Path, frontmatter_data: Dict[str, Any], content: str):
        self.file_path = file_path
        self.content = content
        
        # Extract frontmatter fields with defaults
        self.name = frontmatter_data.get('name', file_path.stem)
        self.description = frontmatter_data.get('description', 'No description available')
        self.author = frontmatter_data.get('author', 'Unknown')
        self.date = frontmatter_data.get('date', 'Unknown')
        self.module = frontmatter_data.get('module', 'Unknown')
        self.files = frontmatter_data.get('files', [])
        
        # Additional computed properties
        self.relative_path = file_path.name
        self.size = file_path.stat().st_size if file_path.exists() else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            'name': self.name,
            'description': self.description,
            'author': self.author,
            'date': self.date,
            'module': self.module,
            'files': self.files,
            'path': str(self.relative_path),
            'size': f"{self.size:,} bytes"
        }

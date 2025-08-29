"""
Helper functions for common boilerplate operations.
Provides reusable utilities for scanning directories and formatting output.
"""

from pathlib import Path
from typing import List
import frontmatter

from .models import Boilerplate


def find_boilerplates(library_path: Path, file_names: List[str]) -> List[Boilerplate]:
    """
    Find all boilerplate files in the library directory and extract metadata.
    
    Args:
        library_path: Path to the library directory to scan
        file_names: List of file names to search for (e.g., ['compose.yaml', 'docker-compose.yaml'])
    
    Returns:
        List of Boilerplate objects sorted by name
    """
    boilerplates = []
    
    # Recursively scan all directories
    for boilerplate_file in library_path.rglob("*"):
        if boilerplate_file.is_file() and boilerplate_file.name in file_names:
            try:
                # Parse frontmatter
                with open(boilerplate_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                    boilerplate = Boilerplate(boilerplate_file, post.metadata, post.content)
                    
                    # If no name in frontmatter, use a meaningful name based on path
                    if boilerplate.name == boilerplate_file.stem:
                        # For nested paths like factory/runner-pool, use "Factory Runner Pool"
                        relative_path = boilerplate_file.relative_to(library_path)
                        path_parts = relative_path.parent.parts
                        boilerplate.name = " ".join(part.replace("_", " ").replace("-", " ").title() for part in path_parts)
                    
                    boilerplates.append(boilerplate)
                    
            except Exception as e:
                # If frontmatter parsing fails, create basic info
                boilerplate = Boilerplate(boilerplate_file, {}, "")
                relative_path = boilerplate_file.relative_to(library_path)
                path_parts = relative_path.parent.parts
                boilerplate.name = " ".join(part.replace("_", " ").replace("-", " ").title() for part in path_parts)
                boilerplates.append(boilerplate)
    
    return sorted(boilerplates, key=lambda x: x.name)


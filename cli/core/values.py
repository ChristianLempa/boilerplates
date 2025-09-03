"""
Core values loading functionality for handling template values from various sources.
Provides consistent value loading from files and command line arguments.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)

class ValuesLoader:
    """Handles loading and merging of template values from various sources."""

    @staticmethod
    def load_from_file(file_path: Path) -> Dict[str, Any]:
        """
        Load values from a YAML or JSON file.
        
        Args:
            file_path: Path to the values file
            
        Returns:
            Dictionary of loaded values
            
        Raises:
            ValueError: If file format is unsupported or file doesn't exist
            Exception: If file loading fails
        """
        if not file_path.exists():
            raise ValueError(f"Values file '{file_path}' not found.")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    if not yaml:
                        raise ImportError("PyYAML is required to load YAML files. Install it and retry.")
                    return yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    raise ValueError(
                        f"Unsupported file format '{file_path.suffix}'. Use .yaml, .yml, or .json"
                    )
        except Exception as e:
            raise Exception(f"Failed to load values from {file_path}: {e}")

    @staticmethod
    def parse_cli_values(values: List[str]) -> Dict[str, Any]:
        """
        Parse values provided via command line arguments.
        
        Args:
            values: List of key=value strings
            
        Returns:
            Dictionary of parsed values
            
        Raises:
            ValueError: If value format is invalid
        """
        result = {}
        
        for value_pair in values:
            if '=' not in value_pair:
                raise ValueError(
                    f"Invalid value format '{value_pair}'. Use key=value format."
                )
                
            key, val = value_pair.split('=', 1)
            
            # Try to parse as JSON for complex values
            try:
                result[key] = json.loads(val)
            except json.JSONDecodeError:
                # If not valid JSON, use as string
                result[key] = val
                
        return result

    @staticmethod
    def merge_values(*sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple value sources with later sources taking precedence.
        
        Args:
            *sources: Dictionaries of values to merge
            
        Returns:
            Merged values dictionary
        """
        result = {}
        
        for source in sources:
            result.update(source)
            
        return result

def load_and_merge_values(
    values_file: Optional[Path] = None,
    cli_values: Optional[List[str]] = None,
    config_values: Optional[Dict[str, Any]] = None,
    defaults: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load and merge values from all available sources in order of precedence:
    defaults <- config <- file <- CLI
    
    Args:
        values_file: Optional path to values file
        cli_values: Optional list of CLI key=value pairs
        config_values: Optional values from configuration
        defaults: Optional default values
        
    Returns:
        Dictionary of merged values
        
    Raises:
        Exception: If value loading fails
    """
    sources = []
    
    # Start with defaults if provided
    if defaults:
        sources.append(defaults)
        
    # Add config values if provided
    if config_values:
        sources.append(config_values)
        
    # Load from file if specified
    if values_file:
        try:
            file_values = ValuesLoader.load_from_file(values_file)
            sources.append(file_values)
        except Exception as e:
            raise Exception(f"Failed to load values file: {e}")
            
    # Parse CLI values if provided
    if cli_values:
        try:
            parsed_cli_values = ValuesLoader.parse_cli_values(cli_values)
            sources.append(parsed_cli_values)
        except ValueError as e:
            raise Exception(f"Failed to parse CLI values: {e}")
            
    # Merge all sources
    return ValuesLoader.merge_values(*sources)

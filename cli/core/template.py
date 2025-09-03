"""
Core template utilities for processing and rendering boilerplate templates.
Provides shared functionality for template cleaning, validation, and rendering
across different module types (compose, ansible, etc.).
"""
import re
import logging
from pathlib import Path
from typing import Optional, Tuple

try:
    import jinja2
except ImportError:
    jinja2 = None

logger = logging.getLogger(__name__)

def clean_template_content(content: str) -> str:
    """
    Remove template metadata blocks and prepare content for Jinja2 rendering.
    
    Args:
        content: Raw template content
        
    Returns:
        Cleaned template content with metadata blocks removed
    """
    # Remove variables block as it's not valid Jinja2 syntax
    return re.sub(r"\{%\s*variables\s*%\}(.+?)\{%\s*endvariables\s*%\}\n?", "", content, flags=re.S)

def validate_template(content: str, template_path: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate Jinja2 template syntax before rendering.
    
    Args:
        content: Template content to validate
        template_path: Optional path to template file for error messages
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not jinja2:
        return False, "Jinja2 is required to render templates. Install it and retry."
        
    try:
        env = jinja2.Environment(loader=jinja2.BaseLoader())
        env.parse(content)
        return True, None
    except jinja2.exceptions.TemplateSyntaxError as e:
        path_info = f" in '{template_path}'" if template_path else ""
        return False, f"Template syntax error{path_info}: {e.message} (line {e.lineno})"
    except Exception as e:
        path_info = f" '{template_path}'" if template_path else ""
        return False, f"Failed to parse template{path_info}: {e}"

def render_template(content: str, values: dict) -> Tuple[bool, str, Optional[str]]:
    """
    Render a template with the provided values.
    
    Args:
        content: Template content to render
        values: Dictionary of values to use in rendering
        
    Returns:
        Tuple of (success, rendered_content or empty string, error_message or None)
    """
    if not jinja2:
        return False, "", "Jinja2 is required to render templates. Install it and retry."
        
    try:
        # Enable whitespace control for cleaner output
        env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True
        )
        template = env.from_string(content)
        rendered = template.render(**values)
        return True, rendered, None
    except jinja2.exceptions.TemplateError as e:
        return False, "", f"Template rendering error: {e}"
    except Exception as e:
        return False, "", f"Unexpected error while rendering: {e}"

from abc import ABC
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import yaml
from typer import Typer, Option, Argument
from rich.console import Console
# Using standard Python exceptions
from .library import LibraryManager

logger = logging.getLogger(__name__)
console = Console()


class Module(ABC):
  """Streamlined base module that auto-detects variables from templates."""
  
  # Required class attributes for subclasses
  name = None
  description = None  
  files = None
  
  def __init__(self):
    if not all([self.name, self.description, self.files]):
      raise ValueError(
        f"Module {self.__class__.__name__} must define name, description, and files"
      )
    
    logger.info(f"Initializing module '{self.name}'")
    logger.debug(f"Module '{self.name}' configuration: files={self.files}, description='{self.description}'")
    self.libraries = LibraryManager()
    
    # Initialize variables if the subclass defines _init_variables method
    if hasattr(self, '_init_variables'):
      logger.debug(f"Module '{self.name}' has variable initialization method")
      self._init_variables()
      
      # Validate module variable registry consistency after initialization
      # NOTE: This ensures the module's variable hierarchy is properly structured (e.g., traefik.host requires traefik to exist).
      # The registry defines parent-child relationships where child variables like 'traefik.tls.certresolver' can only be used
      # when their parents ('traefik' and 'traefik.tls') are enabled. This prevents invalid module configurations.
      if hasattr(self, 'variables') and self.variables:
        var_count = len(self.variables.get_all_variables())
        logger.info(f"Module '{self.name}' registered {var_count} variables")
        
        registry_errors = self.variables.validate_parent_child_relationships()
        if registry_errors:
          error_msg = f"Module '{self.name}' has invalid variable registry:\n" + "\n".join(f"  - {e}" for e in registry_errors)
          logger.error(error_msg)
          raise ValueError(error_msg)
        logger.debug(f"Module '{self.name}' variable registry validation completed successfully")
    
    self.metadata = self._build_metadata()
    logger.info(f"Module '{self.name}' initialization completed successfully")
  
  def _build_metadata(self) -> Dict[str, Any]:
    """Build metadata from class attributes."""
    metadata = {}
    
    # Add categories if defined
    if hasattr(self, 'categories'):
      metadata['categories'] = self.categories
    
    # Add variable metadata if defined
    if hasattr(self, 'variable_metadata'):
      metadata['variables'] = self.variable_metadata
    
    return metadata

  def list(self):
    """List all templates."""
    logger.debug(f"Listing templates for module '{self.name}'")
    templates = self.libraries.find(self.name, self.files, sorted=True)
    
    if templates:
      logger.info(f"Listing {len(templates)} templates for module '{self.name}'")
    else:
      logger.info(f"No templates found for module '{self.name}'")
    
    # Display templates without enrichment (enrichment only needed for generation)
    for template in templates:
      console.print(f"[cyan]{template.id}[/cyan] - {template.name}")
    
    return templates

  def show(self, id: str = Argument(..., help="Template ID")):
    """Show template details."""
    logger.debug(f"Showing template '{id}' from module '{self.name}'")
    # Get template directly from library without enrichment (not needed for display)
    template = self.libraries.find_by_id(self.name, self.files, id)
    
    if not template:
      logger.debug(f"Template '{id}' not found in module '{self.name}'")
      raise FileNotFoundError(f"Template '{id}' not found in module '{self.name}'")

    # Header
    version = f" v{template.version}" if template.version else ""
    console.print(f"[bold magenta]{template.name} ({template.id}{version})[/bold magenta]")
    console.print(f"[dim white]{template.description}[/dim white]\n")
    
    # Metadata (only print if exists)
    metadata = [
      ("Author", template.author),
      ("Date", template.date),
      ("Tags", ', '.join(template.tags) if template.tags else None)
    ]
    
    for label, value in metadata:
      if value:
        console.print(f"{label}: [cyan]{value}[/cyan]")
    
    # Variables (show raw template variables without module enrichment)
    if template.vars:
      console.print(f"Variables: [cyan]{', '.join(sorted(template.vars))}[/cyan]")
    
    # Content
    if template.content:
      print(f"\n{template.content}")


  def _enrich_template_with_variables(self, template):
    """Enrich template with module variable registry defaults (optimized).
    
    This method updates the template's vars with module defaults while preserving
    template-specific variables and frontmatter definitions.
    
    Args:
        template: Template instance to enrich
    """
    # Skip if already enriched or no variables
    if template._is_enriched or not hasattr(self, 'variables') or not self.variables:
      if template._is_enriched:
        logger.debug(f"Template '{template.id}' already enriched, skipping")
      else:
        logger.debug(f"Module '{self.name}' has no variables, skipping enrichment for '{template.id}'")
      return
    
    logger.debug(f"Enriching template '{template.id}' with {len(self.variables.get_all_variables())} module variables")
    
    # Get template variables first (this is cached)
    template_vars = template._parse_template_variables(
      template.content, 
      getattr(template, 'frontmatter_variables', {})
    )
    
    # Only get module variables that are actually used in the template
    used_variables = template._get_used_variables()
    module_vars = {}
    module_defaults = {}
    
    for var_name in used_variables:
      var_obj = self.variables.get_variable(var_name)
      if var_obj:
        module_vars[var_name] = var_obj.default if var_obj.default is not None else None
        if var_obj.default is not None:
          module_defaults[var_name] = var_obj.default
    
    if module_defaults:
      logger.debug(f"Module provides {len(module_defaults)} defaults for used variables")
      logger.debug(f"Module default values: {module_defaults}")
    
    # Merge with template taking precedence
    final_vars = dict(module_vars)
    overrides = {}
    
    for var_name, var_value in template_vars.items():
      if var_name in final_vars and final_vars[var_name] != var_value and var_value is not None:
        logger.warning(
          f"Variable '{var_name}' defined in both module and template. Template takes precedence."
        )
        overrides[var_name] = var_value
      final_vars[var_name] = var_value
    
    if overrides:
      logger.debug(f"Template overrode {len(overrides)} module variables")
    
    # Set final variables and mark as enriched
    template.vars = final_vars
    template._is_enriched = True
    
    if final_vars:
      logger.info(f"Template '{template.id}' enriched with {len(final_vars)} variables from module '{self.name}'")
    else:
      logger.debug(f"Template '{template.id}' has no variables after enrichment")

  def _check_template_readiness(self, template):
    """Check if template is ready for generation (replaces complex validation).
    
    Args:
        template: Template instance to check
    
    Raises:
        ValueError: If template has critical issues preventing generation
    """
    logger.debug(f"Checking template readiness for '{template.id}'")
    errors = []
    
    # Check for basic template issues
    if not template.content.strip():
      errors.append("Template has no content")
    
    # Check for undefined variables (variables used but not available)
    undefined_vars = []
    for var_name, var_value in template.vars.items():
      if var_value is None:
        # Check if it's in module registry
        if hasattr(self, 'variables') and self.variables:
          var_obj = self.variables.get_variable(var_name)
          if not var_obj:
            # Not in module registry and no template default - problematic
            undefined_vars.append(var_name)
    
    if undefined_vars:
      errors.append(
        f"Template uses undefined variables: {', '.join(undefined_vars)}. "
        f"These variables are not registered in the module and have no template defaults."
      )
    
    # Check for syntax errors by attempting to create AST
    try:
      template._get_ast()
    except Exception as e:
      errors.append(f"Template has Jinja2 syntax errors: {str(e)}")
    
    if errors:
      logger.error(f"Template '{template.id}' failed readiness check with {len(errors)} errors")
      error_msg = f"Template '{template.id}' is not ready for generation:\n" + "\n".join(f"  - {e}" for e in errors)
      raise ValueError(error_msg)
    
    logger.debug(f"Template '{template.id}' passed readiness check")

  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    out: Optional[Path] = Option(None, "--out", "-o")
  ):
    """Generate from template."""

    logger.info(f"Starting generation for template '{id}' from module '{self.name}'")
    # Fetch template from library
    template = self.libraries.find_by_id(self.name, self.files, id)
    
    if not template:
      logger.error(f"Template '{id}' not found for generation in module '{self.name}'")
      raise FileNotFoundError(f"Template '{id}' not found in module '{self.name}'")
    
    # Enrich template with module variables if available
    self._enrich_template_with_variables(template)
    
    # Check for critical template issues after enrichment
    self._check_template_readiness(template)
    
    logger.info(f"Template '{id}' generation completed successfully for module '{self.name}'")
    print("TEST SUCCESSFUL")
  
  def register_cli(self, app: Typer):
    """Register module commands with the main app."""
    logger.debug(f"Registering CLI commands for module '{self.name}'")
    module_app = Typer()
    module_app.command()(self.list)
    module_app.command()(self.show)
    module_app.command()(self.generate)
    app.add_typer(module_app, name=self.name, help=self.description)
    logger.info(f"Module '{self.name}' CLI commands registered")

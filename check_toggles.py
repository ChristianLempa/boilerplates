#!/usr/bin/env python3
"""
Comprehensive check for missing toggle variables and their sections
"""
import re
import yaml
from pathlib import Path
from collections import defaultdict

def extract_variables(compose_content):
    """Extract all {{ variable_name }} from compose file"""
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    return set(re.findall(pattern, compose_content))

def extract_conditionals(compose_content):
    """Extract variables used in conditionals {% if var %}"""
    pattern = r'\{%\s*if\s+(\w+)'
    return set(re.findall(pattern, compose_content))

def get_existing_variables(template_data):
    """Get set of existing variables in template spec"""
    if not template_data or 'spec' not in template_data:
        return set()
    
    existing = set()
    spec = template_data['spec']
    
    for section_name, section_data in spec.items():
        if isinstance(section_data, dict) and 'vars' in section_data:
            existing.update(section_data['vars'].keys())
    
    return existing

def analyze_template(template_dir):
    """Analyze template for missing variables"""
    compose_path = template_dir / "compose.yaml.j2"
    template_path = template_dir / "template.yaml"
    
    if not compose_path.exists() or not template_path.exists():
        return None
    
    # Read files
    with open(compose_path, 'r') as f:
        compose_content = f.read()
    
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Extract all referenced variables
    used_vars = extract_variables(compose_content)
    conditional_vars = extract_conditionals(compose_content)
    all_used = used_vars | conditional_vars
    
    existing_vars = get_existing_variables(template_data)
    missing_vars = all_used - existing_vars
    
    return {
        'name': template_dir.name,
        'used_vars': used_vars,
        'conditional_vars': conditional_vars,
        'all_used': all_used,
        'existing_vars': existing_vars,
        'missing_vars': missing_vars
    }

def main():
    base_dir = Path("/Users/xcad/Projects/christianlempa/boilerplates/library/compose")
    
    toggle_vars = {
        'traefik_enabled', 'traefik_tls_enabled', 'volume_mode', 
        'swarm_enabled', 'database_enabled', 'email_enabled', 
        'authentik_enabled', 'resources_enabled'
    }
    
    print("="*80)
    print("CHECKING FOR MISSING TOGGLE VARIABLES")
    print("="*80)
    
    issues = []
    
    for template_dir in sorted(base_dir.iterdir()):
        if template_dir.is_dir():
            result = analyze_template(template_dir)
            if result and result['missing_vars']:
                # Check if any missing vars are toggle variables
                missing_toggles = result['missing_vars'] & toggle_vars
                if missing_toggles:
                    issues.append({
                        'template': result['name'],
                        'missing_toggles': missing_toggles,
                        'all_missing': result['missing_vars']
                    })
                    print(f"\n{result['name']}:")
                    print(f"  Missing toggle vars: {', '.join(sorted(missing_toggles))}")
                    if result['missing_vars'] - missing_toggles:
                        print(f"  Other missing vars: {', '.join(sorted(result['missing_vars'] - missing_toggles))}")
    
    print(f"\n\n{'='*80}")
    print(f"SUMMARY: {len(issues)} templates missing toggle variables")
    print('='*80)
    
    if issues:
        for issue in issues:
            print(f"  - {issue['template']}: {len(issue['missing_toggles'])} toggle(s), {len(issue['all_missing'])} total missing")

if __name__ == "__main__":
    main()

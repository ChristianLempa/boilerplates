#!/usr/bin/env python3
"""
Script to fix all compose templates by adding missing schema variables
"""
import os
import re
import yaml
from pathlib import Path

# Complete schema definition based on v1.2
SCHEMA = {
    "GENERAL": {
        "service_name": {"type": "string", "required": True},
        "container_name": {"type": "string", "required": True},
        "container_hostname": {"type": "string", "required": True},
        "container_timezone": {"type": "string", "default": "UTC"},
        "user_uid": {"type": "integer", "default": 1000},
        "user_gid": {"type": "integer", "default": 1000},
        "container_loglevel": {"type": "string", "default": "INFO"},
        "restart_policy": {"type": "string", "default": "unless-stopped"},
    },
    "NETWORK": {
        "network_mode": {"type": "string", "default": "bridge"},
        "network_name": {"type": "string", "default": ""},
        "network_external": {"type": "boolean", "default": False},
        "network_macvlan_ipv4_address": {"type": "string", "default": ""},
        "network_macvlan_parent_interface": {"type": "string", "default": ""},
        "network_macvlan_subnet": {"type": "string", "default": ""},
        "network_macvlan_gateway": {"type": "string", "default": ""},
    },
    "PORTS": {
        "ports_http": {"type": "integer", "default": 80},
        "ports_https": {"type": "integer", "default": 443},
        "ports_ssh": {"type": "integer", "default": 22},
        "ports_dns": {"type": "integer", "default": 53},
        "ports_dhcp": {"type": "integer", "default": 67},
        "ports_smtp": {"type": "integer", "default": 25},
        "ports_snmp": {"type": "integer", "default": 161},
    },
    "TRAEFIK": {
        "traefik_enabled": {"type": "boolean", "default": False},
        "traefik_network": {"type": "string", "default": "traefik"},
        "traefik_host": {"type": "string", "default": ""},
        "traefik_domain": {"type": "string", "default": ""},
    },
    "TRAEFIK_TLS": {
        "traefik_tls_enabled": {"type": "boolean", "default": False},
        "traefik_tls_certresolver": {"type": "string", "default": "letsencrypt"},
    },
    "VOLUME": {
        "volume_mode": {"type": "string", "default": "local"},
        "volume_mount_path": {"type": "string", "default": "/mnt/data"},
        "volume_nfs_server": {"type": "string", "default": ""},
        "volume_nfs_path": {"type": "string", "default": ""},
        "volume_nfs_options": {"type": "string", "default": "nfsvers=4,soft,timeo=180,intr"},
    },
    "RESOURCES": {
        "resources_cpu_limit": {"type": "string", "default": "1.0"},
        "resources_memory_limit": {"type": "string", "default": "512M"},
    },
    "SWARM": {
        "swarm_enabled": {"type": "boolean", "default": False},
        "swarm_replicas": {"type": "integer", "default": 1},
        "swarm_placement_mode": {"type": "string", "default": "replicated"},
        "swarm_placement_host": {"type": "string", "default": ""},
    },
    "DATABASE": {
        "database_enabled": {"type": "boolean", "default": False},
        "database_type": {"type": "string", "default": "postgres"},
        "database_external": {"type": "boolean", "default": False},
        "database_host": {"type": "string", "default": "localhost"},
        "database_port": {"type": "integer", "default": 5432},
        "database_name": {"type": "string", "default": ""},
        "database_user": {"type": "string", "default": ""},
        "database_password": {"type": "string", "default": ""},
    },
    "EMAIL": {
        "email_enabled": {"type": "boolean", "default": False},
        "email_host": {"type": "string", "default": ""},
        "email_port": {"type": "integer", "default": 587},
        "email_username": {"type": "string", "default": ""},
        "email_password": {"type": "string", "default": ""},
        "email_from": {"type": "string", "default": ""},
        "email_encryption": {"type": "string", "default": "tls"},
    },
    "AUTHENTIK": {
        "authentik_enabled": {"type": "boolean", "default": False},
        "authentik_url": {"type": "string", "default": ""},
        "authentik_slug": {"type": "string", "default": ""},
        "authentik_client_id": {"type": "string", "default": ""},
        "authentik_client_secret": {"type": "string", "default": ""},
    },
}

# Toggle variables that trigger entire sections
TOGGLE_SECTIONS = {
    "traefik_enabled": "TRAEFIK",
    "traefik_tls_enabled": "TRAEFIK_TLS",
    "volume_mode": "VOLUME",
    "swarm_enabled": "SWARM",
    "database_enabled": "DATABASE",
    "email_enabled": "EMAIL",
    "authentik_enabled": "AUTHENTIK",
}

def extract_variables(compose_content):
    """Extract all {{ variable_name }} from compose file"""
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    return set(re.findall(pattern, compose_content))

def get_variable_section(var_name):
    """Find which section a variable belongs to"""
    for section, variables in SCHEMA.items():
        if var_name in variables:
            return section
    return None

def load_template_yaml(path):
    """Load and parse template.yaml"""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_existing_variables(template_spec):
    """Get list of existing variables in template spec"""
    if not template_spec or 'spec' not in template_spec:
        return set()
    
    existing = set()
    spec = template_spec['spec']
    
    # Handle nested structure (sections with vars)
    for section_name, section_data in spec.items():
        if isinstance(section_data, dict) and 'vars' in section_data:
            existing.update(section_data['vars'].keys())
    
    return existing

def create_variable_entry(var_name, schema_info, description_prefix=""):
    """Create a template.yaml variable entry"""
    entry = {
        'name': var_name,
        'type': schema_info['type'],
    }
    
    # Add default if present
    if 'default' in schema_info:
        entry['default'] = schema_info['default']
    
    # Add required if present
    if schema_info.get('required'):
        entry['required'] = True
    
    # Generate description
    desc = description_prefix if description_prefix else f"The {var_name.replace('_', ' ')}"
    entry['description'] = desc
    
    return entry

def analyze_template(template_dir):
    """Analyze a single template and return missing variables"""
    compose_path = template_dir / "compose.yaml.j2"
    template_path = template_dir / "template.yaml"
    
    if not compose_path.exists():
        return None
    
    # Read compose file
    with open(compose_path, 'r') as f:
        compose_content = f.read()
    
    # Extract variables used
    used_vars = extract_variables(compose_content)
    
    # Load template.yaml
    if template_path.exists():
        template_data = load_template_yaml(template_path)
        existing_vars = get_existing_variables(template_data)
    else:
        template_data = {'spec': []}
        existing_vars = set()
    
    # Find missing variables
    missing_vars = used_vars - existing_vars
    
    # Group missing variables by section
    missing_by_section = {}
    sections_to_add = set()
    
    for var in missing_vars:
        section = get_variable_section(var)
        if section:
            if section not in missing_by_section:
                missing_by_section[section] = []
            missing_by_section[section].append(var)
            sections_to_add.add(section)
    
    # Check for toggle variables and add complete sections
    for var in used_vars:
        if var in TOGGLE_SECTIONS:
            section = TOGGLE_SECTIONS[var]
            # Add entire section if toggle is used
            for schema_var in SCHEMA[section].keys():
                if schema_var not in existing_vars:
                    if section not in missing_by_section:
                        missing_by_section[section] = []
                    if schema_var not in missing_by_section[section]:
                        missing_by_section[section].append(schema_var)
                    sections_to_add.add(section)
    
    return {
        'template_dir': template_dir,
        'used_vars': used_vars,
        'existing_vars': existing_vars,
        'missing_vars': missing_vars,
        'missing_by_section': missing_by_section,
        'sections_to_add': sections_to_add,
        'template_data': template_data
    }

def main():
    base_dir = Path("/Users/xcad/Projects/christianlempa/boilerplates/library/compose")
    
    results = {}
    for template_dir in sorted(base_dir.iterdir()):
        if template_dir.is_dir():
            print(f"\n{'='*60}")
            print(f"Analyzing: {template_dir.name}")
            print('='*60)
            
            result = analyze_template(template_dir)
            if result:
                results[template_dir.name] = result
                
                print(f"Used variables: {len(result['used_vars'])}")
                print(f"Existing variables: {len(result['existing_vars'])}")
                print(f"Missing variables: {len(result['missing_vars'])}")
                
                if result['missing_by_section']:
                    print("\nMissing by section:")
                    for section, vars in sorted(result['missing_by_section'].items()):
                        print(f"  {section}: {', '.join(sorted(vars))}")
                else:
                    print("\n✓ No missing variables!")
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total templates analyzed: {len(results)}")
    templates_with_missing = sum(1 for r in results.values() if r['missing_vars'])
    print(f"Templates with missing variables: {templates_with_missing}")
    print(f"Templates complete: {len(results) - templates_with_missing}")
    
    return results

if __name__ == "__main__":
    main()

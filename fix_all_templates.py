#!/usr/bin/env python3
"""
Script to fix all compose templates by adding ALL missing schema variables
"""
import os
import re
import yaml
from pathlib import Path
from collections import defaultdict

# Complete schema definition based on v1.2
SCHEMA_VARS = {
    # GENERAL section variables
    "service_name": {"section": "general", "type": "string", "required": True, "description": "The name of the service"},
    "container_name": {"section": "general", "type": "string", "required": True, "description": "The name of the container"},
    "container_hostname": {"section": "general", "type": "string", "required": True, "description": "The hostname of the container"},
    "container_timezone": {"section": "general", "type": "string", "default": "UTC", "description": "The timezone for the container"},
    "user_uid": {"section": "general", "type": "integer", "default": 1000, "description": "The user ID to run the container as"},
    "user_gid": {"section": "general", "type": "integer", "default": 1000, "description": "The group ID to run the container as"},
    "container_loglevel": {"section": "general", "type": "string", "default": "INFO", "description": "The log level for the container"},
    "restart_policy": {"section": "general", "type": "enum", "default": "unless-stopped", "description": "The restart policy for the container"},
    
    # NETWORK section variables
    "network_mode": {"section": "network", "type": "string", "default": "bridge", "description": "The network mode for the container"},
    "network_name": {"section": "network", "type": "string", "default": "", "description": "The name of the network"},
    "network_external": {"section": "network", "type": "boolean", "default": False, "description": "Whether the network is external"},
    "network_macvlan_ipv4_address": {"section": "network", "type": "string", "default": "", "description": "The IPv4 address for macvlan network"},
    "network_macvlan_parent_interface": {"section": "network", "type": "string", "default": "", "description": "The parent interface for macvlan network"},
    "network_macvlan_subnet": {"section": "network", "type": "string", "default": "", "description": "The subnet for macvlan network"},
    "network_macvlan_gateway": {"section": "network", "type": "string", "default": "", "description": "The gateway for macvlan network"},
    
    # PORTS section variables
    "ports_http": {"section": "ports", "type": "integer", "default": 80, "description": "The HTTP port"},
    "ports_https": {"section": "ports", "type": "integer", "default": 443, "description": "The HTTPS port"},
    "ports_ssh": {"section": "ports", "type": "integer", "default": 22, "description": "The SSH port"},
    "ports_dns": {"section": "ports", "type": "integer", "default": 53, "description": "The DNS port"},
    "ports_dhcp": {"section": "ports", "type": "integer", "default": 67, "description": "The DHCP port"},
    "ports_smtp": {"section": "ports", "type": "integer", "default": 25, "description": "The SMTP port"},
    "ports_snmp": {"section": "ports", "type": "integer", "default": 161, "description": "The SNMP port"},
    
    # TRAEFIK section variables
    "traefik_enabled": {"section": "traefik", "type": "boolean", "default": False, "description": "Enable Traefik integration"},
    "traefik_network": {"section": "traefik", "type": "string", "default": "traefik", "description": "The Traefik network name"},
    "traefik_host": {"section": "traefik", "type": "string", "default": "", "description": "The Traefik host"},
    "traefik_domain": {"section": "traefik", "type": "string", "default": "", "description": "The Traefik domain"},
    
    # TRAEFIK_TLS section variables
    "traefik_tls_enabled": {"section": "traefik_tls", "type": "boolean", "default": False, "description": "Enable Traefik TLS"},
    "traefik_tls_certresolver": {"section": "traefik_tls", "type": "string", "default": "letsencrypt", "description": "The Traefik TLS certificate resolver"},
    
    # VOLUME section variables
    "volume_mode": {"section": "volume", "type": "enum", "default": "local", "description": "The volume mode"},
    "volume_mount_path": {"section": "volume", "type": "string", "default": "/mnt/data", "description": "The volume mount path"},
    "volume_nfs_server": {"section": "volume", "type": "string", "default": "", "description": "The NFS server"},
    "volume_nfs_path": {"section": "volume", "type": "string", "default": "", "description": "The NFS path"},
    "volume_nfs_options": {"section": "volume", "type": "string", "default": "nfsvers=4,soft,timeo=180,intr", "description": "The NFS mount options"},
    
    # RESOURCES section variables
    "resources_cpu_limit": {"section": "resources", "type": "string", "default": "1.0", "description": "The CPU limit"},
    "resources_memory_limit": {"section": "resources", "type": "string", "default": "512M", "description": "The memory limit"},
    
    # SWARM section variables
    "swarm_enabled": {"section": "swarm", "type": "boolean", "default": False, "description": "Enable Docker Swarm mode"},
    "swarm_replicas": {"section": "swarm", "type": "integer", "default": 1, "description": "The number of replicas"},
    "swarm_placement_mode": {"section": "swarm", "type": "string", "default": "replicated", "description": "The placement mode"},
    "swarm_placement_host": {"section": "swarm", "type": "string", "default": "", "description": "The placement host"},
    
    # DATABASE section variables
    "database_enabled": {"section": "database", "type": "boolean", "default": False, "description": "Enable database integration"},
    "database_type": {"section": "database", "type": "string", "default": "postgres", "description": "The database type"},
    "database_external": {"section": "database", "type": "boolean", "default": False, "description": "Use external database"},
    "database_host": {"section": "database", "type": "string", "default": "localhost", "description": "The database host"},
    "database_port": {"section": "database", "type": "integer", "default": 5432, "description": "The database port"},
    "database_name": {"section": "database", "type": "string", "default": "", "description": "The database name"},
    "database_user": {"section": "database", "type": "string", "default": "", "description": "The database user"},
    "database_password": {"section": "database", "type": "string", "default": "", "description": "The database password"},
    
    # EMAIL section variables
    "email_enabled": {"section": "email", "type": "boolean", "default": False, "description": "Enable email integration"},
    "email_host": {"section": "email", "type": "string", "default": "", "description": "The email host"},
    "email_port": {"section": "email", "type": "integer", "default": 587, "description": "The email port"},
    "email_username": {"section": "email", "type": "string", "default": "", "description": "The email username"},
    "email_password": {"section": "email", "type": "string", "default": "", "description": "The email password"},
    "email_from": {"section": "email", "type": "string", "default": "", "description": "The email from address"},
    "email_encryption": {"section": "email", "type": "string", "default": "tls", "description": "The email encryption type"},
    
    # AUTHENTIK section variables
    "authentik_enabled": {"section": "authentik", "type": "boolean", "default": False, "description": "Enable Authentik SSO integration"},
    "authentik_url": {"section": "authentik", "type": "string", "default": "", "description": "The Authentik URL"},
    "authentik_slug": {"section": "authentik", "type": "string", "default": "", "description": "The Authentik application slug"},
    "authentik_client_id": {"section": "authentik", "type": "string", "default": "", "description": "The Authentik client ID"},
    "authentik_client_secret": {"section": "authentik", "type": "string", "default": "", "description": "The Authentik client secret"},
}

# Toggle variables that should trigger adding entire section
TOGGLE_SECTIONS = {
    "traefik_enabled": ["traefik_enabled", "traefik_network", "traefik_host", "traefik_domain"],
    "traefik_tls_enabled": ["traefik_tls_enabled", "traefik_tls_certresolver"],
    "volume_mode": ["volume_mode", "volume_mount_path", "volume_nfs_server", "volume_nfs_path", "volume_nfs_options"],
    "swarm_enabled": ["swarm_enabled", "swarm_replicas", "swarm_placement_mode", "swarm_placement_host"],
    "database_enabled": ["database_enabled", "database_type", "database_external", "database_host", "database_port", "database_name", "database_user", "database_password"],
    "email_enabled": ["email_enabled", "email_host", "email_port", "email_username", "email_password", "email_from", "email_encryption"],
    "authentik_enabled": ["authentik_enabled", "authentik_url", "authentik_slug", "authentik_client_id", "authentik_client_secret"],
}

def extract_variables(compose_content):
    """Extract all {{ variable_name }} from compose file"""
    pattern = r'\{\{\s*(\w+)\s*\}\}'
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

def analyze_and_fix_template(template_dir, dry_run=True):
    """Analyze a single template and fix missing variables"""
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
        with open(template_path, 'r') as f:
            template_data = yaml.safe_load(f)
        existing_vars = get_existing_variables(template_data)
    else:
        return None
    
    # Find variables to add
    vars_to_add = {}
    
    # Add missing used variables
    for var in used_vars:
        if var not in existing_vars and var in SCHEMA_VARS:
            vars_to_add[var] = SCHEMA_VARS[var]
    
    # Check for toggle variables and add complete sections
    for var in used_vars:
        if var in TOGGLE_SECTIONS:
            for section_var in TOGGLE_SECTIONS[var]:
                if section_var not in existing_vars and section_var in SCHEMA_VARS:
                    vars_to_add[section_var] = SCHEMA_VARS[section_var]
    
    if not vars_to_add:
        return {
            'template': template_dir.name,
            'status': 'complete',
            'vars_to_add': {}
        }
    
    # Group by section
    by_section = defaultdict(list)
    for var_name, var_info in vars_to_add.items():
        by_section[var_info['section']].append((var_name, var_info))
    
    result = {
        'template': template_dir.name,
        'status': 'needs_fix',
        'vars_to_add': vars_to_add,
        'by_section': dict(by_section),
        'template_path': template_path,
        'template_data': template_data
    }
    
    if not dry_run:
        # Apply fixes
        apply_fixes(result)
    
    return result

def apply_fixes(result):
    """Apply fixes to template.yaml"""
    template_data = result['template_data']
    by_section = result['by_section']
    
    if 'spec' not in template_data:
        template_data['spec'] = {}
    
    # Add missing variables to appropriate sections
    for section_name, vars_list in by_section.items():
        if section_name not in template_data['spec']:
            template_data['spec'][section_name] = {'vars': {}}
        elif 'vars' not in template_data['spec'][section_name]:
            template_data['spec'][section_name]['vars'] = {}
        
        for var_name, var_info in vars_list:
            var_entry = {}
            
            # Add type
            if var_info['type'] == 'enum':
                var_entry['type'] = 'enum'
                if var_name == 'restart_policy':
                    var_entry['options'] = ['unless-stopped', 'always', 'on-failure', 'no']
                elif var_name == 'volume_mode':
                    var_entry['options'] = ['local', 'mount', 'nfs']
            elif var_info['type'] == 'integer':
                var_entry['type'] = 'int'
            elif var_info['type'] == 'boolean':
                var_entry['type'] = 'bool'
            else:
                var_entry['type'] = 'str'
            
            # Add default
            if 'default' in var_info:
                var_entry['default'] = var_info['default']
            
            # Add required
            if var_info.get('required'):
                var_entry['required'] = True
            
            # Add description
            var_entry['description'] = var_info['description']
            
            template_data['spec'][section_name]['vars'][var_name] = var_entry
    
    # Write back to file
    with open(result['template_path'], 'w') as f:
        yaml.dump(template_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    base_dir = Path("/Users/xcad/Projects/christianlempa/boilerplates/library/compose")
    
    print("="*80)
    print("ANALYZING ALL COMPOSE TEMPLATES")
    print("="*80)
    
    results = []
    templates_to_fix = []
    
    for template_dir in sorted(base_dir.iterdir()):
        if template_dir.is_dir():
            result = analyze_and_fix_template(template_dir, dry_run=True)
            if result:
                results.append(result)
                if result['status'] == 'needs_fix':
                    templates_to_fix.append(result)
                    print(f"\n{result['template']}:")
                    for section, vars_list in result['by_section'].items():
                        print(f"  [{section}]")
                        for var_name, _ in vars_list:
                            print(f"    - {var_name}")
    
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Total templates analyzed: {len(results)}")
    print(f"Templates needing fixes: {len(templates_to_fix)}")
    print(f"Templates complete: {len(results) - len(templates_to_fix)}")
    
    if templates_to_fix:
        print(f"\n\nTemplates that need fixes:")
        for r in templates_to_fix:
            print(f"  - {r['template']} ({len(r['vars_to_add'])} missing variables)")
        
        response = input("\n\nApply fixes to all templates? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            print("\nApplying fixes...")
            for result in templates_to_fix:
                apply_fixes(result)
                print(f"  ✓ Fixed {result['template']}")
            print("\n✓ All fixes applied!")
        else:
            print("\nNo changes made.")
    else:
        print("\n✓ All templates are complete!")

if __name__ == "__main__":
    main()

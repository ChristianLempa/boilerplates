#!/usr/bin/env python3
"""
Comprehensive script to add ALL missing schema variables to compose templates
"""
import re
import yaml
from pathlib import Path
from collections import OrderedDict

# Complete v1.2 schema
SCHEMA_SECTIONS = OrderedDict([
    ('general', {
        'service_name': {'type': 'str', 'required': True, 'description': 'The name of the service'},
        'container_name': {'type': 'str', 'required': True, 'description': 'The name of the container'},
        'container_hostname': {'type': 'str', 'required': True, 'description': 'The hostname of the container'},
        'container_timezone': {'type': 'str', 'default': 'UTC', 'description': 'The timezone for the container'},
        'user_uid': {'type': 'int', 'default': 1000, 'description': 'The user ID to run the container as'},
        'user_gid': {'type': 'int', 'default': 1000, 'description': 'The group ID to run the container as'},
        'container_loglevel': {'type': 'str', 'default': 'INFO', 'description': 'The log level for the container'},
        'restart_policy': {'type': 'enum', 'options': ['unless-stopped', 'always', 'on-failure', 'no'], 'default': 'unless-stopped', 'required': True, 'description': 'The restart policy for the container'},
    }),
    ('network', {
        'network_mode': {'type': 'str', 'default': 'bridge', 'description': 'The network mode for the container'},
        'network_name': {'type': 'str', 'default': '', 'description': 'The name of the network'},
        'network_external': {'type': 'bool', 'default': False, 'description': 'Whether the network is external'},
        'network_macvlan_ipv4_address': {'type': 'str', 'default': '', 'description': 'The IPv4 address for macvlan network'},
        'network_macvlan_parent_interface': {'type': 'str', 'default': '', 'description': 'The parent interface for macvlan network'},
        'network_macvlan_subnet': {'type': 'str', 'default': '', 'description': 'The subnet for macvlan network'},
        'network_macvlan_gateway': {'type': 'str', 'default': '', 'description': 'The gateway for macvlan network'},
    }),
    ('ports', {
        'ports_http': {'type': 'int', 'default': 80, 'description': 'The HTTP port'},
        'ports_https': {'type': 'int', 'default': 443, 'description': 'The HTTPS port'},
        'ports_ssh': {'type': 'int', 'default': 22, 'description': 'The SSH port'},
        'ports_dns': {'type': 'int', 'default': 53, 'description': 'The DNS port'},
        'ports_dhcp': {'type': 'int', 'default': 67, 'description': 'The DHCP port'},
        'ports_smtp': {'type': 'int', 'default': 25, 'description': 'The SMTP port'},
        'ports_snmp': {'type': 'int', 'default': 161, 'description': 'The SNMP port'},
    }),
    ('traefik', {
        'traefik_enabled': {'type': 'bool', 'default': False, 'description': 'Enable Traefik integration'},
        'traefik_network': {'type': 'str', 'default': 'traefik', 'description': 'The Traefik network name'},
        'traefik_host': {'type': 'str', 'default': '', 'description': 'The Traefik host'},
        'traefik_domain': {'type': 'str', 'default': '', 'description': 'The Traefik domain'},
    }),
    ('traefik_tls', {
        'traefik_tls_enabled': {'type': 'bool', 'default': False, 'description': 'Enable Traefik TLS'},
        'traefik_tls_certresolver': {'type': 'str', 'default': 'letsencrypt', 'description': 'The Traefik TLS certificate resolver'},
    }),
    ('volume', {
        'volume_mode': {'type': 'enum', 'options': ['local', 'mount', 'nfs'], 'default': 'local', 'description': 'The volume mode'},
        'volume_mount_path': {'type': 'str', 'default': '/mnt/data', 'description': 'The volume mount path'},
        'volume_nfs_server': {'type': 'str', 'default': '', 'description': 'The NFS server'},
        'volume_nfs_path': {'type': 'str', 'default': '', 'description': 'The NFS path'},
        'volume_nfs_options': {'type': 'str', 'default': 'nfsvers=4,soft,timeo=180,intr', 'description': 'The NFS mount options'},
    }),
    ('resources', {
        'resources_cpu_limit': {'type': 'str', 'default': '1.0', 'description': 'The CPU limit'},
        'resources_memory_limit': {'type': 'str', 'default': '512M', 'description': 'The memory limit'},
    }),
    ('swarm', {
        'swarm_enabled': {'type': 'bool', 'default': False, 'description': 'Enable Docker Swarm mode'},
        'swarm_replicas': {'type': 'int', 'default': 1, 'description': 'The number of replicas'},
        'swarm_placement_mode': {'type': 'str', 'default': 'replicated', 'description': 'The placement mode'},
        'swarm_placement_host': {'type': 'str', 'default': '', 'description': 'The placement host'},
    }),
    ('database', {
        'database_enabled': {'type': 'bool', 'default': False, 'description': 'Enable database integration'},
        'database_type': {'type': 'str', 'default': 'postgres', 'description': 'The database type'},
        'database_external': {'type': 'bool', 'default': False, 'description': 'Use external database'},
        'database_host': {'type': 'str', 'default': 'localhost', 'description': 'The database host'},
        'database_port': {'type': 'int', 'default': 5432, 'description': 'The database port'},
        'database_name': {'type': 'str', 'default': '', 'description': 'The database name'},
        'database_user': {'type': 'str', 'default': '', 'description': 'The database user'},
        'database_password': {'type': 'str', 'default': '', 'description': 'The database password'},
    }),
    ('email', {
        'email_enabled': {'type': 'bool', 'default': False, 'description': 'Enable email integration'},
        'email_host': {'type': 'str', 'default': '', 'description': 'The email host'},
        'email_port': {'type': 'int', 'default': 587, 'description': 'The email port'},
        'email_username': {'type': 'str', 'default': '', 'description': 'The email username'},
        'email_password': {'type': 'str', 'default': '', 'description': 'The email password'},
        'email_from': {'type': 'str', 'default': '', 'description': 'The email from address'},
        'email_encryption': {'type': 'str', 'default': 'tls', 'description': 'The email encryption type'},
    }),
    ('authentik', {
        'authentik_enabled': {'type': 'bool', 'default': False, 'description': 'Enable Authentik SSO integration'},
        'authentik_url': {'type': 'str', 'default': '', 'description': 'The Authentik URL'},
        'authentik_slug': {'type': 'str', 'default': '', 'description': 'The Authentik application slug'},
        'authentik_client_id': {'type': 'str', 'default': '', 'description': 'The Authentik client ID'},
        'authentik_client_secret': {'type': 'str', 'default': '', 'description': 'The Authentik client secret'},
    }),
])

# Mapping of all vars to their sections
VAR_TO_SECTION = {}
for section, vars_dict in SCHEMA_SECTIONS.items():
    for var_name in vars_dict.keys():
        VAR_TO_SECTION[var_name] = section

# Toggle variables that trigger entire sections
TOGGLE_SECTIONS = {
    'traefik_enabled': ['traefik_enabled', 'traefik_network', 'traefik_host', 'traefik_domain'],
    'traefik_tls_enabled': ['traefik_tls_enabled', 'traefik_tls_certresolver'],
    'volume_mode': ['volume_mode', 'volume_mount_path', 'volume_nfs_server', 'volume_nfs_path', 'volume_nfs_options'],
    'swarm_enabled': ['swarm_enabled', 'swarm_replicas', 'swarm_placement_mode', 'swarm_placement_host'],
    'database_enabled': ['database_enabled', 'database_type', 'database_external', 'database_host', 'database_port', 'database_name', 'database_user', 'database_password'],
    'email_enabled': ['email_enabled', 'email_host', 'email_port', 'email_username', 'email_password', 'email_from', 'email_encryption'],
    'authentik_enabled': ['authentik_enabled', 'authentik_url', 'authentik_slug', 'authentik_client_id', 'authentik_client_secret'],
}

def extract_all_vars(compose_content):
    """Extract all referenced variables from compose file"""
    # Variables in {{ }}
    vars_pattern = r'\{\{\s*(\w+)\s*\}\}'
    vars_in_braces = set(re.findall(vars_pattern, compose_content))
    
    # Variables in {% if %}
    cond_pattern = r'\{%\s*if\s+(\w+)'
    vars_in_conds = set(re.findall(cond_pattern, compose_content))
    
    # Variables in {% if not var %}
    not_pattern = r'\{%\s*if\s+not\s+(\w+)'
    vars_in_not = set(re.findall(not_pattern, compose_content))
    
    # Variables in comparisons like {% if var == 'value' %}
    comp_pattern = r'\{%\s*if\s+(\w+)\s*=='
    vars_in_comps = set(re.findall(comp_pattern, compose_content))
    
    # Variables in {% elif %}
    elif_pattern = r'\{%\s*elif\s+(\w+)'
    vars_in_elif = set(re.findall(elif_pattern, compose_content))
    
    # Variables in {% elif not var %}
    elif_not_pattern = r'\{%\s*elif\s+not\s+(\w+)'
    vars_in_elif_not = set(re.findall(elif_not_pattern, compose_content))
    
    # Variables in "and not" / "or not" conditions
    and_not_pattern = r'and\s+not\s+(\w+)'
    vars_in_and_not = set(re.findall(and_not_pattern, compose_content))
    
    or_not_pattern = r'or\s+not\s+(\w+)'
    vars_in_or_not = set(re.findall(or_not_pattern, compose_content))
    
    return (vars_in_braces | vars_in_conds | vars_in_not | vars_in_comps | 
            vars_in_elif | vars_in_elif_not | vars_in_and_not | vars_in_or_not)

def get_existing_vars(template_data):
    """Get existing variables from template.yaml"""
    if not template_data or 'spec' not in template_data:
        return set()
    
    existing = set()
    for section_name, section_data in template_data['spec'].items():
        if isinstance(section_data, dict) and 'vars' in section_data:
            existing.update(section_data['vars'].keys())
    
    return existing

def determine_vars_to_add(used_vars, existing_vars):
    """Determine which variables need to be added"""
    to_add = {}
    
    # Add directly used schema variables
    for var in used_vars:
        if var in VAR_TO_SECTION and var not in existing_vars:
            section = VAR_TO_SECTION[var]
            to_add[var] = (section, SCHEMA_SECTIONS[section][var])
    
    # Check for toggle variables and add complete sections
    for var in used_vars:
        if var in TOGGLE_SECTIONS:
            for section_var in TOGGLE_SECTIONS[var]:
                if section_var not in existing_vars and section_var in VAR_TO_SECTION:
                    section = VAR_TO_SECTION[section_var]
                    to_add[section_var] = (section, SCHEMA_SECTIONS[section][section_var])
    
    return to_add

def apply_fixes(template_path, template_data, vars_to_add):
    """Add missing variables to template.yaml"""
    if 'spec' not in template_data:
        template_data['spec'] = {}
    
    # Group vars by section
    by_section = {}
    for var_name, (section_name, var_def) in vars_to_add.items():
        if section_name not in by_section:
            by_section[section_name] = []
        by_section[section_name].append((var_name, var_def))
    
    # Add to each section
    for section_name, vars_list in by_section.items():
        if section_name not in template_data['spec']:
            template_data['spec'][section_name] = {'vars': {}}
        elif 'vars' not in template_data['spec'][section_name]:
            template_data['spec'][section_name]['vars'] = {}
        
        for var_name, var_def in sorted(vars_list):
            var_entry = {}
            
            # Add type
            if 'type' in var_def:
                var_entry['type'] = var_def['type']
            
            # Add options for enums
            if 'options' in var_def:
                var_entry['options'] = var_def['options']
            
            # Add default
            if 'default' in var_def:
                var_entry['default'] = var_def['default']
            
            # Add required
            if var_def.get('required'):
                var_entry['required'] = True
            
            # Add description
            if 'description' in var_def:
                var_entry['description'] = var_def['description']
            
            template_data['spec'][section_name]['vars'][var_name] = var_entry
    
    # Write back to file with proper formatting
    with open(template_path, 'w') as f:
        yaml.dump(template_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)

def analyze_template(template_dir):
    """Analyze a template and return what needs to be fixed"""
    compose_path = template_dir / "compose.yaml.j2"
    template_path = template_dir / "template.yaml"
    
    if not compose_path.exists() or not template_path.exists():
        return None
    
    # Read compose file
    with open(compose_path, 'r') as f:
        compose_content = f.read()
    
    # Read template
    with open(template_path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    # Extract vars
    used_vars = extract_all_vars(compose_content)
    existing_vars = get_existing_vars(template_data)
    
    # Filter out non-schema vars and special keywords
    schema_used_vars = {v for v in used_vars if v in VAR_TO_SECTION}
    
    # Determine what to add
    vars_to_add = determine_vars_to_add(used_vars, existing_vars)
    
    if not vars_to_add:
        return None
    
    return {
        'name': template_dir.name,
        'template_path': template_path,
        'template_data': template_data,
        'vars_to_add': vars_to_add,
        'count': len(vars_to_add)
    }

def main():
    base_dir = Path("/Users/xcad/Projects/christianlempa/boilerplates/library/compose")
    
    print("="*80)
    print("ANALYZING ALL 34 COMPOSE TEMPLATES")
    print("="*80)
    
    templates_to_fix = []
    
    for template_dir in sorted(base_dir.iterdir()):
        if template_dir.is_dir():
            result = analyze_template(template_dir)
            if result:
                templates_to_fix.append(result)
                print(f"\n{result['name']}:")
                by_section = {}
                for var_name, (section, _) in result['vars_to_add'].items():
                    if section not in by_section:
                        by_section[section] = []
                    by_section[section].append(var_name)
                
                for section in sorted(by_section.keys()):
                    print(f"  [{section}]")
                    for var_name in sorted(by_section[section]):
                        print(f"    - {var_name}")
    
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Total templates needing fixes: {len(templates_to_fix)}")
    if templates_to_fix:
        total_vars = sum(t['count'] for t in templates_to_fix)
        print(f"Total variables to add: {total_vars}")
        print(f"\nTemplates:")
        for t in templates_to_fix:
            print(f"  - {t['name']}: {t['count']} variable(s)")
        
        print(f"\n{'='*80}")
        response = input("Apply fixes to all templates? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            print("\nApplying fixes...")
            for result in templates_to_fix:
                apply_fixes(result['template_path'], result['template_data'], result['vars_to_add'])
                print(f"  ✓ Fixed {result['name']} ({result['count']} variables added)")
            print("\n✓ All fixes applied successfully!")
        else:
            print("\nNo changes made.")
    else:
        print("\n✓ All templates are complete!")

if __name__ == "__main__":
    main()

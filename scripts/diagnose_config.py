#!/usr/bin/env python3
"""
Diagnostic script for boilerplates configuration issues.
Run this script if you encounter errors with 'boilerplates repo update'.
"""
import sys
from pathlib import Path
import yaml


def check_config():
    """Check and diagnose boilerplates configuration."""
    print("Boilerplates Configuration Diagnostic")
    print("=" * 60)
    
    # Check config file exists
    config_path = Path.home() / ".config" / "boilerplates" / "config.yaml"
    
    if not config_path.exists():
        print("❌ Config file not found")
        print(f"   Expected location: {config_path}")
        print("\n✓ Solution: Run 'boilerplates repo update' to create default config")
        return False
    
    print(f"✓ Config file found: {config_path}")
    
    # Try to load config
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"\n❌ Config file has invalid YAML syntax")
        print(f"   Error: {e}")
        print("\n✓ Solution: Fix YAML syntax or delete config file and run 'boilerplates repo update'")
        return False
    except Exception as e:
        print(f"\n❌ Error reading config file: {e}")
        return False
    
    print("✓ Config file is valid YAML")
    
    # Check config structure
    if not isinstance(config, dict):
        print("\n❌ Config is not a dictionary")
        return False
    
    # Check libraries section
    if "libraries" not in config:
        print("\n⚠️  No libraries section found (will be added automatically)")
    else:
        libraries = config["libraries"]
        if not isinstance(libraries, list):
            print("\n❌ Libraries section is not a list")
            return False
        
        print(f"\n✓ Found {len(libraries)} library configuration(s):")
        
        for i, lib in enumerate(libraries):
            if not isinstance(lib, dict):
                print(f"  ❌ Library {i+1}: Not a dictionary")
                continue
            
            name = lib.get("name", f"<unnamed-{i}>")
            url = lib.get("url", "<missing>")
            branch = lib.get("branch", "main")
            directory = lib.get("directory", ".")
            enabled = lib.get("enabled", True)
            
            status = "✓" if enabled else "⚠️ (disabled)"
            print(f"\n  {status} Library: {name}")
            print(f"      URL: {url}")
            print(f"      Branch: {branch}")
            print(f"      Directory: {directory}")
            
            # Check for common issues
            if not name:
                print(f"      ❌ Missing 'name' field")
            if not url:
                print(f"      ❌ Missing 'url' field")
            if branch and branch != "main" and "refactor" in branch:
                print(f"      ⚠️  Using development branch - consider using 'main'")
    
    # Check library directories
    libraries_path = config_path.parent / "libraries"
    if not libraries_path.exists():
        print(f"\n⚠️  Libraries directory not found: {libraries_path}")
        print("   Run 'boilerplates repo update' to sync libraries")
    else:
        print(f"\n✓ Libraries directory exists: {libraries_path}")
        
        # Check each library
        for lib_dir in libraries_path.iterdir():
            if lib_dir.is_dir() and not lib_dir.name.startswith('.'):
                print(f"  ✓ Library synced: {lib_dir.name}")
    
    print("\n" + "=" * 60)
    print("Diagnostic complete!")
    print("\nIf you're still experiencing issues:")
    print("  1. Delete the config file and run 'boilerplates repo update'")
    print("  2. Check the GitHub issue tracker")
    print("  3. Run with --log-level DEBUG for more details")
    
    return True


if __name__ == "__main__":
    try:
        success = check_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

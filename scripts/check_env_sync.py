#!/usr/bin/env python3
"""
Check that .env.example contains all variables used in .env
"""

import sys
from pathlib import Path

def get_env_variables(file_path: Path) -> set:
    """Extract variable names from an env file"""
    variables = set()

    if not file_path.exists():
        return variables

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                if '=' in line:
                    var_name = line.split('=')[0].strip()
                    variables.add(var_name)

    return variables

def main():
    """Check sync between .env and .env.example"""
    env_file = Path('.env')
    example_file = Path('.env.example')

    if not env_file.exists():
        print("✅ No .env file to check")
        sys.exit(0)

    if not example_file.exists():
        print("❌ .env.example not found!")
        sys.exit(1)

    env_vars = get_env_variables(env_file)
    example_vars = get_env_variables(example_file)

    missing_in_example = env_vars - example_vars

    if missing_in_example:
        print("❌ Variables in .env but not in .env.example:")
        for var in sorted(missing_in_example):
            print(f"  - {var}")
        print("\nPlease add these variables to .env.example with placeholder values")
        sys.exit(1)
    else:
        print("✅ .env.example is up to date")
        sys.exit(0)

if __name__ == "__main__":
    main()
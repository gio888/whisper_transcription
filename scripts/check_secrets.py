#!/usr/bin/env python3
"""
Check for potential secrets and API keys in the codebase
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Common secret patterns
SECRET_PATTERNS = [
    # API Keys
    (r'(?i)(api[_-]?key|apikey)\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "API Key"),
    (r'(?i)(secret[_-]?key|secretkey)\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "Secret Key"),

    # OpenAI
    (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key"),

    # Anthropic
    (r'sk-ant-[a-zA-Z0-9]{90,}', "Anthropic API Key"),

    # Notion
    (r'secret_[a-zA-Z0-9]{43}', "Notion API Key"),

    # AWS
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'(?i)aws_secret_access_key\s*=\s*["\'][a-zA-Z0-9/+=]{40}["\']', "AWS Secret Key"),

    # GitHub
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
    (r'gho_[a-zA-Z0-9]{36}', "GitHub OAuth Token"),

    # Generic patterns
    (r'(?i)password\s*=\s*["\'][^"\']{8,}["\']', "Password"),
    (r'(?i)token\s*=\s*["\'][a-zA-Z0-9_\-\.]{20,}["\']', "Token"),

    # Database URLs with credentials
    (r'(?i)(postgres|mysql|mongodb)://[^:]+:[^@]+@', "Database URL with credentials"),

    # Private keys
    (r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----', "Private Key"),
]

# Files to skip
SKIP_FILES = {
    '.env.example',
    '.env.test',
    'check_secrets.py',
    'test_*.py',
    '*.md',
}

# Allowed patterns (false positives)
ALLOWED_PATTERNS = [
    'your_.*_key_here',
    'your_.*_id_here',
    'sk-\\.\\.\\.',
    'secret_\\.\\.\\.',
    'example',
    'placeholder',
    'dummy',
    'test',
]

def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped"""
    # Skip hidden directories
    for part in file_path.parts:
        if part.startswith('.') and part not in {'.', '..'}:
            return True

    # Skip specific files
    for pattern in SKIP_FILES:
        if file_path.match(pattern):
            return True

    # Skip binary files
    try:
        with open(file_path, 'r') as f:
            f.read(1)
    except (UnicodeDecodeError, PermissionError):
        return True

    return False

def is_allowed(content: str) -> bool:
    """Check if the found pattern is in the allowed list"""
    for allowed in ALLOWED_PATTERNS:
        if re.search(allowed, content, re.IGNORECASE):
            return True
    return False

def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a file for potential secrets"""
    findings = []

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except:
        return findings

    for line_num, line in enumerate(lines, 1):
        for pattern, secret_type in SECRET_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                matched_text = match.group(0)
                if not is_allowed(matched_text):
                    findings.append((line_num, secret_type, matched_text[:50]))

    return findings

def main():
    """Main function to scan the repository"""
    print("🔍 Scanning for potential secrets...")

    # Get all Python and JavaScript files
    repo_root = Path.cwd()
    files_to_check = []

    for pattern in ['**/*.py', '**/*.js', '**/*.json', '**/*.yaml', '**/*.yml']:
        files_to_check.extend(repo_root.glob(pattern))

    # Also check root level dot files
    for file in repo_root.glob('.*'):
        if file.is_file() and file.name not in {'.DS_Store', '.gitignore'}:
            files_to_check.append(file)

    secrets_found = False

    for file_path in files_to_check:
        if should_skip_file(file_path):
            continue

        findings = scan_file(file_path)
        if findings:
            secrets_found = True
            print(f"\n❌ Potential secrets found in {file_path.relative_to(repo_root)}:")
            for line_num, secret_type, preview in findings:
                print(f"  Line {line_num}: {secret_type} - {preview}...")

    if secrets_found:
        print("\n⚠️  Potential secrets detected! Please review and remove them.")
        print("If these are false positives, add them to the ALLOWED_PATTERNS list.")
        sys.exit(1)
    else:
        print("✅ No secrets detected")
        sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Check for hardcoded IDs and personal information in the codebase
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns to detect hardcoded values
HARDCODED_PATTERNS = [
    # Notion database IDs (32 character hex)
    (r'["\'][0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}["\']', "Database ID"),
    (r'["\'][0-9a-f]{32}["\']', "Notion Database ID"),

    # Personal paths
    (r'/Users/[a-zA-Z0-9_]+/[^"\']*["\']', "Personal file path"),
    (r'/home/[a-zA-Z0-9_]+/[^"\']*["\']', "Personal file path"),

    # API endpoints with specific domains
    (r'https://[a-zA-Z0-9\-]+\.notion\.so/[^"\']*', "Notion workspace URL"),

    # Hardcoded company names (adjust as needed)
    (r'(?i)["\'][^"\']*\b(acme|example|mycorp|testcorp)\b[^"\']*["\']', "Company-specific name"),
]

# Files to check
INCLUDE_PATTERNS = ['*.py', '*.js', '*.json', '*.yaml', '*.yml']

# Files/paths to skip
SKIP_PATTERNS = [
    'test_*.py',
    '*_test.py',
    'tests/*',
    '.env*',
    'node_modules/*',
    '.git/*',
    '__pycache__/*',
    '*.pyc',
    'check_hardcoded.py',  # Skip this file itself
]

# Known allowed patterns (won't trigger alerts)
ALLOWED_PATTERNS = [
    'your_.*_here',
    'example',
    'placeholder',
    'test',
    'dummy',
    'sample',
]

def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped"""
    for pattern in SKIP_PATTERNS:
        if file_path.match(pattern):
            return True
    return False

def is_allowed(content: str) -> bool:
    """Check if the found pattern is in the allowed list"""
    for allowed in ALLOWED_PATTERNS:
        if re.search(allowed, content, re.IGNORECASE):
            return True
    return False

def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a file for hardcoded values"""
    findings = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (UnicodeDecodeError, PermissionError):
        return findings

    for line_num, line in enumerate(lines, 1):
        for pattern, issue_type in HARDCODED_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                matched_text = match.group(0)
                if not is_allowed(matched_text):
                    # Truncate very long matches
                    preview = matched_text[:50] + '...' if len(matched_text) > 50 else matched_text
                    findings.append((line_num, issue_type, preview))

    return findings

def main():
    """Main function to scan for hardcoded values"""
    print("🔍 Scanning for hardcoded values...")

    repo_root = Path.cwd()
    files_to_check = []

    # Collect files to check
    for pattern in INCLUDE_PATTERNS:
        files_to_check.extend(repo_root.rglob(pattern))

    issues_found = False

    for file_path in files_to_check:
        if should_skip_file(file_path):
            continue

        findings = scan_file(file_path)
        if findings:
            issues_found = True
            print(f"\n❌ Hardcoded values found in {file_path.relative_to(repo_root)}:")
            for line_num, issue_type, preview in findings:
                print(f"  Line {line_num}: {issue_type} - {preview}")

    if issues_found:
        print("\n⚠️  Hardcoded values detected!")
        print("Consider moving these to environment variables or configuration files.")
        sys.exit(1)
    else:
        print("✅ No hardcoded values detected")
        sys.exit(0)

if __name__ == "__main__":
    main()
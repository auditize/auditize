#!/usr/bin/env python3

"""
Script to check for missing translation keys in fr.ts compared to en.ts.
Implemented by Cursor / Composer 1.

Usage:
    python check-missing.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Set


def normalize_ts_to_json(content: str) -> str:
    """
    Convert TypeScript object syntax to valid JSON.
    - Removes export default
    - Removes comments
    - Adds quotes to unquoted keys
    - Removes trailing commas
    - Removes trailing semicolon
    """
    # Remove export default statement
    content = re.sub(r'^export\s+default\s+', '', content, flags=re.MULTILINE)
    
    # Remove single-line comments
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Remove trailing semicolon at the end
    content = re.sub(r';\s*$', '', content, flags=re.MULTILINE)
    
    # Process character by character to add quotes to unquoted keys
    # This handles string contexts correctly
    result = []
    i = 0
    in_string = False
    string_char = None
    
    while i < len(content):
        char = content[i]
        
        # Track string boundaries (handle escaped quotes)
        if char in ('"', "'") and (i == 0 or content[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            result.append(char)
            i += 1
            continue
        
        # If we're in a string, just copy the character
        if in_string:
            result.append(char)
            i += 1
            continue
        
        # Outside strings: look for unquoted keys
        # Pattern: identifier (word chars) or numeric key followed by colon
        # Must be preceded by { or , or whitespace/newline
        if re.match(r'[a-zA-Z_$0-9]', char):
            # Potential start of unquoted key
            # Check what's before this position
            if i == 0 or content[i-1] in ('{', ',', '\n', ' ', '\t', '\r'):
                # Extract the potential key - can be identifier or number
                key_match = re.match(r'([a-zA-Z_$][a-zA-Z0-9_$]*|[0-9]+)\s*:', content[i:])
                if key_match:
                    key = key_match.group(1)
                    # Don't quote keywords (but do quote numbers)
                    if key not in ('true', 'false', 'null', 'undefined'):
                        result.append(f'"{key}":')
                        i += len(key_match.group(0))
                        continue
        
        result.append(char)
        i += 1
    
    content = ''.join(result)
    
    # Remove trailing commas before closing braces/brackets
    # This regex handles commas that are followed by whitespace and then } or ]
    content = re.sub(r',(\s*[}\]])', r'\1', content)
    
    return content.strip()


def extract_keys_from_dict(obj: Any, prefix: str = '') -> Set[str]:
    """
    Recursively extract all keys from a nested dictionary.
    Returns a set of keys in dot notation (e.g., 'navigation.management').
    """
    keys = set()
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f'{prefix}.{key}' if prefix else key
            keys.add(full_key)
            
            # Recursively extract keys from nested objects
            if isinstance(value, dict):
                keys.update(extract_keys_from_dict(value, full_key))
    
    return keys


def extract_keys_from_ts_file(file_path: Path) -> Set[str]:
    """
    Extract all nested keys from a TypeScript translation file.
    Returns a set of keys in dot notation (e.g., 'navigation.management').
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Normalize TypeScript to JSON
    json_content = normalize_ts_to_json(content)
    
    try:
        # Parse as JSON
        data = json.loads(json_content)
        
        # Extract all keys recursively
        keys = extract_keys_from_dict(data)
        
        return keys
    except json.JSONDecodeError as e:
        print(f"Error parsing {file_path} as JSON:", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print("\nNormalized content (first 500 chars):", file=sys.stderr)
        print(json_content[:500], file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to check for missing keys."""
    script_dir = Path(__file__).parent
    en_file = script_dir / 'en.ts'
    fr_file = script_dir / 'fr.ts'
    
    if not en_file.exists():
        print(f"Error: {en_file} not found", file=sys.stderr)
        sys.exit(1)
    
    if not fr_file.exists():
        print(f"Error: {fr_file} not found", file=sys.stderr)
        sys.exit(1)
    
    print("Extracting keys from en.ts (reference)...")
    en_keys = extract_keys_from_ts_file(en_file)
    print(f"Found {len(en_keys)} keys in en.ts")
    
    print("Extracting keys from fr.ts (target)...")
    fr_keys = extract_keys_from_ts_file(fr_file)
    print(f"Found {len(fr_keys)} keys in fr.ts")
    
    # Find missing keys
    missing_keys = en_keys - fr_keys
    
    # Also find extra keys in fr.ts (for informational purposes)
    extra_keys = fr_keys - en_keys
    
    if missing_keys:
        print(f"\n❌ Found {len(missing_keys)} missing key(s) in fr.ts:\n")
        for key in sorted(missing_keys):
            print(f"  - {key}")
        sys.exit(1)
    else:
        print("\n✅ All keys from en.ts are present in fr.ts!")
        
        if extra_keys:
            print(f"\n⚠️  Note: fr.ts contains {len(extra_keys)} extra key(s) not in en.ts:")
            for key in sorted(extra_keys):
                print(f"  - {key}")
        
        sys.exit(0)


if __name__ == '__main__':
    main()

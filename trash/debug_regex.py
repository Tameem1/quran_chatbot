#!/usr/bin/env python3
"""
Debug script for regex patterns
"""
import re

def test_pattern(pattern, text, pattern_name):
    print(f"\nTesting pattern: {pattern_name}")
    print(f"Text: {text}")
    print(f"Pattern: {pattern.pattern}")
    
    match = pattern.search(text)
    if match:
        print(f"✓ MATCHED!")
        print(f"  Groups: {match.groups()}")
        print(f"  Word1: '{match.group(1)}'")
        print(f"  Word2: '{match.group(2)}'")
    else:
        print("✗ NO MATCH")
    
    return match is not None

# Test cases
test_cases = [
    "ما الفرق بين القتل والذبح في القرآن؟",
    "هل هناك فرق بين الرحمة والرأفة؟",
    "الفرق بين يمشون ويسيرون في آيات الحركة",
    "ما الفرق في معنى نور وضياء؟",
]

# Test each pattern individually
patterns = [
    (re.compile(r'(?:ما\s+الفرق\s+بين\s+)([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)', re.I), "Pattern 1: ما الفرق بين X و Y"),
    (re.compile(r'(?:هل\s+هناك\s+فرق\s+بين\s+)([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)', re.I), "Pattern 2: هل هناك فرق بين X و Y"),
    (re.compile(r'(?:الفرق\s+بين\s+)([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)', re.I), "Pattern 3: الفرق بين X و Y"),
    (re.compile(r'(?:ما\s+الفرق\s+في\s+معنى\s+)([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)', re.I), "Pattern 4: ما الفرق في معنى X و Y"),
]

print("Debugging regex patterns:")
print("=" * 60)

for pattern, pattern_name in patterns:
    for test_case in test_cases:
        test_pattern(pattern, test_case, pattern_name)
        print("-" * 40) 
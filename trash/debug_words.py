#!/usr/bin/env python3
"""
Debug script to examine word boundaries in Arabic text
"""
import re

# Test text
text = "ما الفرق بين القتل والذبح في القرآن؟"
print(f"Testing text: '{text}'")

# Split by spaces to see the words
words = text.split()
print(f"Words split by space: {words}")

# Find all occurrences of و
pattern = re.compile(r'و')
matches = pattern.finditer(text)
print("Positions of 'و':")
for match in matches:
    start, end = match.span()
    print(f"  Position {start}-{end}: '{text[start:end]}'")
    # Show context around و
    context_start = max(0, start - 10)
    context_end = min(len(text), end + 10)
    print(f"    Context: '{text[context_start:context_end]}'")

# Try to find the specific pattern around و
pattern_specific = re.compile(r'([^\s]+)\s+و\s+([^\s]+)')
matches_specific = pattern_specific.finditer(text)
print("\nSpecific pattern matches:")
for match in matches_specific:
    print(f"  Match: '{match.group(1)}' و '{match.group(2)}'")
    print(f"  Full match: '{match.group(0)}'")

# Try a more flexible pattern
pattern_flexible = re.compile(r'(\S+)\s+و\s+(\S+)')
matches_flexible = pattern_flexible.finditer(text)
print("\nFlexible pattern matches:")
for match in matches_flexible:
    print(f"  Match: '{match.group(1)}' و '{match.group(2)}'")
    print(f"  Full match: '{match.group(0)}'")

# Try with Arabic-specific characters
pattern_arabic = re.compile(r'([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)')
matches_arabic = pattern_arabic.finditer(text)
print("\nArabic-specific pattern matches:")
for match in matches_arabic:
    print(f"  Match: '{match.group(1)}' و '{match.group(2)}'")
    print(f"  Full match: '{match.group(0)}'") 
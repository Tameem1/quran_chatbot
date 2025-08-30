#!/usr/bin/env python3
"""
Test script to examine characters in Arabic text
"""
import re

def examine_text(text):
    print(f"\nExamining text: '{text}'")
    print(f"Length: {len(text)}")
    print("Character codes:")
    for i, char in enumerate(text):
        print(f"  {i}: '{char}' (ord: {ord(char)})")
    
    # Test a simple pattern
    simple_pattern = re.compile(r'الفرق')
    match = simple_pattern.search(text)
    print(f"Simple 'الفرق' match: {match is not None}")
    
    # Test the word boundary
    word_pattern = re.compile(r'بين')
    match = word_pattern.search(text)
    print(f"'بين' match: {match is not None}")
    
    # Test the conjunction
    conj_pattern = re.compile(r'و')
    match = conj_pattern.search(text)
    print(f"'و' match: {match is not None}")

# Test cases
test_cases = [
    "ما الفرق بين القتل والذبح في القرآن؟",
    "هل هناك فرق بين الرحمة والرأفة؟",
    "الفرق بين يمشون ويسيرون في آيات الحركة",
    "ما الفرق في معنى نور وضياء؟",
]

print("Examining Arabic text characters:")
print("=" * 50)

for test_case in test_cases:
    examine_text(test_case)
    print("-" * 30) 
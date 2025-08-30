#!/usr/bin/env python3
"""
Test script for updated two-word extraction regex patterns
"""
import re

# Updated regex patterns
TWO_WORD_PATTERNS = [
    # ما الفرق بين X و Y
    re.compile(
        r'(?:ما\s+الفرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)',
        re.I,
    ),
    # هل هناك فرق بين X و Y
    re.compile(
        r'(?:هل\s+هناك\s+فرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)',
        re.I,
    ),
    # الفرق بين X و Y
    re.compile(
        r'(?:الفرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)',
        re.I,
    ),
    # ما الفرق في معنى X و Y
    re.compile(
        r'(?:ما\s+الفرق\s+في\s+معنى\s+)'
        r'([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)',
        re.I,
    ),
    # Generic pattern for "difference between X and Y"
    re.compile(
        r'(?:.*?فرق.*?بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s+([^\s\?\.،؟]+)',
        re.I,
    ),
]

def test_two_word_extraction():
    """Test the two-word extraction patterns"""
    
    test_cases = [
        "ما الفرق بين القتل والذبح في القرآن؟",
        "هل هناك فرق بين الرحمة والرأفة؟",
        "الفرق بين يمشون ويسيرون في آيات الحركة",
        "ما الفرق في معنى نور وضياء؟",
        "ما معنى كلمة تبّ في قوله تعالى: «تبت يدا أبي لهب»؟",  # This should NOT match
    ]
    
    print("Testing updated two-word extraction patterns:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        
        matched = False
        for j, pattern in enumerate(TWO_WORD_PATTERNS):
            match = pattern.search(test_case)
            if match:
                word1 = match.group(1)
                word2 = match.group(2)
                print(f"  ✓ Pattern {j} matched: '{word1}' و '{word2}'")
                matched = True
                break
        
        if not matched:
            print("  ✗ No pattern matched")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_two_word_extraction() 
#!/usr/bin/env python3
"""
Test script for two-word extraction patterns
"""
import re
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the regex patterns directly
from services.extractors.quranic_word_extractor import _TWO_WORD_PATTERNS

def test_two_word_extraction():
    """Test the two-word extraction patterns"""
    
    test_cases = [
        "ما الفرق بين القتل والذبح في القرآن؟",
        "هل هناك فرق بين الرحمة والرأفة؟",
        "الفرق بين يمشون ويسيرون في آيات الحركة",
        "ما الفرق في معنى نور وضياء؟",
        "ما معنى كلمة تبّ في قوله تعالى: «تبت يدا أبي لهب»؟",  # This should NOT match
    ]
    
    print("Testing two-word extraction patterns:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        
        matched = False
        for j, pattern in enumerate(_TWO_WORD_PATTERNS):
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
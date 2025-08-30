#!/usr/bin/env python3
"""
Final test script for updated two-word extraction regex patterns
"""
import re
from typing import Optional, Tuple

# Updated regex patterns with و handling
TWO_WORD_PATTERNS = [
    # ما الفرق بين X و Y (where Y might start with و)
    re.compile(
        r'(?:ما\s+الفرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # هل هناك فرق بين X و Y (where Y might start with و)
    re.compile(
        r'(?:هل\s+هناك\s+فرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # الفرق بين X و Y (where Y might start with و)
    re.compile(
        r'(?:الفرق\s+بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # ما الفرق في معنى X و Y (where Y might start with و)
    re.compile(
        r'(?:ما\s+الفرق\s+في\s+معنى\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # Generic pattern for "difference between X and Y"
    re.compile(
        r'(?:.*?فرق.*?بين\s+)'
        r'([^\s\?\.،؟]+)\s+و\s*([^\s\?\.،؟]+)',
        re.I,
    ),
    # Alternative pattern for cases where و is attached to the second word
    re.compile(
        r'(?:.*?فرق.*?بين\s+)'
        r'([^\s\?\.،؟]+)\s+و([^\s\?\.،؟]+)',
        re.I,
    ),
]

def extract_two_words_simple(text: str) -> Optional[Tuple[str, str]]:
    """Simple version of the extraction function for testing"""
    print(f"\n🔍 Extracting two words from: {text}")
    for i, p in enumerate(TWO_WORD_PATTERNS):
        m = p.search(text)
        if m:
            word1 = m.group(1)
            word2 = m.group(2)
            
            # Clean up word2 if it starts with و
            if word2.startswith('و'):
                word2 = word2[1:]  # Remove the leading و
            
            print(f"Two-word pattern {i} matched: {word1} and {word2}")
            return word1, word2
    print("No two-word pattern matched")
    return None

def test_two_word_extraction():
    """Test the two-word extraction patterns"""
    
    test_cases = [
        "ما الفرق بين القتل والذبح في القرآن؟",
        "هل هناك فرق بين الرحمة والرأفة؟",
        "الفرق بين يمشون ويسيرون في آيات الحركة",
        "ما الفرق في معنى نور وضياء؟",
        "ما معنى كلمة تبّ في قوله تعالى: «تبت يدا أبي لهب»؟",  # This should NOT match
    ]
    
    print("Testing final two-word extraction patterns:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case}")
        result = extract_two_words_simple(test_case)
        if result:
            word1, word2 = result
            print(f"  ✓ Extracted: '{word1}' و '{word2}'")
        else:
            print("  ✗ No words extracted")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_two_word_extraction() 
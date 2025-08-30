#!/usr/bin/env python3
"""
Simple test to debug regex step by step
"""
import re

# Test text
text = "ما الفرق بين القتل والذبح في القرآن؟"
print(f"Testing text: '{text}'")

# Test 1: Simple word match
pattern1 = re.compile(r'الفرق')
match1 = pattern1.search(text)
print(f"1. 'الفرق' match: {match1 is not None}")

# Test 2: Simple word match
pattern2 = re.compile(r'بين')
match2 = pattern2.search(text)
print(f"2. 'بين' match: {match2 is not None}")

# Test 3: Simple word match
pattern3 = re.compile(r'و')
match3 = pattern3.search(text)
print(f"3. 'و' match: {match3 is not None}")

# Test 4: Two words with و
pattern4 = re.compile(r'([^\s]+)\s+و\s+([^\s]+)')
match4 = pattern4.search(text)
if match4:
    print(f"4. Two words with و: '{match4.group(1)}' و '{match4.group(2)}'")
else:
    print("4. No match for two words with و")

# Test 5: More specific pattern
pattern5 = re.compile(r'بين\s+([^\s]+)\s+و\s+([^\s]+)')
match5 = pattern5.search(text)
if match5:
    print(f"5. بين + two words: '{match5.group(1)}' و '{match5.group(2)}'")
else:
    print("5. No match for بين + two words")

# Test 6: Full pattern
pattern6 = re.compile(r'الفرق\s+بين\s+([^\s]+)\s+و\s+([^\s]+)')
match6 = pattern6.search(text)
if match6:
    print(f"6. Full pattern: '{match6.group(1)}' و '{match6.group(2)}'")
else:
    print("6. No match for full pattern")

# Test 7: With question mark
pattern7 = re.compile(r'الفرق\s+بين\s+([^\s\?]+)\s+و\s+([^\s\?]+)')
match7 = pattern7.search(text)
if match7:
    print(f"7. With question mark exclusion: '{match7.group(1)}' و '{match7.group(2)}'")
else:
    print("7. No match with question mark exclusion") 